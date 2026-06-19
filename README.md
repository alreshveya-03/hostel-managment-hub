<<<<<<< HEAD
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
=======
# 🏠 Hostel Hub — Smart AI-Powered Hostel Management System

A comprehensive hostel management platform built with **Streamlit** and **Python**, featuring dual portals for students and wardens with authentication, registration, and AI-powered management capabilities.

---

## ✨ Features

### 🎓 Student Portal
- User registration and authentication
- Profile management
- Room booking and allocation
- Hostel information and facilities
- Complaint/request submission

### 🛡️ Warden Portal
- Student management and monitoring
- Room allocation and management
- Complaint resolution tracking
- Hostel block administration
- Report generation

### 🔐 Security
- Secure authentication with password hashing
- Session management
- Role-based access control
- Input validation and sanitization

### 🤖 AI Integration
- Smart hostel management features
- Automated recommendations
- Data analytics and insights

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Backend | Python 3.8+ |
| Database | MySQL/PostgreSQL |
| Authentication | Custom Auth Utils |
| AI/ML | TensorFlow/Scikit-learn |

---

## 📋 Requirements

```
streamlit>=1.28.0
mysql-connector-python>=8.0
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=1.0.0
tensorflow>=2.10.0
python-dotenv>=0.19.0
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/alreshveya-03/hostel-managment-hub.git
cd hostel-managment-hub/hostel_hub
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database
Create a `.env` file in the `hostel_hub` directory:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hostel_hub
DB_PORT=3306
```

### 5. Initialize Database
```bash
# Run your database setup script (if available)
python database/setup.py
```

### 6. Run the Application
```bash
streamlit run app.py
```

The application will open at **http://localhost:8501**
>>>>>>> 1587fd57fcb19cd3e991996e1f14a42eaa6fe062

---

## 📁 Project Structure

```
<<<<<<< HEAD
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
=======
hostel-managment-hub/
├── hostel_hub/
│   ├── app.py                      # Main Streamlit application
│   ├── requirements.txt            # Python dependencies
│   ├── test_auth.py               # Authentication tests
│   ├── database/
│   │   ├── connection.py          # Database connection handler
│   │   ├── queries.py             # Database queries
│   │   └── setup.py               # Database initialization
│   ├── utils/
│   │   ├── auth_utils.py          # Authentication utilities
│   │   ├── validators.py          # Input validation
│   │   └── helpers.py             # Helper functions
│   ├── pages/
│   │   ├── student_portal.py      # Student dashboard
│   │   └── warden_portal.py       # Warden dashboard
│   └── ai_models/
│       └── models.py              # AI/ML models
└── README.md                       # This file
>>>>>>> 1587fd57fcb19cd3e991996e1f14a42eaa6fe062
```

---

<<<<<<< HEAD
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
=======
## 🔑 Key Functions

### Authentication
- `login_student()` - Authenticate student users
- `login_warden()` - Authenticate warden users
- `register_student()` - Register new students
- `register_warden()` - Register new wardens
- `validate_register_number()` - Validate student registration format
- `validate_warden_id()` - Validate warden ID format
- `validate_password()` - Enforce password requirements

### Session Management
- `set_student_session()` - Create student session
- `set_warden_session()` - Create warden session
- `clear_session()` - Clear active session
- `is_logged_in()` - Check if user is logged in
- `get_current_role()` - Get current user role

---

## 🧪 Testing

Run authentication tests:
```bash
python test_auth.py
```

---

## 🐛 Troubleshooting

### Issue: "Code showing in output" / HTML rendering as text

**Solution:** Ensure you're running through Streamlit:
```bash
# ✅ Correct
streamlit run app.py

# ❌ Wrong - Don't run with Python directly
python app.py
```

**Verify:**
- Access at `http://localhost:8501` (not 3501)
- Check browser console for errors (F12)
- Ensure no proxy or reverse proxy is interfering

### Issue: Database connection errors

**Solution:**
- Verify `.env` file has correct credentials
- Ensure MySQL/PostgreSQL service is running
- Check database exists and is initialized

### Issue: Registration not working

**Solution:**
- Verify all required fields are filled
- Check validation rules in `utils/auth_utils.py`
- Review database logs for constraint violations

---

## 📝 Usage Examples

### Login as Student
1. Go to **Student Portal** tab
2. Click **Sign In**
3. Enter Register Number (e.g., `21CS001`)
4. Enter Password
5. Click **Sign In** button

### Register as New Student
1. Go to **Student Portal** tab
2. Click **Register** tab
3. Fill in all required fields:
   - Full Name
   - Register Number (format: `YYCSXXX`)
   - Department
   - Year
   - Phone (10 digits)
   - Email
   - Gender
   - Room Number (optional)
4. Set password (min 6 characters)
5. Click **Create Student Account**

### Login as Warden
1. Go to **Warden Portal** tab
2. Click **Sign In**
3. Enter Warden ID (e.g., `WD001`)
4. Enter Password
5. Click **Sign In** button

---

## 🔐 Security Notes

⚠️ **Important:**
- Passwords are hashed using bcrypt before storage
- Session tokens expire after inactivity
- Never commit `.env` files with real credentials
- All inputs are validated and sanitized
- SQL injection protections are in place

---

## 📧 Support & Contact

For issues or questions:
- Create an [Issue](https://github.com/alreshveya-03/hostel-managment-hub/issues)
- Contact: [Your Email]

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👥 Contributors

- **alreshveya-03** - Project Lead & Developer

---

## 🎯 Future Enhancements

- [ ] Mobile app version (Flutter/React Native)
- [ ] Advanced analytics dashboard
- [ ] Email notifications
- [ ] SMS alerts
- [ ] Payment integration
- [ ] Document upload system
- [ ] Video call support
- [ ] Mobile-optimized responsive design

---

**Last Updated:** 2026-05-26
>>>>>>> 1587fd57fcb19cd3e991996e1f14a42eaa6fe062
