"""routes/warden.py"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import fetch_one, fetch_all, execute_query, insert_and_get_id
from auth_utils import warden_required
from datetime import date

warden_bp = Blueprint('warden', __name__)

STATUS_MAP_TO_DB = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'resolved': 'Resolved'
}

DAY_TO_DATE = {
    'Monday': '2025-04-28',
    'Tuesday': '2025-04-29',
    'Wednesday': '2025-04-30',
    'Thursday': '2025-05-01',
    'Friday': '2025-05-02',
    'Saturday': '2025-05-03',
    'Sunday': '2025-05-04',
}

def format_complaint(c):
    if not c:
        return c
    parts = c['complaint_text'].split('\n', 1)
    c['title'] = parts[0]
    c['description'] = parts[1] if len(parts) > 1 else parts[0]
    c['id'] = c.get('complaint_id') or c.get('id')
    c['warden_response'] = c.get('warden_remarks')
    c['ai_category'] = None
    c['ai_priority'] = None
    if c.get('status'):
        c['status'] = c['status'].lower().replace(' ', '_')
    if c.get('priority'):
        c['priority'] = c['priority'].lower()
    return c

def format_leave(l):
    if not l:
        return l
    l['id'] = l['leave_id']
    l['created_at'] = l['applied_on']
    if l.get('status'):
        l['status'] = l['status'].lower()
    return l


@warden_bp.route('/dashboard')
@warden_required
def dashboard():
    total_students = fetch_one("SELECT COUNT(*) AS c FROM students")['c']
    total_rooms    = fetch_one("SELECT COUNT(*) AS c FROM v_room_summary")['c']
    occupied_rooms = fetch_one("SELECT COUNT(*) AS c FROM v_room_summary WHERE occupied>0")['c']
    vacant_rooms   = total_rooms - occupied_rooms
    pending_comp   = fetch_one("SELECT COUNT(*) AS c FROM complaints WHERE status='Pending'")['c']
    pending_leave  = fetch_one("SELECT COUNT(*) AS c FROM leave_requests WHERE status='Pending'")['c']
    today_present  = fetch_one(
        "SELECT COUNT(*) AS c FROM attendance WHERE att_date=%s AND status='Present'", (date.today(),))['c']
    avg_feedback   = fetch_one("SELECT ROUND(AVG(rating),1) AS avg FROM food_feedback WHERE feedback_date >= DATE_SUB(CURDATE(),INTERVAL 7 DAY)")
    recent_comp    = fetch_all("""
        SELECT c.complaint_id, c.complaint_text, c.category, c.priority, c.status, c.warden_remarks,
               c.created_at, s.name AS student_name, s.register_number AS reg_number,
               s.room_no AS room_number, r.block
        FROM complaints c
        JOIN students s ON c.student_id = s.student_id
        LEFT JOIN rooms r ON s.room_no = r.room_no
        ORDER BY c.created_at DESC LIMIT 5
    """)
    for rc in recent_comp:
        format_complaint(rc)
    recent_ann     = fetch_all("""
        SELECT a.announcement_id AS id, a.title, a.description AS content, a.ann_type AS priority,
               'all' AS target_audience, a.is_active, a.posted_date AS created_at, w.name AS warden_name
        FROM announcements a
        JOIN wardens w ON a.posted_by=w.warden_id
        ORDER BY a.posted_date DESC LIMIT 3
    """)
    return render_template('warden/dashboard.html',
        total_students=total_students, total_rooms=total_rooms,
        occupied_rooms=occupied_rooms, vacant_rooms=vacant_rooms,
        pending_comp=pending_comp, pending_leave=pending_leave,
        today_present=today_present,
        avg_feedback=avg_feedback['avg'] if avg_feedback and avg_feedback['avg'] is not None else 'N/A',
        recent_comp=recent_comp, recent_ann=recent_ann)


@warden_bp.route('/students')
@warden_required
def students():
    search = request.args.get('q','')
    dept   = request.args.get('dept','')
    year   = request.args.get('year','')
    q  = """
        SELECT student_id AS id, name, register_number AS reg_number, department, year, phone, email, gender,
               room_no AS room_number, block, floor, room_type
        FROM v_student_profile
        WHERE 1=1
    """
    params = []
    if search:
        q += " AND (name LIKE %s OR register_number LIKE %s OR email LIKE %s)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if dept:
        q += " AND department=%s"; params.append(dept)
    if year:
        q += " AND year=%s"; params.append(year)
    q += " ORDER BY name"
    student_list = fetch_all(q, params)
    depts = fetch_all("SELECT DISTINCT department FROM students ORDER BY department")
    return render_template('warden/students.html',
        students=student_list, search=search, dept=dept, year=year,
        departments=depts)


@warden_bp.route('/students/<int:sid>')
@warden_required
def student_detail(sid):
    student = fetch_one("""
        SELECT student_id AS id, name, register_number AS reg_number, department, year, phone, email, gender,
               room_no AS room_number, block, floor, room_type
        FROM v_student_profile
        WHERE student_id=%s
    """, (sid,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('warden.students'))
    comp  = fetch_all("SELECT * FROM complaints WHERE student_id=%s ORDER BY created_at DESC", (sid,))
    for c in comp:
        format_complaint(c)
    leave = fetch_all("SELECT * FROM leave_requests WHERE student_id=%s ORDER BY applied_on DESC", (sid,))
    for l in leave:
        format_leave(l)
    att   = fetch_all("""
        SELECT attendance_id AS id, student_id, att_date AS date, status, marked_by, remarks, created_at
        FROM attendance WHERE student_id=%s ORDER BY att_date DESC LIMIT 30
    """, (sid,))
    for a in att:
        a['status'] = a['status'].lower()
    return render_template('warden/student_detail.html',
        student=student, complaints=comp, leaves=leave, attendance=att)


@warden_bp.route('/rooms')
@warden_required
def rooms():
    rooms_list = fetch_all("""
        SELECT room_no AS room_number, block, floor, capacity, occupied, available_beds AS available,
               ROUND((occupied / capacity) * 100, 1) AS occupancy_pct, room_type, ac_available
        FROM v_room_summary
        ORDER BY block, floor, room_no
    """)
    return render_template('warden/rooms.html', rooms=rooms_list)


@warden_bp.route('/rooms/add', methods=['GET','POST'])
@warden_required
def add_room():
    if request.method == 'POST':
        f = request.form
        room_no = f['room_number'].strip()
        block = f.get('block', '').strip()
        floor_val = f.get('floor', '')
        capacity_val = f.get('capacity', '')
        room_type = f.get('room_type', 'Standard').strip()

        errors = []
        if block not in ('Block A', 'Block B', 'Block C'):
            errors.append("Invalid Block value.")
        if room_type not in ('Standard', 'Premium', 'Deluxe'):
            errors.append("Invalid Room Type value.")
        
        try:
            floor = int(floor_val)
            if floor < 1:
                errors.append("Floor must be 1 or higher.")
        except (ValueError, TypeError):
            errors.append("Floor must be a valid number.")

        try:
            capacity = int(capacity_val)
            if capacity < 1:
                errors.append("Capacity must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Capacity must be a valid number.")

        if fetch_one("SELECT room_no FROM rooms WHERE room_no=%s", (room_no,)):
            errors.append("Room number already exists.")

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            amenities_text = f.get('amenities', '').lower()
            ac_val = 1 if 'ac' in amenities_text else 0
            insert_and_get_id(
                "INSERT INTO rooms (room_no,block,floor,capacity,room_type,ac_available) VALUES (%s,%s,%s,%s,%s,%s)",
                (room_no, block, floor, capacity, room_type, ac_val))
            flash('Room added!', 'success')
            return redirect(url_for('warden.rooms'))
    return render_template('warden/add_room.html')


@warden_bp.route('/rooms/assign', methods=['POST'])
@warden_required
def assign_room():
    sid  = int(request.form['student_id'])
    r_no = request.form['room_id'].strip()
    room = fetch_one("SELECT * FROM v_room_summary WHERE room_no=%s", (r_no,))
    if not room or room['occupied'] >= room['capacity']:
        flash('Room is full or invalid.', 'danger')
        return redirect(url_for('warden.rooms'))
    old = fetch_one("SELECT room_no FROM students WHERE student_id=%s", (sid,))
    if old and old['room_no']:
        execute_query("UPDATE rooms SET occupied=GREATEST(0,occupied-1) WHERE room_no=%s", (old['room_no'],))
    execute_query("UPDATE students SET room_no=%s WHERE student_id=%s", (r_no, sid))
    execute_query("UPDATE rooms SET occupied=occupied+1 WHERE room_no=%s", (r_no,))
    flash('Room assigned!', 'success')
    return redirect(request.form.get('next') or url_for('warden.students'))


@warden_bp.route('/complaints')
@warden_required
def complaints():
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    q = """
        SELECT c.complaint_id, c.complaint_text, c.category, c.priority, c.status, c.warden_remarks,
               c.created_at, s.name AS student_name, s.register_number AS reg_number,
               s.room_no AS room_number, r.block
        FROM complaints c
        JOIN students s ON c.student_id = s.student_id
        LEFT JOIN rooms r ON s.room_no = r.room_no
        WHERE 1=1
    """
    params = []
    if status:
        q += " AND c.status=%s"; params.append(STATUS_MAP_TO_DB.get(status, status))
    if priority:
        q += " AND c.priority=%s"; params.append(priority.title())
    q += " ORDER BY c.created_at DESC"
    comp_list = fetch_all(q, params)
    for c in comp_list:
        format_complaint(c)
    return render_template('warden/complaints.html',
        complaints=comp_list, status=status, priority=priority)


@warden_bp.route('/complaints/<int:cid>/respond', methods=['POST'])
@warden_required
def respond_complaint(cid):
    resp   = request.form.get('response','')
    status = request.form.get('status','in_progress')
    db_status = STATUS_MAP_TO_DB.get(status, 'In Progress')
    resolved_date_val = date.today() if db_status == 'Resolved' else None
    execute_query(
        "UPDATE complaints SET warden_remarks=%s, status=%s, resolved_date=%s WHERE complaint_id=%s",
        (resp, db_status, resolved_date_val, cid))
    flash('Response recorded.', 'success')
    return redirect(url_for('warden.complaints'))


@warden_bp.route('/leave')
@warden_required
def leave():
    status = request.args.get('status','pending')
    db_status = STATUS_MAP_TO_DB.get(status, 'Pending')
    leaves = fetch_all(
        """SELECT lr.*, s.name AS student_name, s.register_number AS reg_number, s.phone
           FROM leave_requests lr JOIN students s ON lr.student_id=s.student_id
           WHERE lr.status=%s ORDER BY lr.applied_on DESC""", (db_status,))
    for l in leaves:
        format_leave(l)
    return render_template('warden/leave.html', leaves=leaves, status=status)


@warden_bp.route('/leave/<int:lid>/action', methods=['POST'])
@warden_required
def leave_action(lid):
    action  = request.form.get('action','reject')
    remarks = request.form.get('remarks','')
    db_status  = 'Approved' if action == 'approve' else 'Rejected'
    execute_query(
        "UPDATE leave_requests SET status=%s, warden_remarks=%s WHERE leave_id=%s",
        (db_status, remarks, lid))
    flash(f'Leave {db_status.lower()}.', 'success')
    return redirect(url_for('warden.leave'))


@warden_bp.route('/attendance', methods=['GET','POST'])
@warden_required
def attendance():
    if request.method == 'POST':
        att_date = request.form.get('date', str(date.today()))
        for key, val in request.form.items():
            if key.startswith('att_'):
                sid = int(key.split('_')[1])
                db_status = 'Present' if val == 'present' else 'Absent'
                try:
                    execute_query(
                        """INSERT INTO attendance (student_id,att_date,status,marked_by)
                           VALUES (%s,%s,%s,%s)
                           ON DUPLICATE KEY UPDATE status=%s, marked_by=%s""",
                        (sid, att_date, db_status, session['user_id'], db_status, session['user_id']))
                except Exception:
                    pass
        flash('Attendance marked!', 'success')
        return redirect(url_for('warden.attendance'))
    att_date  = request.args.get('date', str(date.today()))
    students  = fetch_all("SELECT student_id AS id, name, register_number AS reg_number FROM students ORDER BY name")
    existing  = {r['student_id']: r['status'].lower() for r in
                 fetch_all("SELECT student_id, status FROM attendance WHERE att_date=%s", (att_date,))}
    return render_template('warden/attendance.html',
        students=students, existing=existing, att_date=att_date)


@warden_bp.route('/mess', methods=['GET','POST'])
@warden_required
def mess():
    if request.method == 'POST':
        f = request.form
        target_date = DAY_TO_DATE.get(f['day'], '2025-05-02')
        col = f['meal_type'].lower()
        if col in ('breakfast', 'lunch', 'snacks', 'dinner'):
            existing = fetch_one("SELECT * FROM mess_menu WHERE menu_date=%s", (target_date,))
            if existing:
                execute_query(f"UPDATE mess_menu SET `{col}`=%s WHERE menu_date=%s", (f['items'], target_date))
            else:
                execute_query(
                    "INSERT INTO mess_menu (menu_date, breakfast, lunch, snacks, dinner) VALUES (%s, %s, %s, %s, %s)",
                    (target_date,
                     f['items'] if col == 'breakfast' else "",
                     f['items'] if col == 'lunch' else "",
                     f['items'] if col == 'snacks' else "",
                     f['items'] if col == 'dinner' else ""))
        flash('Menu updated!', 'success')
        return redirect(url_for('warden.mess'))
    db_menu = fetch_all("SELECT * FROM mess_menu")
    menu = []
    for row in db_menu:
        day = row['menu_date'].strftime('%A')
        if row.get('breakfast'):
            menu.append({'day_of_week': day, 'meal_type': 'breakfast', 'items': row['breakfast'], 'calories': None})
        if row.get('lunch'):
            menu.append({'day_of_week': day, 'meal_type': 'lunch', 'items': row['lunch'], 'calories': None})
        if row.get('dinner'):
            menu.append({'day_of_week': day, 'meal_type': 'dinner', 'items': row['dinner'], 'calories': None})
    fb = fetch_all("""
        SELECT f.feedback_id AS id, f.feedback_date AS date, f.meal_type, f.rating, f.feedback_text,
               f.sentiment, s.name AS student_name, f.created_at
        FROM food_feedback f
        JOIN students s ON f.student_id = s.student_id
        ORDER BY f.created_at DESC LIMIT 20
    """)
    for item in fb:
        if item.get('sentiment'):
            item['sentiment'] = item['sentiment'].lower()
        if item.get('meal_type'):
            item['meal_type'] = item['meal_type'].lower()
    stats_db = fetch_all("SELECT sentiment, COUNT(*) AS cnt FROM food_feedback GROUP BY sentiment")
    stats = []
    for s in stats_db:
        if s.get('sentiment'):
            stats.append({'sentiment': s['sentiment'].lower(), 'cnt': s['cnt']})
    avg_r_db = fetch_all("SELECT meal_type, ROUND(AVG(rating),1) AS avg_rating FROM food_feedback GROUP BY meal_type")
    avg_r = []
    for item in avg_r_db:
        if item.get('meal_type'):
            avg_r.append({'meal_type': item['meal_type'].lower(), 'avg_rating': item['avg_rating']})
    return render_template('warden/mess.html', menu=menu, feedbacks=fb, stats=stats, avg_ratings=avg_r)


@warden_bp.route('/announcements', methods=['GET','POST'])
@warden_required
def announcements():
    if request.method == 'POST':
        f = request.form
        insert_and_get_id(
            "INSERT INTO announcements (posted_by,title,description,ann_type) VALUES (%s,%s,%s,%s)",
            (session['user_id'], f['title'], f['content'], f.get('priority','General').title()))
        flash('Announcement posted!', 'success')
        return redirect(url_for('warden.announcements'))
    items = fetch_all("""
        SELECT a.announcement_id AS id, a.title, a.description AS content, a.ann_type AS priority,
               'all' AS target_audience, a.is_active, a.posted_date AS created_at, w.name AS warden_name
        FROM announcements a
        JOIN wardens w ON a.posted_by=w.warden_id
        ORDER BY a.posted_date DESC
    """)
    return render_template('warden/announcements.html', announcements=items)


@warden_bp.route('/announcements/<int:aid>/delete', methods=['POST'])
@warden_required
def delete_announcement(aid):
    execute_query("UPDATE announcements SET is_active=0 WHERE announcement_id=%s", (aid,))
    flash('Announcement removed.', 'success')
    return redirect(url_for('warden.announcements'))


@warden_bp.route('/ai_room')
@warden_required
def ai_room():
    students_without_room = fetch_all(
        "SELECT student_id AS id, name, register_number AS reg_number, department, year, gender FROM students WHERE room_no IS NULL ORDER BY name")
    rooms_available = fetch_all(
        "SELECT room_no AS room_number, block, floor, capacity, occupied, available_beds AS available, room_type FROM v_room_summary WHERE available_beds>0 ORDER BY block, room_no")
    return render_template('warden/ai_room.html',
        students=students_without_room, rooms=rooms_available)


@warden_bp.route('/ai_room/suggest', methods=['POST'])
@warden_required
def ai_room_suggest():
    sid = int(request.form['student_id'])
    student = fetch_one("SELECT student_id AS id, name, register_number AS reg_number, department, year, gender, room_no FROM students WHERE student_id=%s", (sid,))
    rooms = fetch_all("SELECT room_no, block, floor, capacity, occupied, available_beds AS available, room_type FROM v_room_summary WHERE available_beds>0")
    suggestions = []
    try:
        from ai_modules.room_suggest import suggest_rooms
        suggestions = suggest_rooms(student, rooms)
    except Exception:
        suggestions = rooms[:3] if rooms else []
    return jsonify({'suggestions': suggestions})


@warden_bp.route('/analytics')
@warden_required
def analytics():
    comp_by_cat  = fetch_all("SELECT category, COUNT(*) AS cnt FROM complaints GROUP BY category ORDER BY cnt DESC")
    comp_by_pri  = fetch_all("SELECT priority AS pr, COUNT(*) AS cnt FROM complaints GROUP BY pr")
    comp_by_status = fetch_all("SELECT status, COUNT(*) AS cnt FROM complaints GROUP BY status")
    att_trend = fetch_all(
        """SELECT att_date AS date, SUM(status='Present') AS present, SUM(status='Absent') AS absent
           FROM attendance WHERE att_date >= DATE_SUB(CURDATE(),INTERVAL 14 DAY)
           GROUP BY att_date ORDER BY att_date""")
    occ_block = fetch_all(
        "SELECT block, SUM(capacity) AS cap, SUM(occupied) AS occ FROM v_room_summary GROUP BY block")
    sentiment_stats_db = fetch_all("SELECT sentiment, COUNT(*) AS cnt FROM food_feedback WHERE sentiment IS NOT NULL GROUP BY sentiment")
    sentiment_stats = []
    for s in sentiment_stats_db:
        if s.get('sentiment'):
            sentiment_stats.append({'sentiment': s['sentiment'].lower(), 'cnt': s['cnt']})
    room_stats = fetch_one(
        "SELECT SUM(capacity) AS total_cap, SUM(occupied) AS total_occ FROM v_room_summary")
    try:
        from ai_modules.predictor import predict_at_risk_students, predict_complaint_trends
        at_risk    = predict_at_risk_students()
        comp_trend = predict_complaint_trends()
    except Exception:
        at_risk = comp_trend = None
    return render_template('warden/analytics.html',
        comp_by_cat=comp_by_cat, comp_by_pri=comp_by_pri,
        comp_by_status=comp_by_status, att_trend=att_trend,
        occ_block=occ_block, sentiment_stats=sentiment_stats,
        room_stats=room_stats, at_risk=at_risk, comp_trend=comp_trend)


@warden_bp.route('/emergency', methods=['GET','POST'])
@warden_required
def emergency():
    if request.method == 'POST':
        f = request.form
        insert_and_get_id(
            """INSERT INTO emergency_records
               (reported_by,student_id,type,description,severity,location)
               VALUES (%s,%s,%s,%s,%s,%s)""",
            (session['user_id'],
             int(f['student_id']) if f.get('student_id') else None,
             f['type'], f['description'],
             f.get('severity','medium'), f.get('location','')))
        flash('Emergency recorded and alerts sent!', 'danger')
        return redirect(url_for('warden.emergency'))
    records = fetch_all(
        """SELECT e.*, s.name AS student_name, w.name AS warden_name
           FROM emergency_records e
           LEFT JOIN students s ON e.student_id=s.student_id
           LEFT JOIN wardens w ON e.reported_by=w.warden_id
           ORDER BY e.created_at DESC""")
    students = fetch_all("SELECT student_id AS id, name, register_number AS reg_number FROM students ORDER BY name")
    return render_template('warden/emergency.html', records=records, students=students)


@warden_bp.route('/emergency/<int:eid>/resolve', methods=['POST'])
@warden_required
def resolve_emergency(eid):
    notes = request.form.get('notes','')
    execute_query(
        "UPDATE emergency_records SET status='resolved', resolved_at=NOW(), resolution_notes=%s WHERE id=%s",
        (notes, eid))
    flash('Emergency resolved.', 'success')
    return redirect(url_for('warden.emergency'))


@warden_bp.route('/rooms/<room_no>')
@warden_required
def room_detail(room_no):
    room = fetch_one("""
        SELECT room_no AS room_number, block, floor, capacity, occupied, available_beds AS available, room_type, ac_available
        FROM v_room_summary
        WHERE room_no=%s
    """, (room_no,))
    if not room:
        flash('Room not found.', 'danger')
        return redirect(url_for('warden.rooms'))
    
    occupants = fetch_all("""
        SELECT student_id AS id, name, register_number AS reg_number, department, year, phone, email
        FROM students
        WHERE room_no=%s
        ORDER BY name
    """, (room_no,))
    
    unassigned = fetch_all("""
        SELECT student_id AS id, name, register_number AS reg_number, department, year
        FROM students
        WHERE room_no IS NULL
        ORDER BY name
    """)
    
    return render_template('warden/room_detail.html', room=room, occupants=occupants, unassigned=unassigned)


@warden_bp.route('/rooms/unassign/<int:sid>', methods=['POST'])
@warden_required
def unassign_room(sid):
    student = fetch_one("SELECT room_no FROM students WHERE student_id=%s", (sid,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('warden.rooms'))
    
    r_no = student['room_no']
    if r_no:
        execute_query("UPDATE students SET room_no=NULL WHERE student_id=%s", (sid,))
        execute_query("UPDATE rooms SET occupied=GREATEST(0, occupied-1) WHERE room_no=%s", (r_no,))
        flash('Student unassigned from room.', 'success')
        return redirect(url_for('warden.room_detail', room_no=r_no))
    
    flash('Student does not have an assigned room.', 'warning')
    return redirect(url_for('warden.rooms'))


@warden_bp.route('/students/<int:sid>/delete', methods=['POST'])
@warden_required
def delete_student(sid):
    student = fetch_one("SELECT name, room_no FROM students WHERE student_id=%s", (sid,))
    if not student:
        flash('Student not found.', 'danger')
        print(f"[Delete Student] Error: Student not found with ID {sid}")
        return redirect(url_for('warden.students'))
    
    # Log deletion in Flask console
    print(f"[Delete Student] Warden initiated deletion of student: '{student['name']}' (ID: {sid})")
    
    room_no = student.get('room_no')
    if room_no:
        # Prevent room occupancy from becoming negative when decrementing
        execute_query("UPDATE rooms SET occupied=GREATEST(0, occupied-1) WHERE room_no=%s", (room_no,))
        print(f"[Delete Student] Decremented occupancy count for room: '{room_no}'")
        
    execute_query("DELETE FROM students WHERE student_id=%s", (sid,))
    print(f"[Delete Student] Successfully deleted student record and all cascaded dependents for ID: {sid}")
    
    flash(f"Student '{student['name']}' deleted successfully.", 'success')
    return redirect(url_for('warden.students'))


@warden_bp.route('/rooms/<room_no>/delete', methods=['POST'])
@warden_required
def delete_room(room_no):
    room = fetch_one("SELECT * FROM rooms WHERE room_no=%s", (room_no,))
    if not room:
        flash('Room not found.', 'danger')
        print(f"[Delete Room] Error: Room '{room_no}' not found.")
        return redirect(url_for('warden.rooms'))
    
    # Check if students are assigned to this room
    occupants = fetch_all("SELECT name FROM students WHERE room_no=%s", (room_no,))
    if occupants:
        names = ", ".join([s['name'] for s in occupants])
        flash(f"Cannot delete room '{room_no}' because it is currently occupied by: {names}. Please unassign all students first.", 'danger')
        print(f"[Delete Room] Error: Prevented deletion of room '{room_no}' because it is occupied by: {names}")
        return redirect(url_for('warden.room_detail', room_no=room_no))
    
    # Delete the room
    execute_query("DELETE FROM rooms WHERE room_no=%s", (room_no,))
    flash(f"Room '{room_no}' deleted successfully.", 'success')
    print(f"[Delete Room] Successfully deleted room: '{room_no}'")
    return redirect(url_for('warden.rooms'))


# ── Student-Warden Messaging System ───────────────────────────

@warden_bp.route('/messages')
@warden_required
def messages():
    warden_id = session['user_id']
    search_query = request.args.get('q', '').strip()
    
    if search_query:
        # Search all students matching name, reg_number, or email
        students = fetch_all("""
            SELECT s.student_id, s.name, s.register_number AS reg_number, s.room_no,
                (SELECT m.message_text FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                 ORDER BY m.created_at DESC LIMIT 1) AS last_message,
                (SELECT m.created_at FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                 ORDER BY m.created_at DESC LIMIT 1) AS last_message_time,
                (SELECT COUNT(*) FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                   AND m.sender_role = 'student' AND m.is_read = FALSE) AS unread_count
            FROM students s
            WHERE s.name LIKE %s OR s.register_number LIKE %s OR s.email LIKE %s
            ORDER BY 
                COALESCE((SELECT m.created_at FROM messages m 
                          WHERE m.student_id = s.student_id AND m.warden_id = %s 
                          ORDER BY m.created_at DESC LIMIT 1), '1970-01-01 00:00:00') DESC,
                s.name ASC
        """, (warden_id, warden_id, warden_id, f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', warden_id))
    else:
        # Get only students who have messaged this warden or been messaged by them
        students = fetch_all("""
            SELECT s.student_id, s.name, s.register_number AS reg_number, s.room_no,
                (SELECT m.message_text FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                 ORDER BY m.created_at DESC LIMIT 1) AS last_message,
                (SELECT m.created_at FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                 ORDER BY m.created_at DESC LIMIT 1) AS last_message_time,
                (SELECT COUNT(*) FROM messages m 
                 WHERE m.student_id = s.student_id AND m.warden_id = %s 
                   AND m.sender_role = 'student' AND m.is_read = FALSE) AS unread_count
            FROM students s
            WHERE EXISTS (
                SELECT 1 FROM messages m 
                WHERE m.student_id = s.student_id AND m.warden_id = %s
            )
            ORDER BY 
                COALESCE((SELECT m.created_at FROM messages m 
                          WHERE m.student_id = s.student_id AND m.warden_id = %s 
                          ORDER BY m.created_at DESC LIMIT 1), '1970-01-01 00:00:00') DESC,
                s.name ASC
        """, (warden_id, warden_id, warden_id, warden_id, warden_id))
        
    active_student_id = request.args.get('student_id', type=int)
    if not active_student_id and students:
        active_student_id = students[0]['student_id']
        
    active_student = None
    if active_student_id:
        active_student = fetch_one("SELECT student_id, name, register_number AS reg_number, room_no FROM students WHERE student_id = %s", (active_student_id,))
        
    return render_template('warden/messages.html',
                           students=students,
                           active_student=active_student,
                           search_query=search_query)


@warden_bp.route('/messages/history/<int:student_id>')
@warden_required
def message_history(student_id):
    warden_id = session['user_id']
    
    # Mark messages from this student to this warden as read
    execute_query("""
        UPDATE messages 
        SET is_read = TRUE 
        WHERE student_id = %s AND warden_id = %s AND sender_role = 'student' AND is_read = FALSE
    """, (student_id, warden_id))
    
    # Fetch message history
    msgs = fetch_all("""
        SELECT message_id, sender_role, message_text, is_read, created_at 
        FROM messages 
        WHERE student_id = %s AND warden_id = %s 
        ORDER BY created_at ASC
    """, (student_id, warden_id))
    
    # Format timestamps
    for m in msgs:
        m['created_at'] = m['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
    return jsonify({'messages': msgs})


@warden_bp.route('/messages/send', methods=['POST'])
@warden_required
def send_message():
    warden_id = session['user_id']
    student_id = request.json.get('student_id')
    message_text = request.json.get('message_text', '').strip()
    
    if not student_id or not message_text:
        return jsonify({'error': 'Message text and Student ID are required.'}), 400
        
    if len(message_text) > 1000:
        return jsonify({'error': 'Message cannot exceed 1000 characters.'}), 400
        
    # Verify student exists
    student = fetch_one("SELECT name FROM students WHERE student_id = %s", (student_id,))
    if not student:
        return jsonify({'error': 'Student not found.'}), 404
        
    # Insert message
    insert_and_get_id("""
        INSERT INTO messages (student_id, warden_id, sender_role, message_text, is_read, created_at)
        VALUES (%s, %s, 'warden', %s, FALSE, UTC_TIMESTAMP())
    """, (student_id, warden_id, message_text))
    
    return jsonify({'success': True})

