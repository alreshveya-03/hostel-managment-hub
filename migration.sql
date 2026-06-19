-- ============================================================
--  HOSTEL HUB DATABASE MIGRATION REFERENCE
--  This file documents the SQL modifications representing the
--  differences between the original schema.sql and the actual
--  running MySQL database schema.
-- ============================================================

-- 1. Update Wardens table: change primary key to warden_id (VARCHAR(10))
-- ALTER TABLE wardens CHANGE id warden_id VARCHAR(10) NOT NULL;
-- ALTER TABLE wardens ADD COLUMN gender VARCHAR(10);

-- 2. Update Students table: align IDs, register number, and remove non-existent columns
-- ALTER TABLE students CHANGE id student_id INT AUTO_INCREMENT;
-- ALTER TABLE students CHANGE reg_number register_number VARCHAR(20) UNIQUE NOT NULL;
-- ALTER TABLE students CHANGE room_id room_no VARCHAR(10);
-- ALTER TABLE students ADD COLUMN food_preference VARCHAR(20) NOT NULL DEFAULT 'Veg';
-- ALTER TABLE students DROP COLUMN guardian_name;
-- ALTER TABLE students DROP COLUMN guardian_phone;
-- ALTER TABLE students DROP COLUMN profile_photo;
-- ALTER TABLE students DROP COLUMN is_active;

-- 3. Update Rooms table: primary key is room_no (VARCHAR(10))
-- ALTER TABLE rooms DROP COLUMN id;
-- ALTER TABLE rooms CHANGE room_number room_no VARCHAR(10) PRIMARY KEY;
-- ALTER TABLE rooms ADD COLUMN ac_available TINYINT(1) NOT NULL DEFAULT 0;
-- ALTER TABLE rooms DROP COLUMN room_type; -- (if applicable, but room_type is standard)
-- ALTER TABLE rooms DROP COLUMN amenities;
-- ALTER TABLE rooms DROP COLUMN is_active;

-- 4. Update Leave Requests table: align PK and columns
-- ALTER TABLE leave_requests CHANGE id leave_id INT AUTO_INCREMENT;
-- ALTER TABLE leave_requests CHANGE created_at applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
-- ALTER TABLE leave_requests DROP COLUMN contact_during_leave;
-- ALTER TABLE leave_requests DROP COLUMN destination;
-- ALTER TABLE leave_requests DROP COLUMN approved_by;

-- 5. Update Attendance table: align PK, date, and marked_by
-- ALTER TABLE attendance CHANGE id attendance_id INT AUTO_INCREMENT;
-- ALTER TABLE attendance CHANGE date att_date DATE NOT NULL;
-- ALTER TABLE attendance CHANGE marked_by marked_by VARCHAR(10);

-- 6. Update Food Feedback table: align PK and date
-- ALTER TABLE food_feedback CHANGE id feedback_id INT AUTO_INCREMENT;
-- ALTER TABLE food_feedback CHANGE date feedback_date DATE NOT NULL;
-- ALTER TABLE food_feedback DROP COLUMN sentiment_score;

-- 7. Update Announcements table: align PK, content, and date
-- ALTER TABLE announcements CHANGE id announcement_id INT AUTO_INCREMENT;
-- ALTER TABLE announcements CHANGE content description TEXT NOT NULL;
-- ALTER TABLE announcements CHANGE created_at posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
-- ALTER TABLE announcements CHANGE warden_id posted_by VARCHAR(10);
-- ALTER TABLE announcements DROP COLUMN priority;
-- ALTER TABLE announcements DROP COLUMN target_audience;
-- ALTER TABLE announcements ADD COLUMN ann_type VARCHAR(30) NOT NULL DEFAULT 'General';

-- 8. Recreate database views to align with actual view structures:
CREATE OR REPLACE VIEW v_student_profile AS
SELECT s.student_id, s.name, s.register_number, s.department, s.year, s.phone, s.email, s.gender, s.food_preference, s.room_no,
       r.block, r.floor, r.room_type
FROM students s
LEFT JOIN rooms r ON s.room_no = r.room_no;

CREATE OR REPLACE VIEW v_room_summary AS
SELECT 
    r.room_no, 
    r.block, 
    r.floor, 
    r.capacity, 
    (SELECT COUNT(*) FROM students s WHERE s.room_no = r.room_no) AS occupied, 
    (r.capacity - (SELECT COUNT(*) FROM students s WHERE s.room_no = r.room_no)) AS available_beds, 
    r.room_type, 
    r.ac_available,
    (CASE 
        WHEN (SELECT COUNT(*) FROM students s WHERE s.room_no = r.room_no) = 0 THEN 'Vacant' 
        WHEN (SELECT COUNT(*) FROM students s WHERE s.room_no = r.room_no) = r.capacity THEN 'Full' 
        ELSE 'Partial' 
     END) AS occupancy_status
FROM rooms r;

CREATE OR REPLACE VIEW v_pending_complaints AS
SELECT c.complaint_id, s.name AS student_name, s.register_number, s.room_no, c.complaint_text, c.category, c.priority, c.status, c.filed_date
FROM complaints c
JOIN students s ON c.student_id = s.student_id
WHERE c.status <> 'Resolved'
ORDER BY FIELD(c.priority, 'Emergency', 'Urgent', 'Normal'), c.filed_date;

CREATE OR REPLACE VIEW v_today_meal_count AS
SELECT meal_attendance.meal_type, COUNT(0) AS total_attended
FROM meal_attendance
WHERE meal_attendance.meal_date = CURDATE() AND meal_attendance.attended = TRUE
GROUP BY meal_attendance.meal_type;

-- 9. Create missing tables to support emergency records and prediction logging:
CREATE TABLE IF NOT EXISTS emergency_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reported_by VARCHAR(10),
    student_id INT,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    location VARCHAR(100),
    status VARCHAR(30) DEFAULT 'active',
    resolved_at TIMESTAMP NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reported_by) REFERENCES wardens(warden_id) ON DELETE SET NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL
);

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
