# =============================================================
#  HOSTEL HUB — database/queries.py
#  Reusable database query functions for all tables.
#
#  Design principles:
#    - Every function takes a 'conn' (connection) argument
#    - Returns dicts (dictionary=True cursor) for easy access
#    - Raises exceptions on failure — let caller decide how to handle
#    - Uses parameterized queries (%s) to prevent SQL injection
#    - All write operations are committed by the caller
#      (or use HostelDBConnection context manager)
# =============================================================

import bcrypt
from mysql.connector import Error


# =============================================================
# SECTION 1 — GENERIC LOW-LEVEL HELPERS
# These are the building blocks used by all specific functions.
# =============================================================

def fetch_one(conn, sql, params=None):
    """
    Runs a SELECT query and returns a single row as a dict.
    Returns None if no row found.

    Example:
        row = fetch_one(conn, "SELECT * FROM students WHERE student_id = %s", (1,))
        print(row["name"])
    """
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()   # Returns dict or None
    finally:
        cursor.close()


def fetch_all(conn, sql, params=None):
    """
    Runs a SELECT query and returns all matching rows as a list of dicts.
    Returns an empty list [] if no rows found.

    Example:
        rows = fetch_all(conn, "SELECT * FROM students WHERE department = %s", ("CSE",))
        for row in rows:
            print(row["name"])
    """
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()   # Returns list of dicts
    finally:
        cursor.close()


def execute_query(conn, sql, params=None):
    """
    Runs an INSERT, UPDATE, or DELETE query.
    Returns the number of affected rows.
    Commits the transaction.

    Example:
        rows_affected = execute_query(
            conn,
            "UPDATE complaints SET status = %s WHERE complaint_id = %s",
            ("Resolved", 5)
        )
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount   # Number of rows changed
    finally:
        cursor.close()


def insert_and_get_id(conn, sql, params=None):
    """
    Runs an INSERT query and returns the AUTO_INCREMENT ID of the new row.
    Use this when you need the ID of the just-inserted record.

    Example:
        new_id = insert_and_get_id(
            conn,
            "INSERT INTO complaints (student_id, complaint_text, ...) VALUES (%s, %s, ...)",
            (1, "Fan not working", ...)
        )
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid   # ID of the newly inserted row
    finally:
        cursor.close()


# =============================================================
# SECTION 2 — WARDEN QUERIES
# =============================================================

def get_warden_by_id(conn, warden_id):
    """Fetch a single warden record by warden_id (used for login)."""
    return fetch_one(
        conn,
        "SELECT * FROM wardens WHERE warden_id = %s",
        (warden_id,)
    )


def get_warden_by_email(conn, email):
    """Fetch a warden by email (alternative login)."""
    return fetch_one(
        conn,
        "SELECT * FROM wardens WHERE email = %s",
        (email,)
    )


def get_all_wardens(conn):
    """Return all wardens (for admin/overview)."""
    return fetch_all(conn, "SELECT warden_id, name, hostel_block, phone, email FROM wardens")


# =============================================================
# SECTION 3 — STUDENT QUERIES
# =============================================================

def get_student_by_register(conn, register_number):
    """
    Fetch a student by register number (used for student login).
    Returns full row including password hash.
    """
    return fetch_one(
        conn,
        "SELECT * FROM students WHERE register_number = %s",
        (register_number,)
    )


def get_student_by_id(conn, student_id):
    """Fetch a student with their room info (joined view)."""
    return fetch_one(
        conn,
        "SELECT * FROM v_student_profile WHERE student_id = %s",
        (student_id,)
    )


def get_all_students(conn):
    """Return all students with room info for the warden dashboard."""
    return fetch_all(
        conn,
        """
        SELECT
            s.student_id,
            s.name,
            s.register_number,
            s.department,
            s.year,
            s.room_no,
            r.block,
            s.phone,
            s.email,
            s.gender,
            s.food_preference
        FROM students s
        LEFT JOIN rooms r ON s.room_no = r.room_no
        ORDER BY s.department, s.year, s.name
        """
    )


def search_students(conn, keyword):
    """
    Search students by name, register number, or department.
    Uses LIKE for partial matching.
    """
    pattern = f"%{keyword}%"
    return fetch_all(
        conn,
        """
        SELECT student_id, name, register_number, department, year, room_no, phone, email
        FROM students
        WHERE name            LIKE %s
           OR register_number LIKE %s
           OR department      LIKE %s
        ORDER BY name
        """,
        (pattern, pattern, pattern)
    )


def add_student(conn, name, register_number, department, year,
                room_no, phone, email, hashed_password, gender, food_preference, address):
    """
    Insert a new student record.
    Password must already be hashed before calling this function.
    Returns the new student_id.
    """
    return insert_and_get_id(
        conn,
        """
        INSERT INTO students
            (name, register_number, department, year, room_no,
             phone, email, password, gender, food_preference, address)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (name, register_number, department, year, room_no,
         phone, email, hashed_password, gender, food_preference, address)
    )


def update_student(conn, student_id, name, phone, email, department, year, food_preference, address):
    """Update editable student fields (not password, not register number)."""
    return execute_query(
        conn,
        """
        UPDATE students
        SET name = %s, phone = %s, email = %s,
            department = %s, year = %s,
            food_preference = %s, address = %s
        WHERE student_id = %s
        """,
        (name, phone, email, department, year, food_preference, address, student_id)
    )


def delete_student(conn, student_id):
    """
    Delete a student record.
    Related complaints, leaves, attendance cascade-delete automatically
    (defined in schema with ON DELETE CASCADE).
    """
    return execute_query(
        conn,
        "DELETE FROM students WHERE student_id = %s",
        (student_id,)
    )


def update_student_password(conn, student_id, hashed_password):
    """Update a student's bcrypt-hashed password."""
    return execute_query(
        conn,
        "UPDATE students SET password = %s WHERE student_id = %s",
        (hashed_password, student_id)
    )


def get_students_by_dept_year(conn, department, year):
    """
    Get students filtered by department and year.
    Used by the AI room suggestion module to find compatible roommates.
    """
    return fetch_all(
        conn,
        """
        SELECT student_id, name, register_number, room_no, food_preference
        FROM students
        WHERE department = %s AND year = %s
        ORDER BY name
        """,
        (department, year)
    )


def get_student_count(conn):
    """Return total number of students (warden dashboard KPI)."""
    result = fetch_one(conn, "SELECT COUNT(*) AS total FROM students")
    return result["total"] if result else 0


# =============================================================
# SECTION 4 — ROOM QUERIES
# =============================================================

def get_all_rooms(conn):
    """Return all rooms with computed available_beds (uses the view)."""
    return fetch_all(conn, "SELECT * FROM v_room_summary ORDER BY block, room_no")


def get_room_by_no(conn, room_no):
    """Fetch a single room by room number."""
    return fetch_one(
        conn,
        "SELECT * FROM v_room_summary WHERE room_no = %s",
        (room_no,)
    )


def get_available_rooms(conn):
    """Return rooms that still have at least 1 free bed."""
    return fetch_all(
        conn,
        """
        SELECT room_no, block, floor, capacity, occupied,
               (capacity - occupied) AS available_beds, room_type, ac_available
        FROM rooms
        WHERE occupied < capacity
        ORDER BY block, room_no
        """
    )


def get_roommates(conn, room_no, student_id):
    """
    Return other students in the same room (excluding the querying student).
    Used in the student dashboard → Room Details section.
    """
    return fetch_all(
        conn,
        """
        SELECT student_id, name, register_number, department, year, phone
        FROM students
        WHERE room_no = %s AND student_id != %s
        """,
        (room_no, student_id)
    )


def allocate_room(conn, student_id, room_no):
    """
    Assign a room to a student and increment the room's occupied count.
    Uses two queries wrapped in a transaction (commit happens together).
    """
    # Step 1: Update student's room
    execute_query(
        conn,
        "UPDATE students SET room_no = %s WHERE student_id = %s",
        (room_no, student_id)
    )
    # Step 2: Increment room occupancy
    execute_query(
        conn,
        "UPDATE rooms SET occupied = occupied + 1 WHERE room_no = %s",
        (room_no,)
    )


def deallocate_room(conn, student_id, room_no):
    """
    Remove a student from their room and decrement occupancy.
    Called when a student is transferred or deleted.
    """
    execute_query(
        conn,
        "UPDATE students SET room_no = NULL WHERE student_id = %s",
        (student_id,)
    )
    execute_query(
        conn,
        "UPDATE rooms SET occupied = GREATEST(occupied - 1, 0) WHERE room_no = %s",
        (room_no,)
    )


def get_room_occupancy_stats(conn):
    """
    Return counts of Vacant, Partial, and Full rooms.
    Used in warden dashboard pie chart.
    """
    return fetch_all(
        conn,
        """
        SELECT occupancy_status, COUNT(*) AS count
        FROM v_room_summary
        GROUP BY occupancy_status
        """
    )


# =============================================================
# SECTION 5 — COMPLAINT QUERIES
# =============================================================

def add_complaint(conn, student_id, complaint_text, category, priority, filed_date):
    """Insert a new complaint. Category and priority are AI-detected before calling."""
    return insert_and_get_id(
        conn,
        """
        INSERT INTO complaints
            (student_id, complaint_text, category, priority, status, filed_date)
        VALUES
            (%s, %s, %s, %s, 'Pending', %s)
        """,
        (student_id, complaint_text, category, priority, filed_date)
    )


def get_complaints_by_student(conn, student_id):
    """Return all complaints filed by a specific student (newest first)."""
    return fetch_all(
        conn,
        """
        SELECT complaint_id, complaint_text, category, priority,
               status, warden_remarks, filed_date, resolved_date
        FROM complaints
        WHERE student_id = %s
        ORDER BY filed_date DESC
        """,
        (student_id,)
    )


def get_all_complaints(conn):
    """
    Return ALL complaints (including Resolved) with student name,
    room info, and warden_remarks for the warden portal.
    Ordered by priority (Emergency first) then filed_date.
    NOTE: Does NOT use v_pending_complaints because that view
    excludes Resolved complaints.
    """
    return fetch_all(
        conn,
        """
        SELECT
            c.complaint_id,
            s.name          AS student_name,
            s.register_number,
            s.room_no,
            c.complaint_text,
            c.category,
            c.priority,
            c.status,
            c.warden_remarks,
            c.filed_date,
            c.resolved_date
        FROM complaints c
        JOIN students s ON c.student_id = s.student_id
        ORDER BY
            FIELD(c.priority, 'Emergency', 'Urgent', 'Normal'),
            c.filed_date ASC
        """
    )


def get_complaints_filtered(conn, status=None, priority=None, category=None):
    """
    Return complaints filtered by any combination of status/priority/category.
    None values are treated as 'any' (no filter applied for that column).
    """
    conditions = ["1=1"]   # Always-true base condition
    params = []

    if status:
        conditions.append("c.status = %s")
        params.append(status)
    if priority:
        conditions.append("c.priority = %s")
        params.append(priority)
    if category:
        conditions.append("c.category = %s")
        params.append(category)

    where_clause = " AND ".join(conditions)

    return fetch_all(
        conn,
        f"""
        SELECT
            c.complaint_id, s.name AS student_name,
            s.register_number, s.room_no,
            c.complaint_text, c.category, c.priority,
            c.status, c.warden_remarks, c.filed_date
        FROM complaints c
        JOIN students s ON c.student_id = s.student_id
        WHERE {where_clause}
        ORDER BY FIELD(c.priority, 'Emergency', 'Urgent', 'Normal'), c.filed_date
        """,
        tuple(params)
    )


def update_complaint_status(conn, complaint_id, new_status, remarks=None):
    """
    Warden updates complaint status and optionally adds remarks.
    If marking as Resolved, also sets resolved_date to today.
    """
    if new_status == "Resolved":
        return execute_query(
            conn,
            """
            UPDATE complaints
            SET status = %s, warden_remarks = %s, resolved_date = CURDATE()
            WHERE complaint_id = %s
            """,
            (new_status, remarks, complaint_id)
        )
    else:
        return execute_query(
            conn,
            """
            UPDATE complaints
            SET status = %s, warden_remarks = %s
            WHERE complaint_id = %s
            """,
            (new_status, remarks, complaint_id)
        )


def get_complaint_summary(conn):
    """
    Return counts grouped by status.
    Used in warden dashboard bar chart.
    """
    return fetch_all(
        conn,
        "SELECT status, COUNT(*) AS count FROM complaints GROUP BY status"
    )


def get_emergency_complaints(conn):
    """Return unresolved Emergency-priority complaints (warden alert widget)."""
    return fetch_all(
        conn,
        """
        SELECT c.complaint_id, s.name, s.room_no, c.complaint_text, c.filed_date
        FROM complaints c
        JOIN students s ON c.student_id = s.student_id
        WHERE c.priority = 'Emergency' AND c.status != 'Resolved'
        ORDER BY c.filed_date
        """
    )


# =============================================================
# SECTION 6 — LEAVE REQUEST QUERIES
# =============================================================

def apply_leave(conn, student_id, reason, from_date, to_date):
    """Student submits a leave request. Status defaults to 'Pending'."""
    return insert_and_get_id(
        conn,
        """
        INSERT INTO leave_requests (student_id, reason, from_date, to_date, status)
        VALUES (%s, %s, %s, %s, 'Pending')
        """,
        (student_id, reason, from_date, to_date)
    )


def get_leaves_by_student(conn, student_id):
    """Return all leave requests for a student (newest first)."""
    return fetch_all(
        conn,
        """
        SELECT leave_id, reason, from_date, to_date,
               status, warden_remarks, applied_on
        FROM leave_requests
        WHERE student_id = %s
        ORDER BY applied_on DESC
        """,
        (student_id,)
    )


def get_all_leaves(conn):
    """
    Return all leave requests with student info for warden dashboard.
    Pending requests appear first.
    """
    return fetch_all(
        conn,
        """
        SELECT
            lr.leave_id, s.name AS student_name,
            s.register_number, s.department, s.room_no,
            lr.reason, lr.from_date, lr.to_date,
            lr.status, lr.warden_remarks, lr.applied_on
        FROM leave_requests lr
        JOIN students s ON lr.student_id = s.student_id
        ORDER BY
            FIELD(lr.status, 'Pending', 'Approved', 'Rejected'),
            lr.applied_on DESC
        """
    )


def update_leave_status(conn, leave_id, new_status, remarks=None):
    """Warden approves or rejects a leave request."""
    return execute_query(
        conn,
        "UPDATE leave_requests SET status = %s, warden_remarks = %s WHERE leave_id = %s",
        (new_status, remarks, leave_id)
    )


def get_approved_leaves_on_date(conn, target_date):
    """
    Return students who have approved leave on a specific date.
    Used by the AI mess attendance predictor.
    """
    return fetch_all(
        conn,
        """
        SELECT s.student_id, s.name
        FROM leave_requests lr
        JOIN students s ON lr.student_id = s.student_id
        WHERE lr.status = 'Approved'
          AND %s BETWEEN lr.from_date AND lr.to_date
        """,
        (target_date,)
    )


def get_pending_leave_count(conn):
    """Count of pending leave requests (warden dashboard KPI)."""
    result = fetch_one(
        conn,
        "SELECT COUNT(*) AS total FROM leave_requests WHERE status = 'Pending'"
    )
    return result["total"] if result else 0


# =============================================================
# SECTION 7 — ATTENDANCE QUERIES
# =============================================================

def mark_attendance(conn, student_id, att_date, status, marked_by):
    """
    Mark or update attendance for a student on a given date.
    Uses INSERT ... ON DUPLICATE KEY UPDATE to handle re-marking.
    """
    return execute_query(
        conn,
        """
        INSERT INTO attendance (student_id, att_date, status, marked_by)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE status = VALUES(status), marked_by = VALUES(marked_by)
        """,
        (student_id, att_date, status, marked_by)
    )


def get_attendance_by_student(conn, student_id):
    """Return full attendance history for a student (newest first)."""
    return fetch_all(
        conn,
        """
        SELECT att_date, status, marked_by, remarks
        FROM attendance
        WHERE student_id = %s
        ORDER BY att_date DESC
        """,
        (student_id,)
    )


def get_attendance_percentage(conn, student_id):
    """
    Calculate attendance percentage for a student.
    Returns a float (e.g. 85.71).
    """
    result = fetch_one(
        conn,
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present_days
        FROM attendance
        WHERE student_id = %s
        """,
        (student_id,)
    )
    if result and result["total"] > 0:
        return round((result["present_days"] / result["total"]) * 100, 2)
    return 0.0


def get_attendance_by_date(conn, att_date):
    """Return all student attendance records for a specific date (warden view)."""
    return fetch_all(
        conn,
        """
        SELECT s.name, s.register_number, s.room_no,
               a.status, a.marked_by
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.att_date = %s
        ORDER BY s.department, s.name
        """,
        (att_date,)
    )


# =============================================================
# SECTION 8 — ANNOUNCEMENT QUERIES
# =============================================================

def post_announcement(conn, title, description, ann_type, posted_by):
    """Warden posts a new announcement."""
    return insert_and_get_id(
        conn,
        """
        INSERT INTO announcements (title, description, ann_type, posted_by)
        VALUES (%s, %s, %s, %s)
        """,
        (title, description, ann_type, posted_by)
    )


def get_active_announcements(conn):
    """Return all active announcements (newest first) for students."""
    return fetch_all(
        conn,
        """
        SELECT announcement_id, title, description, ann_type, posted_date
        FROM announcements
        WHERE is_active = TRUE
        ORDER BY posted_date DESC
        """
    )


def get_announcements_by_type(conn, ann_type):
    """Return announcements of a specific type (e.g., 'Emergency')."""
    return fetch_all(
        conn,
        """
        SELECT announcement_id, title, description, ann_type, posted_date
        FROM announcements
        WHERE ann_type = %s AND is_active = TRUE
        ORDER BY posted_date DESC
        """,
        (ann_type,)
    )


def deactivate_announcement(conn, announcement_id):
    """Soft-delete: mark announcement as inactive instead of deleting."""
    return execute_query(
        conn,
        "UPDATE announcements SET is_active = FALSE WHERE announcement_id = %s",
        (announcement_id,)
    )


# =============================================================
# SECTION 9 — MESS MENU QUERIES
# =============================================================

def get_menu_by_date(conn, menu_date):
    """Return the mess menu for a specific date."""
    return fetch_one(
        conn,
        "SELECT * FROM mess_menu WHERE menu_date = %s",
        (menu_date,)
    )


def get_recent_menus(conn, days=7):
    """Return the last N days of menus (for student mess section)."""
    return fetch_all(
        conn,
        """
        SELECT * FROM mess_menu
        ORDER BY menu_date DESC
        LIMIT %s
        """,
        (days,)
    )


def upsert_menu(conn, menu_date, breakfast, lunch, snacks, dinner):
    """
    Insert today's menu or update it if it already exists.
    Uses INSERT ... ON DUPLICATE KEY UPDATE.
    """
    return execute_query(
        conn,
        """
        INSERT INTO mess_menu (menu_date, breakfast, lunch, snacks, dinner)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            breakfast = VALUES(breakfast),
            lunch     = VALUES(lunch),
            snacks    = VALUES(snacks),
            dinner    = VALUES(dinner)
        """,
        (menu_date, breakfast, lunch, snacks, dinner)
    )


# =============================================================
# SECTION 10 — MEAL ATTENDANCE QUERIES
# =============================================================

def mark_meal_attendance(conn, student_id, meal_date, meal_type, attended):
    """
    Mark or update meal attendance.
    Uses INSERT ... ON DUPLICATE KEY UPDATE.
    """
    return execute_query(
        conn,
        """
        INSERT INTO meal_attendance (student_id, meal_date, meal_type, attended)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE attended = VALUES(attended)
        """,
        (student_id, meal_date, meal_type, attended)
    )


def get_meal_history_by_student(conn, student_id, days=7):
    """Return a student's meal attendance for the last N days."""
    return fetch_all(
        conn,
        """
        SELECT meal_date, meal_type, attended
        FROM meal_attendance
        WHERE student_id = %s
        ORDER BY meal_date DESC, FIELD(meal_type, 'Breakfast', 'Lunch', 'Snacks', 'Dinner')
        LIMIT %s
        """,
        (student_id, days * 4)   # 4 meals per day
    )


def get_meal_attendance_counts(conn, meal_date):
    """
    Return attendance counts for all 4 meals on a given date.
    Used in warden dashboard and AI predictor training.
    """
    return fetch_all(
        conn,
        """
        SELECT meal_type, COUNT(*) AS attended_count
        FROM meal_attendance
        WHERE meal_date = %s AND attended = TRUE
        GROUP BY meal_type
        ORDER BY FIELD(meal_type, 'Breakfast', 'Lunch', 'Snacks', 'Dinner')
        """,
        (meal_date,)
    )


def get_historical_meal_counts(conn, days=30):
    """
    Return daily meal attendance counts for the past N days.
    Used to train the AI mess attendance predictor.
    Returns rows: (meal_date, meal_type, attended_count, day_of_week)
    """
    return fetch_all(
        conn,
        """
        SELECT
            meal_date,
            meal_type,
            COUNT(*) AS attended_count,
            DAYOFWEEK(meal_date) AS day_of_week
        FROM meal_attendance
        WHERE meal_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
          AND attended = TRUE
        GROUP BY meal_date, meal_type
        ORDER BY meal_date, meal_type
        """,
        (days,)
    )


# =============================================================
# SECTION 11 — FOOD FEEDBACK QUERIES
# =============================================================

def add_food_feedback(conn, student_id, feedback_text, sentiment, rating, meal_type, feedback_date):
    """Insert a food feedback record with AI-detected sentiment."""
    return insert_and_get_id(
        conn,
        """
        INSERT INTO food_feedback
            (student_id, feedback_text, sentiment, rating, meal_type, feedback_date)
        VALUES
            (%s, %s, %s, %s, %s, %s)
        """,
        (student_id, feedback_text, sentiment, rating, meal_type, feedback_date)
    )


def get_feedback_by_student(conn, student_id):
    """Return a student's own feedback history (newest first)."""
    return fetch_all(
        conn,
        """
        SELECT feedback_id, feedback_text, sentiment, rating, meal_type, feedback_date
        FROM food_feedback
        WHERE student_id = %s
        ORDER BY feedback_date DESC
        """,
        (student_id,)
    )


def get_all_feedback(conn):
    """
    Return all feedback with student name.
    Used by warden to monitor food quality.
    """
    return fetch_all(
        conn,
        """
        SELECT
            f.feedback_id, s.name AS student_name,
            f.feedback_text, f.sentiment, f.rating,
            f.meal_type, f.feedback_date
        FROM food_feedback f
        JOIN students s ON f.student_id = s.student_id
        ORDER BY f.feedback_date DESC
        """
    )


def get_sentiment_summary(conn):
    """
    Return counts of Positive, Neutral, and Negative feedback.
    Used in warden dashboard sentiment pie chart.
    """
    return fetch_all(
        conn,
        "SELECT sentiment, COUNT(*) AS count FROM food_feedback GROUP BY sentiment"
    )


def get_average_rating(conn):
    """Return the average food rating across all feedback."""
    result = fetch_one(conn, "SELECT ROUND(AVG(rating), 2) AS avg_rating FROM food_feedback")
    return result["avg_rating"] if result and result["avg_rating"] else 0.0



def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def register_student(
    conn,
    full_name,
    register_number,
    department,
    year,
    phone,
    email,
    gender,
    password
):
    """
    Self-registration for a new student from the login page.
    Hashes the password with bcrypt before storing.
    Returns {"success": True} or {"success": False, "message": "..."}.
    """
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT student_id FROM students WHERE register_number=%s",
            (register_number.strip().upper(),)
        )
        existing = cursor.fetchone()
        if existing:
            return {"success": False, "message": "Register number already exists."}

        hashed = hash_password(password)

        cursor.execute(
            """
            INSERT INTO students
                (name, register_number, department, year, phone, email, gender, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                full_name.strip(),
                register_number.strip().upper(),
                department,
                year,
                phone.strip(),
                email.strip().lower(),
                gender,
                hashed,
            )
        )
        conn.commit()
        return {"success": True}

    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Registration failed: {str(e)}"}
    finally:
        cursor.close()


def register_warden(
    conn,
    full_name,
    warden_id,
    phone,
    email,
    gender,
    hostel_block,
    password
):
    """
    Self-registration for a new warden from the login page.
    hostel_block is required (NOT NULL, CHECK in schema).
    Hashes the password with bcrypt before storing.
    Returns {"success": True} or {"success": False, "message": "..."}.
    """
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT warden_id FROM wardens WHERE warden_id=%s",
            (warden_id.strip().upper(),)
        )
        existing = cursor.fetchone()
        if existing:
            return {"success": False, "message": "Warden ID already exists."}

        hashed = hash_password(password)

        cursor.execute(
            """
            INSERT INTO wardens
                (name, warden_id, phone, email, gender, hostel_block, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                full_name.strip(),
                warden_id.strip().upper(),
                phone.strip(),
                email.strip().lower(),
                gender,
                hostel_block,
                hashed,
            )
        )
        conn.commit()
        return {"success": True}

    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Registration failed: {str(e)}"}
    finally:
        cursor.close()