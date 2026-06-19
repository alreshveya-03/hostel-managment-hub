"""routes/student.py"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import fetch_one, fetch_all, execute_query, insert_and_get_id
from auth_utils import student_required, hash_password, check_password
from datetime import date

student_bp = Blueprint('student', __name__)

STATUS_MAP_TO_DB = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'resolved': 'Resolved'
}

COMPLAINT_CATEGORY_MAP = {
    'electrical': 'Electrical',
    'plumbing': 'Plumbing',
    'internet': 'Internet',
    'cleanliness': 'Cleaning',
    'cleaning': 'Cleaning',
    'furniture': 'Furniture'
}

COMPLAINT_PRIORITY_MAP = {
    'low': 'Normal',
    'medium': 'Normal',
    'normal': 'Normal',
    'high': 'Urgent',
    'urgent': 'Urgent',
    'emergency': 'Emergency'
}

def map_complaint_category(cat):
    if not cat:
        return 'Others'
    c_lower = cat.lower().strip()
    return COMPLAINT_CATEGORY_MAP.get(c_lower, 'Others')

def map_complaint_priority(pri):
    if not pri:
        return 'Normal'
    p_lower = pri.lower().strip()
    return COMPLAINT_PRIORITY_MAP.get(p_lower, 'Normal')

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


@student_bp.route('/dashboard')
@student_required
def dashboard():
    sid = session['user_id']
    student = fetch_one("""
        SELECT student_id AS id, name, register_number AS reg_number, department, year, room_no AS room_number, block, floor, room_type
        FROM v_student_profile
        WHERE student_id=%s
    """, (sid,))
    pending_complaints = fetch_one(
        "SELECT COUNT(*) AS cnt FROM complaints WHERE student_id=%s AND status='Pending'", (sid,))
    pending_leaves = fetch_one(
        "SELECT COUNT(*) AS cnt FROM leave_requests WHERE student_id=%s AND status='Pending'", (sid,))
    today_att = fetch_one(
        "SELECT status FROM attendance WHERE student_id=%s AND att_date=%s", (sid, date.today()))
    if today_att:
        today_att['status'] = today_att['status'].lower()
    announcements = fetch_all("""
        SELECT a.announcement_id AS id, a.title, a.description AS content, a.ann_type AS priority,
               'all' AS target_audience, a.is_active, a.posted_date AS created_at
        FROM announcements a
        WHERE a.is_active=1
        ORDER BY a.posted_date DESC LIMIT 5
    """)
    recent_complaints = fetch_all(
        "SELECT * FROM complaints WHERE student_id=%s ORDER BY created_at DESC LIMIT 3", (sid,))
    for c in recent_complaints:
        format_complaint(c)
    return render_template('student/dashboard.html',
        student=student,
        pending_complaints=pending_complaints['cnt'] if pending_complaints else 0,
        pending_leaves=pending_leaves['cnt'] if pending_leaves else 0,
        today_att=today_att,
        announcements=announcements,
        recent_complaints=recent_complaints)


@student_bp.route('/profile', methods=['GET', 'POST'])
@student_required
def profile():
    sid = session['user_id']
    if request.method == 'POST':
        f = request.form
        execute_query(
            "UPDATE students SET name=%s,phone=%s,address=%s WHERE student_id=%s",
            (f['name'], f['phone'], f['address'], sid))
        session['name'] = f['name']
        flash('Profile updated!', 'success')
        return redirect(url_for('student.profile'))
    student = fetch_one("""
        SELECT student_id AS id, name, register_number AS reg_number, email, phone, department, year, gender, food_preference, address, room_no AS room_number
        FROM students
        WHERE student_id=%s
    """, (sid,))
    return render_template('student/profile.html', student=student, warden=get_block_warden_for_student(sid))


@student_bp.route('/room')
@student_required
def room():
    sid = session['user_id']
    student = fetch_one("""
        SELECT student_id AS id, name, register_number AS reg_number, department, year, room_no AS room_number, block, floor, room_type
        FROM v_student_profile
        WHERE student_id=%s
    """, (sid,))
    room_mates = []
    if student and student['room_number']:
        room_mates = fetch_all(
            """SELECT s.name, s.register_number AS reg_number, s.department, s.year, s.phone
               FROM students s
               WHERE s.room_no=%s AND s.student_id != %s""",
            (student['room_number'], sid))
    return render_template('student/room.html', student=student, room_mates=room_mates)


@student_bp.route('/complaints', methods=['GET', 'POST'])
@student_required
def complaints():
    sid = session['user_id']
    if request.method == 'POST':
        f = request.form
        title       = f.get('title', '').strip()
        description = f.get('description', '').strip()
        category    = f.get('category', 'general')
        # AI priority prediction
        ai_priority = ai_category = None
        try:
            from ai_modules.complaint_ai import predict_priority, predict_category
            ai_priority = predict_priority(title + ' ' + description)
            ai_category = predict_category(title + ' ' + description)
        except Exception:
            pass
        full_text = f"{title}\n{description}"
        final_category = ai_category or category
        final_priority = ai_priority or 'Normal'
        db_category = map_complaint_category(final_category)
        db_priority = map_complaint_priority(final_priority)
        cid = insert_and_get_id(
            """INSERT INTO complaints (student_id,complaint_text,category,priority,status,filed_date)
               VALUES (%s,%s,%s,%s,'Pending',%s)""",
            (sid, full_text, db_category, db_priority, date.today()))
        # log AI prediction
        if ai_priority:
            try:
                insert_and_get_id(
                    "INSERT INTO ai_prediction_logs (module,prediction,reference_id,reference_type) VALUES (%s,%s,%s,%s)",
                    ('complaint_priority', ai_priority, cid, 'complaint'))
            except Exception:
                pass
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('student.complaints'))
    comp_list = fetch_all(
        "SELECT * FROM complaints WHERE student_id=%s ORDER BY created_at DESC", (sid,))
    for c in comp_list:
        format_complaint(c)
    return render_template('student/complaints.html', complaints=comp_list, warden=get_block_warden_for_student(sid))


@student_bp.route('/leave', methods=['GET', 'POST'])
@student_required
def leave():
    sid = session['user_id']
    if request.method == 'POST':
        f = request.form
        insert_and_get_id(
            """INSERT INTO leave_requests (student_id,reason,from_date,to_date,status)
               VALUES (%s,%s,%s,%s,'Pending')""",
            (sid, f['reason'], f['from_date'], f['to_date']))
        flash('Leave request submitted!', 'success')
        return redirect(url_for('student.leave'))
    leaves = fetch_all(
        "SELECT * FROM leave_requests WHERE student_id=%s ORDER BY applied_on DESC", (sid,))
    for l in leaves:
        format_leave(l)
    return render_template('student/leave.html', leaves=leaves, warden=get_block_warden_for_student(sid))


@student_bp.route('/attendance')
@student_required
def attendance():
    sid = session['user_id']
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    records = fetch_all(
        "SELECT attendance_id AS id, student_id, att_date AS date, status, marked_by, remarks, created_at FROM attendance WHERE student_id=%s AND DATE_FORMAT(att_date,'%%Y-%%m')=%s ORDER BY att_date",
        (sid, month))
    for r in records:
        r['status'] = r['status'].lower()
    present = sum(1 for r in records if r['status'] == 'present')
    absent  = sum(1 for r in records if r['status'] == 'absent')
    pct     = round(present / len(records) * 100, 1) if records else 0
    return render_template('student/attendance.html',
        records=records, month=month, present=present, absent=absent, pct=pct)


@student_bp.route('/mess')
@student_required
def mess():
    sid = session['user_id']
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
    feedbacks = fetch_all(
        """SELECT feedback_id AS id, feedback_date AS date, meal_type, rating, feedback_text, sentiment, created_at
           FROM food_feedback WHERE student_id=%s ORDER BY created_at DESC LIMIT 10""", (sid,))
    for fb in feedbacks:
        if fb.get('sentiment'):
            fb['sentiment'] = fb['sentiment'].lower()
        if fb.get('meal_type'):
            fb['meal_type'] = fb['meal_type'].lower()
    return render_template('student/mess.html', menu=menu, feedbacks=feedbacks)


@student_bp.route('/mess/feedback', methods=['POST'])
@student_required
def mess_feedback():
    sid = session['user_id']
    f   = request.form
    text = f.get('feedback_text', '')
    sentiment = None
    try:
        from ai_modules.sentiment import analyze_sentiment
        result = analyze_sentiment(text)
        sentiment = result['sentiment']
    except Exception:
        pass
    insert_and_get_id(
        """INSERT INTO food_feedback (student_id,meal_type,rating,feedback_text,sentiment,feedback_date)
           VALUES (%s,%s,%s,%s,%s,%s)""",
        (sid, f.get('meal_type','lunch').title(), int(f.get('rating',3)),
         text, sentiment.title() if sentiment else 'Neutral', date.today()))
    flash('Feedback submitted! Thank you.', 'success')
    return redirect(url_for('student.mess'))


@student_bp.route('/announcements')
@student_required
def announcements():
    items = fetch_all("""
        SELECT a.announcement_id AS id, a.title, a.description AS content, a.ann_type AS priority,
               'all' AS target_audience, a.is_active, a.posted_date AS created_at, w.name AS warden_name
        FROM announcements a
        JOIN wardens w ON a.posted_by=w.warden_id
        WHERE a.is_active=1
        ORDER BY a.posted_date DESC
    """)
    return render_template('student/announcements.html', announcements=items)


@student_bp.route('/chatbot')
@student_required
def chatbot():
    return render_template('student/chatbot.html')


@student_bp.route('/chatbot/ask', methods=['POST'])
@student_required
def chatbot_ask():
    sid  = session['user_id']
    msg  = request.json.get('message', '')
    resp = "I'm here to help! Please ask about rooms, leave, complaints, attendance or mess."
    try:
        from ai_modules.chatbot import get_response
        resp = get_response(msg, sid)
    except Exception:
        pass
    return jsonify({'response': resp})


# ── Student-Warden Messaging System ───────────────────────────

def get_block_warden_for_student(student_id):
    student_room = fetch_one("SELECT room_no FROM students WHERE student_id = %s", (student_id,))
    if student_room and student_room['room_no']:
        room_block = fetch_one("SELECT block FROM rooms WHERE room_no = %s", (student_room['room_no'],))
        if room_block and room_block['block']:
            w = fetch_one("SELECT warden_id, name FROM wardens WHERE hostel_block = %s LIMIT 1", (room_block['block'],))
            if w:
                return w
    # Fallback
    return fetch_one("SELECT warden_id, name FROM wardens ORDER BY warden_id LIMIT 1")


@student_bp.route('/messages')
@student_required
def messages():
    student_id = session['user_id']
    
    # Query wardens with latest message snippet, time, and unread count
    wardens = fetch_all("""
        SELECT w.warden_id, w.name, w.hostel_block,
            (SELECT m.message_text FROM messages m 
             WHERE m.student_id = %s AND m.warden_id = w.warden_id 
             ORDER BY m.created_at DESC LIMIT 1) AS last_message,
            (SELECT m.created_at FROM messages m 
             WHERE m.student_id = %s AND m.warden_id = w.warden_id 
             ORDER BY m.created_at DESC LIMIT 1) AS last_message_time,
            (SELECT COUNT(*) FROM messages m 
             WHERE m.student_id = %s AND m.warden_id = w.warden_id 
               AND m.sender_role = 'warden' AND m.is_read = FALSE) AS unread_count
        FROM wardens w
        ORDER BY 
            COALESCE((SELECT m.created_at FROM messages m 
                      WHERE m.student_id = %s AND m.warden_id = w.warden_id 
                      ORDER BY m.created_at DESC LIMIT 1), '1970-01-01 00:00:00') DESC,
            w.name ASC
    """, (student_id, student_id, student_id, student_id))
    
    active_warden_id = request.args.get('warden_id')
    if not active_warden_id and wardens:
        # Default to block warden or first warden
        block_warden = get_block_warden_for_student(student_id)
        if block_warden:
            active_warden_id = block_warden['warden_id']
        else:
            active_warden_id = wardens[0]['warden_id']
        
    active_warden = None
    if active_warden_id:
        active_warden = fetch_one("SELECT warden_id, name, hostel_block FROM wardens WHERE warden_id = %s", (active_warden_id,))
        
    return render_template('student/messages.html', 
                           wardens=wardens, 
                           active_warden=active_warden)


@student_bp.route('/messages/history/<warden_id>')
@student_required
def message_history(warden_id):
    student_id = session['user_id']
    
    # Mark messages from this warden to this student as read
    execute_query("""
        UPDATE messages 
        SET is_read = TRUE 
        WHERE student_id = %s AND warden_id = %s AND sender_role = 'warden' AND is_read = FALSE
    """, (student_id, warden_id))
    
    # Fetch messages sorted by created_at ascending
    msgs = fetch_all("""
        SELECT message_id, sender_role, message_text, is_read, created_at 
        FROM messages 
        WHERE student_id = %s AND warden_id = %s 
        ORDER BY created_at ASC
    """, (student_id, warden_id))
    
    # Format timestamps in ISO format
    for m in msgs:
        m['created_at'] = m['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
    return jsonify({'messages': msgs})


@student_bp.route('/messages/send', methods=['POST'])
@student_required
def send_message():
    student_id = session['user_id']
    warden_id = request.json.get('warden_id')
    message_text = request.json.get('message_text', '').strip()
    
    if not warden_id or not message_text:
        return jsonify({'error': 'Message text and Warden ID are required.'}), 400
        
    if len(message_text) > 1000:
        return jsonify({'error': 'Message cannot exceed 1000 characters.'}), 400
        
    # Verify warden exists
    warden = fetch_one("SELECT name FROM wardens WHERE warden_id = %s", (warden_id,))
    if not warden:
        return jsonify({'error': 'Warden not found.'}), 404
        
    # Insert message using UTC timestamp
    insert_and_get_id("""
        INSERT INTO messages (student_id, warden_id, sender_role, message_text, is_read, created_at)
        VALUES (%s, %s, 'student', %s, FALSE, UTC_TIMESTAMP())
    """, (student_id, warden_id, message_text))
    
    return jsonify({'success': True})

