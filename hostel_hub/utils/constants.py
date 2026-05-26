# =============================================================
#  HOSTEL HUB — utils/constants.py
#  Single source of truth for all fixed values used across
#  the application. Change here → updates everywhere.
# =============================================================

# ── Hostel layout ────────────────────────────────────────────
HOSTEL_BLOCKS = ["Block A", "Block B", "Block C"]

ROOM_TYPES = ["Standard", "Premium", "Deluxe"]

# ── Academic ─────────────────────────────────────────────────
DEPARTMENTS = ["CSE", "AIDS", "IT", "ECE", "EEE", "MECH", "CIVIL", "MBA", "MCA"]

YEARS = [1, 2, 3, 4, 5]

# ── Student profile ──────────────────────────────────────────
GENDERS = ["Male", "Female", "Other"]

FOOD_PREFERENCES = ["Veg", "Non-Veg", "Vegan"]

# ── Complaint module ─────────────────────────────────────────
COMPLAINT_CATEGORIES = [
    "Electrical", "Plumbing", "Internet",
    "Cleaning", "Furniture", "Others",
]

COMPLAINT_PRIORITIES = ["Normal", "Urgent", "Emergency"]

COMPLAINT_STATUSES = ["Pending", "In Progress", "Resolved"]

# Priority badge colors (for UI rendering)
PRIORITY_COLORS = {
    "Normal"    : "#16A34A",   # green
    "Urgent"    : "#D97706",   # amber
    "Emergency" : "#DC2626",   # red
}

PRIORITY_ICONS = {
    "Normal"    : "🟢",
    "Urgent"    : "🟡",
    "Emergency" : "🔴",
}

STATUS_ICONS = {
    "Pending"     : "⏳",
    "In Progress" : "🔧",
    "Resolved"    : "✅",
}

# ── Leave module ─────────────────────────────────────────────
LEAVE_STATUSES = ["Pending", "Approved", "Rejected"]

LEAVE_STATUS_ICONS = {
    "Pending"  : "⏳",
    "Approved" : "✅",
    "Rejected" : "❌",
}

# ── Attendance module ────────────────────────────────────────
ATTENDANCE_STATUSES = ["Present", "Absent", "Leave"]

# ── Mess module ──────────────────────────────────────────────
MEAL_TYPES = ["Breakfast", "Lunch", "Snacks", "Dinner"]

MEAL_ICONS = {
    "Breakfast" : "🌅",
    "Lunch"     : "☀️",
    "Snacks"    : "🍪",
    "Dinner"    : "🌙",
}

# ── Announcements ────────────────────────────────────────────
ANNOUNCEMENT_TYPES = ["General", "Emergency", "Mess Update", "Holiday"]

ANNOUNCEMENT_ICONS = {
    "General"     : "📢",
    "Emergency"   : "🚨",
    "Mess Update" : "🍽️",
    "Holiday"     : "🎉",
}

ANNOUNCEMENT_COLORS = {
    "General"     : "#EEF3FD",
    "Emergency"   : "#FEF2F2",
    "Mess Update" : "#F0FDF4",
    "Holiday"     : "#FFFBEB",
}

# ── Sentiment ────────────────────────────────────────────────
SENTIMENT_ICONS = {
    "Positive" : "😊",
    "Neutral"  : "😐",
    "Negative" : "😞",
}

SENTIMENT_COLORS = {
    "Positive" : "#16A34A",
    "Neutral"  : "#D97706",
    "Negative" : "#DC2626",
}

# ── App metadata ─────────────────────────────────────────────
APP_NAME    = "Hostel Hub"
APP_VERSION = "1.0.0"
COLLEGE     = "Sri Venkateswara College of Engineering"
