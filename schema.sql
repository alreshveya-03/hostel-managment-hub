-- ============================================================
--  HOSTEL HUB DATABASE SCHEMA
-- ============================================================
CREATE DATABASE IF NOT EXISTS hostel_hub;
USE hostel_hub;

-- Wardens
CREATE TABLE IF NOT EXISTS wardens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    hostel_block VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rooms
CREATE TABLE IF NOT EXISTS rooms (
    room_no VARCHAR(10) PRIMARY KEY,
    block VARCHAR(10) NOT NULL,
    floor INT NOT NULL DEFAULT 1,
    capacity INT NOT NULL DEFAULT 3,
    occupied INT NOT NULL DEFAULT 0,
    room_type VARCHAR(20) NOT NULL DEFAULT 'Standard',
    ac_available TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_room_block CHECK (block IN ('Block A', 'Block B', 'Block C')),
    CONSTRAINT chk_room_capacity CHECK (capacity > 0),
    CONSTRAINT chk_room_occupied CHECK (occupied <= capacity AND occupied >= 0),
    CONSTRAINT chk_room_type CHECK (room_type IN ('Standard', 'Premium', 'Deluxe'))
);

-- Students
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    reg_number VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    department VARCHAR(80),
    year INT DEFAULT 1,
    room_id INT,
    gender VARCHAR(10),
    address TEXT,
    guardian_name VARCHAR(100),
    guardian_phone VARCHAR(15),
    profile_photo VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
);

-- Complaints
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(30) DEFAULT 'pending',
    ai_priority VARCHAR(20),
    ai_category VARCHAR(50),
    warden_response TEXT,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Leave Requests
CREATE TABLE IF NOT EXISTS leave_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    reason TEXT NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    destination VARCHAR(200),
    contact_during_leave VARCHAR(15),
    status VARCHAR(20) DEFAULT 'pending',
    warden_remarks TEXT,
    approved_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES wardens(id) ON DELETE SET NULL
);

-- Attendance
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'present',
    marked_by INT,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_attendance (student_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES wardens(id) ON DELETE SET NULL
);

-- Mess Menu
CREATE TABLE IF NOT EXISTS mess_menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    day_of_week VARCHAR(15) NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    items TEXT NOT NULL,
    calories INT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_menu (day_of_week, meal_type)
);

-- Meal Attendance
CREATE TABLE IF NOT EXISTS meal_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    meal_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'present',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_meal (student_id, date, meal_type),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Food Feedback
CREATE TABLE IF NOT EXISTS food_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    meal_type VARCHAR(20),
    rating INT DEFAULT 3,
    feedback_text TEXT,
    sentiment VARCHAR(20),
    sentiment_score FLOAT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Announcements
CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warden_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    target_audience VARCHAR(30) DEFAULT 'all',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warden_id) REFERENCES wardens(id) ON DELETE CASCADE
);

-- Emergency Records
CREATE TABLE IF NOT EXISTS emergency_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reported_by INT,
    student_id INT,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    location VARCHAR(100),
    status VARCHAR(30) DEFAULT 'active',
    resolved_at TIMESTAMP NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reported_by) REFERENCES wardens(id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
);

-- AI Prediction Logs
CREATE TABLE IF NOT EXISTS ai_prediction_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module VARCHAR(50) NOT NULL,
    input_data TEXT,
    prediction VARCHAR(100),
    confidence FLOAT,
    reference_id INT,
    reference_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
--  VIEWS
-- ============================================================
CREATE OR REPLACE VIEW student_details AS
SELECT s.id, s.name, s.reg_number, s.email, s.phone, s.department,
       s.year, s.gender, s.is_active, s.created_at,
       r.room_number, r.block, r.floor, r.room_type
FROM students s
LEFT JOIN rooms r ON s.room_id = r.id;

CREATE OR REPLACE VIEW room_occupancy AS
SELECT r.id, r.room_number, r.block, r.floor, r.capacity, r.occupied,
       (r.capacity - r.occupied) AS available,
       ROUND((r.occupied / r.capacity) * 100, 1) AS occupancy_pct
FROM rooms r WHERE r.is_active = TRUE;

CREATE OR REPLACE VIEW complaint_summary AS
SELECT c.id, c.title, c.category, c.priority, c.ai_priority, c.status,
       c.created_at, s.name AS student_name, s.reg_number,
       r.room_number, r.block
FROM complaints c
JOIN students s ON c.student_id = s.id
LEFT JOIN rooms r ON s.room_id = r.id;

CREATE OR REPLACE VIEW feedback_summary AS
SELECT f.id, f.date, f.meal_type, f.rating, f.feedback_text,
       f.sentiment, f.sentiment_score, s.name AS student_name
FROM food_feedback f
JOIN students s ON f.student_id = s.id;

-- ============================================================
--  INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_students_room ON students(room_id);
CREATE INDEX IF NOT EXISTS idx_complaints_student ON complaints(student_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_leave_status ON leave_requests(status);

-- ============================================================
--  SEED DATA
-- ============================================================
-- Default warden (password: warden123)
INSERT IGNORE INTO wardens (name, email, password, phone, hostel_block)
VALUES ('Admin Warden', 'warden@hostelhub.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMZJool12345678901234567890',
        '9876543210', 'A');

-- Rooms (Block A, B, C)
INSERT IGNORE INTO rooms (room_no, block, floor, capacity, room_type, ac_available) VALUES
('A101','Block A',1,3,'Standard',0),('A102','Block A',1,3,'Standard',0),('A103','Block A',1,3,'Standard',0),
('A201','Block A',2,3,'Standard',0),('A202','Block A',2,3,'Standard',0),('A203','Block A',2,2,'Premium',1),
('B101','Block B',1,3,'Standard',0),('B102','Block B',1,3,'Standard',0),('B103','Block B',1,3,'Standard',0),
('B201','Block B',2,3,'Standard',0),('B202','Block B',2,3,'Standard',0),('B203','Block B',2,2,'Premium',1),
('C101','Block C',1,3,'Standard',0),('C102','Block C',1,3,'Standard',0),('C103','Block C',1,3,'Standard',0),
('C201','Block C',2,3,'Standard',0),('C202','Block C',2,3,'Standard',0),('C203','Block C',2,1,'Deluxe',1);

-- Mess menu
INSERT IGNORE INTO mess_menu (day_of_week, meal_type, items, calories) VALUES
('Monday','breakfast','Idli, Sambar, Chutney, Tea',350),
('Monday','lunch','Rice, Sambar, Rajma, Papad, Curd',650),
('Monday','dinner','Chapati, Dal, Sabzi, Rice, Pickle',550),
('Tuesday','breakfast','Poha, Banana, Tea, Boiled Egg',320),
('Tuesday','lunch','Rice, Dal, Aloo Gobi, Raita',620),
('Tuesday','dinner','Paratha, Paneer Curry, Rice, Dal',600),
('Wednesday','breakfast','Dosa, Chutney, Sambar, Coffee',340),
('Wednesday','lunch','Rice, Rasam, Egg Curry, Salad',680),
('Wednesday','dinner','Chapati, Chana Dal, Mixed Veg, Rice',540),
('Thursday','breakfast','Upma, Coconut Chutney, Tea',310),
('Thursday','lunch','Rice, Sambar, Fish Curry, Papad',700),
('Thursday','dinner','Chapati, Dal Makhani, Aloo, Rice',590),
('Friday','breakfast','Bread, Egg Omelette, Butter, Tea',380),
('Friday','lunch','Pulao, Raita, Chicken Curry, Salad',750),
('Friday','dinner','Chapati, Palak Paneer, Dal, Rice',580),
('Saturday','breakfast','Pongal, Sambar, Chutney, Tea',360),
('Saturday','lunch','Biryani, Raita, Boiled Egg, Papad',800),
('Saturday','dinner','Chapati, Dal, Mixed Veg, Rice, Payasam',620),
('Sunday','breakfast','Poori, Chana Masala, Tea',420),
('Sunday','lunch','Rice, Sambar, Mutton Curry, Papad, Curd',850),
('Sunday','dinner','Chapati, Dal, Paneer, Rice, Ice Cream',640);
