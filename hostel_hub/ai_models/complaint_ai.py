# =============================================================
#  HOSTEL HUB — ai_models/complaint_ai.py
#
#  PURPOSE:
#    Automatically detect the CATEGORY and PRIORITY of a
#    hostel complaint from its text — no training data needed.
#
#  HOW IT WORKS:
#    1. CATEGORY DETECTION — Weighted keyword matching
#       Each category (Electrical, Plumbing, etc.) has a list
#       of keywords. Each keyword has a weight (1–3).
#       We score the text against every category and pick
#       the highest-scoring one.
#
#    2. PRIORITY DETECTION — Rule-based escalation pipeline
#       Step 1 : Check Emergency keywords (sparks, fire, flood…)
#       Step 2 : Check Urgent keywords (leakage, no water…)
#       Step 3 : Check phrase patterns (e.g. "since X days")
#       Step 4 : Cross-signal boost (e.g. Electrical + Urgent word = bump up)
#       Step 5 : Default → Normal
#
#  WHY NO ML MODEL HERE:
#    Complaint text in a hostel is short and domain-specific.
#    A keyword model with weights outperforms naive ML classifiers
#    that need labelled training data. This approach is also fully
#    explainable — we can show exactly which keywords triggered
#    the result.
#
#  INTEGRATION:
#    Called in student_portal.py → render_complaints() before
#    inserting a new complaint into the database:
#
#      from ai_models.complaint_ai import detect_category, detect_priority
#      category = detect_category(complaint_text)
#      priority = detect_priority(complaint_text)
#      add_complaint(conn, student_id, text, category, priority, date)
#
#  FUTURE IMPROVEMENTS:
#    - Train a Naive Bayes / SVM classifier on labelled complaint data
#    - Use spaCy NER to extract room numbers and equipment names
#    - Add multi-label support (e.g. both Electrical + Cleaning)
# =============================================================

import re
from typing import Tuple


# =============================================================
# KEYWORD DICTIONARIES
# Format: { keyword: weight }
# Higher weight = stronger signal for that category / priority
# =============================================================

# ── Category keywords ────────────────────────────────────────
CATEGORY_KEYWORDS: dict[str, dict[str, int]] = {
    "Electrical": {
        "light": 2, "tube light": 3, "fan": 2, "switch": 2, "socket": 2,
        "wire": 2, "wiring": 2, "electricity": 2, "electric": 2, "power": 2,
        "voltage": 3, "bulb": 2, "fuse": 3, "spark": 3, "short circuit": 3,
        "shock": 3, "mcb": 3, "trip": 2, "tripped": 2, "no power": 3,
        "power cut": 2, "power failure": 3, "generator": 2, "inverter": 2,
        "plug": 2, "current": 2, "electrocute": 3, "burn": 2, "burnt": 2,
    },
    "Plumbing": {
        "water": 2, "tap": 3, "pipe": 2, "drain": 3, "leak": 2, "leaking": 2,
        "leakage": 3, "toilet": 3, "flush": 3, "bathroom": 2, "shower": 2,
        "tank": 2, "block": 2, "blocked": 3, "clog": 3, "clogged": 3,
        "overflow": 3, "sewage": 3, "drainage": 3, "no water": 3,
        "hot water": 2, "cold water": 2, "water supply": 3, "burst": 3,
        "seepage": 3, "damp": 2, "wet floor": 3, "water logging": 3,
        "pipeline": 2,
    },
    "Internet": {
        "wifi": 3, "internet": 3, "network": 2, "router": 3, "connection": 2,
        "broadband": 3, "signal": 2, "speed": 2, "bandwidth": 3,
        "disconnected": 2, "no signal": 3, "slow internet": 3, "ping": 2,
        "lag": 2, "offline": 2, "network issue": 3, "lan": 3, "ethernet": 3,
        "streaming": 2, "download": 2, "upload": 2, "password": 2,
    },
    "Cleaning": {
        "clean": 2, "cleaning": 2, "dirty": 2, "dirt": 2, "garbage": 3,
        "dustbin": 3, "sweep": 2, "sweeping": 2, "mop": 2, "mopping": 2,
        "cockroach": 3, "rat": 3, "mouse": 3, "pest": 3, "mosquito": 2,
        "insects": 2, "smell": 2, "stink": 3, "stinking": 3, "odour": 3,
        "odor": 3, "hygiene": 2, "unhygienic": 3, "waste": 2, "trash": 2,
        "dusty": 2, "cobweb": 2, "dust": 2, "fungus": 3, "mold": 3,
        "not cleaned": 3, "bathroom clean": 2,
    },
    "Furniture": {
        "bed": 2, "chair": 2, "table": 2, "almirah": 3, "cupboard": 3,
        "wardrobe": 3, "door": 2, "window": 2, "lock": 2, "hinge": 3,
        "broken": 2, "broken furniture": 3, "shelf": 2, "shelves": 2,
        "mattress": 3, "pillow": 2, "ladder": 3, "bunk": 3, "bunk bed": 3,
        "handle": 2, "knob": 2, "drawer": 2, "curtain": 2, "rod": 2,
        "glass": 2, "mirror": 2, "bolt": 2, "latch": 2,
    },
    "Others": {},   # fallback — always scores 0
}


# ── Priority keywords ─────────────────────────────────────────

# EMERGENCY: Immediate danger to life or property
EMERGENCY_KEYWORDS: list[str] = [
    "spark", "sparks", "fire", "smoke", "burning", "burnt smell",
    "short circuit", "electrical fire", "electrocute", "electric shock",
    "flood", "flooding", "burst pipe", "gas leak", "gas smell",
    "injury", "injured", "bleeding", "collapse", "collapsed",
    "ceiling collapsed", "wall crack", "structural damage",
    "overflow flooding", "sewage overflow", "major leak",
    "cannot breathe", "fumes", "toxic",
]

# URGENT: Significant disruption — needs attention within 24 hours
URGENT_KEYWORDS: list[str] = [
    "leakage", "no water", "water not coming", "no electricity",
    "power failure", "not working", "broken", "blocked", "damage",
    "damaged", "seepage", "stuck", "stuck lock", "door not opening",
    "cannot open", "foul smell", "unbearable", "since yesterday",
    "since 2 days", "since 3 days", "two days", "three days",
    "no hot water", "cockroach infestation", "rat", "mice", "pest",
    "sewage", "clog", "clogged", "overflowing", "wet ceiling",
    "mold", "fungus", "major issue", "urgent", "immediately",
    "asap", "as soon as possible", "critical",
]

# NORMAL: Minor inconvenience — can be scheduled
NORMAL_BOOST_KEYWORDS: list[str] = [
    "not bright", "flickering", "slow", "minor", "small", "little",
    "slightly", "sometimes", "occasionally", "request", "please fix",
    "when possible", "whenever", "not urgent",
]

# Patterns that indicate how long the issue has been going on
# More days = higher priority
DURATION_PATTERN = re.compile(
    r"since\s+(\d+)\s*(day|days|week|weeks)",
    re.IGNORECASE
)


# =============================================================
# PUBLIC FUNCTION 1 — detect_category()
# =============================================================
def detect_category(complaint_text: str) -> str:
    """
    Detect the most likely category of a complaint using
    weighted keyword scoring.

    Args:
        complaint_text: The raw complaint text from the student.

    Returns:
        One of: "Electrical", "Plumbing", "Internet",
                "Cleaning", "Furniture", "Others"

    How it works:
        For each category, we sum up the weights of all
        keywords that appear in the complaint text.
        The category with the highest total score wins.
        Ties go to the first category in the dict.
    """
    if not complaint_text or not complaint_text.strip():
        return "Others"

    text = complaint_text.lower().strip()

    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword, weight in keywords.items():
            if keyword in text:
                score += weight
        scores[category] = score

    # Find the category with the highest score
    best_category = max(scores, key=scores.get)

    # If all scores are 0, return "Others"
    if scores[best_category] == 0:
        return "Others"

    return best_category


def get_category_confidence(complaint_text: str) -> dict[str, int]:
    """
    Returns the score for EVERY category, not just the winner.
    Useful for showing a confidence breakdown in the UI.

    Args:
        complaint_text: The raw complaint text.

    Returns:
        { "Electrical": 5, "Plumbing": 2, "Internet": 0, ... }
    """
    if not complaint_text:
        return {cat: 0 for cat in CATEGORY_KEYWORDS}

    text = complaint_text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(w for kw, w in keywords.items() if kw in text)
    return scores


# =============================================================
# PUBLIC FUNCTION 2 — detect_priority()
# =============================================================
def detect_priority(complaint_text: str) -> str:
    """
    Detect the urgency/priority of a complaint using a
    multi-step rule pipeline.

    Args:
        complaint_text: The raw complaint text from the student.

    Returns:
        One of: "Emergency", "Urgent", "Normal"

    Pipeline (stops at first match):
        Step 1: Emergency keyword check
        Step 2: Urgent keyword check
        Step 3: Duration analysis (e.g. "since 5 days" → Urgent)
        Step 4: Cross-signal boost (Electrical + urgent word)
        Step 5: Default → Normal
    """
    if not complaint_text or not complaint_text.strip():
        return "Normal"

    text = complaint_text.lower().strip()

    # ── Step 1: Emergency check ──
    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return "Emergency"

    # ── Step 2: Urgent check ──
    for kw in URGENT_KEYWORDS:
        if kw in text:
            return "Urgent"

    # ── Step 3: Duration analysis ──
    # "since 4 days" → Urgent,  "since 1 week" → Urgent
    match = DURATION_PATTERN.search(text)
    if match:
        number = int(match.group(1))
        unit   = match.group(2).lower()
        if "week" in unit or number >= 3:
            return "Urgent"

    # ── Step 4: Cross-signal boost ──
    # If Electrical category + any urgency indicator → bump to Urgent
    elec_score    = sum(w for kw, w in CATEGORY_KEYWORDS["Electrical"].items() if kw in text)
    plumbing_score= sum(w for kw, w in CATEGORY_KEYWORDS["Plumbing"].items()   if kw in text)
    minor_signals = ["not working", "broken", "fused", "no light", "dark",
                     "no fan", "heat", "hot", "no flush", "dripping"]

    if elec_score >= 4 and any(s in text for s in minor_signals):
        return "Urgent"
    if plumbing_score >= 4 and any(s in text for s in minor_signals):
        return "Urgent"

    # ── Step 5: Default ──
    return "Normal"


def get_priority_explanation(complaint_text: str) -> dict:
    """
    Returns both the priority AND which keywords triggered it.
    Used in the warden's AI Complaint Analyser section.

    Returns:
        {
          "priority": "Urgent",
          "triggered_by": ["leakage", "not working"],
          "category": "Plumbing",
          "confidence_scores": { "Plumbing": 7, "Electrical": 2, ... }
        }
    """
    text       = complaint_text.lower().strip() if complaint_text else ""
    priority   = detect_priority(complaint_text)
    category   = detect_category(complaint_text)
    scores     = get_category_confidence(complaint_text)

    triggered = []
    for kw in EMERGENCY_KEYWORDS + URGENT_KEYWORDS:
        if kw in text:
            triggered.append(kw)

    return {
        "priority":          priority,
        "category":          category,
        "triggered_by":      triggered,
        "confidence_scores": scores,
    }


# =============================================================
# SELF-TEST — run with: python ai_models/complaint_ai.py
# =============================================================
def _run_tests():
    print("\n" + "="*60)
    print("  COMPLAINT AI — Self Test")
    print("="*60)

    test_cases = [
        # (text, expected_category, expected_priority)
        ("There is an electrical spark near the switchboard in room A101. Very dangerous.",
         "Electrical", "Emergency"),
        ("Water leakage from the ceiling since 3 days. Floor is always wet.",
         "Plumbing", "Urgent"),
        ("WiFi signal is very weak. Cannot attend online classes.",
         "Internet", "Normal"),
        ("The tube light in my room is fused. Please replace it.",
         "Electrical", "Normal"),
        ("Bathroom drain is completely blocked. Water not draining at all.",
         "Plumbing", "Urgent"),
        ("Room has not been cleaned for a week. Garbage piling up.",
         "Cleaning", "Urgent"),
        ("Bed frame is broken. The side railing came off.",
         "Furniture", "Normal"),
        ("There is a gas leak smell near the corridor. Emergency!",
         "Others", "Emergency"),
        ("Fan sometimes makes noise. Not urgent.",
         "Electrical", "Normal"),
        ("No water supply in the entire hostel since this morning.",
         "Plumbing", "Urgent"),
    ]

    passed = 0
    for i, (text, exp_cat, exp_pri) in enumerate(test_cases, 1):
        got_cat = detect_category(text)
        got_pri = detect_priority(text)
        cat_ok  = got_cat == exp_cat
        pri_ok  = got_pri == exp_pri
        status  = "✓" if (cat_ok and pri_ok) else "✗"
        if cat_ok and pri_ok:
            passed += 1
        print(f"\n  [{status}] Test {i:02d}")
        print(f"  Text     : {text[:60]}…")
        print(f"  Category : {got_cat:12s}  (expected {exp_cat}){' ✓' if cat_ok else ' ✗'}")
        print(f"  Priority : {got_pri:10s}  (expected {exp_pri}){' ✓' if pri_ok else ' ✗'}")

    print(f"\n  {'─'*40}")
    print(f"  Result: {passed}/{len(test_cases)} tests passed\n")


if __name__ == "__main__":
    _run_tests()