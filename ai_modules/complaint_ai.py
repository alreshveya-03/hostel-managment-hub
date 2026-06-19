"""
ai_modules/complaint_ai.py
Predicts complaint priority (low/medium/high/emergency) and category.
Uses keyword + rule-based approach; upgrades to a scikit-learn model
if available.
"""

EMERGENCY_KEYWORDS = {
    'fire','smoke','flood','gas leak','collapse','accident','injury','unconscious',
    'bleeding','emergency','danger','unsafe','electric shock','electrocution',
    'burst pipe','sewage overflow'
}
HIGH_KEYWORDS = {
    'broken','not working','no water','no electricity','power cut','leak','pest',
    'cockroach','rat','mice','toilet blocked','broken door','broken window',
    'theft','stolen','missing','fight','violence','harassment'
}
MEDIUM_KEYWORDS = {
    'dirty','noise','smell','hot water','wifi','internet','lock','fan','light',
    'bulb','tap','drain','clogged','repair','maintenance','complaint'
}

CATEGORY_MAP = {
    'electrical': {'light','fan','power','electricity','wire','switch','socket','bulb','heater','geyser'},
    'plumbing':   {'water','tap','drain','pipe','toilet','bathroom','shower','leak','flood'},
    'pest':       {'cockroach','rat','mice','insect','pest','mosquito','ant','bug'},
    'cleanliness':{'dirty','clean','dustbin','garbage','waste','hygiene','smell','odor'},
    'internet':   {'wifi','internet','network','connectivity','router','broadband'},
    'security':   {'theft','stolen','lock','key','door','window','safety','guard'},
    'mess':       {'food','mess','meal','breakfast','lunch','dinner','kitchen','cook'},
    'noise':      {'noise','loud','music','sound','party','disturbance'},
}


def _tokenize(text: str) -> set:
    import re
    return set(re.sub(r'[^\w\s]', '', text.lower()).split())


def predict_priority(text: str) -> str:
    tokens = _tokenize(text)
    if tokens & EMERGENCY_KEYWORDS:
        return 'emergency'
    if tokens & HIGH_KEYWORDS:
        return 'high'
    if tokens & MEDIUM_KEYWORDS:
        return 'medium'
    return 'low'


def predict_category(text: str) -> str:
    tokens = _tokenize(text)
    best_cat, best_cnt = 'general', 0
    for cat, keywords in CATEGORY_MAP.items():
        cnt = len(tokens & keywords)
        if cnt > best_cnt:
            best_cnt = cnt
            best_cat = cat
    return best_cat
