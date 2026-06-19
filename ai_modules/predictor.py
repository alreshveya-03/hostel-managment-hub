"""
ai_modules/predictor.py
Analytics and prediction module.
- Attendance risk prediction
- Complaint frequency trends
"""
from database import fetch_all


def predict_at_risk_students(threshold: float = 0.75) -> list:
    """
    Returns students whose attendance % this month is below threshold.
    """
    from datetime import date
    month = date.today().strftime('%Y-%m')
    rows = fetch_all(
        """SELECT s.student_id AS id, s.name, s.register_number AS reg_number, s.department,
                  COUNT(*) AS total,
                  SUM(a.status='Present') AS present
           FROM attendance a
           JOIN students s ON a.student_id = s.student_id
           WHERE DATE_FORMAT(a.att_date,'%%Y-%%m') = %s
           GROUP BY s.student_id, s.name, s.register_number, s.department
           HAVING (SUM(a.status='Present') / COUNT(*)) < %s
           ORDER BY (SUM(a.status='Present') / COUNT(*)) ASC""",
        (month, threshold))
    for r in rows:
        r['pct'] = round((r['present'] / r['total']) * 100, 1) if r['total'] else 0
        r['risk'] = 'high' if r['pct'] < 50 else 'medium'
    return rows


def predict_complaint_trends() -> dict:
    """
    Returns complaint counts for the last 7 days and an estimated
    7-day projection based on 7-day average.
    """
    rows = fetch_all(
        """SELECT DATE(created_at) AS day, COUNT(*) AS cnt
           FROM complaints
           WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
           GROUP BY day ORDER BY day""")
    days  = [str(r['day']) for r in rows]
    counts = [r['cnt'] for r in rows]
    avg   = sum(counts) / len(counts) if counts else 0
    # Simple linear projection: repeat average for next 7 days
    projection = [round(avg)] * 7
    return {
        'labels':     days,
        'actuals':    counts,
        'projection': projection,
        'avg_per_day': round(avg, 1),
    }
