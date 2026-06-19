"""
ai_modules/chatbot.py
Intent-based hostel chatbot with live DB lookups.
"""
import re
import sys
from datetime import date


def _intent(text: str) -> str:
    t = text.lower().strip()
    
    # Check greetings first: matches word boundary of common greeting words
    if any(re.search(rf'\b{w}\b', t) for w in ['hi', 'hello', 'hlo', 'hey', 'yo', 'greetings']):
        return 'greeting'
        
    # Check WARDEN_CONTACT intent
    if any(w in t for w in ['talk to', 'contact', 'message', 'chat with', 'speak to']):
        if 'warden' in t or any(name in t for name in ['aaslin', 'ramesh', 'priya', 'senthil', 'karthick']):
            return 'warden_contact'

    # Check other intents
    if any(w in t for w in ['room', 'block', 'floor', 'roommate', 'bed', 'living', 'assigned']):
        return 'room'
    if any(w in t for w in ['leave', 'absence', 'outing', 'permission', 'vacation', 'home']):
        return 'leave'
    if any(w in t for w in ['complaint', 'issue', 'problem', 'broken', 'repair', 'defect']):
        return 'complaint'
    if any(w in t for w in ['attendance', 'present', 'absent', 'percentage', 'attend']):
        return 'attendance'
    if any(w in t for w in ['mess', 'food', 'menu', 'meal', 'breakfast', 'lunch', 'dinner', 'eat']):
        return 'mess'
    if any(w in t for w in ['announcement', 'notice', 'circular', 'news']):
        return 'announcement'
        
    # Fallback to greeting if greeting words are contained anywhere
    if any(w in t for w in ['hello', 'hi', 'hey', 'hlo', 'help', 'what can', 'how are']):
        return 'greeting'
        
    return 'unknown'


def get_response(message: str, student_id: int) -> str:
    from database import fetch_one, fetch_all

    intent = _intent(message)
    normalized_message = message.lower().strip()
    
    # Add debug logging
    print(f"[Chatbot Debug] Raw user message: '{message}'")
    print(f"[Chatbot Debug] Normalized message: '{normalized_message}'")
    print(f"[Chatbot Debug] Detected intent: '{intent}'")
    sys.stdout.flush()

    response = ""

    if intent == 'greeting':
        student = fetch_one("SELECT name FROM students WHERE student_id=%s", (student_id,))
        name = student['name'].split()[0] if student else 'there'
        response = (f"Hello {name}! 👋 I'm your Hostel AI Assistant. "
                    "I can help you with rooms, leave requests, complaints, attendance, and mess info. What would you like to know?")

    elif intent == 'room':
        info = fetch_one(
            """SELECT s.name, s.room_no AS room_number, r.block, r.floor, r.capacity, r.occupied, r.room_type
               FROM students s LEFT JOIN rooms r ON s.room_no=r.room_no WHERE s.student_id=%s""",
            (student_id,))
        if info and info['room_number']:
            block = info['block'] or 'Block C'
            floor = info['floor'] if info['floor'] is not None else 1
            capacity = info['capacity'] if info['capacity'] is not None else 3
            occupied = info['occupied'] if info['occupied'] is not None else 0
            room_type = info['room_type'].title() if info['room_type'] else 'Standard'
            response = (f"🏠 Your room details:\n"
                        f"• Room: **{info['room_number']}** ({block}, Floor {floor})\n"
                        f"• Type: {room_type} | Occupancy: {occupied}/{capacity}")
        else:
            response = "You haven't been assigned a room yet. Please contact the warden for room allocation."

    elif intent == 'leave':
        leaves = fetch_all(
            "SELECT status, from_date, to_date FROM leave_requests WHERE student_id=%s ORDER BY applied_on DESC LIMIT 3",
            (student_id,))
        if leaves:
            lines = [f"• {l['from_date']} → {l['to_date']}: **{l['status'].upper()}**" for l in leaves]
            response = "📋 Your recent leave requests:\n" + "\n".join(lines) + "\n\nTo submit a new leave, go to the Leave section."
        else:
            response = "📋 You have no leave requests yet. Use the Leave section to submit one."

    elif intent == 'complaint':
        comps = fetch_all(
            "SELECT complaint_text, status, created_at FROM complaints WHERE student_id=%s ORDER BY created_at DESC LIMIT 3",
            (student_id,))
        if comps:
            lines = []
            for c in comps:
                title = c['complaint_text'].split('\n')[0]
                lines.append(f"• {title[:40]}… — **{c['status'].upper()}**")
            response = "🔧 Your recent complaints:\n" + "\n".join(lines) + "\n\nYou can track full details in the Complaints section."
        else:
            response = "🔧 You have no complaints registered. Go to Complaints to file one."

    elif intent == 'attendance':
        month  = date.today().strftime('%Y-%m')
        records = fetch_all(
            "SELECT status FROM attendance WHERE student_id=%s AND DATE_FORMAT(att_date,'%%Y-%%m')=%s",
            (student_id, month))
        if records:
            present = sum(1 for r in records if r['status'].lower() == 'present')
            total   = len(records)
            pct     = round(present/total*100, 1)
            emoji   = '✅' if pct >= 75 else '⚠️'
            response = (f"{emoji} This month's attendance: **{present}/{total} days** ({pct}%)\n"
                        f"{'Great! Keep it up.' if pct >= 75 else 'Caution: Low attendance may affect your record.'}")
        else:
            response = "📊 No attendance records found for this month yet."

    elif intent == 'mess':
        today_name = date.today().strftime('%A')
        # 1. Try to fetch menu for today's actual date
        row = fetch_one("SELECT breakfast, lunch, dinner FROM mess_menu WHERE menu_date=%s", (date.today(),))
        
        # 2. If not found, try to fetch weekly menu for today's day of week
        if not row:
            all_menus = fetch_all("SELECT menu_date, breakfast, lunch, dinner FROM mess_menu")
            for m in all_menus:
                if m['menu_date'].strftime('%A') == today_name:
                    row = m
                    break
                    
        if row:
            lines = []
            if row.get('breakfast'):
                lines.append(f"• **Breakfast**: {row['breakfast']}")
            if row.get('lunch'):
                lines.append(f"• **Lunch**: {row['lunch']}")
            if row.get('dinner'):
                lines.append(f"• **Dinner**: {row['dinner']}")
            if lines:
                response = f"🍽️ Today's ({today_name}) mess menu:\n" + "\n".join(lines)
                
        if not response:
            response = "🍽️ Today's menu is not available yet. Check the Mess section for the full weekly menu."

    elif intent == 'announcement':
        ann = fetch_all("SELECT title, posted_date AS created_at FROM announcements WHERE is_active=1 ORDER BY posted_date DESC LIMIT 3")
        if ann:
            lines = [f"• {a['title']}" for a in ann]
            response = "📢 Latest announcements:\n" + "\n".join(lines)
        else:
            response = "📢 No recent announcements."

    elif intent == 'warden_contact':
        # Fetch all wardens to match mentioned name
        wardens = fetch_all("SELECT warden_id, name, email, phone, hostel_block FROM wardens")
        target_warden = None
        for w in wardens:
            first_name = w['name'].split()[0].lower() if w['name'] else ""
            last_name = w['name'].split()[-1].lower() if w['name'] else ""
            name_clean = w['name'].lower()
            if (first_name and first_name in normalized_message and len(first_name) > 2) or \
               (last_name and last_name in normalized_message and len(last_name) > 2) or \
               (name_clean in normalized_message):
                target_warden = w
                break
                
        # Fallback to student's block warden
        if not target_warden:
            student_room = fetch_one("SELECT room_no FROM students WHERE student_id = %s", (student_id,))
            if student_room and student_room['room_no']:
                room_block = fetch_one("SELECT block FROM rooms WHERE room_no = %s", (student_room['room_no'],))
                if room_block and room_block['block']:
                    target_warden = fetch_one("SELECT warden_id, name, email, phone, hostel_block FROM wardens WHERE hostel_block = %s LIMIT 1", (room_block['block'],))
                    
        # Last fallback to first warden
        if not target_warden:
            target_warden = fetch_one("SELECT warden_id, name, email, phone, hostel_block FROM wardens ORDER BY warden_id LIMIT 1")
            
        if target_warden:
            # Check if messages table exists
            table_check = fetch_one("SHOW TABLES LIKE 'messages'")
            messaging_enabled = (table_check is not None)
            
            w_name = target_warden['name']
            if messaging_enabled:
                w_id = target_warden['warden_id']
                url = f"/student/messages?warden_id={w_id}"
                response = (f"Yes. You can contact Warden {w_name} through the Messages section.<br>"
                            f"<a href=\"{url}\" class=\"btn btn-primary btn-sm\" style=\"margin-top: 0.5rem; display: inline-block;\">Open Messages</a>")
            else:
                w_email = target_warden['email']
                w_phone = target_warden['phone']
                w_block = target_warden['hostel_block'] or 'General'
                response = (f"📞 Warden Contact Info:\n"
                            f"• Name: **{w_name}**\n"
                            f"• Phone: {w_phone}\n"
                            f"• Email: {w_email}\n"
                            f"• Hostel Block: {w_block}")
        else:
            response = "No wardens found in the system to contact."

    else:
        response = ("I'm not sure I understood that. I can help with:\n"
                    "• 🏠 Room details\n• 📋 Leave requests\n• 🔧 Complaints\n"
                    "• 📊 Attendance\n• 🍽️ Mess menu\n• 📢 Announcements\n\nPlease ask about any of these!")

    print(f"[Chatbot Debug] Generated response: '{response.replace(chr(10), ' ').encode('ascii', 'replace').decode()[:60]}...'")
    sys.stdout.flush()
    return response
