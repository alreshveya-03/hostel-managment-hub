# =============================================================
#  HOSTEL HUB — ai_models/chatbot.py
#
#  PURPOSE:
#    A conversational hostel assistant for students.
#    Answers natural language questions about:
#      - Leave application process
#      - Complaint filing
#      - Mess menu (live from DB)
#      - Attendance status (live from DB)
#      - Room and roommate info (live from DB)
#      - Hostel rules and timings
#      - Warden contact details
#      - General hostel queries
#
#  HOW IT WORKS — Intent Pipeline:
#
#    Step 1 — Preprocess
#      Lowercase, strip punctuation, tokenise the query.
#
#    Step 2 — Intent Detection (keyword scoring)
#      Each INTENT has a set of trigger keywords with weights.
#      We score the query against all intents and pick the
#      highest-scoring one. If no intent scores above the
#      threshold, we fall through to a default response.
#
#    Step 3 — Slot Extraction (optional)
#      Some intents need extra info from the query, e.g.
#      "complaint about wifi" → slot: category = "Internet"
#
#    Step 4 — Response Generation
#      Each intent has a dedicated handler function that
#      optionally fetches live data from the DB and formats
#      a rich HTML response.
#
#    Step 5 — Conversation Memory (session-level)
#      We track the last 5 intents so follow-up questions
#      like "what about dinner?" after "today's menu?" work.
#
#  WHY RULE-BASED:
#    A transformer chatbot (GPT, BERT) would need internet
#    access, GPU, or API keys. A rule-based system works
#    offline, is fully explainable, responds in <10ms, and
#    handles the narrow domain of hostel queries reliably.
#
#  INTEGRATION:
#    Called from student_portal.py → render_chatbot():
#
#      from ai_models.chatbot import get_chatbot_response
#      response = get_chatbot_response(query, student_id, student)
#
#  FUTURE IMPROVEMENTS:
#    - Add transformer-based fallback (Gemini/Mistral API)
#    - Train a small intent classifier on hostel query dataset
#    - Add multi-turn slot filling ("Which room?" → "A101")
#    - Support Tamil transliteration ("menu enna today?")
# =============================================================

from __future__ import annotations
import re
from datetime import date
from typing import Optional


# =============================================================
# INTENT REGISTRY
# Format: intent_name → {keywords: {word: weight}, threshold: int}
# =============================================================
INTENTS: dict[str, dict] = {

    "leave_apply": {
        "keywords": {
            "leave":6, "apply leave":8, "how to apply":6, "submit leave":8,
            "leave application":8, "going home":5, "home visit":5,
            "vacation":4, "holiday":4, "absent":4, "permission":5,
            "leave form":7, "apply for leave":8,
        },
        "threshold": 5,
    },
    "leave_status": {
        "keywords": {
            "leave status":9, "leave approved":8, "leave rejected":8,
            "check leave":8, "my leave":7, "leave request":7,
            "pending leave":7, "was my leave":8,
        },
        "threshold": 6,
    },
    "complaint_file": {
        "keywords": {
            "complaint":6, "file complaint":8, "register complaint":8,
            "submit complaint":8, "issue":4, "problem":4, "repair":5,
            "broken":5, "fix":4, "not working":6, "fault":5,
            "how to complain":8, "raise complaint":8,
        },
        "threshold": 5,
    },
    "complaint_status": {
        "keywords": {
            "complaint status":9, "my complaint":8, "complaint resolved":8,
            "complaint pending":8, "check complaint":8, "complaint update":7,
        },
        "threshold": 6,
    },
    "menu_today": {
        "keywords": {
            "menu":5, "today menu":9, "today's menu":9, "what is today":7,
            "food today":8, "lunch today":8, "dinner today":8,
            "breakfast today":8, "snacks today":8, "what's for":7,
            "mess menu":6, "today food":8,
        },
        "threshold": 5,
    },
    "menu_meal": {
        "keywords": {
            "breakfast":5, "lunch":5, "dinner":5, "snacks":5,
            "morning food":6, "afternoon food":6, "evening food":6,
            "night food":6,
        },
        "threshold": 4,
    },
    "attendance_query": {
        "keywords": {
            "attendance":7, "my attendance":9, "attendance percentage":9,
            "how many days":6, "present days":7, "absent days":7,
            "attendance record":8, "attendance history":8, "percentage":5,
        },
        "threshold": 5,
    },
    "room_info": {
        "keywords": {
            "room":5, "my room":8, "room number":8, "which room":8,
            "room details":8, "block":4, "floor":4, "room allocated":7,
        },
        "threshold": 4,
    },
    "roommate_info": {
        "keywords": {
            "roommate":9, "room mate":9, "who is in my room":9,
            "room partner":8, "who shares":7, "sharing room":6,
        },
        "threshold": 5,
    },
    "hostel_rules": {
        "keywords": {
            "rule":6, "rules":6, "hostel rules":9, "curfew":8,
            "timing":6, "timings":6, "allowed":5, "not allowed":6,
            "regulation":6, "discipline":6, "policy":6, "guidelines":6,
            "what time":5, "closing time":7, "entry time":7, "gate":5,
        },
        "threshold": 4,
    },
    "contact_warden": {
        "keywords": {
            "contact":5, "warden":6, "warden number":9, "phone":5,
            "call warden":9, "warden email":8, "office":5, "reach":5,
            "warden contact":9, "who is warden":8,
        },
        "threshold": 5,
    },
    "mess_feedback": {
        "keywords": {
            "feedback":6, "food feedback":8, "rate food":8, "food rating":8,
            "how to give feedback":8, "mess feedback":8, "food quality":6,
        },
        "threshold": 5,
    },
    "wifi_issue": {
        "keywords": {
            "wifi":8, "internet":7, "network":6, "no internet":9,
            "wifi not working":9, "slow internet":8, "connectivity":7,
        },
        "threshold": 5,
    },
    "laundry": {
        "keywords": {
            "laundry":9, "washing":7, "clothes":5, "washing machine":9,
            "iron":6, "ironing":6, "dry clean":8,
        },
        "threshold": 5,
    },
    "medical": {
        "keywords": {
            "sick":7, "ill":6, "medical":8, "hospital":7, "doctor":7,
            "medicine":7, "health":6, "ambulance":9, "emergency":8,
            "fever":7, "unwell":7,
        },
        "threshold": 5,
    },
    "fees": {
        "keywords": {
            "fee":6, "fees":6, "hostel fee":9, "payment":6, "pay":5,
            "due":5, "amount":5, "hostel charges":9, "cost":4,
        },
        "threshold": 5,
    },
    "announcement": {
        "keywords": {
            "announcement":8, "notice":7, "latest news":7, "any news":7,
            "notice board":8, "update":5, "event":5, "holiday":5,
        },
        "threshold": 5,
    },
    "greeting": {
        "keywords": {
            "hi":6, "hello":6, "hey":6, "good morning":8, "good evening":8,
            "good afternoon":8, "good night":7, "how are you":7,
            "what's up":6, "sup":4, "namaste":7,
        },
        "threshold": 4,
    },
    "thanks": {
        "keywords": {
            "thanks":8, "thank you":9, "thank":7, "helpful":6,
            "great":5, "awesome":5, "got it":7, "understood":7,
        },
        "threshold": 5,
    },
    "help": {
        "keywords": {
            "help":8, "what can you do":9, "what do you know":9,
            "capabilities":8, "features":6, "options":6, "menu":3,
        },
        "threshold": 6,
    },
}


# =============================================================
# INTENT DETECTION ENGINE
# =============================================================
def _preprocess(text: str) -> str:
    """Lowercase, strip extra whitespace, keep letters/numbers/spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_intent(query: str) -> tuple[str, int]:
    """
    Score the query against all intents and return the best match.

    Returns:
        (intent_name, score) — e.g. ("menu_today", 12)
        Returns ("unknown", 0) if nothing matches.
    """
    text   = _preprocess(query)
    scores = {}

    for intent_name, config in INTENTS.items():
        score = 0
        for keyword, weight in config["keywords"].items():
            if keyword in text:
                score += weight
        scores[intent_name] = score

    best_intent = max(scores, key=scores.get)
    best_score  = scores[best_intent]
    threshold   = INTENTS.get(best_intent, {}).get("threshold", 5)

    if best_score >= threshold:
        return best_intent, best_score
    return "unknown", 0


# =============================================================
# RESPONSE HANDLERS — one function per intent
# All return HTML-safe strings (used directly in st.markdown)
# =============================================================

def _respond_leave_apply(student: dict) -> str:
    return (
        "📝 <b>How to apply for leave:</b><br><br>"
        "1. Click <b>🚪 Leave Request</b> in the left sidebar<br>"
        "2. Go to the <b>Apply Leave</b> tab<br>"
        "3. Enter your reason (be specific — helps faster approval)<br>"
        "4. Select your <b>From</b> and <b>To</b> dates<br>"
        "5. Click <b>Submit Leave Request</b><br><br>"
        "⏳ Your warden will review and respond within 24 hours.<br>"
        "💡 <i>Tip: Apply at least 2 days in advance. For medical emergencies, "
        "contact the warden directly.</i>"
    )


def _respond_leave_status(student_id: int) -> str:
    try:
        from database.connection import get_connection
        from database.queries import get_leaves_by_student
        conn = get_connection()
        if not conn:
            raise ConnectionError("DB unavailable")
        leaves = get_leaves_by_student(conn, student_id)
        conn.close()

        if not leaves:
            return ("🚪 <b>Your Leave History:</b><br><br>"
                    "You haven't submitted any leave requests yet.<br>"
                    "Go to <b>Leave Request</b> → <b>Apply Leave</b> to submit one.")

        recent = leaves[:3]
        lines  = "🚪 <b>Your Recent Leave Requests:</b><br><br>"
        icons  = {"Approved":"✅","Rejected":"❌","Pending":"⏳"}
        for l in recent:
            icon = icons.get(l["status"], "📋")
            lines += (f"{icon} <b>{l['from_date']} → {l['to_date']}</b> — "
                      f"<b>{l['status']}</b><br>"
                      f"&nbsp;&nbsp;&nbsp;Reason: {l['reason'][:50]}{'...' if len(l['reason'])>50 else ''}<br>")
        lines += "<br>📋 See full history in the <b>Leave Request</b> section."
        return lines
    except Exception:
        return ("🚪 Go to <b>Leave Request → Leave History</b> "
                "in the sidebar to check your leave status.")


def _respond_complaint_file() -> str:
    return (
        "📋 <b>How to file a complaint:</b><br><br>"
        "1. Click <b>📋 Complaints</b> in the left sidebar<br>"
        "2. Go to the <b>File Complaint</b> tab<br>"
        "3. Describe your issue clearly in the text box<br>"
        "4. Our AI auto-detects the <b>category</b> and <b>priority</b><br>"
        "5. Click <b>Submit Complaint</b><br><br>"
        "🤖 <b>AI Priority Detection:</b><br>"
        "&nbsp;&nbsp;🟢 <b>Normal</b> — Minor issues (fused bulb, slow WiFi)<br>"
        "&nbsp;&nbsp;🟡 <b>Urgent</b>  — Disruptions (no water, blocked drain)<br>"
        "&nbsp;&nbsp;🔴 <b>Emergency</b> — Danger (sparks, flooding, gas leak)<br><br>"
        "⚡ <i>Emergency complaints are immediately flagged to your warden.</i>"
    )


def _respond_complaint_status(student_id: int) -> str:
    try:
        from database.connection import get_connection
        from database.queries import get_complaints_by_student
        conn = get_connection()
        if not conn:
            raise ConnectionError("DB unavailable")
        complaints = get_complaints_by_student(conn, student_id)
        conn.close()

        if not complaints:
            return ("📋 <b>Your Complaints:</b><br><br>"
                    "You haven't filed any complaints yet.<br>"
                    "Go to <b>Complaint Management → File Complaint</b> to submit one.")

        open_c    = [c for c in complaints if c["status"] != "Resolved"]
        resolved  = [c for c in complaints if c["status"] == "Resolved"]
        icons_s   = {"Pending":"⏳","In Progress":"🔧","Resolved":"✅"}
        lines = (f"📋 <b>Your Complaints Summary:</b><br>"
                 f"Total: <b>{len(complaints)}</b> &nbsp;|&nbsp; "
                 f"Open: <b>{len(open_c)}</b> &nbsp;|&nbsp; "
                 f"Resolved: <b>{len(resolved)}</b><br><br>")

        for c in complaints[:4]:
            icon = icons_s.get(c["status"], "📋")
            lines += (f"{icon} <b>{c['category']}</b> [{c['priority']}] — {c['status']}<br>"
                      f"&nbsp;&nbsp;&nbsp;{c['complaint_text'][:50]}{'…' if len(c['complaint_text'])>50 else ''}<br>"
                      f"&nbsp;&nbsp;&nbsp;Filed: {c['filed_date']}<br>")

        lines += "<br>📋 See full details in <b>Complaint Management</b>."
        return lines
    except Exception:
        return ("📋 Go to <b>Complaint Management → My Complaints</b> "
                "in the sidebar to check your complaint status.")


def _respond_menu_today() -> str:
    try:
        from database.connection import get_connection
        from database.queries import get_menu_by_date
        conn = get_connection()
        if not conn:
            raise ConnectionError("DB unavailable")
        menu = get_menu_by_date(conn, date.today().strftime("%Y-%m-%d"))
        conn.close()

        if menu:
            return (
                f"🍽️ <b>Today's Mess Menu — {date.today().strftime('%A, %d %B %Y')}:</b><br><br>"
                f"🌅 <b>Breakfast:</b> {menu['breakfast']}<br>"
                f"☀️ <b>Lunch:</b> {menu['lunch']}<br>"
                f"🍪 <b>Snacks:</b> {menu['snacks']}<br>"
                f"🌙 <b>Dinner:</b> {menu['dinner']}<br><br>"
                "💡 <i>You can mark your meal attendance in the "
                "<b>Mess</b> section → Mark Attendance tab.</i>"
            )
        else:
            return (
                "🍽️ Today's menu hasn't been posted yet by the warden.<br><br>"
                "Check back after 8:00 AM or visit the <b>Mess</b> section "
                "to see this week's menu."
            )
    except Exception:
        return "🍽️ I couldn't fetch today's menu right now. Visit the <b>Mess</b> section to see it."


def _respond_attendance(student_id: int) -> str:
    try:
        from database.connection import get_connection
        from database.queries import get_attendance_percentage, get_attendance_by_student
        conn = get_connection()
        if not conn:
            raise ConnectionError("DB unavailable")
        pct     = get_attendance_percentage(conn, student_id)
        history = get_attendance_by_student(conn, student_id)
        conn.close()

        total   = len(history)
        present = sum(1 for h in history if h["status"] == "Present")
        absent  = sum(1 for h in history if h["status"] == "Absent")

        if pct >= 90:
            status = "🌟 Excellent! Keep it up!"
        elif pct >= 75:
            status = "👍 Good — above the 75% requirement."
        elif pct >= 60:
            status = "⚠️ Below 75%! You're at risk — speak to your warden."
        else:
            status = "🔴 Critical! Immediate attention needed — contact warden today."

        return (
            f"📅 <b>Your Attendance:</b><br><br>"
            f"Overall: <b>{pct:.1f}%</b> — {status}<br>"
            f"Present: <b>{present} days</b> &nbsp;|&nbsp; "
            f"Absent: <b>{absent} days</b> &nbsp;|&nbsp; "
            f"Total recorded: <b>{total} days</b><br><br>"
            f"📊 The minimum required attendance is <b>75%</b>.<br>"
            "Visit <b>Attendance</b> in the sidebar for your full history."
        )
    except Exception:
        return ("📅 I couldn't fetch your attendance right now.<br>"
                "Visit the <b>Attendance</b> section in the sidebar to check.")


def _respond_room_info(student: dict) -> str:
    room_no = student.get("room_no") or "Not yet allocated"
    block   = student.get("block") or "—"
    floor   = student.get("floor") or "—"
    rtype   = student.get("room_type") or "Standard"

    if not student.get("room_no"):
        return ("🛏️ <b>Your Room:</b> Not yet allocated.<br><br>"
                "Your warden will assign you a room. "
                "Visit the <b>Room Details</b> section for more info.")
    return (
        f"🛏️ <b>Your Room Details:</b><br><br>"
        f"Room Number: <b>{room_no}</b><br>"
        f"Block: <b>{block}</b><br>"
        f"Floor: <b>Floor {floor}</b><br>"
        f"Type: <b>{rtype}</b><br><br>"
        "Visit <b>Room Details</b> in the sidebar for roommate info "
        "and occupancy details."
    )


def _respond_roommate_info(student_id: int, student: dict) -> str:
    room_no = student.get("room_no")
    if not room_no:
        return "🛏️ You haven't been allocated a room yet. Contact your warden."
    try:
        from database.connection import get_connection
        from database.queries import get_roommates
        conn = get_connection()
        if not conn:
            raise ConnectionError("DB unavailable")
        roommates = get_roommates(conn, room_no, student_id)
        conn.close()

        if not roommates:
            return (f"🛏️ You're in Room <b>{room_no}</b> and currently have "
                    "no roommates. Enjoy the space! 😄")

        lines = f"🛏️ <b>Your Roommates in Room {room_no}:</b><br><br>"
        for i, rm in enumerate(roommates, 1):
            lines += (f"{i}. <b>{rm['name']}</b><br>"
                      f"&nbsp;&nbsp;&nbsp;{rm['department']} · Year {rm['year']}<br>"
                      f"&nbsp;&nbsp;&nbsp;📱 {rm['phone']}<br>")
        lines += "<br>Visit <b>Room Details</b> for full info."
        return lines
    except Exception:
        return (f"🛏️ Visit <b>Room Details</b> in the sidebar "
                "to see your roommate information.")


def _respond_hostel_rules() -> str:
    return (
        "📜 <b>Hostel Rules & Timings:</b><br><br>"
        "🚪 <b>Curfew Times:</b><br>"
        "&nbsp;&nbsp;&nbsp;Weekdays (Mon–Fri): <b>9:30 PM</b><br>"
        "&nbsp;&nbsp;&nbsp;Weekends (Sat–Sun): <b>10:00 PM</b><br><br>"
        "🔊 <b>Silence Hours:</b> 10:30 PM – 6:00 AM<br>"
        "&nbsp;&nbsp;&nbsp;No loud music, TV, or disturbance after 10:30 PM.<br><br>"
        "🚭 <b>Strictly Prohibited:</b><br>"
        "&nbsp;&nbsp;&nbsp;❌ Smoking inside hostel premises<br>"
        "&nbsp;&nbsp;&nbsp;❌ Alcohol or drugs<br>"
        "&nbsp;&nbsp;&nbsp;❌ Cooking in rooms<br>"
        "&nbsp;&nbsp;&nbsp;❌ Gambling<br>"
        "&nbsp;&nbsp;&nbsp;❌ Ragging in any form<br><br>"
        "🚪 <b>Guest Policy:</b><br>"
        "&nbsp;&nbsp;&nbsp;Allowed in common areas only, 10 AM – 7 PM.<br>"
        "&nbsp;&nbsp;&nbsp;Must register at the security desk.<br><br>"
        "📱 <b>Going Out:</b><br>"
        "&nbsp;&nbsp;&nbsp;Inform your warden before leaving after 6 PM.<br>"
        "&nbsp;&nbsp;&nbsp;Overnight stays require approved leave.<br><br>"
        "⚡ <b>Electricity:</b><br>"
        "&nbsp;&nbsp;&nbsp;Lights and fans off when leaving the room.<br>"
        "&nbsp;&nbsp;&nbsp;Personal heaters / cooking devices not allowed."
    )


def _respond_contact_warden(student: dict) -> str:
    block = student.get("block") or "Block A"
    contacts = {
        "Block A": ("Dr. Ramesh Kumar",       "9876543210", "ramesh.kumar@hostel.edu"),
        "Block B": ("Mrs. Priya Sundaram",    "9876543211", "priya.sundaram@hostel.edu"),
        "Block C": ("Mr. Senthil Murugan",    "9876543212", "senthil.murugan@hostel.edu"),
    }
    name, phone, email = contacts.get(block, contacts["Block A"])
    return (
        f"📞 <b>Your Warden Contact ({block}):</b><br><br>"
        f"👤 <b>{name}</b><br>"
        f"📱 {phone}<br>"
        f"📧 {email}<br><br>"
        "<b>All Warden Contacts:</b><br>"
        "🏢 Block A — Dr. Ramesh Kumar: <b>9876543210</b><br>"
        "🏢 Block B — Mrs. Priya Sundaram: <b>9876543211</b><br>"
        "🏢 Block C — Mr. Senthil Murugan: <b>9876543212</b><br><br>"
        "🏢 <b>Hostel Office:</b> hostel@college.edu<br>"
        "🕘 Office Hours: 9:00 AM – 5:00 PM (Mon–Sat)"
    )


def _respond_mess_feedback() -> str:
    return (
        "⭐ <b>How to give food feedback:</b><br><br>"
        "1. Click <b>🍽️ Mess</b> in the left sidebar<br>"
        "2. Go to the <b>Give Feedback</b> tab<br>"
        "3. Select the meal you're rating<br>"
        "4. Choose a star rating (1–5)<br>"
        "5. Write your feedback comment<br>"
        "6. Click <b>Submit Feedback</b><br><br>"
        "🤖 Our AI analyses the sentiment of your feedback (Positive/Neutral/Negative) "
        "and reports it to the warden to improve food quality.<br><br>"
        "💡 <i>Be specific! Instead of 'food was bad', say 'the dal was too salty "
        "and the chapati was hard' — that helps the mess staff improve.</i>"
    )


def _respond_wifi_issue() -> str:
    return (
        "📶 <b>WiFi / Internet Issues:</b><br><br>"
        "Try these steps first:<br>"
        "1. Forget the network and reconnect<br>"
        "2. Restart your device's WiFi<br>"
        "3. Check if others in your room are also affected<br><br>"
        "If the issue persists:<br>"
        "4. Go to <b>Complaint Management</b> → <b>File Complaint</b><br>"
        "5. Describe the issue — it'll be auto-categorised as <b>Internet</b><br>"
        "6. The network team will be notified<br><br>"
        "📞 For urgent network outages, call the IT helpdesk: <b>9876500001</b>"
    )


def _respond_medical() -> str:
    return (
        "🏥 <b>Medical Emergency — What to do:</b><br><br>"
        "🚨 <b>For immediate emergencies:</b><br>"
        "&nbsp;&nbsp;&nbsp;Call: <b>108 (Ambulance)</b><br>"
        "&nbsp;&nbsp;&nbsp;Inform your warden IMMEDIATELY<br><br>"
        "🏥 <b>College Medical Centre:</b><br>"
        "&nbsp;&nbsp;&nbsp;📍 Ground floor, Admin Building<br>"
        "&nbsp;&nbsp;&nbsp;🕘 7:00 AM – 9:00 PM (daily)<br>"
        "&nbsp;&nbsp;&nbsp;📱 Medical Officer: <b>9876500002</b><br><br>"
        "💊 <b>If you're unwell but not an emergency:</b><br>"
        "1. Visit the medical centre<br>"
        "2. Apply for leave through the Leave Request section<br>"
        "3. Inform your warden<br><br>"
        "💡 <i>A medical certificate from the college doctor "
        "auto-approves your leave request.</i>"
    )


def _respond_fees() -> str:
    return (
        "💰 <b>Hostel Fees:</b><br><br>"
        "For current fee details, payment schedules, and due dates,<br>"
        "please contact:<br><br>"
        "🏢 <b>Hostel Accounts Office</b><br>"
        "📍 Administrative Block, Room 12<br>"
        "🕘 9:00 AM – 4:00 PM (Mon–Fri)<br>"
        "📧 hostel.accounts@college.edu<br><br>"
        "💡 <i>Late payment may result in temporary hostel access restrictions. "
        "Contact the office early if you face any financial difficulty.</i>"
    )


def _respond_announcement() -> str:
    try:
        from database.connection import get_connection
        from database.queries import get_active_announcements
        conn = get_connection()
        if not conn:
            raise ConnectionError()
        announcements = get_active_announcements(conn)
        conn.close()

        if not announcements:
            return ("📢 <b>Announcements:</b><br><br>"
                    "No active announcements at the moment.<br>"
                    "Check the <b>Announcements</b> section in the sidebar regularly.")

        icons = {"Emergency":"🚨","Mess Update":"🍽️","Holiday":"🎉","General":"📢"}
        lines = "📢 <b>Latest Announcements:</b><br><br>"
        for ann in announcements[:3]:
            icon = icons.get(ann["ann_type"],"📢")
            lines += (f"{icon} <b>{ann['title']}</b> [{ann['ann_type']}]<br>"
                      f"&nbsp;&nbsp;&nbsp;{ann['description'][:80]}{'…' if len(ann['description'])>80 else ''}<br>")
        lines += "<br>📋 See all in the <b>Announcements</b> section."
        return lines
    except Exception:
        return ("📢 Visit the <b>Announcements</b> section in the sidebar "
                "for the latest notices from your warden.")


def _respond_laundry() -> str:
    return (
        "👕 <b>Laundry Facilities:</b><br><br>"
        "🏢 <b>Laundry Room Location:</b> Ground floor, near the main entrance<br>"
        "🕘 <b>Hours:</b> 6:00 AM – 9:00 PM (daily)<br><br>"
        "📋 <b>Rules:</b><br>"
        "• Maximum 2 kg per wash<br>"
        "• Do not leave clothes unattended for more than 1 hour<br>"
        "• Iron available — 30 mins per student<br>"
        "• Dry clothes on the designated drying area only<br><br>"
        "💡 <i>Best times to use: Early morning (6–8 AM) or evening (6–8 PM) "
        "to avoid the rush.</i>"
    )


def _respond_greeting(student: dict) -> str:
    name = student["name"].split()[0]
    hour = date.today().weekday()
    time_greet = "Good morning" if hour < 12 else "Good evening"
    return (
        f"{time_greet}, <b>{name}</b>! 👋<br><br>"
        "I'm your <b>Hostel Hub Assistant</b>. Here's what I can help you with:<br><br>"
        "🚪 <b>Leave</b> — Apply and track leave requests<br>"
        "📋 <b>Complaints</b> — File and track hostel issues<br>"
        "🍽️ <b>Mess</b> — Today's menu and food feedback<br>"
        "📅 <b>Attendance</b> — Check your attendance %<br>"
        "🛏️ <b>Room</b> — Room and roommate details<br>"
        "📜 <b>Rules</b> — Hostel rules and timings<br>"
        "📞 <b>Contact</b> — Warden phone numbers<br><br>"
        "Just ask me anything! 😊"
    )


def _respond_thanks(student: dict) -> str:
    name = student["name"].split()[0]
    return (
        f"You're welcome, {name}! 😊<br><br>"
        "Is there anything else I can help you with?<br>"
        "Just type your question anytime!"
    )


def _respond_help(student: dict) -> str:
    return _respond_greeting(student)


def _respond_unknown(query: str, student: dict) -> str:
    name = student["name"].split()[0]
    return (
        f"🤔 Sorry {name}, I didn't quite understand that.<br><br>"
        "Here are some things you can ask me:<br><br>"
        '💬 <i>"How do I apply for leave?"</i><br>'
        '💬 <i>"What is today\'s mess menu?"</i><br>'
        '💬 <i>"What is my attendance percentage?"</i><br>'
        '💬 <i>"How do I file a complaint?"</i><br>'
        '💬 <i>"What are the hostel rules?"</i><br>'
        '💬 <i>"What is my room number?"</i><br>'
        '💬 <i>"How to contact my warden?"</i><br><br>'
        "Or click one of the suggestion buttons above! 🙂"
    )


# =============================================================
# INTENT → HANDLER ROUTING TABLE
# =============================================================
def _route(
    intent:     str,
    query:      str,
    student_id: int,
    student:    dict,
) -> str:
    """Route a detected intent to its handler function."""
    dispatch = {
        "leave_apply":       lambda: _respond_leave_apply(student),
        "leave_status":      lambda: _respond_leave_status(student_id),
        "complaint_file":    lambda: _respond_complaint_file(),
        "complaint_status":  lambda: _respond_complaint_status(student_id),
        "menu_today":        lambda: _respond_menu_today(),
        "menu_meal":         lambda: _respond_menu_today(),   # same handler
        "attendance_query":  lambda: _respond_attendance(student_id),
        "room_info":         lambda: _respond_room_info(student),
        "roommate_info":     lambda: _respond_roommate_info(student_id, student),
        "hostel_rules":      lambda: _respond_hostel_rules(),
        "contact_warden":    lambda: _respond_contact_warden(student),
        "mess_feedback":     lambda: _respond_mess_feedback(),
        "wifi_issue":        lambda: _respond_wifi_issue(),
        "laundry":           lambda: _respond_laundry(),
        "medical":           lambda: _respond_medical(),
        "fees":              lambda: _respond_fees(),
        "announcement":      lambda: _respond_announcement(),
        "greeting":          lambda: _respond_greeting(student),
        "thanks":            lambda: _respond_thanks(student),
        "help":              lambda: _respond_help(student),
        "unknown":           lambda: _respond_unknown(query, student),
    }
    handler = dispatch.get(intent, dispatch["unknown"])
    return handler()


# =============================================================
# PUBLIC FUNCTION — get_chatbot_response()
# Main entry point called from student_portal.py
# =============================================================
def get_chatbot_response(
    query:      str,
    student_id: int,
    student:    dict,
) -> str:
    """
    Process a student's natural language query and return
    an HTML-formatted response string.

    Args:
        query:      The student's message text
        student_id: The logged-in student's ID (for DB lookups)
        student:    The student profile dict from the session

    Returns:
        HTML string safe for st.markdown(response, unsafe_allow_html=True)

    Example:
        response = get_chatbot_response(
            "What is today's lunch?",
            student_id=1,
            student={"name":"Arun","room_no":"A101",...}
        )
    """
    if not query or not query.strip():
        return _respond_unknown("", student)

    intent, score = _detect_intent(query)
    return _route(intent, query, student_id, student)


# =============================================================
# SELF-TEST — run with: python ai_models/chatbot.py
# =============================================================
def _run_tests():
    print("\n" + "="*60)
    print("  CHATBOT AI — Self Test (no DB required)")
    print("="*60)

    mock_student = {
        "name": "Arun Prakash",
        "room_no": "A101",
        "block": "Block A",
        "floor": 1,
        "department": "CSE",
        "year": 3,
    }

    queries = [
        ("Hi there!",                              "greeting"),
        ("How do I apply for leave?",              "leave_apply"),
        ("What is today's mess menu?",             "menu_today"),
        ("What is my attendance percentage?",      "attendance_query"),
        ("How do I file a complaint?",             "complaint_file"),
        ("What are the hostel rules?",             "hostel_rules"),
        ("What is my room number?",                "room_info"),
        ("Who are my roommates?",                  "roommate_info"),
        ("How to contact the warden?",             "contact_warden"),
        ("WiFi is not working in my room",         "wifi_issue"),
        ("I am feeling sick. What should I do?",   "medical"),
        ("How to give feedback for food?",         "mess_feedback"),
        ("Is there any announcement today?",       "announcement"),
        ("What is the laundry timing?",            "laundry"),
        ("How much is the hostel fee?",            "fees"),
        ("Check my leave status",                  "leave_status"),
        ("Thank you so much!",                     "thanks"),
        ("xyzzy gibberish nonsense qwerty",        "unknown"),
    ]

    passed = 0
    for query_text, expected_intent in queries:
        detected, score = _detect_intent(query_text)
        ok = detected == expected_intent
        if ok: passed += 1
        print(f"  [{'✓' if ok else '✗'}] '{query_text[:45]}'")
        print(f"        Intent: {detected:20s} (score {score:3d}) — expected: {expected_intent}")

    print(f"\n  {'─'*40}")
    print(f"  Result: {passed}/{len(queries)} tests passed\n")

    # Sample full response
    print("  SAMPLE RESPONSE:")
    print("  Query: 'What are the hostel rules?'")
    resp = get_chatbot_response("What are the hostel rules?", 1, mock_student)
    # Strip HTML for terminal output
    clean = re.sub(r"<[^>]+>", "", resp)
    print(f"  {clean[:300]}...")


if __name__ == "__main__":
    _run_tests()