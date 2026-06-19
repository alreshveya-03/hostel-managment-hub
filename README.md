# 🏠 Hostel Hub – Smart AI-Powered Hostel Management System

Hostel Hub is a comprehensive Hostel Management System developed using Flask and MySQL to simplify hostel administration and improve communication between students and wardens. The platform automates room allocation, attendance tracking, leave management, complaints handling, mess management, AI-powered room recommendations, messaging, and analytics through dedicated student and warden portals.

---

## 📌 Project Overview

Managing hostel operations manually is time-consuming and prone to errors. Hostel Hub provides a centralized digital platform that helps students and wardens efficiently manage hostel activities.

The system enables:

- Student and Warden Authentication
- Smart Room Allocation
- Attendance Tracking
- Complaint Management
- Leave Management
- Mess Menu Management
- Student-Warden Messaging
- AI Chat Assistant
- Hostel Analytics Dashboard

---

# ✨ Features

## 👨‍🎓 Student Portal

- Student Registration & Login
- Profile Management
- View Room Information
- Attendance Tracking
- Leave Request Submission
- Complaint Submission & Tracking
- Mess Menu Viewing
- Food Feedback Submission
- AI Chat Assistant
- Student-Warden Messaging

---

## 👨‍💼 Warden Portal

- Warden Registration & Login
- Student Management
- Room Management
- Room Allocation
- Attendance Monitoring
- Complaint Resolution
- Leave Approval/Rejection
- Mess Management
- Announcement Management
- Analytics Dashboard
- Student Messaging

---

## 🤖 AI Features

### Smart Room Recommendation System

The AI engine recommends suitable rooms based on:

- Department
- Academic Year
- Room Availability
- Occupancy Levels
- Block Preferences

### Hostel AI Assistant

Students can interact with the chatbot to get information regarding:

- Room Details
- Attendance
- Complaints
- Leave Requests
- Mess Menu
- Announcements

---

# 🛠️ Tech Stack

| Component | Technology |
|------------|------------|
| Frontend | HTML5, CSS3, JavaScript, Jinja2 |
| Backend | Python 3.13, Flask |
| Database | MySQL |
| Authentication | Werkzeug Password Hashing, Session Management |
| AI Module | Room Recommendation Engine, Rule-Based Chatbot |
| Messaging | Student-Warden Messaging System |
| Reports | OpenPyXL |
| Version Control | Git, GitHub |
| Development Tools | VS Code, MySQL Workbench |

---

# 📂 Project Structure

```text
hostel_hub_flask/
│
├── app.py
├── config.py
├── database.py
├── auth_utils.py
├── schema.sql
├── migration.sql
├── requirements.txt
│
├── routes/
│   ├── auth.py
│   ├── student.py
│   ├── warden.py
│   └── api.py
│
├── ai_modules/
│   ├── chatbot.py
│   └── room_suggest.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── student/
│   ├── warden/
│   └── base.html
│
└── README.md
```

---

# 🗄️ Database Modules

The system consists of the following database tables:

- Students
- Wardens
- Rooms
- Attendance
- Complaints
- Leave Requests
- Announcements
- Mess Menu
- Food Feedback
- Meal Attendance
- Messages

---

# 🔐 Authentication & Security

The application provides:

### Student Authentication

- Student Registration
- Student Login
- Secure Session Handling

### Warden Authentication

- Warden Registration
- Warden Login
- Role-Based Authorization

### Security Features

- Password Hashing
- Session Management
- Input Validation
- SQL Injection Prevention
- Database Constraints
- Access Control

---

# 🏠 Room Management

Features include:

- Add Rooms
- Delete Rooms
- View Room Details
- Assign Students
- Remove Students
- Occupancy Tracking
- Availability Monitoring

Room Information:

- Room Number
- Block
- Floor
- Capacity
- Occupied Beds
- Room Type
- AC Availability

---

# 📊 Attendance Management

The attendance module allows:

- Daily Attendance Recording
- Attendance History
- Attendance Percentage Tracking
- Monthly Attendance Reports
- Student Attendance Monitoring

---

# 📝 Complaint Management

Students can:

- Submit Complaints
- View Complaint Status

Wardens can:

- View Complaints
- Update Status
- Add Remarks
- Resolve Complaints

Complaint Status Types:

- Pending
- In Progress
- Resolved

---

# 🏖️ Leave Management

Students can:

- Apply Leave
- View Leave Status

Wardens can:

- Approve Leave
- Reject Leave
- Add Remarks

---

# 🍽️ Mess Management

Features include:

- Weekly Menu Display
- Food Feedback Collection
- Meal Attendance Tracking
- Menu Updates

---

# 💬 Student-Warden Messaging

The messaging system supports:

- Direct Communication
- Read/Unread Status
- Conversation History
- Real-Time Refresh
- Secure Messaging

---

# 📢 Announcement Management

Wardens can:

- Create Announcements
- Publish Notices
- Share Important Updates

Students can:

- View Announcements
- Stay Updated

---

# 📈 Analytics Dashboard

Dashboard Metrics Include:

- Total Students
- Room Occupancy
- Available Rooms
- Complaint Statistics
- Leave Statistics
- Attendance Overview

---

# ⚙️ Installation Guide

## 1️⃣ Clone Repository

```bash
git clone https://github.com/alreshveya-03/hostel-managment-hub.git
cd hostel-managment-hub
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

---

## 3️⃣ Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 5️⃣ Create Database

```sql
CREATE DATABASE hostel_hub;
```

---

## 6️⃣ Import Database Schema

```bash
mysql -u root -p hostel_hub < schema.sql
```

---

## 7️⃣ Configure Database

Update database credentials inside:

```python
config.py
```

Example:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_password"
DB_NAME = "hostel_hub"
```

---

## 8️⃣ Run Application

```bash
python app.py
```

---

## 9️⃣ Open Browser

```text
http://127.0.0.1:5000
```

---

# 🚀 Future Enhancements

- Mobile Application
- Push Notifications
- Email Notifications
- Face Recognition Attendance
- QR-Based Attendance
- AI Complaint Classification
- Predictive Room Allocation
- Cloud Deployment

---

# 👩‍💻 Developer

**AL RESHVEYA RAMJANI S**

B.Tech – Artificial Intelligence & Data Science  
Rathinam Technical Campus

---

# 📄 License

This project is developed for educational, academic, and learning purposes.

---

⭐ If you find this project useful, consider giving it a star on GitHub!
