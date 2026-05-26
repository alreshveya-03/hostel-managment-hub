# =============================================================
#  HOSTEL HUB — pages/student_portal.py
#  Complete Student Portal — All 9 Sections
# =============================================================

import streamlit as st
import matplotlib.pyplot as plt
from datetime import date
from database.connection import get_connection
from database.queries import (
    get_student_by_id, get_room_by_no, get_roommates,
    get_complaints_by_student, add_complaint,
    get_leaves_by_student, apply_leave,
    get_attendance_by_student, get_attendance_percentage,
    get_active_announcements, get_announcements_by_type,
    get_menu_by_date, get_recent_menus,
    mark_meal_attendance, get_meal_history_by_student,
    add_food_feedback, get_feedback_by_student,
    update_student,
)
from utils.auth_utils import require_student_login
from utils.constants import (
    COMPLAINT_CATEGORIES, COMPLAINT_STATUSES,
    PRIORITY_COLORS, PRIORITY_ICONS, STATUS_ICONS,
    LEAVE_STATUS_ICONS,
    MEAL_TYPES, MEAL_ICONS,
    ANNOUNCEMENT_ICONS, ANNOUNCEMENT_COLORS,
    SENTIMENT_ICONS, SENTIMENT_COLORS,
    DEPARTMENTS, FOOD_PREFERENCES,
)

try:
    from ai_models.complaint_ai import detect_category, detect_priority
    AI_COMPLAINT_READY = True
except ImportError:
    AI_COMPLAINT_READY = False

try:
    from ai_models.sentiment import analyze_sentiment
    AI_SENTIMENT_READY = True
except ImportError:
    AI_SENTIMENT_READY = False


# =============================================================
# SHARED CSS
# =============================================================
def _inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    :root {
        --blue:#2D6BE4;--blue-lt:#EEF3FD;--blue-mid:#DBEAFE;
        --green:#16A34A;--green-lt:#F0FDF4;
        --amber:#D97706;--amber-lt:#FFFBEB;
        --red:#DC2626;--red-lt:#FEF2F2;
        --purple:#7C3AED;--purple-lt:#F5F3FF;
        --text-1:#0F172A;--text-2:#475569;--text-3:#94A3B8;
        --border:#E2E8F0;--surface:#FFFFFF;--bg:#F8FAFC;
        --radius:12px;--shadow:0 2px 12px rgba(0,0,0,.07);
    }
    html,[class*="css"]{font-family:'DM Sans',sans-serif!important;}
    #MainMenu,footer,header{visibility:hidden}
    .block-container{padding-top:1.5rem!important;padding-bottom:3rem!important;}
    [data-testid="stSidebar"]{background:#FAFBFF!important;border-right:1px solid var(--border)!important;}
    .kpi-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow);transition:transform .2s;}
    .kpi-card:hover{transform:translateY(-2px);}
    .kpi-value{font-size:1.9rem;font-weight:700;line-height:1;margin-bottom:2px;}
    .kpi-label{font-size:.78rem;font-weight:500;color:var(--text-2);text-transform:uppercase;letter-spacing:.04em;}
    .kpi-delta{font-size:.75rem;margin-top:4px;}
    .sec-header{display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--border);padding-bottom:10px;margin-bottom:1.2rem;}
    .sec-icon{font-size:1.4rem;}
    .sec-title{font-size:1.15rem;font-weight:700;color:var(--text-1);}
    .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;letter-spacing:.03em;}
    .info-row{display:flex;gap:8px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--border);}
    .info-key{min-width:140px;font-size:.82rem;color:var(--text-3);font-weight:500;}
    .info-val{font-size:.88rem;color:var(--text-1);font-weight:500;}
    .comp-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;margin-bottom:10px;box-shadow:var(--shadow);}
    .chat-user{background:var(--blue);color:#fff;border-radius:18px 18px 4px 18px;padding:10px 16px;margin:6px 0 6px 20%;font-size:.88rem;line-height:1.5;}
    .chat-bot{background:var(--surface);border:1px solid var(--border);border-radius:18px 18px 18px 4px;padding:10px 16px;margin:6px 20% 6px 0;font-size:.88rem;line-height:1.5;box-shadow:var(--shadow);}
    .chat-bot-name{font-size:.72rem;color:var(--text-3);margin-bottom:2px;}
    .ann-card{border-radius:var(--radius);padding:16px 18px;margin-bottom:10px;border-left:4px solid;}
    .meal-card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:14px 16px;height:100%;box-shadow:var(--shadow);}
    .meal-title{font-weight:700;font-size:.88rem;margin-bottom:6px;}
    .meal-items{font-size:.82rem;color:var(--text-2);line-height:1.6;}
    .stTabs [data-baseweb="tab-list"]{gap:4px;background:#F1F5F9;border-radius:10px;padding:4px;border:1px solid var(--border);}
    .stTabs [data-baseweb="tab"]{border-radius:7px!important;font-size:.85rem!important;padding:7px 16px!important;}
    .stTabs [aria-selected="true"]{background:var(--blue)!important;color:#fff!important;}
    .stTextInput>div>div>input,.stTextArea>div>textarea{border:1.5px solid var(--border)!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;}
    .stButton>button{border-radius:8px!important;font-weight:600!important;font-family:'DM Sans',sans-serif!important;transition:all .2s!important;}
    .att-present{background:#DCFCE7;color:#166534;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600;}
    .att-absent{background:#FEE2E2;color:#991B1B;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600;}
    .att-leave{background:#FEF3C7;color:#92400E;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:600;}
    </style>
    """, unsafe_allow_html=True)


# =============================================================
# HELPERS
# =============================================================
def _sec(icon, title):
    st.markdown(f'<div class="sec-header"><span class="sec-icon">{icon}</span><span class="sec-title">{title}</span></div>', unsafe_allow_html=True)

def _badge(text, color, bg):
    return f'<span class="badge" style="background:{bg};color:{color};">{text}</span>'

def _kpi(label, value, icon, color, bg, delta=""):
    delta_html = f'<div class="kpi-delta" style="color:{color};">{delta}</div>' if delta else ""
    st.markdown(f'<div class="kpi-card" style="border-top:3px solid {color};"><div style="font-size:1.6rem;margin-bottom:6px;">{icon}</div><div class="kpi-value" style="color:{color};">{value}</div><div class="kpi-label">{label}</div>{delta_html}</div>', unsafe_allow_html=True)

def _chart_style(ax, fig):
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#E2E8F0")
    ax.tick_params(colors="#475569", labelsize=9)
    ax.yaxis.grid(True, color="#E2E8F0", linestyle="--", alpha=.7)
    ax.set_axisbelow(True)


# =============================================================
# SECTION 1 — DASHBOARD
# =============================================================
def render_dashboard(student_id, student):
    _sec("📊", "Dashboard Overview")
    conn = get_connection()
    if not conn:
        st.error("Database connection failed."); return
    try:
        complaints  = get_complaints_by_student(conn, student_id)
        leaves      = get_leaves_by_student(conn, student_id)
        att_pct     = get_attendance_percentage(conn, student_id)
        att_history = get_attendance_by_student(conn, student_id)
        meal_hist   = get_meal_history_by_student(conn, student_id, days=7)
    finally:
        conn.close()

    pending_c   = sum(1 for c in complaints if c["status"] == "Pending")
    approved_l  = sum(1 for l in leaves if l["status"] == "Approved")
    meals_count = sum(1 for m in meal_hist if m["attended"])

    c1,c2,c3,c4 = st.columns(4)
    with c1: _kpi("Attendance",     f"{att_pct:.0f}%",  "📅","#2D6BE4","#EEF3FD","🟢 Good" if att_pct>=75 else "🔴 Low")
    with c2: _kpi("Complaints",     len(complaints),     "📋","#7C3AED","#F5F3FF",f"{pending_c} pending")
    with c3: _kpi("Leave Requests", len(leaves),         "🚪","#D97706","#FFFBEB",f"{approved_l} approved")
    with c4: _kpi("Meals This Week",meals_count,         "🍽️","#16A34A","#F0FDF4","of 28 possible")

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("**Attendance Breakdown**")
        if att_history:
            counts = {"Present":0,"Absent":0,"Leave":0}
            for r in att_history: counts[r["status"]] = counts.get(r["status"],0)+1
            fig,ax = plt.subplots(figsize=(4,3.2))
            wedges,texts,autotexts = ax.pie(
                counts.values(), labels=counts.keys(), autopct="%1.0f%%",
                colors=["#2D6BE4","#DC2626","#D97706"],
                wedgeprops={"width":.55,"edgecolor":"white","linewidth":2}, startangle=90)
            for t in texts: t.set_fontsize(9); t.set_color("#475569")
            for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
            ax.set_title("All-time attendance",fontsize=9,color="#475569",pad=8)
            fig.patch.set_facecolor("white")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        else:
            st.info("No attendance data yet.")

    with ch2:
        st.markdown("**Complaint Status**")
        if complaints:
            s_counts = {"Pending":0,"In Progress":0,"Resolved":0}
            for c in complaints: s_counts[c["status"]] = s_counts.get(c["status"],0)+1
            fig,ax = plt.subplots(figsize=(4,3.2))
            bars = ax.bar(s_counts.keys(),s_counts.values(),color=["#FCA5A5","#FCD34D","#86EFAC"],edgecolor="white",linewidth=1.5,width=.5)
            for bar,val in zip(bars,s_counts.values()):
                if val>0: ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.05,str(val),ha="center",va="bottom",fontsize=10,fontweight="bold",color="#475569")
            _chart_style(ax,fig); ax.set_ylabel("Count",fontsize=9,color="#475569"); ax.set_title("Your complaints",fontsize=9,color="#475569")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        else:
            st.info("No complaints filed yet.")

    st.markdown("---")
    st.markdown("**Recent Complaints**")
    if complaints:
        for c in complaints[:3]:
            p_col = PRIORITY_COLORS.get(c["priority"],"#475569")
            p_bg  = {"Normal":"#DCFCE7","Urgent":"#FEF3C7","Emergency":"#FEE2E2"}.get(c["priority"],"#F1F5F9")
            st.markdown(f"""<div class="comp-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span style="font-weight:600;font-size:.9rem;">{c['category']}</span>
                    <div style="display:flex;gap:6px;">{_badge(c['priority'],p_col,p_bg)}{_badge(STATUS_ICONS.get(c['status'],'')+' '+c['status'],'#475569','#F1F5F9')}</div>
                </div>
                <div style="font-size:.83rem;color:#475569;">{c['complaint_text'][:120]}{'...' if len(c['complaint_text'])>120 else ''}</div>
                <div style="font-size:.73rem;color:#94A3B8;margin-top:6px;">Filed: {c['filed_date']}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No complaints yet. You're all good! 🎉")


# =============================================================
# SECTION 2 — PROFILE
# =============================================================
def render_profile(student_id, student):
    _sec("👤","My Profile")
    view_tab,edit_tab = st.tabs(["📋  View Profile","✏️  Edit Profile"])

    with view_tab:
        col1,col2 = st.columns([1,2])
        with col1:
            initials = "".join([n[0] for n in student["name"].split()[:2]])
            st.markdown(f"""<div style="width:100px;height:100px;border-radius:50%;background:linear-gradient(135deg,#2D6BE4,#7C3AED);display:flex;align-items:center;justify-content:center;font-size:2rem;font-weight:700;color:white;margin:0 auto 1rem;box-shadow:0 6px 20px rgba(45,107,228,.3);">{initials}</div>
            <div style="text-align:center;font-weight:700;font-size:1.05rem;">{student['name']}</div>
            <div style="text-align:center;font-size:.8rem;color:#64748B;margin-top:2px;">{student['department']} · Year {student['year']}</div>""", unsafe_allow_html=True)
        with col2:
            fields = [("Register No.",student.get("register_number","—"),"🎓"),("Department",student.get("department","—"),"🏛️"),("Year",f"Year {student.get('year','—')}","📚"),("Room No.",student.get("room_no") or "Not Allocated","🛏️"),("Block",student.get("block") or "—","🏢"),("Phone",student.get("phone","—"),"📱"),("Email",student.get("email","—"),"📧"),("Gender",student.get("gender","—"),"👤"),("Food Pref",student.get("food_preference","—"),"🍽️")]
            for label,value,icon in fields:
                st.markdown(f'<div class="info-row"><span class="info-key">{icon} {label}</span><span class="info-val">{value}</span></div>',unsafe_allow_html=True)
            if student.get("address"):
                st.markdown(f'<div class="info-row"><span class="info-key">📍 Address</span><span class="info-val">{student["address"]}</span></div>',unsafe_allow_html=True)

    with edit_tab:
        st.markdown("**Update your personal details below.**")
        with st.form("edit_profile_form"):
            c1,c2 = st.columns(2)
            with c1:
                new_name  = st.text_input("Full Name",  value=student.get("name",""),  max_chars=100)
                new_phone = st.text_input("Phone",      value=student.get("phone",""), max_chars=15)
                new_dept  = st.selectbox("Department",  DEPARTMENTS, index=DEPARTMENTS.index(student["department"]) if student.get("department") in DEPARTMENTS else 0)
            with c2:
                new_email = st.text_input("Email",      value=student.get("email",""), max_chars=100)
                new_year  = st.selectbox("Year",        [1,2,3,4,5], index=(student.get("year",1)-1))
                new_food  = st.selectbox("Food Preference", FOOD_PREFERENCES, index=FOOD_PREFERENCES.index(student["food_preference"]) if student.get("food_preference") in FOOD_PREFERENCES else 0)
            new_addr = st.text_area("Address", value=student.get("address","") or "", height=80, max_chars=300)
            if st.form_submit_button("💾  Save Changes", use_container_width=True):
                if not new_name.strip():
                    st.error("Name cannot be empty.")
                elif len(new_phone.strip()) < 10:
                    st.error("Enter a valid 10-digit phone number.")
                elif "@" not in new_email:
                    st.error("Enter a valid email address.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            update_student(conn,student_id,new_name.strip(),new_phone.strip(),new_email.strip(),new_dept,new_year,new_food,new_addr.strip())
                            st.success("✅ Profile updated successfully!"); st.rerun()
                        except Exception as e:
                            st.error(f"Update failed: {e}")
                        finally:
                            conn.close()


# =============================================================
# SECTION 3 — ROOM DETAILS
# =============================================================
def render_room(student_id, student):
    _sec("🛏️","Room Details")
    room_no = student.get("room_no")
    if not room_no:
        st.warning("⚠️ You have not been allocated a room yet. Contact your warden."); return
    conn = get_connection()
    if not conn:
        st.error("Database connection failed."); return
    try:
        room      = get_room_by_no(conn, room_no)
        roommates = get_roommates(conn, room_no, student_id)
    finally:
        conn.close()
    if not room:
        st.warning("Room details not found. Contact warden."); return

    c1,c2,c3,c4 = st.columns(4)
    with c1: _kpi("Room Number",room["room_no"],"🚪","#2D6BE4","#EEF3FD")
    with c2: _kpi("Block",room["block"],"🏢","#7C3AED","#F5F3FF")
    with c3: _kpi("Floor",f"Floor {room['floor']}","🏗️","#D97706","#FFFBEB")
    with c4: _kpi("Room Type",room["room_type"],"⭐","#16A34A","#F0FDF4")
    st.markdown("<div style='height:1rem'></div>",unsafe_allow_html=True)

    col1,col2 = st.columns(2)
    with col1:
        st.markdown("**Room Specifications**")
        specs = [("Capacity",f"{room['capacity']} beds","🛏️"),("Occupied",f"{room['occupied']} beds","👥"),("Available Beds",str(room['available_beds']),"✅"),("AC Available","Yes ❄️" if room.get("ac_available") else "No","🌡️"),("Status",room.get("occupancy_status","—"),"📊")]
        for label,val,icon in specs:
            st.markdown(f'<div class="info-row"><span class="info-key">{icon} {label}</span><span class="info-val">{val}</span></div>',unsafe_allow_html=True)
        pct = (room["occupied"]/room["capacity"]*100) if room["capacity"] else 0
        bar_color = "#DC2626" if pct>=100 else "#D97706" if pct>=66 else "#16A34A"
        st.markdown(f"""<div style="margin-top:14px;"><div style="font-size:.78rem;color:#94A3B8;margin-bottom:4px;">Occupancy</div><div style="background:#E2E8F0;border-radius:20px;height:10px;overflow:hidden;"><div style="width:{pct:.0f}%;height:100%;background:{bar_color};border-radius:20px;"></div></div><div style="font-size:.75rem;color:{bar_color};margin-top:3px;font-weight:600;">{pct:.0f}% occupied</div></div>""",unsafe_allow_html=True)

    with col2:
        st.markdown(f"**Roommates ({len(roommates)} found)**")
        if roommates:
            palette = ["#2D6BE4","#7C3AED","#16A34A","#D97706"]
            for i,rm in enumerate(roommates,1):
                initials = "".join([n[0] for n in rm["name"].split()[:2]])
                c = palette[i % len(palette)]
                st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;background:white;border:1px solid #E2E8F0;border-radius:10px;padding:12px 14px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.05);">
                    <div style="width:42px;height:42px;border-radius:50%;background:{c};display:flex;align-items:center;justify-content:center;font-size:.9rem;font-weight:700;color:white;flex-shrink:0;">{initials}</div>
                    <div><div style="font-weight:600;font-size:.9rem;">{rm['name']}</div><div style="font-size:.78rem;color:#64748B;">{rm['department']} · Year {rm['year']}</div><div style="font-size:.75rem;color:#94A3B8;font-family:'DM Mono',monospace;">{rm['register_number']}</div></div>
                </div>""",unsafe_allow_html=True)
        else:
            st.info("You currently have no roommates. Enjoy the space! 😄")


# =============================================================
# SECTION 4 — COMPLAINTS
# =============================================================
def render_complaints(student_id):
    _sec("📋","Complaint Management")
    submit_tab,history_tab = st.tabs(["➕  File Complaint","📜  My Complaints"])

    with submit_tab:
        st.markdown("**Describe your issue. AI will auto-detect category and priority.**")
        with st.form("complaint_form"):
            complaint_text = st.text_area("Describe your complaint", placeholder="e.g. The fan in my room is not working since yesterday...", height=130, max_chars=1000)
            c1,c2 = st.columns(2)
            with c1: manual_cat = st.selectbox("Category (AI override)", COMPLAINT_CATEGORIES)
            with c2: manual_pri = st.selectbox("Priority (AI override)", ["Normal","Urgent","Emergency"])
            submitted = st.form_submit_button("🚀  Submit Complaint", use_container_width=True)
        if submitted:
            if not complaint_text.strip():
                st.error("⚠️ Complaint text cannot be empty.")
            elif len(complaint_text.strip()) < 10:
                st.error("⚠️ Please describe your issue in at least 10 characters.")
            else:
                category = detect_category(complaint_text) if AI_COMPLAINT_READY else manual_cat
                priority = detect_priority(complaint_text)  if AI_COMPLAINT_READY else manual_pri
                conn = get_connection()
                if conn:
                    try:
                        cid = add_complaint(conn,student_id,complaint_text.strip(),category,priority,date.today())
                        st.success(f"✅ Complaint #{cid} filed successfully!")
                        st.markdown(f'<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:10px;padding:12px 16px;margin-top:8px;font-size:.85rem;">AI detected → Category: <b>{category}</b> · Priority: <b style="color:{PRIORITY_COLORS.get(priority,"#475569")}">{priority}</b></div>',unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Failed: {e}")
                    finally:
                        conn.close()

    with history_tab:
        conn = get_connection()
        if not conn: st.error("Database error"); return
        try:
            complaints = get_complaints_by_student(conn, student_id)
        finally:
            conn.close()
        if not complaints:
            st.info("You haven't filed any complaints yet."); return
        status_filter = st.selectbox("Filter by status",["All"]+COMPLAINT_STATUSES,key="comp_filter")
        filtered = [c for c in complaints if status_filter=="All" or c["status"]==status_filter]
        st.markdown(f"Showing **{len(filtered)}** of {len(complaints)} complaints")
        for c in filtered:
            pri=c["priority"]; sts=c["status"]
            p_col=PRIORITY_COLORS.get(pri,"#475569")
            p_bg={"Normal":"#DCFCE7","Urgent":"#FEF3C7","Emergency":"#FEE2E2"}.get(pri,"#F1F5F9")
            s_bg={"Pending":"#F1F5F9","In Progress":"#FEF3C7","Resolved":"#DCFCE7"}.get(sts,"#F1F5F9")
            s_col={"Pending":"#475569","In Progress":"#92400E","Resolved":"#166534"}.get(sts,"#475569")
            with st.expander(f"{PRIORITY_ICONS.get(pri,'')}  {c['category']}  ·  {sts}  ·  {c['filed_date']}", expanded=False):
                st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:10px;">{_badge(pri,p_col,p_bg)}{_badge(STATUS_ICONS.get(sts,'')+' '+sts,s_col,s_bg)}{_badge(c['category'],'#475569','#F1F5F9')}</div>
                <div style="font-size:.88rem;color:#0F172A;margin-bottom:10px;line-height:1.6;">{c['complaint_text']}</div>""",unsafe_allow_html=True)
                if c.get("warden_remarks"):
                    st.markdown(f'<div style="background:#F0FDF4;border-left:3px solid #16A34A;padding:10px 14px;border-radius:0 8px 8px 0;font-size:.83rem;"><b>Warden Response:</b><br>{c["warden_remarks"]}</div>',unsafe_allow_html=True)
                if c.get("resolved_date"):
                    st.caption(f"✅ Resolved: {c['resolved_date']}")


# =============================================================
# SECTION 5 — LEAVE
# =============================================================
def render_leave(student_id):
    _sec("🚪","Leave Request")
    apply_tab,history_tab = st.tabs(["📝  Apply Leave","📜  Leave History"])

    with apply_tab:
        st.markdown("**Fill in your leave details. Warden will review and respond.**")
        with st.form("leave_form"):
            reason = st.text_area("Reason for Leave", placeholder="e.g. Going home for family function / Medical appointment...", height=110, max_chars=500)
            c1,c2 = st.columns(2)
            with c1: from_date = st.date_input("From Date", value=date.today(), min_value=date.today())
            with c2: to_date   = st.date_input("To Date",   value=date.today(), min_value=date.today())
            submitted = st.form_submit_button("📤  Submit Leave Request", use_container_width=True)
        if submitted:
            if not reason.strip():        st.error("⚠️ Please provide a reason.")
            elif len(reason.strip())<10:  st.error("⚠️ Reason must be at least 10 characters.")
            elif to_date < from_date:     st.error("⚠️ End date cannot be before start date.")
            else:
                num_days = (to_date - from_date).days + 1
                conn = get_connection()
                if conn:
                    try:
                        lid = apply_leave(conn,student_id,reason.strip(),from_date.strftime("%Y-%m-%d"),to_date.strftime("%Y-%m-%d"))
                        st.success(f"✅ Leave request #{lid} submitted for {num_days} day(s)!")
                        st.info("⏳ Pending warden approval.")
                    except Exception as e:
                        st.error(f"Failed: {e}")
                    finally:
                        conn.close()

    with history_tab:
        conn = get_connection()
        if not conn: st.error("Database error"); return
        try:
            leaves = get_leaves_by_student(conn, student_id)
        finally:
            conn.close()
        if not leaves:
            st.info("No leave requests found."); return
        counts={"Pending":0,"Approved":0,"Rejected":0}
        for l in leaves: counts[l["status"]]=counts.get(l["status"],0)+1
        c1,c2,c3=st.columns(3)
        c1.metric("⏳ Pending",counts["Pending"]); c2.metric("✅ Approved",counts["Approved"]); c3.metric("❌ Rejected",counts["Rejected"])
        st.markdown("---")
        for l in leaves:
            sts=l["status"]
            s_col={"Pending":"#92400E","Approved":"#166534","Rejected":"#991B1B"}.get(sts,"#475569")
            s_bg={"Pending":"#FEF3C7","Approved":"#DCFCE7","Rejected":"#FEE2E2"}.get(sts,"#F1F5F9")
            try: num_days=(l["to_date"]-l["from_date"]).days+1
            except: num_days="—"
            with st.expander(f"{LEAVE_STATUS_ICONS.get(sts,'')}  {l['from_date']} → {l['to_date']}  ·  {num_days} day(s)  ·  {sts}"):
                st.markdown(f"""<div style="display:flex;gap:8px;margin-bottom:10px;">{_badge(LEAVE_STATUS_ICONS.get(sts,'')+' '+sts,s_col,s_bg)}{_badge(str(num_days)+' day(s)','#475569','#F1F5F9')}</div>
                <div style="font-size:.88rem;color:#0F172A;margin-bottom:6px;"><b>Reason:</b> {l['reason']}</div>
                <div style="font-size:.78rem;color:#94A3B8;">Applied: {str(l['applied_on'])[:10]}</div>""",unsafe_allow_html=True)
                if l.get("warden_remarks"):
                    st.markdown(f'<div style="background:#EFF6FF;border-left:3px solid #2D6BE4;padding:10px 14px;border-radius:0 8px 8px 0;font-size:.83rem;margin-top:8px;"><b>Warden Remarks:</b><br>{l["warden_remarks"]}</div>',unsafe_allow_html=True)


# =============================================================
# SECTION 6 — ATTENDANCE
# =============================================================
def render_attendance(student_id):
    _sec("📅","Attendance")
    conn = get_connection()
    if not conn: st.error("Database error"); return
    try:
        history = get_attendance_by_student(conn, student_id)
        pct     = get_attendance_percentage(conn, student_id)
    finally:
        conn.close()

    col1,col2 = st.columns([1,2])
    with col1:
        gauge_color = "#16A34A" if pct>=75 else "#D97706" if pct>=60 else "#DC2626"
        status_text = "Excellent ✨" if pct>=90 else "Good 👍" if pct>=75 else "Low ⚠️" if pct>=60 else "Critical 🔴"
        st.markdown(f"""<div style="background:linear-gradient(135deg,{gauge_color}15,{gauge_color}08);border:2px solid {gauge_color}40;border-radius:16px;padding:28px 20px;text-align:center;">
            <div style="font-size:3rem;font-weight:800;color:{gauge_color};line-height:1;">{pct:.1f}%</div>
            <div style="font-size:.85rem;color:{gauge_color};font-weight:600;margin-top:4px;">{status_text}</div>
            <div style="font-size:.75rem;color:#94A3B8;margin-top:8px;">Overall Attendance</div>
        </div>""",unsafe_allow_html=True)
        if pct < 75: st.warning("⚠️ Attendance below 75%! Please inform your warden.")

    with col2:
        if history:
            counts_s={"Present":0,"Absent":0,"Leave":0}
            for h in history: counts_s[h["status"]]=counts_s.get(h["status"],0)+1
            fig,ax=plt.subplots(figsize=(5,3))
            bars=ax.bar(counts_s.keys(),counts_s.values(),color=["#86EFAC","#FCA5A5","#FCD34D"],edgecolor="white",linewidth=1.5,width=.45)
            for bar,val in zip(bars,counts_s.values()):
                ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.1,str(val),ha="center",va="bottom",fontsize=11,fontweight="bold",color="#475569")
            _chart_style(ax,fig); ax.set_title("Attendance summary",fontsize=9,color="#475569"); ax.set_ylabel("Days",fontsize=9,color="#475569")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown("---"); st.markdown("**Attendance History (last 30 records)**")
    if not history:
        st.info("No attendance records found."); return
    rows=[]
    for h in history[:30]:
        sts=h["status"]
        pill={"Present":"att-present","Absent":"att-absent","Leave":"att-leave"}.get(sts,"")
        rows.append({"Date":str(h["att_date"]),"Status":f'<span class="{pill}">{sts}</span>',"Marked By":h.get("marked_by","—")})
    tbl="<table style='width:100%;border-collapse:collapse;font-size:.85rem;'><thead><tr>"
    for col in ["Date","Status","Marked By"]:
        tbl+=f"<th style='text-align:left;padding:8px 12px;background:#F8FAFC;border-bottom:2px solid #E2E8F0;font-size:.78rem;color:#475569;text-transform:uppercase;letter-spacing:.04em;'>{col}</th>"
    tbl+="</tr></thead><tbody>"
    for i,row in enumerate(rows):
        bg="#FFFFFF" if i%2==0 else "#F8FAFC"
        tbl+=f"<tr style='background:{bg};'>"
        for col in ["Date","Status","Marked By"]:
            tbl+=f"<td style='padding:8px 12px;border-bottom:1px solid #F1F5F9;'>{row[col]}</td>"
        tbl+="</tr>"
    tbl+="</tbody></table>"
    st.markdown(tbl, unsafe_allow_html=True)


# =============================================================
# SECTION 7 — ANNOUNCEMENTS
# =============================================================
def render_announcements():
    _sec("📢","Announcements")
    conn = get_connection()
    if not conn: st.error("Database error"); return
    try:
        all_ann   = get_active_announcements(conn)
        emergency = get_announcements_by_type(conn,"Emergency")
    finally:
        conn.close()

    if emergency:
        for ann in emergency:
            st.markdown(f"""<div style="background:#FEF2F2;border:1.5px solid #FECACA;border-left:5px solid #DC2626;border-radius:12px;padding:16px 18px;margin-bottom:10px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="font-size:1.1rem;">🚨</span><span style="font-weight:700;font-size:.95rem;color:#991B1B;">EMERGENCY NOTICE</span></div>
                <div style="font-weight:600;color:#7F1D1D;margin-bottom:4px;">{ann['title']}</div>
                <div style="font-size:.83rem;color:#991B1B;line-height:1.55;">{ann['description']}</div>
                <div style="font-size:.72rem;color:#EF4444;margin-top:8px;">📅 {str(ann['posted_date'])[:16]}</div>
            </div>""",unsafe_allow_html=True)
        st.markdown("---")

    filter_type = st.radio("Filter by type",["All","General","Mess Update","Holiday"],horizontal=True,key="ann_filter")
    shown = [a for a in all_ann if filter_type=="All" or a["ann_type"]==filter_type]
    if not shown:
        st.info("No announcements to show."); return
    st.markdown(f"**{len(shown)} announcement(s)**")
    border_colors={"General":"#2D6BE4","Emergency":"#DC2626","Mess Update":"#16A34A","Holiday":"#D97706"}
    for ann in shown:
        t=ann["ann_type"]; bg=ANNOUNCEMENT_COLORS.get(t,"#F8FAFC"); icon=ANNOUNCEMENT_ICONS.get(t,"📢"); bc=border_colors.get(t,"#2D6BE4")
        st.markdown(f"""<div class="ann-card" style="background:{bg};border-color:{bc};">
            <div style="display:flex;align-items:center;gap:8px;">{icon}&nbsp;<span style="font-weight:700;font-size:.95rem;">{ann['title']}</span>&nbsp;{_badge(t,bc,bg)}</div>
            <div style="font-size:.83rem;color:#475569;line-height:1.55;margin-top:8px;">{ann['description']}</div>
            <div style="font-size:.73rem;color:#94A3B8;margin-top:8px;">📅 {str(ann['posted_date'])[:16]}</div>
        </div>""",unsafe_allow_html=True)


# =============================================================
# SECTION 8 — MESS
# =============================================================
def render_mess(student_id):
    _sec("🍽️","Mess Management")
    menu_tab,mark_tab,feedback_tab,history_tab = st.tabs(["📋  Today's Menu","✅  Mark Attendance","💬  Give Feedback","📜  My History"])

    with menu_tab:
        conn = get_connection()
        if not conn: st.error("Database error"); return
        try:
            today_menu = get_menu_by_date(conn, date.today().strftime("%Y-%m-%d"))
            recent     = get_recent_menus(conn, 7)
        finally:
            conn.close()
        if today_menu:
            st.markdown(f"**Menu for {date.today().strftime('%A, %d %B %Y')}**")
            c1,c2,c3,c4 = st.columns(4)
            for col,meal in zip([c1,c2,c3,c4],MEAL_TYPES):
                with col:
                    items = today_menu.get(meal.lower(),"—")
                    st.markdown(f'<div class="meal-card"><div class="meal-title">{MEAL_ICONS[meal]} {meal}</div><div class="meal-items">{items}</div></div>',unsafe_allow_html=True)
        else:
            st.info("Today's menu has not been posted yet.")
        if recent:
            st.markdown("---"); st.markdown("**This Week's Menu**")
            for menu in recent[1:5]:
                with st.expander(f"📅 {menu['menu_date']}"):
                    mc1,mc2,mc3,mc4=st.columns(4)
                    for col,meal in zip([mc1,mc2,mc3,mc4],MEAL_TYPES):
                        col.markdown(f"**{MEAL_ICONS[meal]} {meal}**"); col.caption(menu.get(meal.lower(),"—"))

    with mark_tab:
        st.markdown("**Mark which meals you attended today.**")
        conn = get_connection()
        if not conn: st.error("Database error"); return
        try:
            existing={m["meal_type"]:m["attended"] for m in get_meal_history_by_student(conn,student_id,1) if str(m["meal_date"])==date.today().strftime("%Y-%m-%d")}
        finally:
            conn.close()
        with st.form("meal_attendance_form"):
            st.markdown(f"**{date.today().strftime('%A, %d %B %Y')}**")
            checks={}
            c1,c2,c3,c4=st.columns(4)
            for col,meal in zip([c1,c2,c3,c4],MEAL_TYPES):
                with col: checks[meal]=st.checkbox(f"{MEAL_ICONS[meal]} {meal}",value=bool(existing.get(meal,False)),key=f"meal_{meal}")
            if st.form_submit_button("💾  Save Meal Attendance", use_container_width=True):
                conn=get_connection()
                if conn:
                    try:
                        for meal,attended in checks.items():
                            mark_meal_attendance(conn,student_id,date.today().strftime("%Y-%m-%d"),meal,attended)
                        st.success(f"✅ Saved! You attended {sum(checks.values())} meal(s) today.")
                    except Exception as e: st.error(f"Failed: {e}")
                    finally: conn.close()

    with feedback_tab:
        st.markdown("**Rate today's food and share your feedback.**")
        with st.form("feedback_form"):
            c1,c2=st.columns(2)
            with c1: fb_meal=st.selectbox("Meal",MEAL_TYPES); fb_rating=st.slider("⭐ Rating",1,5,3)
            with c2:
                st.markdown("<div style='height:1.8rem'></div>",unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:1.4rem;margin-top:8px;'>{'⭐'*fb_rating}{'☆'*(5-fb_rating)}</div>",unsafe_allow_html=True)
            fb_text=st.text_area("Your feedback",placeholder="e.g. The biryani was excellent today!",height=100,max_chars=500)
            if st.form_submit_button("📤  Submit Feedback",use_container_width=True):
                if not fb_text.strip(): st.error("⚠️ Please write some feedback.")
                else:
                    sentiment = analyze_sentiment(fb_text) if AI_SENTIMENT_READY else ("Positive" if fb_rating>=4 else "Negative" if fb_rating<=2 else "Neutral")
                    conn=get_connection()
                    if conn:
                        try:
                            add_food_feedback(conn,student_id,fb_text.strip(),sentiment,fb_rating,fb_meal,date.today().strftime("%Y-%m-%d"))
                            s_col=SENTIMENT_COLORS.get(sentiment,"#475569"); s_icon=SENTIMENT_ICONS.get(sentiment,"")
                            st.success("✅ Feedback submitted!")
                            st.markdown(f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:12px 16px;margin-top:6px;">AI Sentiment: <b style="color:{s_col};">{s_icon} {sentiment}</b> &nbsp;·&nbsp; Rating: {"⭐"*fb_rating}</div>',unsafe_allow_html=True)
                        except Exception as e: st.error(f"Failed: {e}")
                        finally: conn.close()

    with history_tab:
        conn=get_connection()
        if not conn: st.error("Database error"); return
        try:
            feedbacks=get_feedback_by_student(conn,student_id)
        finally:
            conn.close()
        if not feedbacks:
            st.info("You haven't submitted any feedback yet."); return
        for fb in feedbacks:
            s_col=SENTIMENT_COLORS.get(fb["sentiment"],"#475569"); s_icon=SENTIMENT_ICONS.get(fb["sentiment"],"")
            stars="⭐"*fb["rating"]+"☆"*(5-fb["rating"])
            st.markdown(f"""<div class="comp-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <div><span style="font-weight:600;font-size:.9rem;">{MEAL_ICONS.get(fb['meal_type'],'🍽️')} {fb['meal_type']}</span><span style="font-size:.88rem;margin-left:8px;">{stars}</span></div>
                    <span style="font-size:.8rem;color:{s_col};font-weight:600;">{s_icon} {fb['sentiment']}</span>
                </div>
                <div style="font-size:.84rem;color:#475569;line-height:1.5;">{fb['feedback_text']}</div>
                <div style="font-size:.73rem;color:#94A3B8;margin-top:6px;">{fb['feedback_date']}</div>
            </div>""",unsafe_allow_html=True)


# =============================================================
# SECTION 9 — AI CHATBOT
# =============================================================
def _fallback_chatbot(query, student_id, student):
    q = query.lower().strip()
    if any(w in q for w in ["leave","vacation","home","absent"]):
        return ("📝 <b>How to apply for leave:</b><br>"
                "1. Go to <b>Leave Request</b> in the sidebar.<br>"
                "2. Fill in your reason and select dates.<br>"
                "3. Click <b>Submit Leave Request</b>.<br>"
                "4. Your warden will approve/reject — check Leave History for updates.<br><br>"
                "💡 <i>Apply at least 2 days in advance for non-emergency leaves.</i>")
    if any(w in q for w in ["complaint","issue","problem","repair","broken","fix","leak","wifi","fan","light"]):
        return ("🔧 <b>How to file a complaint:</b><br>"
                "1. Go to <b>Complaint Management</b> in the sidebar.<br>"
                "2. Describe the issue clearly in the text box.<br>"
                "3. AI auto-detects category and priority.<br>"
                "4. Click <b>Submit Complaint</b> — warden is notified instantly.<br><br>"
                "⚡ <i>Emergency issues (sparks, flooding) are escalated immediately.</i>")
    if any(w in q for w in ["menu","food","lunch","dinner","breakfast","mess","snack","eat","meal"]):
        conn = get_connection()
        if conn:
            try:
                menu = get_menu_by_date(conn, date.today().strftime("%Y-%m-%d"))
                if menu:
                    return (f"🍽️ <b>Today's Menu ({date.today().strftime('%d %B %Y')}):</b><br>"
                            f"🌅 <b>Breakfast:</b> {menu['breakfast']}<br>"
                            f"☀️ <b>Lunch:</b> {menu['lunch']}<br>"
                            f"🍪 <b>Snacks:</b> {menu['snacks']}<br>"
                            f"🌙 <b>Dinner:</b> {menu['dinner']}")
            finally:
                conn.close()
        return "🍽️ Today's menu hasn't been posted yet. Check the <b>Mess</b> section."
    if any(w in q for w in ["attendance","percent","present","absent","percentage"]):
        conn = get_connection()
        if conn:
            try:
                pct = get_attendance_percentage(conn, student_id)
                status = "Good 👍" if pct>=75 else "Below minimum ⚠️ — please inform your warden"
                return (f"📅 <b>Your attendance: {pct:.1f}%</b><br>Status: {status}<br><br>"
                        "Minimum required is <b>75%</b>. Visit <b>Attendance</b> for full history.")
            finally:
                conn.close()
    if any(w in q for w in ["room","roommate","block","floor","bed"]):
        room_no=student.get("room_no") or "Not allocated"; block=student.get("block") or "—"
        return (f"🛏️ <b>Your Room:</b> {room_no} · <b>Block:</b> {block}<br><br>"
                "Visit <b>Room Details</b> for full info and roommate details.")
    if any(w in q for w in ["rule","curfew","timing","time","allowed","regulation"]):
        return ("📜 <b>Hostel Rules:</b><br>"
                "🕘 Curfew: 9:30 PM weekdays, 10:00 PM weekends<br>"
                "🚭 No smoking or alcohol<br>"
                "🔊 Silence hours: 10:30 PM – 6:00 AM<br>"
                "🚪 Guests: common areas only, 10 AM–7 PM<br>"
                "🔥 No cooking in rooms")
    if any(w in q for w in ["contact","warden","phone","call","help","office"]):
        return ("📞 <b>Warden Contacts:</b><br>"
                "🏢 Block A — Dr. Ramesh Kumar: 9876543210<br>"
                "🏢 Block B — Mrs. Priya Sundaram: 9876543211<br>"
                "🏢 Block C — Mr. Senthil Murugan: 9876543212<br>"
                "📧 hostel@college.edu · 🕘 9 AM–5 PM (Mon–Sat)")
    if any(w in q for w in ["hi","hello","hey","good morning","good evening"]):
        return (f"Hello {student['name'].split()[0]}! 👋 I can help with:<br>"
                "• 🚪 Leave applications<br>• 📋 Complaints<br>• 🍽️ Mess menu<br>"
                "• 📅 Attendance<br>• 📜 Hostel rules<br>• 🛏️ Room info")
    return ("🤔 I didn't understand that. Try:<br>"
            "• 'How to apply for leave?'<br>• 'What is today's menu?'<br>"
            "• 'What is my attendance?'<br>• 'What are hostel rules?'<br>"
            "• 'How to contact the warden?'")


def render_chatbot(student_id, student):
    _sec("🤖","AI Hostel Assistant")
    st.markdown("""<div style="background:linear-gradient(135deg,#EEF3FD,#F5F3FF);border:1px solid #C7D9FA;border-radius:14px;padding:14px 18px;margin-bottom:1.2rem;display:flex;align-items:center;gap:12px;">
        <div style="font-size:2rem;">🤖</div>
        <div><div style="font-weight:700;font-size:.95rem;">Hostel Hub Assistant</div><div style="font-size:.8rem;color:#64748B;">Ask me about hostel rules, room details, mess menu, complaints, leave, and more.</div></div>
        <div style="margin-left:auto;"><span style="background:#DCFCE7;color:#166534;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:600;">🟢 Online</span></div>
    </div>""",unsafe_allow_html=True)

    st.markdown("**💡 Try asking:**")
    suggestions=["How do I apply for leave?","What are hostel rules?","How do I file a complaint?","What is today's menu?","What is my attendance?","What time is curfew?"]
    cols=st.columns(3)
    for i,sug in enumerate(suggestions):
        with cols[i%3]:
            if st.button(sug,key=f"sug_{i}",use_container_width=True):
                st.session_state["chat_prefill"]=sug
    st.markdown("---")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"]=[{"role":"bot","text":f"Hello {student['name'].split()[0]}! 👋 I'm your Hostel Hub Assistant. Ask me anything about hostel rules, mess menu, leave applications, complaints, or attendance!"}]

    for msg in st.session_state["chat_history"]:
        if msg["role"]=="user":
            st.markdown(f'<div class="chat-user">{msg["text"]}</div>',unsafe_allow_html=True)
        else:
            st.markdown(f'<div><div class="chat-bot-name">🤖 Hostel Hub Assistant</div><div class="chat-bot">{msg["text"]}</div></div>',unsafe_allow_html=True)

    prefill=st.session_state.pop("chat_prefill","")
    user_input=st.chat_input("Type your question here...",key="chatbot_input")
    query=user_input or prefill

    if query:
        st.session_state["chat_history"].append({"role":"user","text":query})
        response=_fallback_chatbot(query,student_id,student)
        st.session_state["chat_history"].append({"role":"bot","text":response})
        st.rerun()

    if st.button("🗑️  Clear Chat",key="clear_chat"):
        st.session_state.pop("chat_history",None); st.rerun()


# =============================================================
# SIDEBAR NAV
# =============================================================
NAV_ITEMS=[("📊","Dashboard"),("👤","Profile"),("🛏️","Room Details"),("📋","Complaints"),("🚪","Leave Request"),("📅","Attendance"),("📢","Announcements"),("🍽️","Mess"),("🤖","AI Chatbot")]

def render_nav():
    with st.sidebar:
        st.markdown('<div style="font-size:.7rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.08em;padding:0 4px;margin-bottom:.4rem;">Navigation</div>',unsafe_allow_html=True)
        labels=[f"{icon}  {label}" for icon,label in NAV_ITEMS]
        selection=st.radio("nav",labels,label_visibility="collapsed",key="student_nav")
        st.markdown("<div style='height:.5rem'></div>",unsafe_allow_html=True)
        st.divider()
        st.markdown('<div style="font-size:.72rem;color:#94A3B8;text-align:center;padding:4px 0;">Hostel Hub v1.0 · AI &amp; DS Dept</div>',unsafe_allow_html=True)
    return selection.split("  ",1)[-1].strip()


# =============================================================
# MAIN ENTRY POINT
# =============================================================
def render_student_dashboard():
    require_student_login()
    _inject_css()
    student_id=st.session_state["student_id"]
    conn=get_connection()
    if not conn:
        st.error("❌ Cannot connect to database."); return
    try:
        student=get_student_by_id(conn,student_id)
    finally:
        conn.close()
    if not student:
        st.error("❌ Student record not found."); return

    active=render_nav()
    if   active=="Dashboard":     render_dashboard(student_id,student)
    elif active=="Profile":       render_profile(student_id,student)
    elif active=="Room Details":  render_room(student_id,student)
    elif active=="Complaints":    render_complaints(student_id)
    elif active=="Leave Request": render_leave(student_id)
    elif active=="Attendance":    render_attendance(student_id)
    elif active=="Announcements": render_announcements()
    elif active=="Mess":          render_mess(student_id)
    elif active=="AI Chatbot":    render_chatbot(student_id,student)