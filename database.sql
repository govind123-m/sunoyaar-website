CREATE DATABASE IF NOT EXISTS sunoyaar;
USE sunoyaar;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listeners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    specialty VARCHAR(150) NOT NULL,
    bio TEXT,
    years_experience INT DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    listener_id INT,
    session_date DATE NOT NULL,
    session_time TIME NOT NULL,
    duration_minutes INT NOT NULL,
    service_mode ENUM('online', 'offline') NOT NULL,
    status ENUM('upcoming', 'completed', 'cancelled') DEFAULT 'upcoming',
    notes VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (listener_id) REFERENCES listeners(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(100) DEFAULT 'Google Pay UPI',
    upi_transaction_id VARCHAR(100),
    status ENUM('pending', 'success', 'failed') DEFAULT 'success',
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(220) NOT NULL,
    slug VARCHAR(240) UNIQUE NOT NULL,
    excerpt VARCHAR(500),
    content LONGTEXT NOT NULL,
    author VARCHAR(120) DEFAULT 'SunoYaar Team',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    alias VARCHAR(80) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

INSERT INTO admin (username, password_hash)
SELECT 'admin', '$pbkdf2-sha256$29000$6L13LiVEaE25NwaAEMI4Jw$H4XpuBf4QxN9mm3fH1Vn6QqWi0z7Ojf9xfTwvSF7N5A'
WHERE NOT EXISTS (SELECT 1 FROM admin WHERE username='admin');

INSERT INTO listeners (name, specialty, bio, years_experience) VALUES
('Riya Sharma', 'Stress & Anxiety', 'Compassionate listener for stress and work-life burnout.', 5),
('Aman Verma', 'Relationships', 'Supportive conversations around relationships and loneliness.', 4),
('Neha Jain', 'Student Support', 'Helping students with exam pressure and confidence issues.', 6)
ON DUPLICATE KEY UPDATE name=name;

INSERT INTO blogs (title, slug, excerpt, content) VALUES
('How Talking Helps Emotional Healing', 'how-talking-helps-emotional-healing', 'Discover why safe, non-judgmental conversations reduce emotional burden.', 'When emotions stay inside, they often become heavier. Speaking to a caring listener can help you process feelings, lower stress, and regain clarity.'),
('5 Daily Habits for Mental Wellness', '5-daily-habits-for-mental-wellness', 'Simple habits to make your day calmer and more emotionally balanced.', 'Try mindful breathing, short walks, journaling, hydration, and healthy sleep. Small changes done consistently can transform your mental wellness.')
ON DUPLICATE KEY UPDATE title=VALUES(title);
