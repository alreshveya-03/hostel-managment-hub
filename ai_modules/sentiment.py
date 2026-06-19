"""
ai_modules/sentiment.py
Sentiment analysis for mess feedback.
Uses TextBlob when available, falls back to keyword-based approach.
"""

POSITIVE_WORDS = {
    'excellent','great','good','tasty','delicious','fresh','hot','clean','nice',
    'wonderful','amazing','loved','best','perfect','enjoy','enjoyed','liked',
    'happy','satisfied','yummy','nutritious','superb','awesome'
}
NEGATIVE_WORDS = {
    'bad','poor','terrible','awful','horrible','disgusting','stale','cold','dirty',
    'worst','hate','hated','disliked','unhappy','unsatisfied','pathetic','bland',
    'tasteless','smelly','rotten','insipid','waste','disappointed'
}


def analyze_sentiment(text: str) -> dict:
    if not text or not text.strip():
        return {'sentiment': 'neutral', 'score': 0.0}

    # Try TextBlob first
    try:
        from textblob import TextBlob
        blob  = TextBlob(text)
        score = blob.sentiment.polarity
        if score > 0.1:
            sentiment = 'positive'
        elif score < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        return {'sentiment': sentiment, 'score': round(score, 3)}
    except ImportError:
        pass

    # Keyword fallback
    words   = set(text.lower().split())
    pos_cnt = len(words & POSITIVE_WORDS)
    neg_cnt = len(words & NEGATIVE_WORDS)

    if pos_cnt > neg_cnt:
        score = min(1.0, pos_cnt * 0.2)
        return {'sentiment': 'positive', 'score': round(score, 3)}
    elif neg_cnt > pos_cnt:
        score = max(-1.0, -neg_cnt * 0.2)
        return {'sentiment': 'negative', 'score': round(score, 3)}
    return {'sentiment': 'neutral', 'score': 0.0}
