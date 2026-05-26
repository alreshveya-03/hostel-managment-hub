# =============================================================
#  HOSTEL HUB — app.py
#  ✅ SAFE PATCH — only render_student_login(),
#     render_warden_login(), inject_global_css() extended.
#     ALL other functions, imports, portals untouched.
# =============================================================

import time
import streamlit as st

from database.connection import get_connection
from utils.auth_utils import (
    login_student,
    login_warden,
    set_student_session,
    set_warden_session,
    clear_session,
    is_logged_in,
    get_current_role,
    validate_register_number,
    validate_warden_id,
    validate_password,
)

# 🆕  registration helpers added in this session
from database.queries import register_student, register_warden

# =============================================================
# PAGE CONFIG  (unchanged)
# =============================================================
st.set_page_config(
    page_title="Hostel Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================
# GLOBAL CSS  (original kept + new classes appended)
# =============================================================
def inject_global_css():

    st.markdown("""
    <style>

    /* ── Original styles (unchanged) ──────────────────────── */

    .stApp{
        background:
        linear-gradient(135deg,#EEF2FF 0%,#FDF2F8 50%,#ECFEFF 100%);
    }

    #MainMenu, footer, header{
        visibility:hidden;
    }

    .block-container{
        padding-top:2rem;
    }

    .login-card{
        background:rgba(255,255,255,0.75);
        backdrop-filter:blur(16px);
        padding:40px;
        border-radius:25px;
        box-shadow:0 10px 40px rgba(0,0,0,0.08);
        border:1px solid rgba(255,255,255,0.4);
    }

    .title{
        text-align:center;
        font-size:48px;
        font-weight:800;
        color:#111827;
        margin-top:15px;
    }

    .subtitle{
        text-align:center;
        font-size:18px;
        color:#6B7280;
        margin-bottom:30px;
    }

    .logo-box{
        width:90px;
        height:90px;
        margin:auto;
        border-radius:25px;
        background:linear-gradient(135deg,#4F46E5,#7C3AED);
        display:flex;
        align-items:center;
        justify-content:center;
        font-size:42px;
        color:white;
        box-shadow:0 10px 30px rgba(79,70,229,0.4);
    }

    .stButton button{
        width:100%;
        border:none;
        border-radius:12px;
        background:linear-gradient(135deg,#2563EB,#1D4ED8);
        color:white;
        font-weight:700;
        padding:12px;
        font-size:16px;
    }

    .stButton button:hover{
        background:linear-gradient(135deg,#1D4ED8,#1E40AF);
    }

    .stTextInput input{
        border-radius:10px !important;
        border:1px solid #CBD5E1 !important;
        padding:10px !important;
    }

    section[data-testid="stSidebar"]{
        background:#FFFFFF;
        border-right:1px solid #E2E8F0;
    }

    /* ── NEW: registration banner ──────────────────────────── */

    .reg-banner{
        background:linear-gradient(135deg,#4F46E5,#7C3AED);
        border-radius:14px;
        padding:13px 20px;
        margin-bottom:20px;
        color:white;
        font-weight:700;
        font-size:14px;
        letter-spacing:0.3px;
    }

    .reg-banner-teal{
        background:linear-gradient(135deg,#0F766E,#0D9488);
        border-radius:14px;
        padding:13px 20px;
        margin-bottom:20px;
        color:white;
        font-weight:700;
        font-size:14px;
        letter-spacing:0.3px;
    }

    /* ── NEW: field section label ──────────────────────────── */

    .field-section{
        font-size:12px;
        font-weight:700;
        color:#6B7280;
        text-transform:uppercase;
        letter-spacing:1px;
        margin:14px 0 6px 0;
    }

    /* ── NEW: tab polish ───────────────────────────────────── */

    .stTabs [data-baseweb="tab"]{
        font-weight:600;
        font-size:14px;
    }

    </style>
    """, unsafe_allow_html=True)


# =============================================================
# LOGIN HEADER  (unchanged)
# =============================================================
def render_login_header():

    st.markdown("""
    <div style="text-align:center;padding:20px;">

        <div class="logo-box">
            🏠
        </div>

        <div class="title">
            Hostel Hub
        </div>

        <div class="subtitle">
            Smart AI-Powered Hostel Management System
        </div>

    </div>
    """, unsafe_allow_html=True)


# =============================================================
# STUDENT LOGIN  🆕 dual-tab: Sign In + Register
# =============================================================
def render_student_login():

    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.subheader("🎓 Student Portal")

    signin_tab, register_tab = st.tabs(["🔐  Sign In", "🆕  Register"])

    # ── SIGN IN ──────────────────────────────────────────────
    with signin_tab:

        st.markdown(
            "<p style='color:#6B7280;margin-bottom:18px;'>"
            "Welcome back! Enter your credentials to continue.</p>",
            unsafe_allow_html=True,
        )

        with st.form("student_signin_form"):

            register_number = st.text_input(
                "Register Number",
                placeholder="e.g. 21CS001",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "🔐  Sign In",
                use_container_width=True,
            )

        if submitted:

            valid_reg, reg_error = validate_register_number(register_number)
            valid_pw,  pw_error  = validate_password(password)

            if not valid_reg:
                st.error(reg_error)
            elif not valid_pw:
                st.error(pw_error)
            else:
                with st.spinner("Verifying credentials…"):
                    result = login_student(register_number.strip(), password)

                if result["success"]:
                    set_student_session(result["student"])
                    st.success(f"Welcome back, {result['student']['name']} 🎉")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result["message"])

    # ── REGISTER ─────────────────────────────────────────────
    with register_tab:

        st.markdown(
            '<div class="reg-banner">🎓 &nbsp; New student? Create your account below.</div>',
            unsafe_allow_html=True,
        )

        with st.form("student_register_form"):

            # Row 1
            col1, col2 = st.columns(2)
            with col1:
                r_full_name = st.text_input(
                    "Full Name *",
                    placeholder="e.g. Arjun Sharma",
                )
            with col2:
                r_register_number = st.text_input(
                    "Register Number *",
                    placeholder="e.g. 21CS001",
                )

            # Row 2
            col3, col4 = st.columns(2)
            with col3:
                r_department = st.text_input(
                    "Department *",
                    placeholder="e.g. Computer Science",
                )
            with col4:
                r_year = st.selectbox(
                    "Year *",
                    options=[1, 2, 3, 4],
                    index=0,
                )

            # Row 3
            col5, col6 = st.columns(2)
            with col5:
                r_phone = st.text_input(
                    "Phone Number *",
                    placeholder="10-digit mobile number",
                    max_chars=10,
                )
            with col6:
                r_email = st.text_input(
                    "Email Address *",
                    placeholder="e.g. arjun@college.edu",
                )

            # Row 4
            col7, col8 = st.columns(2)
            with col7:
                r_gender = st.selectbox(
                    "Gender *",
                    options=["Select", "Male", "Female", "Other"],
                    index=0,
                )
            with col8:
                r_room = st.text_input(
                    "Room Number",
                    placeholder="e.g. A-204  (optional)",
                )

            # Row 5 — passwords
            col9, col10 = st.columns(2)
            with col9:
                r_password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Minimum 6 characters",
                )
            with col10:
                r_confirm = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Re-enter password",
                )

            reg_submitted = st.form_submit_button(
                "🆕  Create Student Account",
                use_container_width=True,
            )

        if reg_submitted:

            errors = []

            if not r_full_name.strip():
                errors.append("Full Name is required.")

            valid_reg, reg_err = validate_register_number(r_register_number)
            if not valid_reg:
                errors.append(reg_err)

            if not r_department.strip():
                errors.append("Department is required.")

            if not r_phone.strip() or not r_phone.strip().isdigit() or len(r_phone.strip()) != 10:
                errors.append("Phone Number must be exactly 10 digits.")

            if not r_email.strip() or "@" not in r_email or "." not in r_email.split("@")[-1]:
                errors.append("A valid Email Address is required.")

            if r_gender == "Select":
                errors.append("Please select a Gender.")

            valid_pw, pw_err = validate_password(r_password)
            if not valid_pw:
                errors.append(pw_err)

            if r_password != r_confirm:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)

            else:
                with st.spinner("Creating your account…"):
                    conn = get_connection() 
                    result = register_student(
                        conn=conn,
                        full_name=r_full_name,
                        register_number=r_register_number,
                        department=r_department,
                        year=r_year,
                        phone=r_phone,
                        email=r_email,
                        gender=r_gender,
                        password=r_password,
                    )

                    conn.close()

                if result["success"]:
                    st.success(
                        "✅ Account created! Switch to **Sign In** tab to log in."
                    )
                    st.balloons()
                else:
                    st.error(result["message"])

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# WARDEN LOGIN  🆕 dual-tab: Sign In + Register
# =============================================================
def render_warden_login():

    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.subheader("🛡️ Warden Portal")

    signin_tab, register_tab = st.tabs(["🛡️  Sign In", "🆕  Register"])

    # ── SIGN IN ──────────────────────────────────────────────
    with signin_tab:

        st.markdown(
            "<p style='color:#6B7280;margin-bottom:18px;'>"
            "Welcome back! Enter your credentials to continue.</p>",
            unsafe_allow_html=True,
        )

        with st.form("warden_signin_form"):

            warden_id = st.text_input(
                "Warden ID",
                placeholder="e.g. WD001",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
            )

            submitted = st.form_submit_button(
                "🛡️  Sign In",
                use_container_width=True,
            )

        if submitted:

            valid_id, id_error = validate_warden_id(warden_id)
            valid_pw, pw_error = validate_password(password)

            if not valid_id:
                st.error(id_error)
            elif not valid_pw:
                st.error(pw_error)
            else:
                with st.spinner("Verifying credentials…"):
                    result = login_warden(warden_id.strip(), password)

                if result["success"]:
                    set_warden_session(result["warden"])
                    st.success(f"Welcome back, {result['warden']['name']} 🎉")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result["message"])

    # ── REGISTER ─────────────────────────────────────────────
    with register_tab:

        st.markdown(
            '<div class="reg-banner-teal">🛡️ &nbsp; New warden? Create your account below.</div>',
            unsafe_allow_html=True,
        )

        with st.form("warden_register_form"):

            # Row 1
            col1, col2 = st.columns(2)
            with col1:
                w_full_name = st.text_input(
                    "Full Name *",
                    placeholder="e.g. Dr. Ramesh Kumar",
                )
            with col2:
                w_warden_id = st.text_input(
                    "Warden ID *",
                    placeholder="e.g. WD001",
                )

            # Row 2
            col3, col4 = st.columns(2)
            with col3:
                w_phone = st.text_input(
                    "Phone Number *",
                    placeholder="10-digit mobile number",
                    max_chars=10,
                )
            with col4:
                w_email = st.text_input(
                    "Email Address *",
                    placeholder="e.g. warden@college.edu",
                )

            # Row 3
            col5, col6 = st.columns(2)
            with col5:
                w_gender = st.selectbox(
                    "Gender *",
                    options=["Select", "Male", "Female", "Other"],
                    index=0,
                )
            with col6:
                w_block = st.selectbox(
                    "Hostel Block *",
                    options=["Select", "Block A", "Block B", "Block C"],
                    index=0,
                )

            # Row 4 — optional office info
            col5b, col6b = st.columns(2)
            with col5b:
                w_office = st.text_input(
                    "Office / Cabin",
                    placeholder="e.g. Ground Floor, Block A  (optional)",
                )

            # Row 5 — passwords
            col7, col8 = st.columns(2)
            with col7:
                w_password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Minimum 6 characters",
                )
            with col8:
                w_confirm = st.text_input(
                    "Confirm Password *",
                    type="password",
                    placeholder="Re-enter password",
                )

            wreg_submitted = st.form_submit_button(
                "🆕  Create Warden Account",
                use_container_width=True,
            )

        if wreg_submitted:

            errors = []

            if not w_full_name.strip():
                errors.append("Full Name is required.")

            valid_id, id_err = validate_warden_id(w_warden_id)
            if not valid_id:
                errors.append(id_err)

            if not w_phone.strip() or not w_phone.strip().isdigit() or len(w_phone.strip()) != 10:
                errors.append("Phone Number must be exactly 10 digits.")

            if not w_email.strip() or "@" not in w_email or "." not in w_email.split("@")[-1]:
                errors.append("A valid Email Address is required.")

            if w_gender == "Select":
                errors.append("Please select a Gender.")

            if w_block == "Select":
                errors.append("Please select a Hostel Block.")

            valid_pw, pw_err = validate_password(w_password)
            if not valid_pw:
                errors.append(pw_err)

            if w_password != w_confirm:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)

            else:
                with st.spinner("Creating your account…"):

                    conn = get_connection()

                    result = register_warden(
                        conn=conn,
                        full_name=w_full_name,
                        warden_id=w_warden_id,
                        phone=w_phone,
                        email=w_email,
                        gender=w_gender,
                        hostel_block=w_block,
                        password=w_password,
                    )

                    conn.close()

                if result["success"]:
                    st.success(
                        "✅ Account created! Switch to **Sign In** tab to log in."
                    )
                    st.balloons()
                else:
                    st.error(result["message"])

    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================
# LOGIN PAGE  (unchanged)
# =============================================================
def render_login_page():

    render_login_header()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        tab1, tab2 = st.tabs([
            "🎓 Student",
            "🛡️ Warden",
        ])

        with tab1:
            render_student_login()

        with tab2:
            render_warden_login()


# =============================================================
# SIDEBAR  (unchanged)
# =============================================================
def render_sidebar():

    with st.sidebar:

        st.markdown("""
        <h2 style='text-align:center;color:#2563EB;'>
        🏠 Hostel Hub
        </h2>
        """, unsafe_allow_html=True)

        role = get_current_role()

        if role == "student":
            st.success("Logged in as Student")

        elif role == "warden":
            st.success("Logged in as Warden")

        st.divider()

        if st.button("🚪 Logout"):
            clear_session()
            st.rerun()


# =============================================================
# STUDENT PORTAL  (unchanged)
# =============================================================
def render_student_portal():

    from pages.student_portal import render_student_dashboard

    render_student_dashboard()


# =============================================================
# WARDEN PORTAL  (unchanged)
# =============================================================
def render_warden_portal():

    from pages.warden_portal import render_warden_dashboard

    render_warden_dashboard()


# =============================================================
# MAIN  (unchanged)
# =============================================================
def main():

    inject_global_css()

    if not is_logged_in():
        render_login_page()
        return

    render_sidebar()

    role = get_current_role()

    if role == "student":
        render_student_portal()

    elif role == "warden":
        render_warden_portal()

    else:
        st.error("Invalid session")
        clear_session()
        st.rerun()


# =============================================================
# ENTRY
# =============================================================
if __name__ == "__main__":
    main()
