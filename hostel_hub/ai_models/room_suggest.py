# =============================================================
#  HOSTEL HUB — ai_models/room_suggest.py
#
#  PURPOSE:
#    Recommend the best available hostel rooms for a new or
#    transferring student using a multi-factor compatibility
#    scoring algorithm.
#
#  HOW IT WORKS — Scoring Pipeline:
#
#  For every available room (occupied < capacity) we compute
#  a COMPATIBILITY SCORE by checking five signals:
#
#    Signal 1 — Department Match  (+3 per matching occupant)
#      Students from the same dept share study schedules,
#      similar sleep/wake times, and can help each other.
#
#    Signal 2 — Year Match        (+2 per matching occupant)
#      Same-year students face the same exam pressure and
#      tend to have aligned timetables.
#
#    Signal 3 — Food Preference   (+2 if majority matches)
#      Avoids conflict — a vegan student in a room full of
#      non-veg students may feel uncomfortable.
#
#    Signal 4 — Occupancy Balance (+1 to +3, tunable)
#      Slightly prefer rooms that are partially filled over
#      completely empty ones (avoids one student alone) but
#      never suggest a full room.
#
#    Signal 5 — Room Type Bonus   (+1 for Premium/Deluxe)
#      Tie-breaker: better room type gets a small boost.
#
#  Final score = sum of all signals.
#  Rooms are ranked by score (descending), then by room_no.
#  Top N rooms are returned with full explanations.
#
#  INTEGRATION:
#    Called from warden_portal.py → render_ai_room():
#
#      from ai_models.room_suggest import suggest_rooms
#      results = suggest_rooms(conn, dept, year, food_pref, top_n=3)
#
#    Each result contains: room info + score + explanation dict
#    so the UI can show exactly WHY a room was recommended.
#
#  FUTURE IMPROVEMENTS:
#    - Add student personality survey (introvert/extrovert)
#    - Include sleep schedule preferences
#    - Collaborative filtering: "students like you chose room X"
#    - Historical roommate conflict data to penalise bad pairings
# =============================================================

from __future__ import annotations
from typing import Optional


# =============================================================
# SCORING WEIGHTS — tweak here to change recommendation logic
# =============================================================
WEIGHT_DEPT_MATCH       = 3   # per occupant sharing same dept
WEIGHT_YEAR_MATCH       = 2   # per occupant sharing same year
WEIGHT_FOOD_MAJORITY    = 2   # if majority of room shares food pref
WEIGHT_ROOM_TYPE        = {   # bonus by room type
    "Deluxe":   3,
    "Premium":  2,
    "Standard": 1,
}
WEIGHT_OCCUPANCY_BALANCE = {
    # Score bonus based on current occupancy ratio
    # Slightly occupied rooms are preferred over completely empty
    # Key: (min_ratio, max_ratio) → bonus
    (0.01, 0.40): 3,   # 1–40% full   → best balance
    (0.41, 0.70): 2,   # 41–70% full  → acceptable
    (0.71, 0.99): 1,   # 71–99% full  → nearly full, low bonus
    (0.00, 0.00): 1,   # exactly 0%   → empty room (small bonus)
}


# =============================================================
# INTERNAL HELPERS
# =============================================================
def _occupancy_bonus(occupied: int, capacity: int) -> int:
    """Return occupancy balance bonus based on fill ratio."""
    if capacity == 0:
        return 0
    if occupied == 0:
        return WEIGHT_OCCUPANCY_BALANCE[(0.00, 0.00)]
    ratio = occupied / capacity
    for (lo, hi), bonus in WEIGHT_OCCUPANCY_BALANCE.items():
        if lo <= ratio <= hi:
            return bonus
    return 0


def _score_room(
    room: dict,
    occupants: list[dict],
    target_dept: str,
    target_year: int,
    target_food: str,
) -> tuple[int, dict]:
    """
    Compute the total compatibility score for one room.

    Args:
        room:        Room dict from get_available_rooms()
        occupants:   List of student dicts currently in this room
        target_dept: Incoming student's department
        target_year: Incoming student's year
        target_food: Incoming student's food preference

    Returns:
        (total_score, explanation_dict)
        explanation_dict shows points awarded for each signal
    """
    explanation = {
        "dept_matches":     0,
        "year_matches":     0,
        "dept_score":       0,
        "year_score":       0,
        "food_score":       0,
        "balance_score":    0,
        "type_score":       0,
        "matching_students": [],
    }
    total = 0

    # ── Signal 1 & 2: Per-occupant dept + year match ──
    for occ in occupants:
        dept_match = occ.get("department") == target_dept
        year_match = occ.get("year")       == target_year

        if dept_match:
            total += WEIGHT_DEPT_MATCH
            explanation["dept_score"]   += WEIGHT_DEPT_MATCH
            explanation["dept_matches"] += 1

        if year_match:
            total += WEIGHT_YEAR_MATCH
            explanation["year_score"]   += WEIGHT_YEAR_MATCH
            explanation["year_matches"] += 1

        if dept_match or year_match:
            explanation["matching_students"].append({
                "name":       occ.get("name", "Unknown"),
                "department": occ.get("department", "—"),
                "year":       occ.get("year", "—"),
                "dept_match": dept_match,
                "year_match": year_match,
            })

    # ── Signal 3: Food preference majority ──
    if occupants:
        food_counts = {}
        for occ in occupants:
            fp = occ.get("food_preference", "")
            food_counts[fp] = food_counts.get(fp, 0) + 1
        majority_food = max(food_counts, key=food_counts.get)
        if majority_food == target_food:
            total += WEIGHT_FOOD_MAJORITY
            explanation["food_score"] = WEIGHT_FOOD_MAJORITY

    # ── Signal 4: Occupancy balance ──
    bal_bonus = _occupancy_bonus(room.get("occupied", 0), room.get("capacity", 1))
    total += bal_bonus
    explanation["balance_score"] = bal_bonus

    # ── Signal 5: Room type bonus ──
    type_bonus = WEIGHT_ROOM_TYPE.get(room.get("room_type", "Standard"), 1)
    total += type_bonus
    explanation["type_score"] = type_bonus

    return total, explanation


def _make_result_card(room: dict, score: int, explanation: dict) -> dict:
    """Package a scored room into a clean result dict for the UI."""
    return {
        # ── Room info ──
        "room_no":        room["room_no"],
        "block":          room["block"],
        "floor":          room.get("floor", 1),
        "room_type":      room.get("room_type", "Standard"),
        "capacity":       room["capacity"],
        "occupied":       room["occupied"],
        "available_beds": room["available_beds"],
        "ac_available":   room.get("ac_available", False),
        # ── Score ──
        "score":          score,
        # ── Why this room? ──
        "explanation": {
            "dept_matches":      explanation["dept_matches"],
            "year_matches":      explanation["year_matches"],
            "food_compatible":   explanation["food_score"] > 0,
            "matching_students": explanation["matching_students"],
            "points_breakdown": {
                "Department match": explanation["dept_score"],
                "Year match":       explanation["year_score"],
                "Food preference":  explanation["food_score"],
                "Occupancy balance":explanation["balance_score"],
                "Room type":        explanation["type_score"],
            },
        },
    }


# =============================================================
# PUBLIC FUNCTION 1 — suggest_rooms()
# Main entry point called from warden_portal.py
# =============================================================
def suggest_rooms(
    conn,
    department:      str,
    year:            int,
    food_preference: str,
    top_n:           int = 3,
) -> list[dict]:
    """
    Suggest the best available rooms for a student profile.

    Args:
        conn:            Active MySQL connection from get_connection()
        department:      Student's department (e.g. "CSE")
        year:            Student's year (1–5)
        food_preference: Student's food preference ("Veg"/"Non-Veg"/"Vegan")
        top_n:           How many top rooms to return (default 3)

    Returns:
        List of up to top_n room result dicts, sorted best-first.
        Each dict contains room info + score + explanation.
        Returns [] if no rooms are available.

    Example:
        conn = get_connection()
        results = suggest_rooms(conn, "CSE", 3, "Veg", top_n=3)
        for r in results:
            print(r["room_no"], r["score"])
    """
    # Import here to avoid circular imports at module load
    from database.queries import get_available_rooms, get_all_students

    try:
        available = get_available_rooms(conn)
        all_students = get_all_students(conn)
    except Exception as e:
        print(f"[room_suggest] DB error: {e}")
        return []

    if not available:
        return []

    # Build a lookup: room_no → list of current occupant dicts
    room_occupants: dict[str, list[dict]] = {}
    for s in all_students:
        rno = s.get("room_no")
        if rno:
            room_occupants.setdefault(rno, []).append(s)

    # Score every available room
    scored_rooms = []
    for room in available:
        rno      = room["room_no"]
        occupants = room_occupants.get(rno, [])
        score, explanation = _score_room(room, occupants, department, year, food_preference)
        scored_rooms.append((score, room["room_no"], room, explanation))

    # Sort: highest score first, then alphabetically by room_no
    scored_rooms.sort(key=lambda x: (-x[0], x[1]))

    # Build result cards
    results = []
    for score, _, room, explanation in scored_rooms[:top_n]:
        results.append(_make_result_card(room, score, explanation))

    return results


# =============================================================
# PUBLIC FUNCTION 2 — suggest_rooms_simple()
# Lightweight version that doesn't need a DB connection.
# Useful for testing or when DB is unavailable.
# =============================================================
def suggest_rooms_simple(
    available_rooms: list[dict],
    all_students:    list[dict],
    department:      str,
    year:            int,
    food_preference: str,
    top_n:           int = 3,
) -> list[dict]:
    """
    Same as suggest_rooms() but takes pre-fetched data instead
    of a DB connection. Use this when you've already loaded the
    data for other purposes to avoid a second DB call.

    Args:
        available_rooms: Output of get_available_rooms(conn)
        all_students:    Output of get_all_students(conn)
        department, year, food_preference, top_n: same as above

    Returns:
        Sorted list of room result dicts.
    """
    room_occupants: dict[str, list[dict]] = {}
    for s in all_students:
        rno = s.get("room_no")
        if rno:
            room_occupants.setdefault(rno, []).append(s)

    scored = []
    for room in available_rooms:
        rno       = room["room_no"]
        occupants = room_occupants.get(rno, [])
        score, explanation = _score_room(room, occupants, department, year, food_preference)
        scored.append((score, room["room_no"], room, explanation))

    scored.sort(key=lambda x: (-x[0], x[1]))

    return [_make_result_card(r, s, e) for s, _, r, e in scored[:top_n]]


# =============================================================
# PUBLIC FUNCTION 3 — explain_recommendation()
# Human-readable explanation string for the UI.
# =============================================================
def explain_recommendation(result: dict) -> str:
    """
    Generate a plain-English explanation for a room recommendation.

    Args:
        result: A result dict from suggest_rooms()

    Returns:
        A human-readable explanation string.

    Example:
        "Room A102 has 2 occupant(s) from CSE and 1 from Year 3,
         matching your profile. Food preference is compatible.
         2 beds are available."
    """
    exp   = result["explanation"]
    room  = result["room_no"]
    beds  = result["available_beds"]
    parts = []

    if exp["dept_matches"] > 0:
        parts.append(f"{exp['dept_matches']} occupant(s) share your department")
    if exp["year_matches"] > 0:
        parts.append(f"{exp['year_matches']} occupant(s) are in your year")
    if exp["food_compatible"]:
        parts.append("food preference is compatible with the room majority")
    if not parts:
        parts.append("this is a well-balanced empty room")

    summary = ", ".join(parts)
    return f"Room {room}: {summary.capitalize()}. {beds} bed(s) available."


# =============================================================
# SELF-TEST — run with: python ai_models/room_suggest.py
# =============================================================
def _run_tests():
    print("\n" + "="*60)
    print("  ROOM SUGGEST AI — Self Test (no DB required)")
    print("="*60)

    # ── Mock data ──
    mock_rooms = [
        {"room_no":"A101","block":"Block A","floor":1,"capacity":3,"occupied":2,"available_beds":1,"room_type":"Standard","ac_available":False},
        {"room_no":"A102","block":"Block A","floor":1,"capacity":3,"occupied":1,"available_beds":2,"room_type":"Standard","ac_available":False},
        {"room_no":"A103","block":"Block A","floor":1,"capacity":3,"occupied":0,"available_beds":3,"room_type":"Standard","ac_available":False},
        {"room_no":"B101","block":"Block B","floor":1,"capacity":2,"occupied":1,"available_beds":1,"room_type":"Premium","ac_available":True},
        {"room_no":"C101","block":"Block C","floor":1,"capacity":3,"occupied":2,"available_beds":1,"room_type":"Deluxe","ac_available":True},
    ]
    mock_students = [
        {"student_id":1,"name":"Arun",   "room_no":"A101","department":"CSE","year":3,"food_preference":"Veg"},
        {"student_id":2,"name":"Karthik","room_no":"A101","department":"CSE","year":3,"food_preference":"Non-Veg"},
        {"student_id":3,"name":"Ravi",   "room_no":"A102","department":"AIDS","year":2,"food_preference":"Veg"},
        {"student_id":4,"name":"Rahul",  "room_no":"B101","department":"IT","year":1,"food_preference":"Non-Veg"},
        {"student_id":5,"name":"Suresh", "room_no":"C101","department":"ECE","year":4,"food_preference":"Veg"},
        {"student_id":6,"name":"Naveen", "room_no":"C101","department":"ECE","year":4,"food_preference":"Veg"},
    ]

    test_cases = [
        ("CSE",  3, "Veg",     "Should prefer A101/A102 — CSE Year 3 already there"),
        ("IT",   1, "Non-Veg", "Should prefer B101 — IT Year 1 already there"),
        ("MECH", 2, "Vegan",   "Empty rooms scored by type/balance — A103 or similar"),
    ]

    for dept, year, food, note in test_cases:
        print(f"\n  Query: {dept}, Year {year}, {food}")
        print(f"  Note : {note}")
        results = suggest_rooms_simple(mock_rooms, mock_students, dept, year, food, top_n=3)
        for i, r in enumerate(results, 1):
            exp = explain_recommendation(r)
            pts = r["explanation"]["points_breakdown"]
            print(f"  [{i}] {r['room_no']} ({r['block']}) — Score: {r['score']:2d} — {exp}")
            print(f"       Points: { {k:v for k,v in pts.items() if v>0} }")

    print(f"\n  {'─'*40}")
    print("  All tests complete ✓\n")


if __name__ == "__main__":
    _run_tests()