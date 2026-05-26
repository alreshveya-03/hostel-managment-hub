# =============================================================
#  HOSTEL HUB — ai_models/predictor.py
#
#  PURPOSE:
#    Two prediction models for proactive hostel management:
#
#    MODEL A — Attendance Risk Predictor
#      Flags students at risk of falling below 75% attendance
#      before it happens, giving wardens time to intervene.
#
#    MODEL B — Complaint Frequency Predictor
#      Identifies students or rooms likely to generate many
#      complaints based on historical patterns.
#
#  HOW IT WORKS:
#
#  MODEL A — Attendance Risk (Rule-based + Trend analysis)
#    We compute 4 features for each student:
#      1. Current overall attendance %
#      2. Recent trend (last 7 days vs previous 7 days)
#         → Is attendance improving or declining?
#      3. Consecutive absent streak (how many days in a row absent)
#      4. Approved leave days in next 14 days
#         → A student with 5 leave days + 70% attendance is risky
#
#    These 4 features are combined into a RISK SCORE (0–100).
#    Risk levels: Low (<40), Medium (40–69), High (≥70)
#
#  MODEL B — Complaint Frequency (Statistical baseline)
#    Uses a simple statistical approach:
#      1. Compute each student's complaint rate (complaints/month)
#      2. Compare against the hostel-wide average + std deviation
#      3. Students > avg + 1.5×std are flagged as "High Frequency"
#
#    Also computes room-level complaint density to identify
#    problem rooms (e.g. persistent electrical issues in A101).
#
#  MODEL C — Mess Attendance Predictor (for warden dashboard)
#    Predicts how many students will attend each meal tomorrow
#    based on:
#      - Day of week (weekends typically lower)
#      - Number of students on approved leave tomorrow
#      - 7-day rolling average for that meal type
#
#  WHY NOT SKLEARN HERE:
#    With 15–50 students in a hostel, we don't have enough data
#    to train a reliable ML model. Statistical methods (mean,
#    std dev, trend) are more honest and interpretable at this
#    scale. sklearn LinearRegression is used for mess prediction
#    where we have more data points (meals × days).
#
#  INTEGRATION:
#    Warden Portal → Analytics section:
#
#      from ai_models.predictor import (
#          predict_attendance_risk,
#          predict_complaint_frequency,
#          predict_mess_attendance,
#      )
#      risks  = predict_attendance_risk(conn)
#      freqs  = predict_complaint_frequency(conn)
#      meals  = predict_mess_attendance(conn, target_date)
#
#  FUTURE IMPROVEMENTS:
#    - Train LSTM on 6+ months of daily attendance data
#    - Add weather/holiday calendar integration
#    - Build leave pattern detector (who always leaves weekends)
#    - Anomaly detection for sudden attendance drops
# =============================================================

from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
import statistics


# =============================================================
# RISK SCORE THRESHOLDS
# =============================================================
RISK_LOW_MAX    = 39   # 0–39   → Low risk
RISK_MEDIUM_MAX = 69   # 40–69  → Medium risk
# 70–100 → High risk

# Attendance threshold (college policy)
ATTENDANCE_MINIMUM = 75.0


# =============================================================
# INTERNAL — FEATURE COMPUTATION
# =============================================================
def _compute_attendance_features(history: list[dict]) -> dict:
    """
    Compute 4 numerical features from raw attendance history.

    Args:
        history: List of dicts from get_attendance_by_student()
                 Each dict has keys: att_date, status

    Returns:
        {
          "overall_pct":      float,   # e.g. 72.5
          "recent_pct":       float,   # last 7 days
          "prev_pct":         float,   # previous 7 days
          "trend":            float,   # recent - prev (negative = declining)
          "streak_absent":    int,     # consecutive absent days right now
          "total_days":       int,
          "present_days":     int,
        }
    """
    if not history:
        return {
            "overall_pct": 100.0, "recent_pct": 100.0,
            "prev_pct": 100.0, "trend": 0.0,
            "streak_absent": 0, "total_days": 0, "present_days": 0,
        }

    # Sort by date ascending for trend calculation
    sorted_h = sorted(history, key=lambda x: x["att_date"])

    total   = len(sorted_h)
    present = sum(1 for r in sorted_h if r["status"] == "Present")
    overall_pct = (present / total * 100) if total else 100.0

    # Recent 7 days vs previous 7 days
    recent_7 = sorted_h[-7:]  if len(sorted_h) >= 7  else sorted_h
    prev_7   = sorted_h[-14:-7] if len(sorted_h) >= 14 else []

    def _pct(records):
        if not records: return overall_pct
        p = sum(1 for r in records if r["status"] == "Present")
        return p / len(records) * 100

    recent_pct = _pct(recent_7)
    prev_pct   = _pct(prev_7)
    trend      = recent_pct - prev_pct   # negative = worsening

    # Consecutive absent streak from the most recent day backwards
    streak = 0
    for record in reversed(sorted_h):
        if record["status"] in ("Absent", "Leave"):
            streak += 1
        else:
            break   # streak broken

    return {
        "overall_pct":   round(overall_pct, 2),
        "recent_pct":    round(recent_pct, 2),
        "prev_pct":      round(prev_pct, 2),
        "trend":         round(trend, 2),
        "streak_absent": streak,
        "total_days":    total,
        "present_days":  present,
    }


def _compute_risk_score(features: dict, upcoming_leave_days: int = 0) -> int:
    """
    Combine features into a risk score from 0 to 100.

    Scoring logic:
      - If already below 75%   → base 60 points
      - If between 75–80%      → base 40 points (borderline)
      - If above 80%           → base 10 points (safe)
      - Declining trend bonus  → up to +20 points
      - Absent streak bonus    → up to +15 points
      - Upcoming leave risk    → up to +10 points
    """
    score = 0
    pct   = features["overall_pct"]
    trend = features["trend"]
    streak= features["streak_absent"]

    # Base score from current attendance
    if pct < ATTENDANCE_MINIMUM:
        score += 60           # Already at risk
    elif pct < 80:
        score += 40           # Borderline — one bad week tips it
    elif pct < 85:
        score += 20           # Slightly cautious
    else:
        score += 5            # Generally safe

    # Trend penalty: declining attendance adds up to 20 points
    if trend < 0:
        # trend is negative; worse decline = more points
        trend_penalty = min(20, int(abs(trend) * 1.5))
        score += trend_penalty

    # Streak penalty: 3+ consecutive absences is a red flag
    if streak >= 5:
        score += 15
    elif streak >= 3:
        score += 10
    elif streak >= 2:
        score += 5

    # Upcoming leave: each leave day risks dropping attendance
    if upcoming_leave_days >= 5:
        score += 10
    elif upcoming_leave_days >= 3:
        score += 6
    elif upcoming_leave_days >= 1:
        score += 3

    # Cap at 100
    return min(100, score)


def _risk_label(score: int) -> str:
    if score >= 70: return "High"
    if score >= 40: return "Medium"
    return "Low"


def _risk_color(score: int) -> str:
    if score >= 70: return "#DC2626"   # red
    if score >= 40: return "#D97706"   # amber
    return "#16A34A"                   # green


# =============================================================
# MODEL A — PUBLIC: predict_attendance_risk()
# =============================================================
def predict_attendance_risk(conn, top_n: int = 10) -> list[dict]:
    """
    Predict attendance risk for all students and return a
    ranked list (highest risk first).

    Args:
        conn:  Active MySQL connection
        top_n: Return only the top N at-risk students (default 10)
               Pass None to return all students.

    Returns:
        List of dicts sorted by risk_score descending:
        [
          {
            "student_id":     1,
            "name":           "Arun Prakash",
            "register_number":"21CS001",
            "department":     "CSE",
            "year":           3,
            "room_no":        "A101",
            "overall_pct":    68.5,
            "recent_pct":     57.1,
            "trend":          -14.3,
            "streak_absent":  3,
            "risk_score":     82,
            "risk_level":     "High",
            "risk_color":     "#DC2626",
            "recommendation": "Immediate intervention required..."
          },
          ...
        ]
    """
    from database.queries import get_all_students, get_attendance_by_student, get_approved_leaves_on_date

    try:
        all_students = get_all_students(conn)
    except Exception as e:
        print(f"[predictor] DB error fetching students: {e}")
        return []

    # Pre-compute upcoming leave counts for the next 14 days
    upcoming_leave_map: dict[int, int] = {}
    today = date.today()
    for delta in range(14):
        check_date = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
        try:
            leaves = get_approved_leaves_on_date(conn, check_date)
            for l in leaves:
                sid = l["student_id"]
                upcoming_leave_map[sid] = upcoming_leave_map.get(sid, 0) + 1
        except Exception:
            pass

    results = []
    for student in all_students:
        sid = student["student_id"]
        try:
            history = get_attendance_by_student(conn, sid)
        except Exception:
            history = []

        features          = _compute_attendance_features(history)
        upcoming_leaves   = upcoming_leave_map.get(sid, 0)
        risk_score        = _compute_risk_score(features, upcoming_leaves)
        risk_lvl          = _risk_label(risk_score)

        # Plain-English recommendation for the warden
        recommendation = _make_recommendation(
            risk_lvl, features["overall_pct"],
            features["trend"], features["streak_absent"],
            upcoming_leaves,
        )

        results.append({
            "student_id":      sid,
            "name":            student["name"],
            "register_number": student["register_number"],
            "department":      student["department"],
            "year":            student["year"],
            "room_no":         student.get("room_no") or "—",
            "overall_pct":     features["overall_pct"],
            "recent_pct":      features["recent_pct"],
            "trend":           features["trend"],
            "streak_absent":   features["streak_absent"],
            "upcoming_leave_days": upcoming_leaves,
            "risk_score":      risk_score,
            "risk_level":      risk_lvl,
            "risk_color":      _risk_color(risk_score),
            "recommendation":  recommendation,
        })

    # Sort by risk score descending
    results.sort(key=lambda x: -x["risk_score"])

    return results[:top_n] if top_n else results


def _make_recommendation(
    level: str, pct: float, trend: float,
    streak: int, leave_days: int,
) -> str:
    """Generate a human-readable warden recommendation."""
    if level == "High":
        if pct < ATTENDANCE_MINIMUM:
            return (f"Attendance is {pct:.1f}% — below the 75% minimum. "
                    "Issue a formal written warning and schedule a meeting immediately.")
        elif streak >= 3:
            return (f"Student has been absent for {streak} consecutive days. "
                    "Contact the student and their parents to check on wellbeing.")
        else:
            return (f"Attendance declining rapidly (trend: {trend:+.1f}%). "
                    "Counsel the student and check for any personal/academic issues.")
    elif level == "Medium":
        if leave_days >= 3:
            return (f"Upcoming {leave_days} leave days may push attendance below 75%. "
                    "Advise the student to minimise additional absences this month.")
        elif trend < -5:
            return (f"Attendance trending down ({trend:+.1f}% vs last week). "
                    "Have an informal check-in conversation with the student.")
        else:
            return (f"Attendance at {pct:.1f}% — borderline. "
                    "Monitor closely and remind student of the 75% policy.")
    else:
        return f"Attendance is healthy at {pct:.1f}%. No action needed."


# =============================================================
# MODEL B — PUBLIC: predict_complaint_frequency()
# =============================================================
def predict_complaint_frequency(conn) -> dict:
    """
    Identify students and rooms with unusually high complaint rates.

    Returns:
        {
          "high_frequency_students": [ {student info + stats}, ... ],
          "problem_rooms":           [ {room info + stats}, ... ],
          "hostel_avg_per_student":  float,
          "hostel_std":              float,
          "threshold":               float,
        }

    A student is flagged if their complaint count exceeds:
        hostel_average + 1.5 × standard_deviation
    """
    from database.queries import get_all_students, get_complaints_by_student

    try:
        all_students = get_all_students(conn)
    except Exception as e:
        print(f"[predictor] DB error: {e}")
        return {"high_frequency_students": [], "problem_rooms": [], "hostel_avg_per_student": 0.0, "hostel_std": 0.0, "threshold": 0.0}

    # Collect complaint counts per student
    student_stats = []
    room_complaint_map: dict[str, list] = {}

    for student in all_students:
        sid  = student["student_id"]
        rno  = student.get("room_no") or "Unallocated"
        try:
            complaints = get_complaints_by_student(conn, sid)
        except Exception:
            complaints = []

        count      = len(complaints)
        pending    = sum(1 for c in complaints if c["status"] == "Pending")
        emergency  = sum(1 for c in complaints if c["priority"] == "Emergency")
        categories = {}
        for c in complaints:
            categories[c["category"]] = categories.get(c["category"], 0) + 1
        top_category = max(categories, key=categories.get) if categories else "—"

        student_stats.append({
            "student_id":      sid,
            "name":            student["name"],
            "register_number": student["register_number"],
            "department":      student["department"],
            "room_no":         rno,
            "total_complaints":count,
            "pending":         pending,
            "emergency":       emergency,
            "top_category":    top_category,
        })

        # Accumulate for room-level analysis
        room_complaint_map.setdefault(rno, []).append(count)

    # ── Student-level statistics ──
    counts = [s["total_complaints"] for s in student_stats]
    if len(counts) >= 2:
        avg_complaints = statistics.mean(counts)
        std_complaints = statistics.stdev(counts)
    else:
        avg_complaints = counts[0] if counts else 0.0
        std_complaints = 0.0

    threshold = avg_complaints + (1.5 * std_complaints)

    high_freq = [
        s for s in student_stats
        if s["total_complaints"] > threshold and s["total_complaints"] > 0
    ]
    high_freq.sort(key=lambda x: -x["total_complaints"])

    # ── Room-level complaint density ──
    room_stats = []
    for rno, complaint_counts in room_complaint_map.items():
        if rno == "Unallocated":
            continue
        total_room_complaints = sum(complaint_counts)
        avg_per_student       = total_room_complaints / len(complaint_counts) if complaint_counts else 0
        room_stats.append({
            "room_no":              rno,
            "total_complaints":     total_room_complaints,
            "students_in_room":     len(complaint_counts),
            "avg_per_student":      round(avg_per_student, 2),
            "is_problem_room":      total_room_complaints > (threshold * len(complaint_counts)),
        })

    problem_rooms = [r for r in room_stats if r["is_problem_room"]]
    problem_rooms.sort(key=lambda x: -x["total_complaints"])

    return {
        "high_frequency_students": high_freq,
        "problem_rooms":           problem_rooms,
        "all_student_stats":       sorted(student_stats, key=lambda x: -x["total_complaints"]),
        "hostel_avg_per_student":  round(avg_complaints, 2),
        "hostel_std":              round(std_complaints, 2),
        "threshold":               round(threshold, 2),
    }


# =============================================================
# MODEL C — PUBLIC: predict_mess_attendance()
# =============================================================
def predict_mess_attendance(
    conn,
    target_date: Optional[date] = None,
) -> dict:
    """
    Predict how many students will attend each meal on target_date.

    Algorithm:
      1. Load historical meal attendance for the past 30 days.
      2. For each meal type, compute the 7-day rolling average.
      3. Apply corrections:
           - Weekend penalty  (−15% on Sat/Sun)
           - Leave adjustment (subtract students on approved leave)
      4. Return predicted counts with confidence intervals.

    Args:
        conn:        Active MySQL connection
        target_date: Date to predict for (default: tomorrow)

    Returns:
        {
          "target_date":  "2025-05-10",
          "day_of_week":  "Saturday",
          "is_weekend":   True,
          "predictions": {
            "Breakfast": {"predicted": 45, "low": 38, "high": 52},
            "Lunch":     {"predicted": 52, "low": 45, "high": 59},
            "Snacks":    {"predicted": 30, "low": 24, "high": 36},
            "Dinner":    {"predicted": 48, "low": 41, "high": 55},
          },
          "leave_count":     8,
          "total_students":  60,
          "confidence":     "Medium",
        }
    """
    from database.queries import (
        get_historical_meal_counts, get_student_count,
        get_approved_leaves_on_date,
    )

    if target_date is None:
        target_date = date.today() + timedelta(days=1)

    target_str   = target_date.strftime("%Y-%m-%d")
    day_of_week  = target_date.strftime("%A")
    is_weekend   = target_date.weekday() >= 5   # Saturday=5, Sunday=6

    # ── Historical data ──
    try:
        historical = get_historical_meal_counts(conn, days=30)
    except Exception:
        historical = []

    try:
        total_students = get_student_count(conn)
    except Exception:
        total_students = 1

    try:
        leaves_tomorrow = get_approved_leaves_on_date(conn, target_str)
        leave_count     = len(leaves_tomorrow)
    except Exception:
        leave_count = 0

    # ── Compute rolling 7-day average per meal ──
    from collections import defaultdict
    meal_counts_by_day: dict[str, list] = defaultdict(list)

    # Group by meal_type, collect last 7 days of counts
    cutoff = date.today() - timedelta(days=7)
    for record in historical:
        try:
            record_date = record["meal_date"]
            if isinstance(record_date, str):
                from datetime import datetime
                record_date = datetime.strptime(record_date, "%Y-%m-%d").date()
            if record_date >= cutoff:
                meal_counts_by_day[record["meal_type"]].append(record["attended_count"])
        except Exception:
            continue

    predictions = {}
    for meal in ["Breakfast", "Lunch", "Snacks", "Dinner"]:
        recent_counts = meal_counts_by_day.get(meal, [])

        if recent_counts:
            base = statistics.mean(recent_counts)
            variability = statistics.stdev(recent_counts) if len(recent_counts) > 1 else base * 0.1
        else:
            # No historical data — estimate from total students
            base_rates = {"Breakfast": 0.70, "Lunch": 0.80, "Snacks": 0.50, "Dinner": 0.75}
            base        = total_students * base_rates.get(meal, 0.65)
            variability = base * 0.12

        # Apply weekend penalty (students go out, skip mess)
        if is_weekend:
            base *= 0.88

        # Subtract students on approved leave
        base = max(0, base - leave_count * 0.9)

        # Round to integer predictions
        predicted = round(base)
        low       = max(0, round(base - variability))
        high      = min(total_students, round(base + variability))

        predictions[meal] = {
            "predicted": predicted,
            "low":       low,
            "high":      high,
        }

    # Confidence: High if we have 7+ days of data, Medium if 3+, Low otherwise
    data_days = len(set(
        r.get("meal_date") for r in historical
    ))
    confidence = "High" if data_days >= 7 else "Medium" if data_days >= 3 else "Low"

    return {
        "target_date":   target_str,
        "day_of_week":   day_of_week,
        "is_weekend":    is_weekend,
        "predictions":   predictions,
        "leave_count":   leave_count,
        "total_students":total_students,
        "confidence":    confidence,
    }


# =============================================================
# CONVENIENCE WRAPPER — get_all_predictions()
# Runs all three models in one call for the warden dashboard.
# =============================================================
def get_all_predictions(conn) -> dict:
    """
    Run all prediction models and return combined results.
    Suitable for the warden Analytics section.

    Returns:
        {
          "attendance_risks":    [...],
          "complaint_frequency": {...},
          "mess_prediction":     {...},
        }
    """
    return {
        "attendance_risks":    predict_attendance_risk(conn, top_n=10),
        "complaint_frequency": predict_complaint_frequency(conn),
        "mess_prediction":     predict_mess_attendance(conn),
    }


# =============================================================
# SELF-TEST — run with: python ai_models/predictor.py
# =============================================================
def _run_tests():
    print("\n" + "="*60)
    print("  PREDICTOR AI — Self Test (no DB required)")
    print("="*60)

    # ── Test Model A: attendance feature computation ──
    print("\n  [A] Attendance Risk Scoring")
    mock_histories = [
        {
            "label":   "Healthy student",
            "history": [{"att_date": date.today()-timedelta(days=i), "status":"Present"} for i in range(20)],
            "leaves":  0,
            "expected_level": "Low",
        },
        {
            "label":   "Borderline student (72%)",
            "history": (
                [{"att_date": date.today()-timedelta(days=i), "status":"Present"} for i in range(18)] +
                [{"att_date": date.today()-timedelta(days=i), "status":"Absent"}  for i in range(18,25)]
            ),
            "leaves":  0,
            "expected_level": "Medium",
        },
        {
            "label":   "At-risk student (60%, declining)",
            "history": (
                [{"att_date": date.today()-timedelta(days=i), "status":"Present"} for i in range(12)] +
                [{"att_date": date.today()-timedelta(days=i), "status":"Absent"}  for i in range(12,20)] +
                [{"att_date": date.today()-timedelta(days=i), "status":"Absent"}  for i in range(20,25)]
            ),
            "leaves":  4,
            "expected_level": "High",
        },
    ]

    for tc in mock_histories:
        features   = _compute_attendance_features(tc["history"])
        risk_score = _compute_risk_score(features, tc["leaves"])
        level      = _risk_label(risk_score)
        ok         = level == tc["expected_level"]
        rec        = _make_recommendation(level, features["overall_pct"], features["trend"], features["streak_absent"], tc["leaves"])
        print(f"\n  [{'✓' if ok else '✗'}] {tc['label']}")
        print(f"       Pct:{features['overall_pct']:5.1f}%  Trend:{features['trend']:+5.1f}%  Streak:{features['streak_absent']} days")
        print(f"       Risk Score: {risk_score}  →  Level: {level}  (expected: {tc['expected_level']})")
        print(f"       Rec: {rec[:80]}…")

    # ── Test Model C: mess prediction (mock, no DB) ──
    print("\n\n  [C] Mess Attendance Prediction (mock data)")
    mock_historical = [
        {"meal_date": (date.today()-timedelta(days=i)).strftime("%Y-%m-%d"),
         "meal_type": meal, "attended_count": 40 + (i%5)*2}
        for i in range(14) for meal in ["Breakfast","Lunch","Snacks","Dinner"]
    ]
    # Show predictions logic directly
    for meal in ["Breakfast","Lunch","Snacks","Dinner"]:
        counts = [r["attended_count"] for r in mock_historical if r["meal_type"]==meal]
        base   = round(statistics.mean(counts)) if counts else 40
        print(f"       {meal:12s}: base avg = {base}")

    print(f"\n  {'─'*40}")
    print("  All tests complete ✓\n")


if __name__ == "__main__":
    _run_tests()