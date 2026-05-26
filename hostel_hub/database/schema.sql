-- =============================================================
--  HOSTEL HUB — DATABASE SCHEMA
--  Database  : hostel_hub
--  Engine    : MySQL 8.0+
--  Encoding  : utf8mb4 (supports all Unicode characters)
-- =============================================================
--  TABLE ORDER (respects FK dependencies)
--    1. wardens
--    2. rooms
--    3. students          (FK → rooms)
--    4. complaints        (FK → students)
--    5. leave_requests    (FK → students)
--    6. attendance        (FK → students)
--    7. announcements
--    8. mess_menu
--    9. meal_attendance   (FK → students, mess_menu)
--   10. food_feedback     (FK → students)
-- =============================================================

-- Drop and recreate the database cleanly
DROP DATABASE IF EXISTS hostel_hub;
CREATE DATABASE hostel_hub
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hostel_hub;

-- =============================================================
-- TABLE 1: wardens
-- Stores login credentials and details for hostel wardens.
-- Wardens manage a specific hostel block.
-- =============================================================
CREATE TABLE wardens (
    warden_id       VARCHAR(10)     NOT NULL,   -- e.g. WD001
    name            VARCHAR(100)    NOT NULL,
    hostel_block    VARCHAR(10)     NOT NULL,   -- Block A / B / C
    phone           VARCHAR(15)     NOT NULL,
    email           VARCHAR(100)    NOT NULL    UNIQUE,
    password        VARCHAR(255)    NOT NULL,   -- bcrypt hash stored here
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (warden_id),

    CONSTRAINT chk_warden_phone   CHECK (LENGTH(phone) >= 10),
    CONSTRAINT chk_warden_block   CHECK (hostel_block IN ('Block A', 'Block B', 'Block C'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 2: rooms
-- Represents physical rooms in the hostel.
-- Tracks capacity, occupancy, and availability.
-- =============================================================
CREATE TABLE rooms (
    room_no         VARCHAR(10)     NOT NULL,   -- e.g. A101, B204
    block           VARCHAR(10)     NOT NULL,
    floor           INT             NOT NULL    DEFAULT 1,
    capacity        INT             NOT NULL    DEFAULT 3,
    occupied        INT             NOT NULL    DEFAULT 0,
    room_type       VARCHAR(20)     NOT NULL    DEFAULT 'Standard',
    ac_available    BOOLEAN         NOT NULL    DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (room_no),

    -- occupied can never exceed capacity
    CONSTRAINT chk_room_occupied  CHECK (occupied <= capacity AND occupied >= 0),
    CONSTRAINT chk_room_capacity  CHECK (capacity > 0),
    CONSTRAINT chk_room_block     CHECK (block IN ('Block A', 'Block B', 'Block C')),
    CONSTRAINT chk_room_type      CHECK (room_type IN ('Standard', 'Premium', 'Deluxe'))
) ENGINE=InnoDB;

-- Computed column helper: available_beds
-- We calculate this in application code as (capacity - occupied)


-- =============================================================
-- TABLE 3: students
-- Core student table. Each student is linked to one room.
-- =============================================================
CREATE TABLE students (
    student_id      INT             NOT NULL    AUTO_INCREMENT,
    name            VARCHAR(100)    NOT NULL,
    register_number VARCHAR(20)     NOT NULL,
    department      VARCHAR(50)     NOT NULL,
    year            INT             NOT NULL,
    room_no         VARCHAR(10),                -- FK → rooms; NULL if unallocated
    phone           VARCHAR(15)     NOT NULL,
    email           VARCHAR(100)    NOT NULL,
    password        VARCHAR(255)    NOT NULL,   -- bcrypt hash
    gender          VARCHAR(10)     NOT NULL    DEFAULT 'Male',
    food_preference VARCHAR(20)     NOT NULL    DEFAULT 'Veg',
    address         TEXT,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (student_id),
    UNIQUE KEY uq_register (register_number),
    UNIQUE KEY uq_email    (email),

    FOREIGN KEY (room_no)
        REFERENCES rooms(room_no)
        ON UPDATE CASCADE
        ON DELETE SET NULL,         -- If a room is deleted, student becomes unallocated

    CONSTRAINT chk_student_year   CHECK (year BETWEEN 1 AND 5),
    CONSTRAINT chk_student_gender CHECK (gender IN ('Male', 'Female', 'Other')),
    CONSTRAINT chk_food_pref      CHECK (food_preference IN ('Veg', 'Non-Veg', 'Vegan')),
    CONSTRAINT chk_student_dept   CHECK (department IN (
        'CSE', 'AIDS', 'IT', 'ECE', 'EEE', 'MECH', 'CIVIL', 'MBA', 'MCA'
    ))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 4: complaints
-- Students file complaints about hostel issues.
-- AI auto-detects category and priority on insertion.
-- =============================================================
CREATE TABLE complaints (
    complaint_id    INT             NOT NULL    AUTO_INCREMENT,
    student_id      INT             NOT NULL,   -- FK → students
    complaint_text  TEXT            NOT NULL,
    category        VARCHAR(30)     NOT NULL    DEFAULT 'Others',
    priority        VARCHAR(20)     NOT NULL    DEFAULT 'Normal',
    status          VARCHAR(20)     NOT NULL    DEFAULT 'Pending',
    warden_remarks  TEXT,                       -- Warden's reply/notes
    filed_date      DATE            NOT NULL,
    resolved_date   DATE,                       -- NULL until resolved
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (complaint_id),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_complaint_cat  CHECK (category IN (
        'Electrical', 'Plumbing', 'Internet', 'Cleaning', 'Furniture', 'Others'
    )),
    CONSTRAINT chk_complaint_pri  CHECK (priority IN ('Normal', 'Urgent', 'Emergency')),
    CONSTRAINT chk_complaint_sts  CHECK (status IN ('Pending', 'In Progress', 'Resolved'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 5: leave_requests
-- Students apply for leave. Warden approves or rejects.
-- =============================================================
CREATE TABLE leave_requests (
    leave_id        INT             NOT NULL    AUTO_INCREMENT,
    student_id      INT             NOT NULL,   -- FK → students
    reason          TEXT            NOT NULL,
    from_date       DATE            NOT NULL,
    to_date         DATE            NOT NULL,
    status          VARCHAR(20)     NOT NULL    DEFAULT 'Pending',
    warden_remarks  TEXT,                       -- Approval/rejection note
    applied_on      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (leave_id),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    -- to_date must be on or after from_date
    CONSTRAINT chk_leave_dates CHECK (to_date >= from_date),
    CONSTRAINT chk_leave_status CHECK (status IN ('Pending', 'Approved', 'Rejected'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 6: attendance
-- Daily in/out attendance for each student.
-- Warden marks this; students can view their history.
-- =============================================================
CREATE TABLE attendance (
    attendance_id   INT             NOT NULL    AUTO_INCREMENT,
    student_id      INT             NOT NULL,   -- FK → students
    att_date        DATE            NOT NULL,
    status          VARCHAR(10)     NOT NULL    DEFAULT 'Present',
    marked_by       VARCHAR(10),                -- warden_id who marked
    remarks         VARCHAR(100),
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (attendance_id),
    -- One record per student per day
    UNIQUE KEY uq_att_student_date (student_id, att_date),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_att_status CHECK (status IN ('Present', 'Absent', 'Leave'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 7: announcements
-- Wardens post notices visible to all students.
-- Types: General, Emergency, Mess Update.
-- =============================================================
CREATE TABLE announcements (
    announcement_id INT             NOT NULL    AUTO_INCREMENT,
    title           VARCHAR(200)    NOT NULL,
    description     TEXT            NOT NULL,
    ann_type        VARCHAR(30)     NOT NULL    DEFAULT 'General',
    posted_by       VARCHAR(10),                -- warden_id (soft ref, no FK)
    is_active       BOOLEAN         NOT NULL    DEFAULT TRUE,
    posted_date     TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (announcement_id),

    CONSTRAINT chk_ann_type CHECK (ann_type IN ('General', 'Emergency', 'Mess Update', 'Holiday'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 8: mess_menu
-- Daily mess menu with 4 meal slots.
-- One record per date (UNIQUE on menu_date).
-- =============================================================
CREATE TABLE mess_menu (
    menu_id         INT             NOT NULL    AUTO_INCREMENT,
    menu_date       DATE            NOT NULL,
    breakfast       TEXT            NOT NULL,
    lunch           TEXT            NOT NULL,
    snacks          TEXT            NOT NULL,
    dinner          TEXT            NOT NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (menu_id),
    UNIQUE KEY uq_menu_date (menu_date)  -- Only one menu per day
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 9: meal_attendance
-- Tracks which students attended which meal on which date.
-- One record per student per date per meal slot.
-- =============================================================
CREATE TABLE meal_attendance (
    meal_id         INT             NOT NULL    AUTO_INCREMENT,
    student_id      INT             NOT NULL,   -- FK → students
    meal_date       DATE            NOT NULL,
    meal_type       VARCHAR(15)     NOT NULL,   -- Breakfast / Lunch / Snacks / Dinner
    attended        BOOLEAN         NOT NULL    DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (meal_id),
    -- One record per student per date per meal type
    UNIQUE KEY uq_meal_student_date (student_id, meal_date, meal_type),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_meal_type CHECK (meal_type IN ('Breakfast', 'Lunch', 'Snacks', 'Dinner'))
) ENGINE=InnoDB;


-- =============================================================
-- TABLE 10: food_feedback
-- Students submit feedback on mess food.
-- Sentiment is auto-detected by AI and stored here.
-- =============================================================
CREATE TABLE food_feedback (
    feedback_id     INT             NOT NULL    AUTO_INCREMENT,
    student_id      INT             NOT NULL,   -- FK → students
    feedback_text   TEXT            NOT NULL,
    sentiment       VARCHAR(20)     NOT NULL    DEFAULT 'Neutral',  -- AI-detected
    rating          INT             NOT NULL,   -- 1 to 5 stars
    meal_type       VARCHAR(15),                -- Which meal the feedback is for
    feedback_date   DATE            NOT NULL,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (feedback_id),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_feedback_sentiment CHECK (sentiment IN ('Positive', 'Neutral', 'Negative')),
    CONSTRAINT chk_feedback_rating    CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chk_feedback_meal      CHECK (meal_type IN ('Breakfast', 'Lunch', 'Snacks', 'Dinner'))
) ENGINE=InnoDB;


-- =============================================================
-- INDEXES for performance (on commonly queried columns)
-- =============================================================
CREATE INDEX idx_student_dept_year    ON students(department, year);
CREATE INDEX idx_student_room         ON students(room_no);
CREATE INDEX idx_complaint_student    ON complaints(student_id);
CREATE INDEX idx_complaint_status     ON complaints(status);
CREATE INDEX idx_complaint_priority   ON complaints(priority);
CREATE INDEX idx_leave_student        ON leave_requests(student_id);
CREATE INDEX idx_leave_status         ON leave_requests(status);
CREATE INDEX idx_attendance_date      ON attendance(att_date);
CREATE INDEX idx_meal_date            ON meal_attendance(meal_date);
CREATE INDEX idx_feedback_sentiment   ON food_feedback(sentiment);


-- =============================================================
-- VIEWS (optional helpers for the application layer)
-- =============================================================

-- View: Room occupancy summary (warden dashboard)
CREATE VIEW v_room_summary AS
SELECT
    r.room_no,
    r.block,
    r.floor,
    r.capacity,
    r.occupied,
    (r.capacity - r.occupied) AS available_beds,
    r.room_type,
    r.ac_available,
    CASE
        WHEN r.occupied = 0              THEN 'Vacant'
        WHEN r.occupied = r.capacity     THEN 'Full'
        ELSE                                  'Partial'
    END AS occupancy_status
FROM rooms r;


-- View: Student profile with room info (student dashboard)
CREATE VIEW v_student_profile AS
SELECT
    s.student_id,
    s.name,
    s.register_number,
    s.department,
    s.year,
    s.phone,
    s.email,
    s.gender,
    s.food_preference,
    s.room_no,
    r.block,
    r.floor,
    r.room_type
FROM students s
LEFT JOIN rooms r ON s.room_no = r.room_no;


-- View: Pending complaints (warden dashboard)
CREATE VIEW v_pending_complaints AS
SELECT
    c.complaint_id,
    s.name         AS student_name,
    s.register_number,
    s.room_no,
    c.complaint_text,
    c.category,
    c.priority,
    c.status,
    c.filed_date
FROM complaints c
JOIN students s ON c.student_id = s.student_id
WHERE c.status != 'Resolved'
ORDER BY
    FIELD(c.priority, 'Emergency', 'Urgent', 'Normal'),
    c.filed_date ASC;


-- View: Today's mess attendance count (warden dashboard)
CREATE VIEW v_today_meal_count AS
SELECT
    meal_type,
    COUNT(*) AS total_attended
FROM meal_attendance
WHERE meal_date = CURDATE()
  AND attended = TRUE
GROUP BY meal_type;
