

# =============================================================
#  HOSTEL HUB — ai_models/sentiment.py
#
#  PURPOSE:
#    Analyse the sentiment of student food feedback as:
#    Positive / Neutral / Negative
#
#  HOW IT WORKS — Three-layer pipeline:
#
#  Layer 1 — Food Domain Keyword Override
#    Some words are food-specific and need custom handling.
#    "cold" normally reads neutral/negative but in "cold coffee"
#    it's fine. We check a food-specific override dictionary first.
#
#  Layer 2 — TextBlob Polarity Score
#    TextBlob computes a polarity score from -1.0 to +1.0 using
#    a pattern-based lexicon. We map this to our three classes:
#      polarity >  0.12  → Positive
#      polarity < -0.12  → Negative
#      else              → Neutral
#    The threshold is slightly wider than the default 0.0 to
#    avoid false positives on mildly-worded hostel feedback.
#
#  Layer 3 — Star Rating Cross-check
#    If a rating is provided alongside the text, we use it as a
#    tiebreaker when TextBlob returns Neutral.
#      rating 4-5 → bump to Positive
#      rating 1-2 → bump to Negative
#
#  WHY TEXTBLOB:
#    It works offline with no training data, handles English food
#    reviews well, is simple to understand and modify, and runs
#    instantly with no GPU needed.
#
#  INTEGRATION:
#    Called in student_portal.py → render_mess() before saving:
#
#      from ai_models.sentiment import analyze_sentiment
#      sentiment = analyze_sentiment(feedback_text, rating=3)
#      add_food_feedback(conn, student_id, text, sentiment, ...)
#
#    Called in warden_portal.py → render_mess() analytics section
#    via the sentiment_summary query (pre-stored in DB).
#
#  FUTURE IMPROVEMENTS:
#    - Fine-tune on hostel mess feedback dataset using VADER
#    - Add aspect-based sentiment (detect which dish was bad)
#    - Build a feedback topic extractor ("biryani excellent,
#      dal too salty") to give actionable mess improvement signals
# =============================================================

from textblob import TextBlob
from typing import Optional


# =============================================================
# FOOD-DOMAIN KEYWORD OVERRIDES
# These take priority over TextBlob's generic polarity.
#
# Format: { "keyword": score_adjustment }
# Positive adjustments push toward Positive sentiment.
# Negative adjustments push toward Negative sentiment.
# =============================================================
FOOD_POSITIVE_KEYWORDS: dict[str, float] = {
    # Strong positives
    "excellent":     0.8,  "delicious":    0.8,  "amazing":      0.8,
    "outstanding":   0.8,  "fantastic":    0.8,  "best":         0.7,
    "loved":         0.7,  "love it":      0.7,  "wonderful":    0.7,
    "superb":        0.7,  "very tasty":   0.7,  "very good":    0.6,
    "really good":   0.6,  "really nice":  0.6,  "so good":      0.6,
    # Medium positives
    "tasty":         0.5,  "good":         0.4,  "nice":         0.4,
    "enjoyed":       0.5,  "fresh":        0.4,  "hot":          0.3,
    "well cooked":   0.5,  "soft":         0.3,  "crispy":       0.3,
    "flavourful":    0.5,  "flavorful":    0.5,  "yummy":        0.5,
    "spicy":         0.2,  "satisfying":   0.5,  "filling":      0.4,
    "great":         0.5,  "happy":        0.4,  "thankful":     0.3,
    # Mild positives
    "okay":          0.1,  "fine":         0.1,  "decent":       0.2,
    "acceptable":    0.1,  "alright":      0.1,  "not bad":      0.2,
}

FOOD_NEGATIVE_KEYWORDS: dict[str, float] = {
    # Strong negatives
    "disgusting":    -0.9, "terrible":     -0.8, "horrible":     -0.8,
    "worst":         -0.8, "pathetic":     -0.8, "inedible":     -0.8,
    "vomit":         -0.9, "rotten":       -0.9, "spoiled":      -0.8,
    "very bad":      -0.7, "really bad":   -0.7, "not at all":   -0.6,
    "never again":   -0.7, "awful":        -0.8, "unacceptable": -0.7,
    # Medium negatives
    "bad":           -0.5, "stale":        -0.6, "cold":         -0.4,
    "tasteless":     -0.5, "bland":        -0.5, "undercooked":  -0.6,
    "overcooked":    -0.5, "burnt":        -0.6, "raw":          -0.5,
    "salty":         -0.4, "too salty":    -0.5, "too spicy":    -0.4,
    "oily":          -0.4, "greasy":       -0.5, "hard":         -0.4,
    "dirty":         -0.6, "unhygienic":   -0.7, "hair":         -0.7,
    "stone":         -0.6, "insect":       -0.8, "worm":         -0.9,
    "not fresh":     -0.6, "not cooked":   -0.5, "not tasty":    -0.5,
    # Mild negatives
    "disappointed":  -0.4, "boring":       -0.3, "monotonous":   -0.3,
    "same":          -0.2, "repetitive":   -0.3, "improve":      -0.2,
    "not good":      -0.4, "not nice":     -0.3, "waste":        -0.4,
    "unhappy":       -0.4, "not satisfied": -0.4,
}

# Phrases that flip a negative word to neutral/positive context
# e.g. "not bad" should not be read as negative
NEGATION_FLIP_PHRASES: list[str] = [
    "not bad", "not terrible", "not horrible", "not the worst",
    "could be worse", "not too bad",
]

# Polarity thresholds for classification
POSITIVE_THRESHOLD =  0.12
NEGATIVE_THRESHOLD = -0.12


# =============================================================
# INTERNAL HELPERS
# =============================================================
def _compute_domain_score(text: str) -> float:
    """
    Compute a food-domain adjusted polarity score.
    Scans for positive and negative food keywords and
    returns a weighted sum normalised to [-1, +1].
    """
    t = text.lower()

    # First handle negation-flip phrases — treat as neutral
    for phrase in NEGATION_FLIP_PHRASES:
        t = t.replace(phrase, " neutral_phrase ")

    domain_score = 0.0
    hits = 0

    for kw, score in FOOD_POSITIVE_KEYWORDS.items():
        if kw in t:
            domain_score += score
            hits += 1

    for kw, score in FOOD_NEGATIVE_KEYWORDS.items():
        if kw in t:
            domain_score += score   # score is already negative
            hits += 1

    if hits == 0:
        return 0.0

    # Normalise — prevent extreme outliers from many keyword hits
    normalised = domain_score / hits
    return max(-1.0, min(1.0, normalised))


def _textblob_polarity(text: str) -> float:
    """
    Run TextBlob and return the polarity score in [-1, +1].
    TextBlob uses a pattern-based lexicon internally.
    """
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except Exception:
        return 0.0


def _score_to_label(score: float) -> str:
    """Map a polarity score to one of three sentiment labels."""
    if score >= POSITIVE_THRESHOLD:
        return "Positive"
    elif score <= NEGATIVE_THRESHOLD:
        return "Negative"
    else:
        return "Neutral"


# =============================================================
# PUBLIC FUNCTION 1 — analyze_sentiment()
# Main entry point used by both portals.
# =============================================================
def analyze_sentiment(feedback_text: str, rating: Optional[int] = None) -> str:
    """
    Analyse the sentiment of a food feedback text.

    Args:
        feedback_text: The student's feedback string.
        rating: Optional star rating (1–5). Used as tiebreaker
                when text sentiment is ambiguous (Neutral).

    Returns:
        "Positive", "Neutral", or "Negative"

    Example:
        >>> analyze_sentiment("Food was really good today!")
        'Positive'
        >>> analyze_sentiment("The chapati was too hard and bland.", rating=2)
        'Negative'
        >>> analyze_sentiment("Food was okay.", rating=4)
        'Positive'
    """
    if not feedback_text or not feedback_text.strip():
        # No text — use rating alone if provided
        if rating is not None:
            return "Positive" if rating >= 4 else "Negative" if rating <= 2 else "Neutral"
        return "Neutral"

    text = feedback_text.strip()

    # ── Layer 1: Domain keyword score ──
    domain_score = _compute_domain_score(text)

    # ── Layer 2: TextBlob score ──
    tb_score = _textblob_polarity(text)

    # ── Combine: domain score gets 60% weight, TextBlob 40% ──
    # Domain score is more reliable for food-specific vocabulary
    combined_score = (domain_score * 0.6) + (tb_score * 0.4)

    sentiment = _score_to_label(combined_score)

    # ── Layer 3: Rating cross-check (tiebreaker for Neutral) ──
    if sentiment == "Neutral" and rating is not None:
        if rating >= 4:
            return "Positive"
        elif rating <= 2:
            return "Negative"

    return sentiment


# =============================================================
# PUBLIC FUNCTION 2 — analyze_sentiment_detailed()
# Returns full breakdown — used in warden analytics panel.
# =============================================================
def analyze_sentiment_detailed(feedback_text: str, rating: Optional[int] = None) -> dict:
    """
    Returns detailed sentiment analysis with scores and keywords.

    Returns:
        {
          "sentiment":      "Negative",
          "combined_score": -0.43,
          "domain_score":   -0.60,
          "textblob_score": -0.18,
          "positive_words": ["fresh"],
          "negative_words": ["stale", "cold", "bland"],
          "confidence":     "High"   # High/Medium/Low
        }
    """
    if not feedback_text:
        return {
            "sentiment": "Neutral", "combined_score": 0.0,
            "domain_score": 0.0, "textblob_score": 0.0,
            "positive_words": [], "negative_words": [], "confidence": "Low",
        }

    text = feedback_text.lower().strip()

    domain_score = _compute_domain_score(feedback_text)
    tb_score     = _textblob_polarity(feedback_text)
    combined     = (domain_score * 0.6) + (tb_score * 0.4)
    sentiment    = analyze_sentiment(feedback_text, rating)

    # Extract which words triggered the result
    pos_words = [kw for kw in FOOD_POSITIVE_KEYWORDS if kw in text]
    neg_words = [kw for kw in FOOD_NEGATIVE_KEYWORDS if kw in text]

    # Confidence: High if abs score > 0.4, Medium if > 0.15, else Low
    abs_score = abs(combined)
    confidence = "High" if abs_score > 0.4 else "Medium" if abs_score > 0.15 else "Low"

    return {
        "sentiment":      sentiment,
        "combined_score": round(combined, 3),
        "domain_score":   round(domain_score, 3),
        "textblob_score": round(tb_score, 3),
        "positive_words": pos_words,
        "negative_words": neg_words,
        "confidence":     confidence,
    }


# =============================================================
# PUBLIC FUNCTION 3 — batch_analyze()
# Analyse a list of feedbacks at once (warden dashboard).
# =============================================================
def batch_analyze(feedbacks: list[dict]) -> dict:
    """
    Analyse a list of feedback dicts and return aggregate stats.

    Args:
        feedbacks: List of dicts with keys "feedback_text" and
                   optionally "rating".

    Returns:
        {
          "total": 10,
          "positive": 6,
          "neutral": 2,
          "negative": 2,
          "positive_pct": 60.0,
          "avg_score": 0.23,
          "common_positive_words": ["tasty", "good"],
          "common_negative_words": ["bland", "cold"],
        }
    """
    results = []
    all_pos_words = []
    all_neg_words = []

    for fb in feedbacks:
        text   = fb.get("feedback_text", "")
        rating = fb.get("rating")
        detail = analyze_sentiment_detailed(text, rating)
        results.append(detail["sentiment"])
        all_pos_words.extend(detail["positive_words"])
        all_neg_words.extend(detail["negative_words"])

    total    = len(results)
    positive = results.count("Positive")
    neutral  = results.count("Neutral")
    negative = results.count("Negative")

    # Most common positive and negative words
    from collections import Counter
    top_pos = [w for w, _ in Counter(all_pos_words).most_common(5)]
    top_neg = [w for w, _ in Counter(all_neg_words).most_common(5)]

    return {
        "total":                total,
        "positive":             positive,
        "neutral":              neutral,
        "negative":             negative,
        "positive_pct":         round(positive / total * 100, 1) if total else 0.0,
        "negative_pct":         round(negative / total * 100, 1) if total else 0.0,
        "common_positive_words": top_pos,
        "common_negative_words": top_neg,
    }


# =============================================================
# SELF-TEST
# =============================================================
def _run_tests():
    print("\n" + "="*60)
    print("  SENTIMENT AI — Self Test")
    print("="*60)

    test_cases = [
        ("Breakfast idli was soft and sambar was very tasty today!", None,  "Positive"),
        ("Food was excellent. Best biryani I've had!",                5,    "Positive"),
        ("Dinner chapati was too hard and paneer was bland.",         2,    "Negative"),
        ("Snacks samosa was cold and stale. Very disappointed.",      1,    "Negative"),
        ("Food was okay. Nothing special.",                           3,    "Neutral"),
        ("Lunch was decent. Rice was fine.",                          3,    "Neutral"),
        ("There was a hair in the food today. Disgusting!",           1,    "Negative"),
        ("Really enjoyed the special menu this week. Great food!",    5,    "Positive"),
        ("Not bad. Could be better.",                                 3,    "Neutral"),
        ("The dal was undercooked and oily. Not satisfied at all.",   2,    "Negative"),
    ]

    passed = 0
    for i, (text, rating, expected) in enumerate(test_cases, 1):
        result  = analyze_sentiment(text, rating)
        detail  = analyze_sentiment_detailed(text, rating)
        ok      = result == expected
        if ok: passed += 1
        print(f"\n  [{'✓' if ok else '✗'}] Test {i:02d}")
        print(f"  Text     : {text[:55]}…")
        print(f"  Rating   : {rating}")
        print(f"  Result   : {result:10s}  (expected {expected}){' ✓' if ok else ' ✗'}")
        print(f"  Score    : {detail['combined_score']:+.3f}  (confidence: {detail['confidence']})")
        if detail["positive_words"]: print(f"  Pos words: {detail['positive_words']}")
        if detail["negative_words"]: print(f"  Neg words: {detail['negative_words']}")

    print(f"\n  {'─'*40}")
    print(f"  Result: {passed}/{len(test_cases)} tests passed\n")


if __name__ == "__main__":
    _run_tests()