"""routes/api.py – JSON endpoints consumed by the frontend JS"""
from flask import Blueprint, jsonify, request, session
from database import fetch_all, fetch_one

api_bp = Blueprint('api', __name__)


@api_bp.route('/stats')
def stats():
    if session.get('role') not in ('warden', 'student'):
        return jsonify({'error': 'unauthorized'}), 401
    data = {
        'total_students': fetch_one("SELECT COUNT(*) AS c FROM students")['c'],
        'occupied_rooms': fetch_one("SELECT COUNT(*) AS c FROM v_room_summary WHERE occupied>0")['c'],
        'vacant_rooms':   fetch_one("SELECT COUNT(*) AS c FROM v_room_summary WHERE occupied=0")['c'],
        'pending_complaints': fetch_one("SELECT COUNT(*) AS c FROM complaints WHERE status='Pending'")['c'],
    }
    return jsonify(data)


@api_bp.route('/chart/complaints')
def chart_complaints():
    if session.get('role') != 'warden':
        return jsonify({'error': 'unauthorized'}), 401
    rows = fetch_all("SELECT category, COUNT(*) AS cnt FROM complaints GROUP BY category")
    return jsonify({'labels': [r['category'] for r in rows], 'data': [r['cnt'] for r in rows]})


@api_bp.route('/chart/attendance')
def chart_attendance():
    if session.get('role') not in ('warden', 'student'):
        return jsonify({'error': 'unauthorized'}), 401
    rows = fetch_all(
        """SELECT att_date AS date, SUM(status='Present') AS p, SUM(status='Absent') AS a
           FROM attendance WHERE att_date >= DATE_SUB(CURDATE(),INTERVAL 7 DAY)
           GROUP BY att_date ORDER BY att_date""")
    return jsonify({
        'labels':   [str(r['date']) for r in rows],
        'present':  [int(r['p'] or 0) for r in rows],
        'absent':   [int(r['a'] or 0) for r in rows],
    })


@api_bp.route('/chart/feedback')
def chart_feedback():
    rows = fetch_all("SELECT sentiment, COUNT(*) AS cnt FROM food_feedback WHERE sentiment IS NOT NULL GROUP BY sentiment")
    return jsonify({'labels': [r['sentiment'].lower() for r in rows], 'data': [r['cnt'] for r in rows]})


@api_bp.route('/rooms/available')
def rooms_available():
    if session.get('role') not in ('warden', 'student'):
        return jsonify({'error': 'unauthorized'}), 401
    rooms = fetch_all("""
        SELECT room_no AS id, room_no AS room_number, block, floor, available_beds AS available, capacity, room_type
        FROM v_room_summary WHERE available_beds>0
    """)
    return jsonify(rooms)


@api_bp.route('/rooms/suggest')
def rooms_suggest():
    if session.get('role') not in ('warden', 'student'):
        return jsonify({'error': 'unauthorized'}), 401
    
    student_id = request.args.get('student_id', type=int)
    if not student_id:
        if session.get('role') == 'student':
            student_id = session.get('user_id')
        else:
            return jsonify({'error': 'student_id is required'}), 400

    student = fetch_one("SELECT student_id, name, department, year, gender FROM students WHERE student_id=%s", (student_id,))
    if not student:
        return jsonify({'error': 'student not found'}), 404
    
    rooms = fetch_all("""
        SELECT room_no AS room_number, block, floor, capacity, occupied, available_beds AS available, room_type
        FROM v_room_summary WHERE available_beds>0
    """)
    
    limit = request.args.get('limit', 3, type=int)
    from ai_modules.room_suggest import suggest_rooms
    suggestions = suggest_rooms(student, rooms, top_n=limit)
    return jsonify({'student': student, 'suggestions': suggestions})


@api_bp.route('/rooms/suggest_guest')
def rooms_suggest_guest():
    dept = request.args.get('department', '').strip()
    year = request.args.get('year', 1, type=int)
    
    if not dept:
        return jsonify({'error': 'department is required'}), 400
        
    mock_student = {'department': dept, 'year': year}
    rooms = fetch_all("""
        SELECT room_no AS room_number, block, floor, capacity, occupied, available_beds AS available, room_type
        FROM v_room_summary WHERE available_beds>0
    """)
    
    from ai_modules.room_suggest import suggest_rooms
    suggestions = suggest_rooms(mock_student, rooms)
    return jsonify({'suggestions': suggestions})
