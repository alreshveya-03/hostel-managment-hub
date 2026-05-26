# =============================================================
#  HOSTEL HUB — utils/auth_utils.py
#  All authentication-related utilities in one place.
#
#  Covers:
#    1. Password hashing and verification  (bcrypt)
#    2. Student and warden login logic
#    3. Streamlit session state management
#    4. Role-based access guards
#    5. Input validation helpers
#    6. Seed password hash generator (for setup)
# =============================================================

import bcrypt
import streamlit as st
from database.connection import get_connection
from database.queries import get_student_by_register, get_warden_by_id

# Re-export hash_password so warden_portal can import it from utils.auth_utils
def hash_password(plain_password: str) -> str:
    """
    Alias for the bcrypt hash function — re-exported here so
    warden_portal.py can do:  from utils.auth_utils import hash_password
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


# =============================================================
# SECTION 1 — PASSWORD HASHING
# We use bcrypt, which is the industry standard for passwords.
# It is slow by design (to resist brute-force attacks) and
# adds a random "salt" automatically, so two identical passwords
# produce different hashes each time.
# =============================================================

def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    The result is a 60-character string safe to store in MySQL.

    Args:
        plain_password: The user's raw password (e.g. "student123")

    Returns:
        A bcrypt hash string (e.g. "$2b$12$...")

    Usage:
        hashed = hash_password("student123")
        # Store hashed in the database, never the plain text
    """
    # encode() converts the string to bytes — bcrypt requires bytes
    # gensalt() generates a random salt with work factor 12
    # (higher = slower to crack; 12 is a good balance for web apps)
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # decode back to string so it can be stored in MySQL VARCHAR
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain-text password matches a stored bcrypt hash.
    Returns True if they match, False otherwise.

    Args:
        plain_password:  The password the user typed in the login form
        hashed_password: The hash stored in the database

    Returns:
        True if password is correct, False if wrong

    Usage:
        if verify_password("student123", stored_hash):
            # login success
    """
    try:
        plain_bytes  = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        # If the hash is malformed or encoding fails, deny access
        return False


# =============================================================
# SECTION 2 — STUDENT LOGIN
# =============================================================

def login_student(register_number: str, password: str) -> dict:
    """
    Attempt to log in a student using register number + password.

    Steps:
      1. Look up the student by register_number in the database
      2. If not found → return failure
      3. Verify the typed password against the stored bcrypt hash
      4. If correct → return student data dict
      5. If wrong → return failure

    Args:
        register_number: Student's unique registration number (e.g. "21CS001")
        password:        Plain-text password from the login form

    Returns:
        {
          "success": True,
          "student": { ...student row from DB... }
        }
        OR
        {
          "success": False,
          "error": "reason string"
        }
    """
    # --- Basic input check ---
    if not register_number or not register_number.strip():
        return {"success": False, "message": "Register number cannot be empty."}
    if not password or not password.strip():
        return {"success": False, "message": "Password cannot be empty."}

    conn = get_connection()
    if conn is None:
        return {"success": False, "message": "Database connection failed. Contact admin."}

    try:
        student = get_student_by_register(conn, register_number.strip().upper())

        if student is None:
            return {"success": False, "message": "Register number not found."}

        # Verify password against the hash stored in the DB
        if not verify_password(password, student["password"]):
            return {"success": False, "message": "Incorrect password."}

        # Remove the password hash before returning (never expose it)
        student.pop("password", None)
        return {"success": True, "student": student}

    except Exception as e:
        return {"success": False, "message": f"Login error: {str(e)}"}

    finally:
        conn.close()


# =============================================================
# SECTION 3 — WARDEN LOGIN
# =============================================================

def login_warden(warden_id: str, password: str) -> dict:
    """
    Attempt to log in a warden using warden_id + password.

    Args:
        warden_id: Warden's unique ID (e.g. "WD001")
        password:  Plain-text password from the login form

    Returns:
        { "success": True, "warden": { ...warden row... } }
        OR
        { "success": False, "error": "reason string" }
    """
    if not warden_id or not warden_id.strip():
        return {"success": False, "message": "Warden ID cannot be empty."}
    if not password or not password.strip():
        return {"success": False, "message": "Password cannot be empty."}

    conn = get_connection()
    if conn is None:
        return {"success": False, "message": "Database connection failed. Contact admin."}

    try:
        warden = get_warden_by_id(conn, warden_id.strip().upper())

        if warden is None:
            return {"success": False, "message": "Warden ID not found."}

        if not verify_password(password, warden["password"]):
            return {"success": False, "message": "Incorrect password."}

        warden.pop("password", None)
        return {"success": True, "warden": warden}

    except Exception as e:
        return {"success": False, "message": f"Login error: {str(e)}"}

    finally:
        conn.close()


# =============================================================
# SECTION 4 — SESSION STATE MANAGEMENT
# Streamlit uses st.session_state as an in-memory key-value store
# that persists across reruns within the same browser session.
# We store the login state here after a successful login.
# =============================================================

def set_student_session(student: dict):
    """
    Store student login data in Streamlit session state.
    Call this right after a successful student login.

    Keys stored in session_state:
        logged_in    : True
        role         : "student"
        student_id   : int
        student_name : str
        register_no  : str
        department   : str
        year         : int
        room_no      : str or None
    """
    st.session_state["logged_in"]    = True
    st.session_state["role"]         = "student"
    st.session_state["student_id"]   = student["student_id"]
    st.session_state["student_name"] = student["name"]
    st.session_state["register_no"]  = student["register_number"]
    st.session_state["department"]   = student["department"]
    st.session_state["year"]         = student["year"]
    st.session_state["room_no"]      = student.get("room_no")


def set_warden_session(warden: dict):
    """
    Store warden login data in Streamlit session state.
    Call this right after a successful warden login.

    Keys stored in session_state:
        logged_in    : True
        role         : "warden"
        warden_id    : str
        warden_name  : str
        hostel_block : str
    """
    st.session_state["logged_in"]    = True
    st.session_state["role"]         = "warden"
    st.session_state["warden_id"]    = warden["warden_id"]
    st.session_state["warden_name"]  = warden["name"]
    st.session_state["hostel_block"] = warden["hostel_block"]


def clear_session():
    """
    Log the current user out by clearing all session state keys.
    After this, the app redirects back to the login page.
    """
    keys_to_clear = [
        "logged_in", "role",
        "student_id", "student_name", "register_no", "department", "year", "room_no",
        "warden_id", "warden_name", "hostel_block",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    """Return True if any user (student or warden) is currently logged in."""
    return st.session_state.get("logged_in", False)


def get_current_role() -> str | None:
    """Return 'student', 'warden', or None if not logged in."""
    return st.session_state.get("role", None)


def get_student_id() -> int | None:
    """Return the logged-in student's ID, or None."""
    return st.session_state.get("student_id", None)


def get_warden_id() -> str | None:
    """Return the logged-in warden's ID, or None."""
    return st.session_state.get("warden_id", None)


# =============================================================
# SECTION 5 — ROLE-BASED ACCESS GUARDS
# Call these at the TOP of every page to block unauthorized access.
# They redirect the user to the login page if they shouldn't be here.
# =============================================================

def require_student_login():
    """
    Page guard for student-only pages.
    If the user is not logged in as a student, stops page rendering
    and redirects to the login page.

    Usage — put this as the FIRST line in student_portal.py:
        from utils.auth_utils import require_student_login
        require_student_login()
    """
    if not is_logged_in() or get_current_role() != "student":
        st.error("🔒 Access denied. Please log in as a student.")
        st.stop()


def require_warden_login():
    """
    Page guard for warden-only pages.
    If the user is not logged in as a warden, stops page rendering
    and redirects to the login page.

    Usage — put this as the FIRST line in warden_portal.py:
        from utils.auth_utils import require_warden_login
        require_warden_login()
    """
    if not is_logged_in() or get_current_role() != "warden":
        st.error("🔒 Access denied. Please log in as a warden.")
        st.stop()


# =============================================================
# SECTION 6 — INPUT VALIDATION HELPERS
# Small focused functions to validate login form inputs before
# hitting the database. Fast-fail on obvious errors.
# =============================================================

def validate_register_number(register_number: str) -> tuple[bool, str]:
    """
    Validate a student register number format.
    Must be 6–15 characters, alphanumeric only.

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    rn = register_number.strip() if register_number else ""

    if not rn:
        return False, "Register number is required."
    if len(rn) < 4:
        return False, "Register number is too short (minimum 4 characters)."
    if len(rn) > 20:
        return False, "Register number is too long (maximum 20 characters)."
    if not rn.replace(" ", "").isalnum():
        return False, "Register number must contain only letters and numbers."

    return True, ""


def validate_warden_id(warden_id: str) -> tuple[bool, str]:
    """
    Validate a warden ID format.
    Must be like WD001 — starts with WD followed by digits.

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    wid = warden_id.strip().upper() if warden_id else ""

    if not wid:
        return False, "Warden ID is required."
    if len(wid) < 3:
        return False, "Warden ID is too short."
    if not wid.startswith("WD"):
        return False, "Warden ID must start with 'WD' (e.g. WD001)."

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password length.
    Minimum 6 characters for security.

    Returns:
        (True, "") if valid
        (False, "error message") if invalid
    """
    if not password:
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


# =============================================================
# SECTION 7 — SEED PASSWORD GENERATOR
# Run this once from the terminal to generate fresh bcrypt hashes
# for your seed data SQL file.
#
# Usage:
#   python -c "from utils.auth_utils import print_seed_hashes; print_seed_hashes()"
# =============================================================

def print_seed_hashes():
    """
    Prints bcrypt hashes for the default test passwords.
    Use the output to update seed_data.sql with real hashes.
    """
    passwords = {
        "warden123":  "Default password for all wardens",
        "student123": "Default password for all students",
    }
    print("\n=== BCRYPT HASHES FOR SEED DATA ===")
    print("Copy these into seed_data.sql\n")
    for plain, label in passwords.items():
        hashed = hash_password(plain)
        print(f"Plain    : {plain}")
        print(f"Label    : {label}")
        print(f"Hash     : {hashed}")
        print(f"SQL      : '{hashed}'")
        print("-" * 60)


if __name__ == "__main__":
    print_seed_hashes()
