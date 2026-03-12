# SunoYaar - Full Stack Flask + MySQL Platform

SunoYaar is a production-ready emotional support platform where users can anonymously connect with listeners.

## Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Flask (Python)
- Database: MySQL

## Setup
1. Create MySQL DB/tables:
   ```bash
   mysql -u root -p < database.sql
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure env vars (optional):
   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_PORT`, `SECRET_KEY`
4. Run:
   ```bash
   python app.py
   ```

## Routes
- Public: `/`, `/about`, `/blog`, `/how-it-works`, `/contact`, `/signup`, `/login`
- User: `/dashboard`, `/chat`, `/payment/<booking_id>`
- Admin: `/admin/login`, `/admin`, `/admin/users`, `/admin/listeners`, `/admin/bookings`, `/admin/payments`, `/admin/blogs`

Default admin username: `admin` (password hash seeded in `database.sql`; set your own secure password in production).
