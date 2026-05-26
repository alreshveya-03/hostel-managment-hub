# =============================================================
#  HOSTEL HUB — pages/warden_portal.py
#  Complete Warden Portal — All 12 Sections
#
#  Sections:
#    1.  Dashboard      — KPI cards + analytics overview
#    2.  Students       — Add / edit / delete / search
#    3.  Rooms          — Allocate, view, manage occupancy
#    4.  Complaints     — View, filter, resolve, emergency alerts
#    5.  Leave          — Approve / reject with remarks
#    6.  Attendance     — Mark daily + view reports
#    7.  Mess           — Upload menu, view feedback & ratings
#    8.  Announcements  — Post / manage notices
#    9.  AI Room Suggest— Smart room recommendation
#   10.  AI Complaints  — Priority & category auto-detection
#   11.  Analytics      — Charts & hostel-wide statistics
#   12.  Emergency      — Critical alerts dashboard
# =============================================================

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from datetime import date, timedelta
from database.connection import get_connection
from database.queries import (
    # students
    get_all_students, get_student_by_id, add_student,
    update_student, delete_student, search_students,
    get_student_count, get_students_by_dept_year,
    # rooms
    get_all_rooms, get_room_by_no, get_available_rooms,
    get_roommates, allocate_room, deallocate_room,
    get_room_occupancy_stats,
    # complaints
    get_all_complaints, get_complaints_filtered,
    update_complaint_status, get_complaint_summary,
    get_emergency_complaints,
    # leaves
    get_all_leaves, update_leave_status, get_pending_leave_count,
    # attendance
    mark_attendance, get_attendance_by_date,
    get_attendance_percentage, get_attendance_by_student,
    # mess
    get_menu_by_date, upsert_menu, get_recent_menus,
    get_all_feedback, get_sentiment_summary, get_average_rating,
    get_meal_attendance_counts,
    # announcements
    post_announcement, get_active_announcements, deactivate_announcement,
)
from utils.auth_utils import require_warden_login, hash_password
from utils.constants import (
    DEPARTMENTS, YEARS, GENDERS, FOOD_PREFERENCES, HOSTEL_BLOCKS,
    COMPLAINT_CATEGORIES, COMPLAINT_STATUSES, COMPLAINT_PRIORITIES,
    PRIORITY_COLORS, PRIORITY_ICONS, STATUS_ICONS,
    LEAVE_STATUSES, LEAVE_STATUS_ICONS,
    ATTENDANCE_STATUSES, MEAL_TYPES, MEAL_ICONS,
    ANNOUNCEMENT_TYPES, ANNOUNCEMENT_ICONS, ANNOUNCEMENT_COLORS,
    SENTIMENT_ICONS, SENTIMENT_COLORS,
)

try:
    from ai_models.room_suggest import suggest_rooms
    AI_ROOM_READY = True
except ImportError:
    AI_ROOM_READY = False

try:
    from ai_models.complaint_ai import detect_category, detect_priority
    AI_COMPLAINT_READY = True
except ImportError:
    AI_COMPLAINT_READY = False


# =============================================================
# SHARED CSS
# =============================================================
def _inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    :root{
        --blue:#2D6BE4;--blue-lt:#EEF3FD;
        --green:#16A34A;--green-lt:#F0FDF4;
        --amber:#D97706;--amber-lt:#FFFBEB;
        --red:#DC2626;--red-lt:#FEF2F2;
        --purple:#7C3AED;--purple-lt:#F5F3FF;
        --teal:#0891B2;--teal-lt:#ECFEFF;
        --text-1:#0F172A;--text-2:#475569;--text-3:#94A3B8;
        --border:#E2E8F0;--surface:#FFFFFF;--bg:#F8FAFC;
        --radius:12px;--shadow:0 2px 12px rgba(0,0,0,.07);
    }
    html,[class*="css"]{font-family:'DM Sans',sans-serif!important;}
    #MainMenu,footer,header{visibility:hidden}
    .block-container{padding-top:1.5rem!important;padding-bottom:3rem!important;}
    [data-testid="stSidebar"]{background:#FAFBFF!important;border-right:1px solid var(--border)!important;}

    /* KPI */
    .kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow);transition:transform .2s;}
    .kpi:hover{transform:translateY(-2px);}
    .kpi-val{font-size:2rem;font-weight:800;line-height:1;margin-bottom:2px;}
    .kpi-lbl{font-size:.75rem;font-weight:600;color:var(--text-2);text-transform:uppercase;letter-spacing:.05em;}
    .kpi-sub{font-size:.73rem;margin-top:4px;}

    /* Section header */
    .sh{display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--border);padding-bottom:10px;margin-bottom:1.2rem;}
    .sh-icon{font-size:1.35rem;}
    .sh-title{font-size:1.12rem;font-weight:700;color:var(--text-1);}

    /* Badge */
    .bx{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.71rem;font-weight:600;letter-spacing:.03em;}

    /* Table */
    .tbl{width:100%;border-collapse:collapse;font-size:.84rem;}
    .tbl th{text-align:left;padding:9px 12px;background:#F8FAFC;border-bottom:2px solid var(--border);font-size:.74rem;color:var(--text-2);text-transform:uppercase;letter-spacing:.04em;}
    .tbl td{padding:9px 12px;border-bottom:1px solid #F1F5F9;color:var(--text-1);}
    .tbl tr:hover td{background:#F8FAFC;}

    /* Card */
    .card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px;margin-bottom:10px;box-shadow:var(--shadow);}

    /* Alert banner */
    .alert-red{background:#FEF2F2;border:1.5px solid #FECACA;border-left:5px solid #DC2626;border-radius:12px;padding:14px 18px;margin-bottom:10px;}
    .alert-amber{background:#FFFBEB;border:1.5px solid #FDE68A;border-left:5px solid #D97706;border-radius:12px;padding:14px 18px;margin-bottom:10px;}
    .alert-green{background:#F0FDF4;border:1.5px solid #86EFAC;border-left:5px solid #16A34A;border-radius:12px;padding:14px 18px;margin-bottom:10px;}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"]{gap:4px;background:#F1F5F9;border-radius:10px;padding:4px;border:1px solid var(--border);}
    .stTabs [data-baseweb="tab"]{border-radius:7px!important;font-size:.84rem!important;padding:7px 14px!important;}
    .stTabs [aria-selected="true"]{background:var(--blue)!important;color:#fff!important;}

    /* Inputs */
    .stTextInput>div>div>input,.stTextArea>div>textarea,.stSelectbox>div>div>div{border:1.5px solid var(--border)!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;}
    .stButton>button{border-radius:8px!important;font-weight:600!important;font-family:'DM Sans',sans-serif!important;transition:all .2s!important;}

    /* Priority pills */
    .p-normal  {background:#DCFCE7;color:#166534;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    .p-urgent  {background:#FEF3C7;color:#92400E;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    .p-emergency{background:#FEE2E2;color:#991B1B;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    .s-pending {background:#F1F5F9;color:#475569;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    .s-progress{background:#FEF3C7;color:#92400E;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    .s-resolved{background:#DCFCE7;color:#166534;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;}
    </style>
    """, unsafe_allow_html=True)


# =============================================================
# SHARED HELPERS
# =============================================================
def _sec(icon, title):
    st.markdown(f'<div class="sh"><span class="sh-icon">{icon}</span><span class="sh-title">{title}</span></div>', unsafe_allow_html=True)

def _badge(text, color, bg):
    return f'<span class="bx" style="background:{bg};color:{color};">{text}</span>'

def _kpi(label, value, icon, color, bg, sub=""):
    sub_html = f'<div class="kpi-sub" style="color:{color};">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="kpi" style="border-top:3px solid {color};">'
        f'<div style="font-size:1.5rem;margin-bottom:6px;">{icon}</div>'
        f'<div class="kpi-val" style="color:{color};">{value}</div>'
        f'<div class="kpi-lbl">{label}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )

def _chart_style(ax, fig):
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#E2E8F0")
    ax.tick_params(colors="#475569", labelsize=9)
    ax.yaxis.grid(True, color="#E2E8F0", linestyle="--", alpha=.7)
    ax.set_axisbelow(True)

def _tbl_header(*cols):
    h = "<thead><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead>"
    return h

def _render_table(headers, rows):
    """Render an HTML table with consistent styling."""
    html = f'<table class="tbl"><thead><tr>'
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr></thead><tbody>"
    for i, row in enumerate(rows):
        bg = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        html += f'<tr style="background:{bg};">'
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


# =============================================================
# SECTION 1 — DASHBOARD OVERVIEW
# =============================================================
def render_dashboard():
    _sec("📊", "Warden Dashboard")

    conn = get_connection()
    if not conn:
        st.error("Database connection failed."); return

    try:
        total_students   = get_student_count(conn)
        rooms            = get_all_rooms(conn)
        complaint_summary= get_complaint_summary(conn)
        emergency_comps  = get_emergency_complaints(conn)
        pending_leaves   = get_pending_leave_count(conn)
        sentiment_data   = get_sentiment_summary(conn)
        avg_rating       = get_average_rating(conn)
        occ_stats        = get_room_occupancy_stats(conn)
        today_meal       = get_meal_attendance_counts(conn, date.today().strftime("%Y-%m-%d"))
    finally:
        conn.close()

    total_rooms    = len(rooms)
    occupied_rooms = sum(1 for r in rooms if r["occupied"] > 0)
    vacant_rooms   = sum(1 for r in rooms if r["occupied"] == 0)
    full_rooms     = sum(1 for r in rooms if r["occupancy_status"] == "Full")
    total_beds     = sum(r["capacity"] for r in rooms)
    occupied_beds  = sum(r["occupied"]  for r in rooms)

    cs = {row["status"]: row["count"] for row in complaint_summary}
    pending_comp   = cs.get("Pending", 0)
    inprogress_comp= cs.get("In Progress", 0)

    # ── Emergency banner ──
    if emergency_comps:
        st.markdown(f"""
        <div class="alert-red">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:1.2rem;">🚨</span>
                <span style="font-weight:700;color:#991B1B;font-size:.95rem;">
                    {len(emergency_comps)} EMERGENCY COMPLAINT(S) REQUIRE IMMEDIATE ATTENTION
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

    # ── KPI Row 1 ──
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: _kpi("Total Students",  total_students,  "👥","#2D6BE4","#EEF3FD")
    with c2: _kpi("Total Rooms",     total_rooms,     "🏠","#7C3AED","#F5F3FF", f"{vacant_rooms} vacant")
    with c3: _kpi("Beds Occupied",   f"{occupied_beds}/{total_beds}", "🛏️","#D97706","#FFFBEB")
    with c4: _kpi("Pending Leaves",  pending_leaves,  "🚪","#0891B2","#ECFEFF")
    with c5: _kpi("Emergencies",     len(emergency_comps),"🚨","#DC2626","#FEF2F2","unresolved")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # ── KPI Row 2 ──
    c1,c2,c3,c4 = st.columns(4)
    with c1: _kpi("Pending Complaints",  pending_comp,    "📋","#DC2626","#FEF2F2")
    with c2: _kpi("In Progress",         inprogress_comp, "🔧","#D97706","#FFFBEB")
    with c3: _kpi("Avg Food Rating",     f"{avg_rating}⭐","🍽️","#16A34A","#F0FDF4")
    with c4:
        meal_today = sum(r["attended_count"] for r in today_meal)
        _kpi("Meals Today", meal_today, "🥘","#7C3AED","#F5F3FF")

    st.markdown("---")

    # ── Charts row ──
    ch1, ch2, ch3 = st.columns(3)

    # Chart 1 — Room occupancy donut
    with ch1:
        st.markdown("**Room Occupancy**")
        occ_map = {r["occupancy_status"]: r["count"] for r in occ_stats}
        if occ_map:
            labels = list(occ_map.keys()); vals = list(occ_map.values())
            colors_map = {"Vacant":"#86EFAC","Partial":"#FCD34D","Full":"#FCA5A5"}
            colors = [colors_map.get(l,"#CBD5E1") for l in labels]
            fig,ax = plt.subplots(figsize=(3.5,3))
            wedges,texts,autotexts = ax.pie(
                vals, labels=labels, autopct="%1.0f%%", colors=colors,
                wedgeprops={"width":.55,"edgecolor":"white","linewidth":2}, startangle=90)
            for t in texts:     t.set_fontsize(9); t.set_color("#475569")
            for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
            fig.patch.set_facecolor("white")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    # Chart 2 — Complaint status bar
    with ch2:
        st.markdown("**Complaint Status**")
        if complaint_summary:
            statuses = [r["status"] for r in complaint_summary]
            counts   = [r["count"]  for r in complaint_summary]
            c_colors = {"Pending":"#FCA5A5","In Progress":"#FCD34D","Resolved":"#86EFAC"}
            bar_colors = [c_colors.get(s,"#CBD5E1") for s in statuses]
            fig,ax = plt.subplots(figsize=(3.5,3))
            bars = ax.bar(statuses, counts, color=bar_colors, edgecolor="white", linewidth=1.5, width=.45)
            for bar,val in zip(bars,counts):
                if val>0: ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+.05, str(val),
                                  ha="center",va="bottom",fontsize=10,fontweight="bold",color="#475569")
            _chart_style(ax,fig); ax.set_ylabel("Count",fontsize=9,color="#475569")
            ax.set_title("All complaints",fontsize=9,color="#475569")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    # Chart 3 — Sentiment pie
    with ch3:
        st.markdown("**Food Sentiment**")
        if sentiment_data:
            s_labels = [r["sentiment"] for r in sentiment_data]
            s_vals   = [r["count"]     for r in sentiment_data]
            s_colors_map = {"Positive":"#86EFAC","Neutral":"#FCD34D","Negative":"#FCA5A5"}
            s_colors = [s_colors_map.get(l,"#CBD5E1") for l in s_labels]
            fig,ax = plt.subplots(figsize=(3.5,3))
            wedges,texts,autotexts = ax.pie(
                s_vals, labels=s_labels, autopct="%1.0f%%", colors=s_colors,
                wedgeprops={"width":.55,"edgecolor":"white","linewidth":2}, startangle=90)
            for t in texts:     t.set_fontsize(9); t.set_color("#475569")
            for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
            fig.patch.set_facecolor("white")
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        else:
            st.info("No feedback data yet.")

    # ── Today's meal counts ──
    st.markdown("---")
    st.markdown("**Today's Meal Attendance**")
    if today_meal:
        mcols = st.columns(4)
        for i, meal in enumerate(MEAL_TYPES):
            count = next((r["attended_count"] for r in today_meal if r["meal_type"]==meal), 0)
            with mcols[i]:
                st.markdown(f"""
                <div class="card" style="text-align:center;border-top:3px solid #2D6BE4;">
                    <div style="font-size:1.6rem;">{MEAL_ICONS[meal]}</div>
                    <div style="font-size:1.4rem;font-weight:800;color:#2D6BE4;">{count}</div>
                    <div style="font-size:.75rem;color:#64748B;font-weight:600;text-transform:uppercase;">{meal}</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("No meal attendance recorded today yet.")


# =============================================================
# SECTION 2 — STUDENT MANAGEMENT
# =============================================================
def render_students():
    _sec("👥", "Student Management")
    view_tab, add_tab, edit_tab = st.tabs(["📋  View & Search", "➕  Add Student", "✏️  Edit / Delete"])

    # ── View & Search ──
    with view_tab:
        col1, col2 = st.columns([3,1])
        with col1:
            keyword = st.text_input("🔍 Search by name, register number, or department", placeholder="e.g. Arun / 21CS001 / CSE")
        with col2:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            search_btn = st.button("Search", use_container_width=True)

        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            students = search_students(conn, keyword.strip()) if keyword.strip() else get_all_students(conn)
        finally:
            conn.close()

        st.markdown(f"**{len(students)} student(s) found**")
        if students:
            rows = []
            for s in students:
                rows.append([
                    s["register_number"], s["name"],
                    s["department"], f"Year {s['year']}",
                    s.get("room_no") or "—",
                    s.get("block") or "—",
                    s["phone"],
                    _badge(s["gender"], "#475569","#F1F5F9"),
                ])
            _render_table(
                ["Reg No.","Name","Dept","Year","Room","Block","Phone","Gender"],
                rows
            )
        else:
            st.info("No students found.")

    # ── Add Student ──
    with add_tab:
        st.markdown("**Fill in the details to register a new student.**")
        with st.form("add_student_form"):
            c1,c2,c3 = st.columns(3)
            with c1:
                s_name   = st.text_input("Full Name *",        max_chars=100)
                s_reg    = st.text_input("Register Number *",  max_chars=20, placeholder="e.g. 21CS006")
                s_dept   = st.selectbox("Department *",        DEPARTMENTS)
            with c2:
                s_year   = st.selectbox("Year *",              YEARS)
                s_gender = st.selectbox("Gender *",            GENDERS)
                s_food   = st.selectbox("Food Preference *",   FOOD_PREFERENCES)
            with c3:
                s_phone  = st.text_input("Phone *",            max_chars=15, placeholder="10-digit number")
                s_email  = st.text_input("Email *",            max_chars=100)
                s_pwd    = st.text_input("Password *",         type="password", placeholder="Min 6 chars")

            conn = get_connection()
            avail_rooms = []
            if conn:
                try:    avail_rooms = get_available_rooms(conn)
                finally: conn.close()

            room_options = ["-- No Room (Allocate Later) --"] + [
                f"{r['room_no']} | {r['block']} | {r['available_beds']} bed(s) free"
                for r in avail_rooms
            ]
            s_room_sel = st.selectbox("Assign Room (optional)", room_options)
            s_addr     = st.text_area("Address", height=70, max_chars=300)

            submitted = st.form_submit_button("➕  Register Student", use_container_width=True)

        if submitted:
            errors = []
            if not s_name.strip():          errors.append("Full name is required.")
            if not s_reg.strip():           errors.append("Register number is required.")
            if len(s_phone.strip()) < 10:   errors.append("Enter a valid 10-digit phone.")
            if "@" not in s_email:          errors.append("Enter a valid email.")
            if len(s_pwd) < 6:              errors.append("Password must be at least 6 characters.")
            if errors:
                for e in errors: st.error(f"⚠️ {e}")
            else:
                room_no = None
                if s_room_sel != "-- No Room (Allocate Later) --":
                    room_no = s_room_sel.split("|")[0].strip()
                conn = get_connection()
                if conn:
                    try:
                        hashed = hash_password(s_pwd)
                        new_id = add_student(conn, s_name.strip(), s_reg.strip().upper(),
                                             s_dept, s_year, room_no,
                                             s_phone.strip(), s_email.strip().lower(),
                                             hashed, s_gender, s_food, s_addr.strip())
                        if room_no:
                            allocate_room(conn, new_id, room_no)
                        st.success(f"✅ Student '{s_name}' registered with ID #{new_id}!")
                    except Exception as e:
                        st.error(f"Registration failed: {e}")
                    finally:
                        conn.close()

    # ── Edit / Delete ──
    with edit_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            all_students = get_all_students(conn)
        finally:
            conn.close()

        if not all_students:
            st.info("No students registered."); return

        options = {f"{s['register_number']} — {s['name']}": s["student_id"] for s in all_students}
        selected_label = st.selectbox("Select Student", list(options.keys()))
        sel_id = options[selected_label]

        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            sel_student = get_student_by_id(conn, sel_id)
        finally:
            conn.close()

        if not sel_student:
            st.warning("Student not found."); return

        edit_sub_tab, del_sub_tab = st.tabs(["✏️  Edit Details", "🗑️  Delete Student"])

        with edit_sub_tab:
            with st.form("edit_student_form"):
                c1,c2 = st.columns(2)
                with c1:
                    e_name  = st.text_input("Full Name",  value=sel_student.get("name",""), max_chars=100)
                    e_phone = st.text_input("Phone",      value=sel_student.get("phone",""), max_chars=15)
                    e_dept  = st.selectbox("Department",  DEPARTMENTS,
                                           index=DEPARTMENTS.index(sel_student["department"])
                                           if sel_student.get("department") in DEPARTMENTS else 0)
                with c2:
                    e_email = st.text_input("Email",      value=sel_student.get("email",""), max_chars=100)
                    e_year  = st.selectbox("Year",        YEARS,
                                           index=(sel_student.get("year",1)-1))
                    e_food  = st.selectbox("Food Pref",   FOOD_PREFERENCES,
                                           index=FOOD_PREFERENCES.index(sel_student["food_preference"])
                                           if sel_student.get("food_preference") in FOOD_PREFERENCES else 0)
                e_addr = st.text_area("Address", value=sel_student.get("address","") or "", height=70)
                if st.form_submit_button("💾  Save Changes", use_container_width=True):
                    if not e_name.strip():         st.error("Name required.")
                    elif len(e_phone.strip()) < 10: st.error("Valid phone required.")
                    elif "@" not in e_email:        st.error("Valid email required.")
                    else:
                        conn = get_connection()
                        if conn:
                            try:
                                update_student(conn, sel_id, e_name.strip(), e_phone.strip(),
                                               e_email.strip(), e_dept, e_year, e_food, e_addr.strip())
                                st.success("✅ Student updated!"); st.rerun()
                            except Exception as ex:
                                st.error(f"Update failed: {ex}")
                            finally:
                                conn.close()

        with del_sub_tab:
            st.warning(f"⚠️ You are about to delete **{sel_student['name']}** ({sel_student['register_number']}). This action is irreversible and will remove all their complaints, leaves, and attendance records.")
            confirm = st.checkbox("I confirm I want to permanently delete this student.")
            if st.button("🗑️  Delete Student", disabled=not confirm):
                conn = get_connection()
                if conn:
                    try:
                        delete_student(conn, sel_id)
                        st.success(f"✅ Student '{sel_student['name']}' deleted."); st.rerun()
                    except Exception as ex:
                        st.error(f"Delete failed: {ex}")
                    finally:
                        conn.close()


# =============================================================
# SECTION 3 — ROOM MANAGEMENT
# =============================================================
def render_rooms():
    _sec("🏠", "Room Management")
    overview_tab, allocate_tab, detail_tab = st.tabs(["📊  Room Overview", "🔑  Allocate Room", "🔍  Room Detail"])

    with overview_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            rooms = get_all_rooms(conn)
        finally:
            conn.close()

        # Summary KPIs
        total  = len(rooms)
        vacant = sum(1 for r in rooms if r["occupancy_status"]=="Vacant")
        full   = sum(1 for r in rooms if r["occupancy_status"]=="Full")
        partial= sum(1 for r in rooms if r["occupancy_status"]=="Partial")
        c1,c2,c3,c4 = st.columns(4)
        with c1: _kpi("Total Rooms",  total,  "🏠","#2D6BE4","#EEF3FD")
        with c2: _kpi("Vacant",       vacant, "✅","#16A34A","#F0FDF4")
        with c3: _kpi("Partial",      partial,"🟡","#D97706","#FFFBEB")
        with c4: _kpi("Full",         full,   "🔴","#DC2626","#FEF2F2")
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Room grid
        filter_block = st.selectbox("Filter by block", ["All"] + HOSTEL_BLOCKS, key="room_block_filter")
        filter_status= st.radio("Filter by status", ["All","Vacant","Partial","Full"], horizontal=True, key="room_status_filter")
        filtered = [r for r in rooms
                    if (filter_block=="All" or r["block"]==filter_block)
                    and (filter_status=="All" or r["occupancy_status"]==filter_status)]

        rows = []
        for r in filtered:
            occ_color = {"Vacant":"#16A34A","Partial":"#D97706","Full":"#DC2626"}.get(r["occupancy_status"],"#475569")
            occ_bg    = {"Vacant":"#DCFCE7","Partial":"#FEF3C7","Full":"#FEE2E2"}.get(r["occupancy_status"],"#F1F5F9")
            bar_pct   = int((r["occupied"]/r["capacity"])*100) if r["capacity"] else 0
            bar_html  = (f'<div style="background:#E2E8F0;border-radius:20px;height:8px;overflow:hidden;">'
                         f'<div style="width:{bar_pct}%;height:100%;background:{occ_color};border-radius:20px;"></div></div>'
                         f'<div style="font-size:.7rem;color:{occ_color};margin-top:1px;">{bar_pct}%</div>')
            rows.append([
                f"<b>{r['room_no']}</b>", r["block"], f"Floor {r['floor']}",
                r["room_type"],
                f"{r['occupied']}/{r['capacity']}",
                str(r["available_beds"]),
                "❄️" if r.get("ac_available") else "—",
                _badge(r["occupancy_status"], occ_color, occ_bg),
                bar_html,
            ])
        _render_table(["Room","Block","Floor","Type","Occupied","Free","AC","Status","Occupancy"], rows)

    with allocate_tab:
        st.markdown("**Assign a student to an available room.**")
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            unallocated = [s for s in get_all_students(conn) if not s.get("room_no")]
            avail_rooms = get_available_rooms(conn)
        finally:
            conn.close()

        if not unallocated:
            st.success("🎉 All students have been allocated rooms!"); return
        if not avail_rooms:
            st.warning("⚠️ No rooms with available beds. Consider adding more rooms."); return

        with st.form("allocate_form"):
            stud_opts = {f"{s['register_number']} — {s['name']} ({s['department']}, Yr {s['year']})": s["student_id"]
                         for s in unallocated}
            room_opts = {f"{r['room_no']} | {r['block']} | Floor {r['floor']} | {r['room_type']} | {r['available_beds']} bed(s) free": r["room_no"]
                         for r in avail_rooms}

            sel_stud = st.selectbox("Select Student (unallocated)", list(stud_opts.keys()))
            sel_room = st.selectbox("Select Room",                   list(room_opts.keys()))

            if st.form_submit_button("🔑  Allocate Room", use_container_width=True):
                s_id    = stud_opts[sel_stud]
                room_no = room_opts[sel_room]
                conn = get_connection()
                if conn:
                    try:
                        allocate_room(conn, s_id, room_no)
                        st.success(f"✅ Room {room_no} allocated successfully!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Allocation failed: {ex}")
                    finally:
                        conn.close()

    with detail_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            rooms = get_all_rooms(conn)
        finally:
            conn.close()

        room_opts = {r["room_no"]: r for r in rooms}
        sel_room_no = st.selectbox("Select Room", list(room_opts.keys()), key="room_detail_sel")
        room = room_opts[sel_room_no]

        c1,c2,c3 = st.columns(3)
        with c1: _kpi("Occupied",  f"{room['occupied']}/{room['capacity']}", "🛏️","#2D6BE4","#EEF3FD")
        with c2: _kpi("Available", room["available_beds"], "✅","#16A34A","#F0FDF4")
        with c3: _kpi("Type",      room["room_type"],      "⭐","#D97706","#FFFBEB")

        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            all_s = get_all_students(conn)
            occupants = [s for s in all_s if s.get("room_no") == sel_room_no]
        finally:
            conn.close()

        st.markdown(f"**Occupants in {sel_room_no} ({len(occupants)} student(s))**")
        if occupants:
            rows = [[s["register_number"], s["name"], s["department"], f"Year {s['year']}", s["phone"]] for s in occupants]
            _render_table(["Reg No.","Name","Dept","Year","Phone"], rows)
        else:
            st.info("This room is currently empty.")

# =============================================================
# SECTION 4 — COMPLAINT MANAGEMENT
# =============================================================
def render_complaints():
    _sec("📋", "Complaint Management")
    tab1, tab2, tab3 = st.tabs(["📋 All Complaints", "🚨 Emergency", "🔧 Resolve Complaints"])

    with tab1:
        conn = get_connection()
        if not conn: st.error("Database connection failed"); return
        try:
            complaints = get_all_complaints(conn)
            st.subheader("All Complaints")
            col1, col2 = st.columns(2)
            with col1: search = st.text_input("🔍 Search Complaint")
            with col2: status_filter = st.selectbox("Filter By Status", ["All", "Pending", "In Progress", "Resolved"])

            total = len(complaints)
            pending = len([c for c in complaints if c["status"] == "Pending"])
            progress = len([c for c in complaints if c["status"] == "In Progress"])
            resolved = len([c for c in complaints if c["status"] == "Resolved"])

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Total", total)
            with c2: st.metric("Pending", pending)
            with c3: st.metric("In Progress", progress)
            with c4: st.metric("Resolved", resolved)
            st.markdown("---")

            for complaint in complaints:
                if search and search.lower() not in complaint["complaint_text"].lower(): continue
                if status_filter != "All" and complaint["status"] != status_filter: continue
                priority = complaint.get("priority", "Normal")
                icon = "🚨" if priority == "Emergency" else "⚠️" if priority == "Urgent" else "📌"

                with st.expander(f"{icon} Complaint #{complaint['complaint_id']} | {complaint['category']} | {complaint['status']}"):
                    st.write(f"👤 Student: {complaint['student_name']}")
                    st.write(f"🆔 Register No: {complaint['register_number']}")
                    st.write(f"🏠 Room: {complaint.get('room_no', 'N/A')}")
                    st.write(f"⚡ Priority: {priority}")
                    st.write(f"📝 Issue: {complaint['complaint_text']}")
                    st.markdown("---")
                    
                    new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], 
                                             index=["Pending", "In Progress", "Resolved"].index(complaint["status"]), 
                                             key=f"status_{complaint['complaint_id']}")
                    remarks = st.text_area("Warden Remarks", value=complaint.get("warden_remarks", ""), key=f"remarks_{complaint['complaint_id']}")
                    
                    if st.button("✅ Update Complaint", key=f"btn_{complaint['complaint_id']}"):
                        conn_upd = get_connection()
                        if conn_upd:
                            try:
                                if update_complaint_status(conn_upd, complaint["complaint_id"], new_status, remarks):
                                    st.success("Complaint updated successfully!"); st.rerun()
                                else: st.error("Failed to update complaint.")
                            finally: conn_upd.close()
        finally:
            conn.close()

    with tab2:
        conn = get_connection()
        if not conn: st.error("Database connection failed"); return
        try:
            emergencies = get_emergency_complaints(conn)
            st.subheader("🚨 Emergency Complaints")
            if not emergencies: st.success("No emergency complaints right now.")
            else:
                for ec in emergencies:
                    with st.container():
                        st.error(f"Complaint #{ec['complaint_id']}\n\nStudent: {ec['student_name']}\n\nIssue: {ec['complaint_text']}")
        finally:
            conn.close()

    with tab3:
        conn = get_connection()
        if not conn:
            st.error("Database connection failed")
        else:
            try:
                all_comp = get_all_complaints(conn)
            finally:
                conn.close()

            unresolved = [c for c in all_comp if c["status"] != "Resolved"]
            st.subheader("🔧 Resolve Complaints")

            if not unresolved:
                st.success("🎉 All complaints are resolved!")
            else:
                st.markdown(f"**{len(unresolved)} unresolved complaint(s)**")
                for comp in unresolved:
                    pri = comp.get("priority", "Normal")
                    pri_color = {
                        "Emergency": "#DC2626",
                        "Urgent":    "#D97706",
                        "Normal":    "#16A34A",
                    }.get(pri, "#475569")

                    with st.expander(
                        f"{PRIORITY_ICONS.get(pri, '')} "
                        f"#{comp['complaint_id']} — "
                        f"{comp['student_name']} — "
                        f"{comp['category']} — {comp['status']}"
                    ):
                        st.markdown(
                            f"""<div style="background:#F8FAFC;border:1px solid #E2E8F0;
                            border-radius:10px;padding:14px 16px;margin-bottom:10px;
                            font-size:.88rem;line-height:1.6;">
                            <b>Student:</b> {comp['student_name']}
                            ({comp['register_number']})<br>
                            <b>Room:</b> {comp.get('room_no','—')} &nbsp;|&nbsp;
                            <b>Priority:</b>
                            <span style="color:{pri_color};font-weight:700;">{pri}</span><br>
                            <b>Filed:</b> {comp['filed_date']}<br><br>
                            {comp['complaint_text']}
                            </div>""",
                            unsafe_allow_html=True
                        )

                        with st.form(f"resolve_form_{comp['complaint_id']}"):
                            resolve_status = st.selectbox(
                                "New Status",
                                ["In Progress", "Resolved"],
                                key=f"resolve_sel_{comp['complaint_id']}"
                            )
                            resolve_remarks = st.text_area(
                                "Warden Remarks *",
                                placeholder="Describe action taken…",
                                key=f"resolve_rem_{comp['complaint_id']}"
                            )
                            if st.form_submit_button(
                                "💾 Save Resolution",
                                use_container_width=True
                            ):
                                if not resolve_remarks.strip():
                                    st.error("Please add remarks before saving.")
                                else:
                                    conn4 = get_connection()
                                    if conn4:
                                        try:
                                            update_complaint_status(
                                                conn4,
                                                comp["complaint_id"],
                                                resolve_status,
                                                resolve_remarks
                                            )
                                            st.success(
                                                f"✅ Complaint #{comp['complaint_id']} "
                                                f"updated to '{resolve_status}'!"
                                            )
                                            st.rerun()
                                        except Exception as ex:
                                            st.error(f"Failed: {ex}")
                                        finally:
                                            conn4.close()


# =============================================================
# SECTION 5 — LEAVE MANAGEMENT
# =============================================================
def render_leaves():
    _sec("🚪", "Leave Management")
    pending_tab, all_tab = st.tabs(["⏳  Pending Approvals", "📜  All Leave Requests"])

    for tab_key, show_all in [(pending_tab, False), (all_tab, True)]:
        with tab_key:
            conn = get_connection()
            if not conn: st.error("DB error"); return
            try:
                all_leaves = get_all_leaves(conn)
            finally:
                conn.close()

            leaves = all_leaves if show_all else [l for l in all_leaves if l["status"]=="Pending"]

            if not show_all:
                if not leaves:
                    st.success("🎉 No pending leave requests!"); continue

                st.markdown(f'<div class="alert-amber">⏳ <b>{len(leaves)} pending leave request(s) awaiting your decision.</b></div>', unsafe_allow_html=True)

                for l in leaves:
                    try: num_days = (l["to_date"]-l["from_date"]).days+1
                    except: num_days = "—"
                    with st.expander(f"📋  {l['student_name']} ({l['register_number']})  ·  {l['from_date']} → {l['to_date']}  ·  {num_days} day(s)"):
                        st.markdown(f"""
                        <div class="card">
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.85rem;margin-bottom:10px;">
                                <div><b>Student:</b> {l['student_name']}</div>
                                <div><b>Dept:</b> {l['department']}</div>
                                <div><b>Room:</b> {l.get('room_no') or '—'}</div>
                                <div><b>Duration:</b> {num_days} day(s)</div>
                                <div><b>From:</b> {l['from_date']}</div>
                                <div><b>To:</b> {l['to_date']}</div>
                            </div>
                            <div style="font-size:.85rem;"><b>Reason:</b> {l['reason']}</div>
                        </div>""", unsafe_allow_html=True)

                        c1,c2 = st.columns(2)
                        with st.form(f"leave_action_{l['leave_id']}"):
                            remarks = st.text_input("Remarks (optional)", placeholder="e.g. Approved. Return by Sunday evening.")
                            a1,a2  = st.columns(2)
                            with a1:
                                if st.form_submit_button("✅  Approve", use_container_width=True):
                                    conn = get_connection()
                                    if conn:
                                        try:
                                            update_leave_status(conn, l["leave_id"], "Approved", remarks or "Approved.")
                                            st.success("✅ Leave approved!"); st.rerun()
                                        except Exception as ex: st.error(f"Error: {ex}")
                                        finally: conn.close()
                            with a2:
                                if st.form_submit_button("❌  Reject", use_container_width=True):
                                    conn = get_connection()
                                    if conn:
                                        try:
                                            update_leave_status(conn, l["leave_id"], "Rejected", remarks or "Rejected.")
                                            st.success("❌ Leave rejected."); st.rerun()
                                        except Exception as ex: st.error(f"Error: {ex}")
                                        finally: conn.close()
            else:
                # All leaves table
                f_status = st.selectbox("Filter by status", ["All"]+LEAVE_STATUSES, key="leave_filter_all")
                shown = [l for l in leaves if f_status=="All" or l["status"]==f_status]
                st.markdown(f"**{len(shown)} request(s)**")
                rows = []
                for l in shown:
                    sts=l["status"]
                    s_col={"Pending":"#92400E","Approved":"#166534","Rejected":"#991B1B"}.get(sts,"#475569")
                    s_bg={"Pending":"#FEF3C7","Approved":"#DCFCE7","Rejected":"#FEE2E2"}.get(sts,"#F1F5F9")
                    try: nd=(l["to_date"]-l["from_date"]).days+1
                    except: nd="—"
                    rows.append([
                        l["student_name"], l["register_number"],
                        str(l["from_date"]), str(l["to_date"]), str(nd),
                        _badge(LEAVE_STATUS_ICONS.get(sts,"")+' '+sts, s_col, s_bg),
                        (l.get("warden_remarks") or "—")[:40],
                    ])
                _render_table(["Student","Reg No.","From","To","Days","Status","Remarks"], rows)


# =============================================================
# SECTION 6 — ATTENDANCE MANAGEMENT
# =============================================================
def render_attendance():
    _sec("📅", "Attendance Management")
    mark_tab, report_tab = st.tabs(["✅  Mark Attendance", "📊  Attendance Report"])

    with mark_tab:
        st.markdown("**Mark daily attendance for all students.**")

        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            all_students = get_all_students(conn)
        finally:
            conn.close()

        if not all_students:
            st.info("No students registered."); return

        att_date  = st.date_input("Attendance Date", value=date.today())
        warden_id = st.session_state.get("warden_id","WD001")

        # Load existing attendance for this date
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            existing = get_attendance_by_date(conn, att_date.strftime("%Y-%m-%d"))
        finally:
            conn.close()
        existing_map = {r["register_number"]: r["status"] for r in existing}

        st.markdown(f"**{len(all_students)} students · {att_date.strftime('%A, %d %B %Y')}**")
        st.caption("Select status for each student and click Save All.")

        status_selections = {}
        for s in all_students:
            current = existing_map.get(s["register_number"], "Present")
            col1,col2,col3 = st.columns([3,2,2])
            with col1:
                st.markdown(f"<div style='padding:6px 0;font-size:.88rem;font-weight:500;'>{s['name']} <span style='color:#94A3B8;font-size:.78rem;'>({s['register_number']})</span></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div style='padding:6px 0;font-size:.82rem;color:#64748B;'>{s['department']} · Yr {s['year']}</div>", unsafe_allow_html=True)
            with col3:
                idx = ATTENDANCE_STATUSES.index(current) if current in ATTENDANCE_STATUSES else 0
                status_selections[s["student_id"]] = st.selectbox(
                    "Status", ATTENDANCE_STATUSES, index=idx,
                    label_visibility="collapsed",
                    key=f"att_{s['student_id']}_{att_date}",
                )

        if st.button("💾  Save All Attendance", use_container_width=True):
            conn = get_connection()
            if conn:
                try:
                    for sid, sts in status_selections.items():
                        mark_attendance(conn, sid, att_date.strftime("%Y-%m-%d"), sts, warden_id)
                    present  = sum(1 for s in status_selections.values() if s=="Present")
                    absent   = sum(1 for s in status_selections.values() if s=="Absent")
                    on_leave = sum(1 for s in status_selections.values() if s=="Leave")
                    st.success(f"✅ Attendance saved! Present: {present} | Absent: {absent} | On Leave: {on_leave}")
                except Exception as ex:
                    st.error(f"Failed: {ex}")
                finally:
                    conn.close()

    with report_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            all_students = get_all_students(conn)
        finally:
            conn.close()

        if not all_students:
            st.info("No students registered."); return

        st.markdown("**Attendance percentage for all students**")
        rows = []
        low_att = []
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            for s in all_students:
                pct = get_attendance_percentage(conn, s["student_id"])
                color = "#16A34A" if pct>=75 else "#D97706" if pct>=60 else "#DC2626"
                bar_pct = int(pct)
                bar = (f'<div style="background:#E2E8F0;border-radius:20px;height:8px;overflow:hidden;min-width:80px;">'
                       f'<div style="width:{bar_pct}%;height:100%;background:{color};border-radius:20px;"></div></div>'
                       f'<div style="font-size:.72rem;color:{color};font-weight:600;">{pct:.1f}%</div>')
                rows.append([s["name"], s["register_number"], s["department"], f"Yr {s['year']}", s.get("room_no") or "—", bar])
                if pct < 75:
                    low_att.append(f"{s['name']} ({pct:.1f}%)")
        finally:
            conn.close()

        if low_att:
            st.markdown(f'<div class="alert-amber">⚠️ <b>{len(low_att)} student(s) below 75% attendance:</b> {", ".join(low_att)}</div>', unsafe_allow_html=True)

        _render_table(["Name","Reg No.","Dept","Year","Room","Attendance %"], rows)


# =============================================================
# SECTION 7 — MESS MANAGEMENT
# =============================================================
def render_mess():
    _sec("🍽️", "Mess Management")
    menu_tab, feedback_tab, analytics_tab = st.tabs(["📋  Upload Menu", "💬  Student Feedback", "📊  Mess Analytics"])

    with menu_tab:
        st.markdown("**Upload or update the mess menu for any date.**")

        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            today_menu = get_menu_by_date(conn, date.today().strftime("%Y-%m-%d"))
            recent     = get_recent_menus(conn, 7)
        finally:
            conn.close()

        with st.form("upload_menu_form"):
            menu_date = st.date_input("Menu Date", value=date.today())
            c1,c2 = st.columns(2)
            with c1:
                breakfast = st.text_area("🌅 Breakfast", value=today_menu.get("breakfast","") if today_menu else "", height=80, placeholder="e.g. Idli, Sambar, Chutney, Tea")
                snacks    = st.text_area("🍪 Snacks",    value=today_menu.get("snacks","")    if today_menu else "", height=80, placeholder="e.g. Samosa, Tea")
            with c2:
                lunch  = st.text_area("☀️ Lunch",  value=today_menu.get("lunch","")  if today_menu else "", height=80, placeholder="e.g. Rice, Dal, Curry, Papad")
                dinner = st.text_area("🌙 Dinner", value=today_menu.get("dinner","") if today_menu else "", height=80, placeholder="e.g. Chapati, Paneer Curry, Rice")

            if st.form_submit_button("💾  Save Menu", use_container_width=True):
                if not all([breakfast.strip(), lunch.strip(), snacks.strip(), dinner.strip()]):
                    st.error("⚠️ All 4 meal slots must be filled.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            upsert_menu(conn, menu_date.strftime("%Y-%m-%d"),
                                        breakfast.strip(), lunch.strip(), snacks.strip(), dinner.strip())
                            st.success(f"✅ Menu for {menu_date.strftime('%d %B %Y')} saved!")
                        except Exception as ex:
                            st.error(f"Failed: {ex}")
                        finally:
                            conn.close()

        # Recent menus
        if recent:
            st.markdown("---"); st.markdown("**Recent Menus**")
            for menu in recent[:5]:
                with st.expander(f"📅 {menu['menu_date']}"):
                    mc1,mc2,mc3,mc4 = st.columns(4)
                    for col,meal in zip([mc1,mc2,mc3,mc4],MEAL_TYPES):
                        col.markdown(f"**{MEAL_ICONS[meal]} {meal}**")
                        col.caption(menu.get(meal.lower(),"—"))

    with feedback_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            feedbacks = get_all_feedback(conn)
        finally:
            conn.close()

        if not feedbacks:
            st.info("No feedback submitted yet."); return

        f_sentiment = st.selectbox("Filter by sentiment", ["All","Positive","Neutral","Negative"], key="fb_sent_filter")
        shown = [f for f in feedbacks if f_sentiment=="All" or f["sentiment"]==f_sentiment]
        st.markdown(f"**{len(shown)} feedback(s)**")

        rows = []
        for f in shown:
            sent = f["sentiment"]
            s_col  = SENTIMENT_COLORS.get(sent,"#475569")
            s_bg   = {"Positive":"#DCFCE7","Neutral":"#FEF3C7","Negative":"#FEE2E2"}.get(sent,"#F1F5F9")
            stars  = "⭐"*f["rating"]+"☆"*(5-f["rating"])
            rows.append([
                f["student_name"],
                MEAL_ICONS.get(f.get("meal_type",""),"") + " " + (f.get("meal_type") or "—"),
                stars,
                _badge(SENTIMENT_ICONS.get(sent,"")+' '+sent, s_col, s_bg),
                f["feedback_text"][:60]+"…" if len(f["feedback_text"])>60 else f["feedback_text"],
                str(f["feedback_date"]),
            ])
        _render_table(["Student","Meal","Rating","Sentiment","Feedback","Date"], rows)

    with analytics_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            sentiment_data = get_sentiment_summary(conn)
            avg_rating     = get_average_rating(conn)
            all_fb         = get_all_feedback(conn)
        finally:
            conn.close()

        c1,c2,c3 = st.columns(3)
        total_fb   = len(all_fb)
        pos_count  = sum(1 for f in all_fb if f["sentiment"]=="Positive")
        neg_count  = sum(1 for f in all_fb if f["sentiment"]=="Negative")
        with c1: _kpi("Avg Rating",   f"{avg_rating}⭐", "🌟","#D97706","#FFFBEB")
        with c2: _kpi("Total Feedback",total_fb,         "📝","#2D6BE4","#EEF3FD")
        with c3: _kpi("Positive Rate", f"{int(pos_count/total_fb*100) if total_fb else 0}%", "😊","#16A34A","#F0FDF4")

        if sentiment_data:
            ch1,ch2 = st.columns(2)
            with ch1:
                st.markdown("**Sentiment Distribution**")
                s_l = [r["sentiment"] for r in sentiment_data]
                s_v = [r["count"]     for r in sentiment_data]
                s_c = [{"Positive":"#86EFAC","Neutral":"#FCD34D","Negative":"#FCA5A5"}.get(l,"#CBD5E1") for l in s_l]
                fig,ax = plt.subplots(figsize=(4,3))
                wedges,texts,autotexts = ax.pie(s_v,labels=s_l,autopct="%1.0f%%",colors=s_c,
                                                 wedgeprops={"width":.55,"edgecolor":"white","linewidth":2},startangle=90)
                for t in texts: t.set_fontsize(9); t.set_color("#475569")
                for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
                fig.patch.set_facecolor("white")
                st.pyplot(fig, use_container_width=True); plt.close(fig)
            with ch2:
                st.markdown("**Rating Distribution**")
                rating_counts = {i:0 for i in range(1,6)}
                for f in all_fb: rating_counts[f["rating"]] = rating_counts.get(f["rating"],0)+1
                fig,ax = plt.subplots(figsize=(4,3))
                bars = ax.bar([f"{'⭐'*i}" for i in rating_counts],[v for v in rating_counts.values()],
                               color=["#FCA5A5","#FCD34D","#FDE68A","#BBF7D0","#86EFAC"],
                               edgecolor="white",linewidth=1.5,width=.5)
                for bar,val in zip(bars,rating_counts.values()):
                    if val>0: ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.05,str(val),ha="center",va="bottom",fontsize=9,fontweight="bold",color="#475569")
                _chart_style(ax,fig); ax.set_ylabel("Count",fontsize=9,color="#475569")
                ax.set_title("Star ratings",fontsize=9,color="#475569")
                st.pyplot(fig, use_container_width=True); plt.close(fig)


# =============================================================
# SECTION 8 — ANNOUNCEMENT MANAGEMENT
# =============================================================
def render_announcements():
    _sec("📢", "Announcement Management")
    post_tab, manage_tab = st.tabs(["✍️  Post Announcement", "📋  Manage Existing"])

    with post_tab:
        st.markdown("**Post a new announcement visible to all students.**")
        with st.form("post_ann_form"):
            ann_title = st.text_input("Title *", max_chars=200, placeholder="e.g. Water Supply Interruption – 10th May")
            ann_type  = st.selectbox("Type *", ANNOUNCEMENT_TYPES)
            ann_desc  = st.text_area("Description *", height=140, max_chars=1000,
                                      placeholder="Enter the full announcement details here...")
            warden_id = st.session_state.get("warden_id","WD001")

            if st.form_submit_button("📢  Post Announcement", use_container_width=True):
                if not ann_title.strip():  st.error("⚠️ Title is required.")
                elif not ann_desc.strip(): st.error("⚠️ Description is required.")
                else:
                    conn = get_connection()
                    if conn:
                        try:
                            aid = post_announcement(conn, ann_title.strip(), ann_desc.strip(), ann_type, warden_id)
                            st.success(f"✅ Announcement #{aid} posted!")
                            icon = ANNOUNCEMENT_ICONS.get(ann_type,"📢")
                            st.markdown(f'<div class="alert-green">{icon} <b>{ann_title}</b> — {ann_type} notice posted successfully.</div>', unsafe_allow_html=True)
                        except Exception as ex:
                            st.error(f"Failed: {ex}")
                        finally:
                            conn.close()

    with manage_tab:
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            announcements = get_active_announcements(conn)
        finally:
            conn.close()

        if not announcements:
            st.info("No active announcements."); return

        st.markdown(f"**{len(announcements)} active announcement(s)**")
        border_colors={"General":"#2D6BE4","Emergency":"#DC2626","Mess Update":"#16A34A","Holiday":"#D97706"}
        for ann in announcements:
            t=ann["ann_type"]; bc=border_colors.get(t,"#2D6BE4"); bg=ANNOUNCEMENT_COLORS.get(t,"#F8FAFC")
            with st.expander(f"{ANNOUNCEMENT_ICONS.get(t,'📢')}  {ann['title']}  ·  {t}  ·  {str(ann['posted_date'])[:10]}"):
                st.markdown(f"""
                <div style="background:{bg};border-left:4px solid {bc};border-radius:0 10px 10px 0;padding:12px 16px;font-size:.86rem;color:#0F172A;line-height:1.6;">
                    {ann['description']}
                </div>""", unsafe_allow_html=True)
                if st.button(f"🗑️  Deactivate #{ann['announcement_id']}", key=f"deact_{ann['announcement_id']}"):
                    conn = get_connection()
                    if conn:
                        try:
                            deactivate_announcement(conn, ann["announcement_id"])
                            st.success("Announcement deactivated."); st.rerun()
                        except Exception as ex:
                            st.error(f"Failed: {ex}")
                        finally:
                            conn.close()


# =============================================================
# SECTION 9 — AI ROOM ALLOCATION SUGGESTIONS
# =============================================================
def render_ai_room():

    _sec("🤖", "AI Smart Room Allocation")

    st.markdown("""
    <div style="
        background:linear-gradient(135deg,#EEF3FD,#F5F3FF);
        border:1px solid #C7D9FA;
        border-radius:14px;
        padding:14px 18px;
        margin-bottom:1.2rem;
    ">
        <b>🧠 How it works:</b>
        Enter a new student's details and the AI will score all available rooms
        based on how many current occupants share the same department, year,
        and food preference.
        Higher score = better compatibility match.
    </div>
    """, unsafe_allow_html=True)

    with st.form("ai_room_form"):

        c1, c2, c3 = st.columns(3)

        with c1:
            ai_dept = st.selectbox(
                "Department",
                DEPARTMENTS
            )

        with c2:
            ai_year = st.selectbox(
                "Year",
                YEARS
            )

        with c3:
            ai_food = st.selectbox(
                "Food Preference",
                FOOD_PREFERENCES
            )

        submitted = st.form_submit_button(
            "🔍 Find Best Rooms",
            use_container_width=True
        )

        if submitted:
            st.session_state["ai_room_query"] = {
                "dept": ai_dept,
                "year": ai_year,
                "food": ai_food
            }

    if "ai_room_query" not in st.session_state:
        return

    q = st.session_state["ai_room_query"]

    conn = get_connection()

    if not conn:
        st.error("Database connection failed")
        return

    try:
        avail_rooms = get_available_rooms(conn)
        all_students = get_all_students(conn)

    finally:
        conn.close()

    if not avail_rooms:
        st.warning("⚠️ No rooms with available beds.")
        return

    scored = []

    for room in avail_rooms:

        room_no = room["room_no"]

        occupants = [
            s for s in all_students
            if s.get("room_no") == room_no
        ]

        score = 0
        match_details = []

        for occ in occupants:

            if occ.get("department") == q["dept"]:
                score += 3
                match_details.append("Department")

            if occ.get("year") == q["year"]:
                score += 2
                match_details.append("Year")

            if occ.get("food_preference") == q["food"]:
                score += 1
                match_details.append("Food Preference")

        scored.append({
            **room,
            "score": score,
            "occupants": len(occupants),
            "match_details": match_details
        })

    scored.sort(
        key=lambda x: (-x["score"], x["room_no"])
    )

    top3 = scored[:3]

    st.markdown(
        f"""
        <h4>
        🏆 Top Recommended Rooms
        </h4>

        <div style="margin-bottom:15px;color:#475569;">
            For:
            <b>{q['dept']} | Year {q['year']} | {q['food']}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    for i, r in enumerate(top3, 1):

        rank_color = [
            "#F59E0B",
            "#9CA3AF",
            "#CD7C41"
        ][i - 1]

        rank_label = [
            "🥇 Best Match",
            "🥈 Good Match",
            "🥉 Suitable"
        ][i - 1]

        match_tags = ", ".join(
            list(set(r["match_details"]))
        )

        if not match_tags:
            match_tags = "No current occupants (empty room)"

        ac_html = ""

        if r.get("ac_available"):
            ac_html = "<span>❄️ AC Room</span>"

        card_html = f"""
        <div style="
            background:white;
            border:1px solid #E2E8F0;
            border-left:5px solid {rank_color};
            border-radius:14px;
            padding:18px;
            margin-bottom:18px;
            box-shadow:0 2px 8px rgba(0,0,0,.05);
        ">

            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:12px;
            ">

                <div>

                    <div style="
                        font-size:1.05rem;
                        font-weight:700;
                        color:#0F172A;
                    ">
                        🏠 Room {r['room_no']}
                    </div>

                    <div style="
                        font-size:.82rem;
                        color:#64748B;
                        margin-top:3px;
                    ">
                        {r['block']} · Floor {r['floor']} · {r['room_type']}
                    </div>

                </div>

                <div style="text-align:right;">

                    <div style="
                        color:{rank_color};
                        font-size:.9rem;
                        font-weight:700;
                    ">
                        {rank_label}
                    </div>

                    <div style="
                        font-size:.78rem;
                        color:#64748B;
                    ">
                        Compatibility Score:
                        <b>{r['score']}</b>
                    </div>

                </div>

            </div>

            <div style="
                display:flex;
                gap:20px;
                flex-wrap:wrap;
                margin-bottom:14px;
                font-size:.84rem;
                color:#475569;
            ">

                <span>
                    🛏️ {r['occupied']}/{r['capacity']} occupied
                </span>

                <span>
                    ✅ {r['available_beds']} bed(s) free
                </span>

                {ac_html}

            </div>

            <div style="
                background:#F8FAFC;
                border:1px solid #E2E8F0;
                border-radius:10px;
                padding:10px 12px;
                font-size:.82rem;
                color:#334155;
            ">

                <b>Matching Traits:</b><br><br>

                {match_tags}

            </div>

        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    if len(scored) > 3:

        with st.expander(
            f"View all {len(scored)} available rooms"
        ):

            rows = []

            for r in scored:

                rows.append([
                    r["room_no"],
                    r["block"],
                    r["room_type"],
                    f"{r['occupied']}/{r['capacity']}",
                    str(r["available_beds"]),
                    str(r["score"])
                ])

            _render_table(
                [
                    "Room",
                    "Block",
                    "Type",
                    "Occupied",
                    "Free Beds",
                    "Score"
                ],
                rows
            )
# =============================================================
# SECTION 10 — AI COMPLAINT ANALYSIS
# =============================================================
def render_ai_complaints():
    _sec("🤖", "AI Complaint Analyser")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#FFF7ED,#FFEDD5);border:1px solid #FED7AA;border-radius:14px;padding:14px 18px;margin-bottom:1.2rem;">
        <b>🧠 How it works:</b> Paste any complaint text and the AI will instantly detect:
        <b>Category</b> (Electrical / Plumbing / Internet / …) and
        <b>Priority</b> (Normal / Urgent / Emergency) using keyword analysis.
    </div>""", unsafe_allow_html=True)

    with st.form("ai_complaint_form"):
        test_text = st.text_area("Enter complaint text to analyse",
                                  placeholder="e.g. There is a water leakage from the ceiling in room A101 which has been going on since yesterday morning...",
                                  height=130, max_chars=1000)
        if st.form_submit_button("🔍  Analyse Complaint", use_container_width=True):
            st.session_state["ai_comp_text"] = test_text

    if "ai_comp_text" not in st.session_state or not st.session_state["ai_comp_text"].strip():
        return

    text = st.session_state["ai_comp_text"]

    # ── Keyword-based detection (standalone, no import needed) ──
    t = text.lower()
    EMERGENCY_KW = ["spark","fire","flood","short circuit","gas leak","electrocute","electric shock","injury","collapsed","burst pipe","overflow"]
    URGENT_KW    = ["leakage","no water","not working","broken","blocked","stuck","damage","crack","no power","no electricity","smell","foul"]
    ELECTRICAL_KW= ["light","tube light","fan","switch","socket","wire","electricity","power","voltage","bulb","fuse","electric","spark","short circuit"]
    PLUMBING_KW  = ["water","tap","pipe","drain","leak","toilet","flush","bathroom","shower","tank","block","overflow"]
    INTERNET_KW  = ["wifi","internet","network","router","connection","broadband","signal","speed","bandwidth"]
    CLEANING_KW  = ["clean","dirt","garbage","dustbin","sweep","mop","cockroach","rat","pest","smell","stink","hygiene"]
    FURNITURE_KW = ["bed","chair","table","almirah","cupboard","door","window","lock","hinge","broken furniture","shelf"]

    # Priority
    if any(kw in t for kw in EMERGENCY_KW):
        priority = "Emergency"; p_col="#DC2626"; p_bg="#FEE2E2"
    elif any(kw in t for kw in URGENT_KW):
        priority = "Urgent"; p_col="#D97706"; p_bg="#FEF3C7"
    else:
        priority = "Normal"; p_col="#16A34A"; p_bg="#DCFCE7"

    # Category
    scores = {
        "Electrical": sum(1 for kw in ELECTRICAL_KW if kw in t),
        "Plumbing":   sum(1 for kw in PLUMBING_KW   if kw in t),
        "Internet":   sum(1 for kw in INTERNET_KW   if kw in t),
        "Cleaning":   sum(1 for kw in CLEANING_KW   if kw in t),
        "Furniture":  sum(1 for kw in FURNITURE_KW  if kw in t),
    }
    category = max(scores, key=scores.get) if max(scores.values()) > 0 else "Others"

    # Matched keywords display
    matched_e = [kw for kw in EMERGENCY_KW if kw in t]
    matched_u = [kw for kw in URGENT_KW    if kw in t]
    cat_kws   = {"Electrical":ELECTRICAL_KW,"Plumbing":PLUMBING_KW,"Internet":INTERNET_KW,"Cleaning":CLEANING_KW,"Furniture":FURNITURE_KW}.get(category,[])
    matched_c = [kw for kw in cat_kws if kw in t]

    st.markdown(f"""
    <div style="background:#FAFBFF;border:1.5px solid #E2E8F0;border-radius:14px;padding:20px 22px;margin-top:1rem;">
        <div style="font-weight:700;font-size:1rem;margin-bottom:14px;">🔍 AI Analysis Result</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
            <div style="background:{p_bg};border:1px solid {p_col}40;border-radius:10px;padding:14px 16px;text-align:center;">
                <div style="font-size:.75rem;color:#94A3B8;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">Priority</div>
                <div style="font-size:1.4rem;font-weight:800;color:{p_col};">{PRIORITY_ICONS.get(priority,'')} {priority}</div>
                <div style="font-size:.75rem;color:{p_col};margin-top:4px;">{'Immediate action required' if priority=='Emergency' else 'Attend within 24 hours' if priority=='Urgent' else 'Schedule at convenience'}</div>
            </div>
            <div style="background:#EEF3FD;border:1px solid #C7D9FA;border-radius:10px;padding:14px 16px;text-align:center;">
                <div style="font-size:.75rem;color:#94A3B8;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">Category</div>
                <div style="font-size:1.4rem;font-weight:800;color:#2D6BE4;">📂 {category}</div>
                <div style="font-size:.75rem;color:#2D6BE4;margin-top:4px;">Assign to {category} department</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    if matched_e or matched_u:
        kw_html = " ".join([_badge(kw,"#991B1B","#FEE2E2") for kw in matched_e] + [_badge(kw,"#92400E","#FEF3C7") for kw in matched_u])
        st.markdown(f"**Priority keywords found:** {kw_html}", unsafe_allow_html=True)
    if matched_c:
        kw_html = " ".join([_badge(kw,"#1E3A8A","#DBEAFE") for kw in matched_c])
        st.markdown(f"**Category keywords found:** {kw_html}", unsafe_allow_html=True)

    # Bulk analysis
    st.markdown("---")
    st.markdown("**Bulk Analysis — Auto-classify all pending complaints**")
    if st.button("🔍  Analyse All Pending Complaints"):
        conn = get_connection()
        if not conn: st.error("DB error"); return
        try:
            pending = get_complaints_filtered(conn, status="Pending")
        finally:
            conn.close()

        if not pending:
            st.info("No pending complaints to analyse."); return

        rows = []
        for c in pending:
            t2 = c["complaint_text"].lower()
            if any(kw in t2 for kw in EMERGENCY_KW): pri="Emergency"; p_c="#DC2626"; p_b="#FEE2E2"
            elif any(kw in t2 for kw in URGENT_KW): pri="Urgent"; p_c="#D97706"; p_b="#FEF3C7"
            else: pri="Normal"; p_c="#16A34A"; p_b="#DCFCE7"
            rows.append([
                f"#{c['complaint_id']}", c["student_name"], c["category"],
                _badge(PRIORITY_ICONS.get(pri,'')+' '+pri, p_c, p_b),
                c["complaint_text"][:80]+"…" if len(c["complaint_text"])>80 else c["complaint_text"],
            ])
        _render_table(["ID","Student","Category","AI Priority","Complaint"], rows)


# =============================================================
# SECTION 11 — ANALYTICS
# =============================================================
def render_analytics():
    _sec("📈", "Hostel Analytics")

    conn = get_connection()
    if not conn: st.error("DB error"); return
    try:
        all_students    = get_all_students(conn)
        rooms           = get_all_rooms(conn)
        complaint_sum   = get_complaint_summary(conn)
        sentiment_data  = get_sentiment_summary(conn)
        avg_rating      = get_average_rating(conn)
        recent_menus    = get_recent_menus(conn, 7)
    finally:
        conn.close()

    st.markdown("**🏠 Hostel-wide Summary**")
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: _kpi("Students",   len(all_students),"👥","#2D6BE4","#EEF3FD")
    with c2: _kpi("Rooms",      len(rooms),        "🏠","#7C3AED","#F5F3FF")
    with c3: _kpi("Total Beds", sum(r["capacity"] for r in rooms),"🛏️","#D97706","#FFFBEB")
    with c4: _kpi("Avg Rating", f"{avg_rating}⭐","🍽️","#16A34A","#F0FDF4")
    with c5: _kpi("Occupied Beds",sum(r["occupied"] for r in rooms),"👤","#0891B2","#ECFEFF")

    st.markdown("---"); st.markdown("**📊 Department-wise Student Distribution**")
    dept_counts = {}
    for s in all_students:
        dept_counts[s["department"]] = dept_counts.get(s["department"],0)+1

    if dept_counts:
        fig,ax = plt.subplots(figsize=(8,3.5))
        depts  = list(dept_counts.keys()); counts = list(dept_counts.values())
        colors = ["#60A5FA","#818CF8","#34D399","#FBBF24","#F87171","#A78BFA","#2DD4BF","#FB923C","#E879F9"]
        bars = ax.bar(depts, counts, color=colors[:len(depts)], edgecolor="white", linewidth=1.5, width=.55)
        for bar,val in zip(bars,counts):
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.1,str(val),ha="center",va="bottom",fontsize=9,fontweight="bold",color="#475569")
        _chart_style(ax,fig); ax.set_ylabel("Students",fontsize=9,color="#475569")
        ax.set_title("Students per department",fontsize=9,color="#475569")
        st.pyplot(fig, use_container_width=True); plt.close(fig)

    ch1,ch2 = st.columns(2)

    with ch1:
        st.markdown("**Year-wise Distribution**")
        year_counts = {}
        for s in all_students: year_counts[f"Year {s['year']}"] = year_counts.get(f"Year {s['year']}",0)+1
        if year_counts:
            fig,ax = plt.subplots(figsize=(4,3.2))
            wedges,texts,autotexts = ax.pie(year_counts.values(),labels=year_counts.keys(),autopct="%1.0f%%",
                colors=["#60A5FA","#818CF8","#34D399","#FBBF24","#F87171"],
                wedgeprops={"width":.55,"edgecolor":"white","linewidth":2},startangle=90)
            for t in texts: t.set_fontsize(9); t.set_color("#475569")
            for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
            fig.patch.set_facecolor("white")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    with ch2:
        st.markdown("**Food Preference Split**")
        food_counts = {}
        for s in all_students: food_counts[s.get("food_preference","—")] = food_counts.get(s.get("food_preference","—"),0)+1
        if food_counts:
            fig,ax = plt.subplots(figsize=(4,3.2))
            wedges,texts,autotexts = ax.pie(food_counts.values(),labels=food_counts.keys(),autopct="%1.0f%%",
                colors=["#86EFAC","#FCA5A5","#FCD34D"],
                wedgeprops={"width":.55,"edgecolor":"white","linewidth":2},startangle=90)
            for t in texts: t.set_fontsize(9); t.set_color("#475569")
            for a in autotexts: a.set_fontsize(8); a.set_color("white"); a.set_fontweight("bold")
            fig.patch.set_facecolor("white")
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown("---"); st.markdown("**🏢 Block-wise Occupancy**")
    block_data = {}
    for r in rooms:
        b = r["block"]
        if b not in block_data: block_data[b] = {"capacity":0,"occupied":0}
        block_data[b]["capacity"] += r["capacity"]
        block_data[b]["occupied"] += r["occupied"]

    if block_data:
        blocks = list(block_data.keys())
        fig,ax = plt.subplots(figsize=(6,3))
        x = range(len(blocks)); width = .35
        bars1 = ax.bar([i-width/2 for i in x],[block_data[b]["capacity"] for b in blocks],width,label="Capacity",color="#DBEAFE",edgecolor="white",linewidth=1.5)
        bars2 = ax.bar([i+width/2 for i in x],[block_data[b]["occupied"] for b in blocks],width,label="Occupied",color="#2D6BE4",edgecolor="white",linewidth=1.5)
        ax.set_xticks(list(x)); ax.set_xticklabels(blocks)
        ax.legend(fontsize=8)
        _chart_style(ax,fig); ax.set_ylabel("Beds",fontsize=9,color="#475569")
        ax.set_title("Capacity vs Occupied per Block",fontsize=9,color="#475569")
        st.pyplot(fig, use_container_width=True); plt.close(fig)


# =============================================================
# SECTION 12 — EMERGENCY ALERTS
# =============================================================
def render_emergency():
    _sec("🚨", "Emergency Alerts")

    conn = get_connection()
    if not conn: st.error("DB error"); return
    try:
        emergencies = get_emergency_complaints(conn)
        all_comps   = get_complaints_filtered(conn, priority="Urgent")
        urgent_open = [c for c in all_comps if c["status"] != "Resolved"]
    finally:
        conn.close()

    # Banner
    if not emergencies and not urgent_open:
        st.markdown('<div class="alert-green"><div style="font-size:1.1rem;">✅</div><b>All clear! No emergency or urgent complaints right now.</b></div>', unsafe_allow_html=True)
        return

    if emergencies:
        st.markdown(f'<div class="alert-red">🚨 <b>{len(emergencies)} EMERGENCY COMPLAINT(S) — Immediate action required!</b></div>', unsafe_allow_html=True)
        for ec in emergencies:
            with st.expander(f"🚨  #{ec['complaint_id']} — {ec['name']} — Room {ec.get('room_no','—')}  |  Filed: {ec['filed_date']}", expanded=True):
                st.markdown(f"""
                <div style="background:#FEF2F2;border:1.5px solid #FECACA;border-radius:10px;padding:14px 16px;font-size:.9rem;color:#7F1D1D;line-height:1.6;">
                    {ec['complaint_text']}
                </div>""", unsafe_allow_html=True)
                with st.form(f"em_resolve_{ec['complaint_id']}"):
                    remarks = st.text_input("Action Taken / Remarks *", placeholder="e.g. Electrician dispatched immediately at 2 PM...")
                    c1,c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("🔧  Mark In Progress", use_container_width=True):
                            if not remarks.strip(): st.error("Please add remarks.")
                            else:
                                conn2=get_connection()
                                if conn2:
                                    try:
                                        update_complaint_status(conn2,ec["complaint_id"],"In Progress",remarks)
                                        st.success("Updated to In Progress"); st.rerun()
                                    except Exception as ex: st.error(f"Error: {ex}")
                                    finally: conn2.close()
                    with c2:
                        if st.form_submit_button("✅  Mark Resolved", use_container_width=True):
                            if not remarks.strip(): st.error("Please add remarks.")
                            else:
                                conn2=get_connection()
                                if conn2:
                                    try:
                                        update_complaint_status(conn2,ec["complaint_id"],"Resolved",remarks)
                                        st.success("Marked as Resolved!"); st.rerun()
                                    except Exception as ex: st.error(f"Error: {ex}")
                                    finally: conn2.close()

    if urgent_open:
        st.markdown("---")
        st.markdown(f'<div class="alert-amber">⚠️ <b>{len(urgent_open)} URGENT COMPLAINT(S) — Attend within 24 hours</b></div>', unsafe_allow_html=True)
        rows = []
        for c in urgent_open:
            rows.append([
                f"#{c['complaint_id']}", c["student_name"], c.get("room_no") or "—",
                c["category"],
                f'<span class="s-pending">{c["status"]}</span>',
                str(c["filed_date"]),
                c["complaint_text"][:70]+"…" if len(c["complaint_text"])>70 else c["complaint_text"],
            ])
        _render_table(["ID","Student","Room","Category","Status","Date","Issue"], rows)


# =============================================================
# SIDEBAR NAVIGATION
# =============================================================
NAV_ITEMS = [
    ("📊","Dashboard"),
    ("👥","Students"),
    ("🏠","Rooms"),
    ("📋","Complaints"),
    ("🚪","Leave"),
    ("📅","Attendance"),
    ("🍽️","Mess"),
    ("📢","Announcements"),
    ("🤖","AI Room Suggest"),
    ("🧠","AI Complaints"),
    ("📈","Analytics"),
    ("🚨","Emergency"),
]

def render_nav() -> str:
    with st.sidebar:
        # Warden profile card
        name  = st.session_state.get("warden_name","Warden")
        block = st.session_state.get("hostel_block","")
        wid   = st.session_state.get("warden_id","")
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#FFF7ED,#FFEDD5);border:1px solid #FED7AA;border-radius:14px;padding:14px;margin-bottom:.8rem;text-align:center;">
            <div style="font-size:1.8rem;">🛡️</div>
            <div style="font-weight:700;font-size:.95rem;color:#0F172A;">{name}</div>
            <div style="font-size:.78rem;color:#C2410C;">{block} Warden</div>
            <div style="font-size:.72rem;color:#94A3B8;font-family:'DM Mono',monospace;">{wid}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div style="font-size:.7rem;font-weight:700;color:#94A3B8;text-transform:uppercase;letter-spacing:.08em;padding:0 4px;margin-bottom:.3rem;">Navigation</div>', unsafe_allow_html=True)
        labels = [f"{icon}  {label}" for icon,label in NAV_ITEMS]
        selection = st.radio("nav", labels, label_visibility="collapsed", key="warden_nav")
        st.divider()
        st.markdown('<div style="font-size:.72rem;color:#94A3B8;text-align:center;">Hostel Hub v1.0 · AI &amp; DS Dept</div>', unsafe_allow_html=True)

    return selection.split("  ",1)[-1].strip()


# =============================================================
# MAIN ENTRY POINT
# =============================================================
def render_warden_dashboard():
    require_warden_login()
    _inject_css()

    active = render_nav()

    if   active == "Dashboard":      render_dashboard()
    elif active == "Students":       render_students()
    elif active == "Rooms":          render_rooms()
    elif active == "Complaints":     render_complaints()
    elif active == "Leave":          render_leaves()
    elif active == "Attendance":     render_attendance()
    elif active == "Mess":           render_mess()
    elif active == "Announcements":  render_announcements()
    elif active == "AI Room Suggest":render_ai_room()
    elif active == "AI Complaints":  render_ai_complaints()
    elif active == "Analytics":      render_analytics()
    elif active == "Emergency":      render_emergency()
