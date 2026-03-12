from functools import wraps
from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector

from config import Config

app = Flask(__name__)
app.config.from_object(Config)


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(
            host=app.config["MYSQL_HOST"],
            user=app.config["MYSQL_USER"],
            password=app.config["MYSQL_PASSWORD"],
            database=app.config["MYSQL_DATABASE"],
            port=app.config["MYSQL_PORT"],
            autocommit=True,
        )
    return g.db


def query_db(query, args=None, one=False):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args or ())
    if query.strip().upper().startswith("SELECT"):
        rows = cursor.fetchall()
        cursor.close()
        return (rows[0] if rows else None) if one else rows
    last_id = cursor.lastrowid
    cursor.close()
    return last_id


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def home():
    listeners = query_db("SELECT * FROM listeners WHERE is_active=1 ORDER BY id DESC LIMIT 6")
    blogs = query_db("SELECT * FROM blogs ORDER BY created_at DESC LIMIT 3")
    stats = {
        "members": 12000,
        "sessions": 43000,
        "listeners": len(listeners) or 20,
        "rating": 4.9,
    }
    return render_template("home.html", listeners=listeners, blogs=blogs, stats=stats)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Thank you for reaching out. Our team will contact you shortly.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        existing = query_db("SELECT id FROM users WHERE email=%s", (email,), one=True)
        if existing:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))

        user_id = query_db(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, generate_password_hash(password)),
        )
        session["user_id"] = user_id
        session["user_name"] = full_name
        flash("Welcome to SunoYaar!", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        password = request.form["password"]

        user = query_db("SELECT * FROM users WHERE email=%s", (email,), one=True)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        flash("Logged in successfully.", "success")
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/book", methods=["POST"])
@login_required
def book():
    listener_id = request.form.get("listener_id") or None
    session_date = request.form["session_date"]
    session_time = request.form["session_time"]
    duration = int(request.form["duration"])
    service_mode = request.form["service_mode"]
    notes = request.form.get("notes", "")

    booking_id = query_db(
        """
        INSERT INTO bookings
        (user_id, listener_id, session_date, session_time, duration_minutes, service_mode, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (session["user_id"], listener_id, session_date, session_time, duration, service_mode, notes),
    )
    flash("Session booked! Please complete payment.", "success")
    return redirect(url_for("payment", booking_id=booking_id))


@app.route("/payment/<int:booking_id>", methods=["GET", "POST"])
@login_required
def payment(booking_id):
    booking = query_db(
        """
        SELECT b.*, l.name AS listener_name
        FROM bookings b
        LEFT JOIN listeners l ON b.listener_id=l.id
        WHERE b.id=%s AND b.user_id=%s
        """,
        (booking_id, session["user_id"]),
        one=True,
    )
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("dashboard"))

    duration = booking["duration_minutes"]
    amount = max(199, (duration // 30) * 299)

    if request.method == "POST":
        txn_id = request.form.get("upi_transaction_id", "").strip()
        payment_id = query_db(
            """
            INSERT INTO payments (booking_id, user_id, amount, upi_transaction_id, status)
            VALUES (%s, %s, %s, %s, 'success')
            """,
            (booking_id, session["user_id"], amount, txn_id),
        )
        return redirect(url_for("payment_success", payment_id=payment_id))

    return render_template("payment.html", booking=booking, amount=amount)


@app.route("/payment/success/<int:payment_id>")
@login_required
def payment_success(payment_id):
    payment = query_db(
        """
        SELECT p.*, b.session_date, b.session_time, b.duration_minutes, b.service_mode,
               l.name AS listener_name
        FROM payments p
        JOIN bookings b ON p.booking_id=b.id
        LEFT JOIN listeners l ON b.listener_id=l.id
        WHERE p.id=%s AND p.user_id=%s
        """,
        (payment_id, session["user_id"]),
        one=True,
    )
    if not payment:
        flash("Payment record not found.", "danger")
        return redirect(url_for("dashboard"))

    return render_template("payment_success.html", payment=payment)


@app.route("/dashboard")
@login_required
def dashboard():
    upcoming = query_db(
        """
        SELECT b.*, l.name AS listener_name
        FROM bookings b LEFT JOIN listeners l ON b.listener_id=l.id
        WHERE b.user_id=%s AND b.session_date >= CURDATE()
        ORDER BY b.session_date, b.session_time
        """,
        (session["user_id"],),
    )
    past = query_db(
        """
        SELECT b.*, l.name AS listener_name
        FROM bookings b LEFT JOIN listeners l ON b.listener_id=l.id
        WHERE b.user_id=%s AND b.session_date < CURDATE()
        ORDER BY b.session_date DESC, b.session_time DESC
        """,
        (session["user_id"],),
    )
    payments = query_db(
        "SELECT * FROM payments WHERE user_id=%s ORDER BY paid_at DESC",
        (session["user_id"],),
    )
    return render_template("dashboard.html", upcoming=upcoming, past=past, payments=payments)


@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        alias = request.form.get("alias", "Anonymous")[:80]
        message = request.form.get("message", "").strip()
        if message:
            query_db(
                "INSERT INTO chat_messages (user_id, alias, message) VALUES (%s, %s, %s)",
                (session["user_id"], alias, message),
            )
            return redirect(url_for("chat"))

    messages = query_db(
        "SELECT alias, message, created_at FROM chat_messages ORDER BY created_at DESC LIMIT 50"
    )
    messages.reverse()
    return render_template("chat.html", messages=messages)


@app.route("/blog")
def blog_list():
    blogs = query_db("SELECT * FROM blogs ORDER BY created_at DESC")
    return render_template("blog_list.html", blogs=blogs)


@app.route("/blog/<slug>")
def blog_detail(slug):
    blog = query_db("SELECT * FROM blogs WHERE slug=%s", (slug,), one=True)
    if not blog:
        flash("Blog post not found.", "danger")
        return redirect(url_for("blog_list"))
    return render_template("blog_detail.html", blog=blog)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        admin_user = query_db("SELECT * FROM admin WHERE username=%s", (username,), one=True)

        if not admin_user or not check_password_hash(admin_user["password_hash"], password):
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("admin_login"))

        session.clear()
        session["admin_id"] = admin_user["id"]
        session["admin_username"] = admin_user["username"]
        flash("Admin login successful.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "users": query_db("SELECT COUNT(*) AS total FROM users", one=True)["total"],
        "listeners": query_db("SELECT COUNT(*) AS total FROM listeners", one=True)["total"],
        "bookings": query_db("SELECT COUNT(*) AS total FROM bookings", one=True)["total"],
        "payments": query_db("SELECT COUNT(*) AS total FROM payments", one=True)["total"],
        "blogs": query_db("SELECT COUNT(*) AS total FROM blogs", one=True)["total"],
    }
    return render_template("admin_dashboard.html", stats=stats)


@app.route("/admin/users")
@admin_required
def admin_users():
    users = query_db("SELECT id, full_name, email, created_at FROM users ORDER BY created_at DESC")
    return render_template("admin_users.html", users=users)


@app.route("/admin/listeners", methods=["GET", "POST"])
@admin_required
def admin_listeners():
    if request.method == "POST":
        query_db(
            "INSERT INTO listeners (name, specialty, bio, years_experience) VALUES (%s, %s, %s, %s)",
            (
                request.form["name"],
                request.form["specialty"],
                request.form.get("bio", ""),
                request.form.get("years_experience", 0),
            ),
        )
        flash("Listener added.", "success")
        return redirect(url_for("admin_listeners"))

    listeners = query_db("SELECT * FROM listeners ORDER BY id DESC")
    return render_template("admin_listeners.html", listeners=listeners)


@app.route("/admin/listeners/delete/<int:listener_id>", methods=["POST"])
@admin_required
def admin_delete_listener(listener_id):
    query_db("DELETE FROM listeners WHERE id=%s", (listener_id,))
    flash("Listener deleted.", "info")
    return redirect(url_for("admin_listeners"))


@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    bookings = query_db(
        """
        SELECT b.*, u.full_name, u.email, l.name AS listener_name
        FROM bookings b
        JOIN users u ON b.user_id=u.id
        LEFT JOIN listeners l ON b.listener_id=l.id
        ORDER BY b.created_at DESC
        """
    )
    return render_template("admin_bookings.html", bookings=bookings)


@app.route("/admin/payments")
@admin_required
def admin_payments():
    payments = query_db(
        """
        SELECT p.*, u.full_name, u.email
        FROM payments p
        JOIN users u ON p.user_id=u.id
        ORDER BY p.paid_at DESC
        """
    )
    return render_template("admin_payments.html", payments=payments)


@app.route("/admin/blogs", methods=["GET", "POST"])
@admin_required
def admin_blogs():
    if request.method == "POST":
        title = request.form["title"].strip()
        slug = request.form["slug"].strip()
        excerpt = request.form.get("excerpt", "").strip()
        content = request.form.get("content", "").strip()
        author = request.form.get("author", "SunoYaar Team").strip()
        query_db(
            "INSERT INTO blogs (title, slug, excerpt, content, author) VALUES (%s, %s, %s, %s, %s)",
            (title, slug, excerpt, content, author),
        )
        flash("Blog post created.", "success")
        return redirect(url_for("admin_blogs"))

    blogs = query_db("SELECT * FROM blogs ORDER BY created_at DESC")
    return render_template("admin_blogs.html", blogs=blogs)


@app.route("/admin/blogs/delete/<int:blog_id>", methods=["POST"])
@admin_required
def admin_delete_blog(blog_id):
    query_db("DELETE FROM blogs WHERE id=%s", (blog_id,))
    flash("Blog deleted.", "info")
    return redirect(url_for("admin_blogs"))


@app.template_filter("datefmt")
def datefmt(value, fmt="%d %b %Y %I:%M %p"):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(fmt) if value else ""


if __name__ == "__main__":
    app.run(debug=True)
