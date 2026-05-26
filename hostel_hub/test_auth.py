#!/usr/bin/env python3
# =============================================================
#  HOSTEL HUB — test_auth.py
#  Standalone test script for the authentication system.
#  Run this from the hostel_hub/ root directory to verify
#  everything works BEFORE starting the Streamlit app.
#
#  Usage:
#    cd hostel_hub
#    python test_auth.py
#
#  What it tests:
#    1. bcrypt hash/verify cycle
#    2. Student login (correct + wrong password)
#    3. Warden login  (correct + wrong password)
#    4. Input validators
#    5. Database connectivity
#    6. Session key structure (printed for reference)
# =============================================================

import sys
import os

# Make sure imports resolve from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Colour helpers for terminal output ───────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"  {GREEN}✓{RESET}  {msg}")
def fail(msg): print(f"  {RED}✗{RESET}  {msg}")
def info(msg): print(f"  {BLUE}ℹ{RESET}  {msg}")
def section(title):
    print(f"\n{BOLD}{YELLOW}{'─'*50}{RESET}")
    print(f"{BOLD}{YELLOW}  {title}{RESET}")
    print(f"{BOLD}{YELLOW}{'─'*50}{RESET}")

passed = 0
failed = 0

def assert_true(condition, label):
    global passed, failed
    if condition:
        ok(label)
        passed += 1
    else:
        fail(label)
        failed += 1

def assert_false(condition, label):
    assert_true(not condition, label)

def assert_equal(a, b, label):
    assert_true(a == b, f"{label}  (got: {a!r})")


# =============================================================
# TEST 1 — bcrypt hash + verify
# =============================================================
section("1. Password Hashing (bcrypt)")

try:
    from utils.auth_utils import hash_password, verify_password

    h1 = hash_password("student123")
    h2 = hash_password("student123")   # Same input → different hash (salted)

    assert_true(h1.startswith("$2b$"),           "Hash starts with $2b$ (bcrypt format)")
    assert_true(len(h1) == 60,                   "Hash is exactly 60 characters")
    assert_true(h1 != h2,                        "Two hashes of same password differ (salting works)")
    assert_true(verify_password("student123", h1),"Correct password verifies against hash 1")
    assert_true(verify_password("student123", h2),"Correct password verifies against hash 2")
    assert_false(verify_password("wrongpass", h1),"Wrong password correctly rejected")
    assert_false(verify_password("", h1),         "Empty password correctly rejected")

except Exception as e:
    fail(f"Hash/verify test crashed: {e}")


# =============================================================
# TEST 2 — Input validators
# =============================================================
section("2. Input Validation")

try:
    from utils.auth_utils import (
        validate_register_number,
        validate_warden_id,
        validate_password,
    )

    # Register number
    ok_rn, _  = validate_register_number("21CS001")
    bad_rn, _ = validate_register_number("")
    short_rn, _= validate_register_number("AB")
    assert_true(ok_rn,    "Valid register number '21CS001' accepted")
    assert_false(bad_rn,  "Empty register number rejected")
    assert_false(short_rn,"Short register number rejected")

    # Warden ID
    ok_wid, _  = validate_warden_id("WD001")
    bad_wid, _ = validate_warden_id("XY999")
    empty_wid, _= validate_warden_id("")
    assert_true(ok_wid,    "Valid warden ID 'WD001' accepted")
    assert_false(bad_wid,  "Warden ID without WD prefix rejected")
    assert_false(empty_wid,"Empty warden ID rejected")

    # Password
    ok_pw, _    = validate_password("student123")
    short_pw, _ = validate_password("abc")
    empty_pw, _ = validate_password("")
    assert_true(ok_pw,     "Password 'student123' accepted")
    assert_false(short_pw, "Short password (<6 chars) rejected")
    assert_false(empty_pw, "Empty password rejected")

except Exception as e:
    fail(f"Validator test crashed: {e}")


# =============================================================
# TEST 3 — Database connectivity
# =============================================================
section("3. Database Connection")

try:
    from database.connection import get_connection, test_connection

    conn = get_connection()
    if conn is not None:
        ok("get_connection() returned a connection object")
        ok(f"Connection is open: {conn.is_connected()}")
        conn.close()
        ok("Connection closed cleanly")
    else:
        fail("get_connection() returned None — check DB_CONFIG in connection.py")
        info("Skipping login tests (no DB connection)")

except Exception as e:
    fail(f"Connection test crashed: {e}")
    info("Make sure MySQL is running and DB_CONFIG is correct")


# =============================================================
# TEST 4 — Student login
# =============================================================
section("4. Student Login")

try:
    from utils.auth_utils import login_student

    # Correct credentials (from seed data)
    result = login_student("21CS001", "student123")
    if result["success"]:
        ok("Correct credentials → login success")
        assert_true("student" in result,           "Response contains 'student' key")
        assert_true("password" not in result.get("student", {}),
                    "Password hash NOT exposed in login response")
        assert_true(result["student"].get("name") is not None,
                    f"Student name present: {result['student'].get('name')}")
        info(f"Logged in as: {result['student'].get('name')} "
             f"| Dept: {result['student'].get('department')} "
             f"| Room: {result['student'].get('room_no')}")
    else:
        fail(f"Correct credentials rejected: {result['error']}")
        info("Make sure seed_data.sql and update_passwords.sql have been run")

    # Wrong password
    result_bad = login_student("21CS001", "wrongpassword")
    assert_false(result_bad["success"], "Wrong password correctly rejected")
    assert_true("error" in result_bad,  f"Error message returned: {result_bad.get('error')}")

    # Non-existent register number
    result_none = login_student("99XXXXX", "student123")
    assert_false(result_none["success"], "Non-existent register number rejected")

    # Empty inputs
    result_empty = login_student("", "")
    assert_false(result_empty["success"], "Empty credentials rejected (no DB call)")

except Exception as e:
    fail(f"Student login test crashed: {e}")


# =============================================================
# TEST 5 — Warden login
# =============================================================
section("5. Warden Login")

try:
    from utils.auth_utils import login_warden

    result = login_warden("WD001", "warden123")
    if result["success"]:
        ok("Correct credentials → login success")
        assert_true("warden" in result,            "Response contains 'warden' key")
        assert_true("password" not in result.get("warden", {}),
                    "Password hash NOT exposed in warden response")
        assert_true(result["warden"].get("name") is not None,
                    f"Warden name present: {result['warden'].get('name')}")
        info(f"Logged in as: {result['warden'].get('name')} "
             f"| Block: {result['warden'].get('hostel_block')}")
    else:
        fail(f"Correct warden credentials rejected: {result['error']}")

    result_bad  = login_warden("WD001", "wrongpass")
    assert_false(result_bad["success"],  "Wrong warden password rejected")

    result_none = login_warden("WD999", "warden123")
    assert_false(result_none["success"], "Non-existent warden ID rejected")

    result_fmt  = login_warden("ABC01", "warden123")
    assert_false(result_fmt["success"],  "Invalid warden ID format rejected by validator")

except Exception as e:
    fail(f"Warden login test crashed: {e}")


# =============================================================
# TEST 6 — Session key reference (no Streamlit, just print)
# =============================================================
section("6. Session State Keys Reference")

info("Keys set by set_student_session():")
student_keys = [
    "logged_in    → True",
    "role         → 'student'",
    "student_id   → int (e.g. 1)",
    "student_name → str (e.g. 'Arun Prakash')",
    "register_no  → str (e.g. '21CS001')",
    "department   → str (e.g. 'CSE')",
    "year         → int (e.g. 3)",
    "room_no      → str or None (e.g. 'A101')",
]
for k in student_keys:
    info(f"  st.session_state['{k}']")

print()
info("Keys set by set_warden_session():")
warden_keys = [
    "logged_in    → True",
    "role         → 'warden'",
    "warden_id    → str (e.g. 'WD001')",
    "warden_name  → str (e.g. 'Dr. Ramesh Kumar')",
    "hostel_block → str (e.g. 'Block A')",
]
for k in warden_keys:
    info(f"  st.session_state['{k}']")


# =============================================================
# SUMMARY
# =============================================================
total = passed + failed
section("Test Summary")
print(f"  {GREEN}{BOLD}{passed} passed{RESET}  ·  {RED}{BOLD}{failed} failed{RESET}  ·  {total} total")

if failed == 0:
    print(f"\n  {GREEN}{BOLD}✓ All tests passed! Auth system is ready.{RESET}")
    print(f"  {BLUE}Next step: Run the app with → streamlit run app.py{RESET}\n")
else:
    print(f"\n  {RED}{BOLD}✗ Some tests failed. Check the errors above.{RESET}")
    print(f"  {YELLOW}Common fixes:{RESET}")
    print(f"    1. Run: mysql -u root -p < database/schema.sql")
    print(f"    2. Run: mysql -u root -p < database/seed_data.sql")
    print(f"    3. Run: mysql -u root -p < database/update_passwords.sql")
    print(f"    4. Update DB_CONFIG password in database/connection.py\n")

sys.exit(0 if failed == 0 else 1)
