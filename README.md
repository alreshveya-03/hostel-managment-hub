# ⬡ Hostel Hub – AI-Powered College Hostel Management System

> A full-stack Flask + MySQL web application with 5 AI modules for intelligent hostel administration.

---

## 🚀 Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | Python 3.10+ · Flask 3.x            |
| Database    | MySQL 8.x                           |
| Frontend    | HTML5 · CSS3 · Vanilla JS · Chart.js|
| AI Modules  | TextBlob · Keyword-rule engine      |
| Auth        | bcrypt password hashing             |

---

## 📁 Project Structure

```
hostel_hub_flask/
├── app.py                  # Flask app factory + entry point
├── config.py               # Configuration (DB, secret key, etc.)
├── database.py             # MySQL helpers (fetch_one, fetch_all, …)
├── auth_utils.py           # bcrypt helpers + role decorators
├── schema.sql              # Full DB schema + seed data
├── requirements.txt
│
├── routes/
│   ├── auth.py             # Login, Register, Logout
│   ├── student.py          # All student-facing routes
│   ├── warden.py           # All warden-facing routes
│   └── api.py              # JSON endpoints (charts, AJAX)
│
├── ai_modules/
│   ├── sentiment.py        # Mess feedback sentiment (TextBlob / keyword)
│   ├── complaint_ai.py     # Priority & category prediction
│   ├── room_suggest.py     # Smart room allocation scoring
│   ├── chatbot.py          # Intent-based chatbot with live DB
│   └── predictor.py        # Attendance risk + complaint trend
│
├── static/
│   ├── css/main.css        # Full design system stylesheet
│   └── js/app.js           # Global JS (modals, tabs, charts)
│
└── templates/
    ├── base.html           # Navbar + flash messages layout
    ├── index.html          # Landing page
    ├── student_login.html
    ├── student_register.html
    ├── warden_login.html
    ├── warden_register.html
    ├── student/            # 9 student-facing templates
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── room.html
    │   ├── complaints.html
    │   ├── leave.html
    │   ├── attendance.html
    │   ├── mess.html
    │   ├── announcements.html
    │   └── chatbot.html
    └── warden/             # 10 warden-facing templates
        ├── dashboard.html
        ├── students.html
        ├── student_detail.html
        ├── rooms.html
        ├── add_room.html
        ├── complaints.html
        ├── leave.html
        ├── attendance.html
        ├── mess.html
        ├── announcements.html
        ├── ai_room.html
        ├── analytics.html
        └── emergency.html
```

---

## ⚙️ Setup Instructions

### 1. Clone / unzip the project
```bash
cd hostel_hub_flask
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
python -m textblob.download_corpora   # Download TextBlob corpus
```

### 4. Set up MySQL database
```sql
-- In MySQL shell:
SOURCE schema.sql;
```
Or via CLI:
```bash
mysql -u root -p < schema.sql
```

### 5. Configure database credentials
Edit `config.py` or set environment variables:
```bash
export MYSQL_HOST=localhost
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=hostel_hub
export SECRET_KEY=change-this-in-production
```

### 6. Run the application
```bash
python app.py
```
Visit: **http://localhost:5000**

---

## 🔑 Default Credentials

### Warden (seed data)
| Field    | Value                  |
|----------|------------------------|
| Email    | `warden@hostelhub.com` |
| Password | `warden123`            |

> **Note:** The seed password hash in schema.sql uses a static hash. Replace it with a proper bcrypt hash using:
> ```python
> from auth_utils import hash_password
> print(hash_password('warden123'))
> ```
> Then update the INSERT in schema.sql.

### Student
Register a new student at `/student/register`

---

## 🤖 AI Modules

### 1. Sentiment Analysis (`ai_modules/sentiment.py`)
- Uses **TextBlob** (with keyword fallback)
- Classifies mess feedback as **Positive / Neutral / Negative**
- Returns a polarity score from -1.0 to +1.0

### 2. Complaint Priority Prediction (`ai_modules/complaint_ai.py`)
- Keyword + rule-based NLP
- Predicts: **Emergency / High / Medium / Low**
- Also predicts category: electrical, plumbing, pest, cleanliness, etc.

### 3. Smart Room Allocation (`ai_modules/room_suggest.py`)
- Multi-factor compatibility scoring
- Factors: availability ratio, department-block preference, year-floor alignment, room type
- Returns top 3 scored recommendations

### 4. AI Chatbot (`ai_modules/chatbot.py`)
- Intent-based with **live database lookups**
- Handles: room info, leave status, complaints, attendance %, mess menu, announcements
- Accessible from the student dashboard

### 5. Analytics & Prediction (`ai_modules/predictor.py`)
- **At-risk student detection**: flags students below 75% attendance
- **Complaint trend forecasting**: 7-day moving average projection
- Powers the warden Analytics dashboard

---

## 🗄️ Database Tables

| Table               | Description                            |
|---------------------|----------------------------------------|
| `students`          | Student profiles + room assignment     |
| `wardens`           | Warden accounts                        |
| `rooms`             | Room inventory + occupancy tracking    |
| `complaints`        | Student complaints + AI priority       |
| `leave_requests`    | Leave applications + approval          |
| `attendance`        | Daily student attendance               |
| `mess_menu`         | Weekly mess timetable                  |
| `food_feedback`     | Mess feedback + sentiment scores       |
| `announcements`     | Warden announcements                   |
| `emergency_records` | Emergency log + resolution             |
| `ai_prediction_logs`| Audit log for AI predictions           |

---

## 👥 User Roles

### Student
- Register & Login
- View dashboard with room, complaint, leave, attendance summary
- File complaints (AI auto-prioritises)
- Submit leave requests
- View attendance with % breakdown
- Browse weekly mess menu + submit feedback (AI sentiment)
- Read announcements
- Chat with AI chatbot

### Warden
- Full student management (search, filter, view details)
- Room management + AI-assisted room allocation
- Complaint monitoring & resolution
- Leave approval / rejection
- Daily attendance marking
- Mess menu management + feedback analytics
- Post announcements
- Full analytics dashboard with Chart.js visualisations
- Emergency logging and resolution

---

## 🔒 Security Features

- **bcrypt** password hashing (12 rounds)
- **Flask session** management
- **Role-based access control** via decorators (`@student_required`, `@warden_required`)
- **Parameterised queries** throughout (SQL injection prevention)
- **Input validation** on all forms
- **CSRF protection** via Flask session secret key

---

## 📊 Analytics Charts (Warden)

All charts use **Chart.js 4.4** loaded from CDN:

| Chart | Type | Data |
|-------|------|------|
| Complaints by Category | Doughnut | All complaints grouped by AI category |
| Complaints by Priority | Doughnut | AI priority distribution |
| Complaint Status | Doughnut | Pending / In-Progress / Resolved |
| Mess Sentiment | Doughnut | Positive / Neutral / Negative |
| Attendance Trend | Line | Last 14 days present vs absent |
| Occupancy by Block | Stacked Bar | Block A/B/C capacity vs occupied |
| Complaint Forecast | Line | 7-day actuals + 7-day projection |

---

## 🖥️ Screenshots

> Dashboard, chatbot, analytics, and room suggestion pages showcase the dark industrial design system with indigo/emerald accents and Sora typography.

---

## 📝 License

Academic capstone project. For educational use only.

---

*Built with Flask · MySQL · TextBlob · Chart.js*  
*Hostel Hub – Automate. Analyse. Improve.*
