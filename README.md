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

---

## 📁 Project Structure

```
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
```

---

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
