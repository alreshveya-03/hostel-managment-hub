"""
ai_modules/room_suggest.py
Recommends rooms for a student based on compatibility scoring.
"""

DEPT_BLOCK_PREF = {
    'CSE': 'Block A',
    'IT': 'Block A',
    'AIDS': 'Block A',
    'ECE': 'Block B',
    'EEE': 'Block B',
    'MECH': 'Block C',
    'CIVIL': 'Block C',
}


def suggest_rooms(student: dict, available_rooms: list, top_n: int = 3) -> list:
    """
    Score each available room and return top_n sorted suggestions.
    Each returned item is the room dict with an added 'score' and 'reason'.
    """
    if not available_rooms:
        return []

    scored = []
    dept   = student.get('department', '')
    year   = student.get('year', 1)
    preferred_block = DEPT_BLOCK_PREF.get(dept, '')

    for room in available_rooms:
        score  = 0
        reasons = []

        # Availability weight: more available → better
        avail = room.get('available', 0)
        cap   = room.get('capacity', 1)
        score += (avail / cap) * 30
        if avail > 0:
            reasons.append(f"{avail} bed(s) available")

        # Block preference
        if preferred_block and room.get('block') == preferred_block:
            score += 25
            reasons.append(f"Preferred block for {dept}")

        # Year-based floor preference
        preferred_floor = min(year, 3)
        if room.get('floor') == preferred_floor:
            score += 20
            reasons.append(f"Floor {preferred_floor} suits Year {year}")

        # Lower occupancy better for privacy
        occ_pct = (cap - avail) / cap * 100
        if occ_pct == 0:
            score += 15
            reasons.append("Private / empty room")
        elif occ_pct < 50:
            score += 10
            reasons.append("Low occupancy")

        # Single room bonus
        if room.get('capacity') == 1:
            score += 10
            reasons.append("Single room")

        room_copy = dict(room)
        room_copy['score']  = round(score, 1)
        room_copy['reason'] = '; '.join(reasons) if reasons else 'Available'
        # Convert date/decimal objects for JSON serialisation
        for k, v in room_copy.items():
            if hasattr(v, 'isoformat'):
                room_copy[k] = str(v)
            elif hasattr(v, '__float__'):
                room_copy[k] = float(v)
        scored.append(room_copy)

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_n]
