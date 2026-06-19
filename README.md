# 🏠 Hostel Hub – Smart AI-Powered Hostel Management System

Hostel Hub is a comprehensive Hostel Management System developed using Flask and MySQL to streamline hostel administration and improve communication between students and wardens. The platform provides room allocation, attendance tracking, leave management, complaints handling, mess management, AI-powered room recommendations, messaging, and chatbot assistance through dedicated student and warden portals.

---

## 📌 Project Overview

Managing hostel operations manually can be time-consuming and prone to errors. Hostel Hub digitizes hostel activities by providing a centralized platform where students and wardens can interact efficiently.

The system automates room allocation, attendance tracking, leave approvals, complaint management, mess services, student-warden communication, and hostel analytics while providing AI-assisted features for smarter decision-making.

---

# ✨ Key Features

## 👨‍🎓 Student Portal

- Student Registration & Login
- Secure Authentication
- Student Profile Management
- View Room Information
- Attendance Tracking
- Leave Request Submission
- Complaint Registration
- Mess Menu Viewing
- Mess Feedback Submission
- AI Chat Assistant
- Student-Warden Messaging

---

## 👨‍💼 Warden Portal

- Warden Registration & Login
- Student Management
- Room Management
- Student Room Allocation
- Attendance Monitoring
- Complaint Resolution
- Leave Approval & Rejection
- Mess Management
- Analytics Dashboard
- Student Messaging System

---

## 🤖 AI Features

### Smart Room Allocation
The AI recommendation engine suggests suitable hostel rooms based on:

- Department
- Academic Year
- Room Occupancy
- Block Preference
- Room Availability

### Hostel AI Assistant

Students can interact with the AI assistant to get information about:

- Room Details
- Attendance
- Leave Requests
- Complaints
- Mess Menu
- Announcements

---

# 🛠️ Technologies Used

## Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

## Backend

- Python
- Flask Framework

## Database

- MySQL
- MySQL Connector

## AI Modules

- Custom Room Recommendation Engine
- Rule-Based Hostel Chatbot

## Authentication & Security

- Werkzeug Password Hashing
- Session Management
- Role-Based Access Control

## Development Tools

- Visual Studio Code
- Git
- GitHub
- MySQL Workbench

## Additional Libraries

- Flask
- Jinja2
- OpenPyXL
- Werkzeug

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
├── migration.sql
├── README.md
│
└── venv/
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

# 🔑 Authentication System

The application supports:

### Student Authentication

- Student Registration
- Student Login
- Session Management

### Warden Authentication

- Warden Registration
- Warden Login
- Role-Based Authorization

Passwords are securely stored using hashing mechanisms.

---

# 🏠 Room Management

The room management module enables:

- Add New Rooms
- Delete Rooms
- View Room Details
- Assign Students
- Remove Students
- Track Occupancy
- Room Availability Monitoring

Room information includes:

- Room Number
- Block
- Floor
- Capacity
- Occupied Beds
- Room Type
- AC Availability

---

# 📊 Attendance Management

The attendance system provides:

- Daily Attendance Recording
- Attendance History
- Student Attendance Reports
- Attendance Percentage Tracking
- Monthly Attendance Monitoring

---

# 📝 Complaint Management

Students can:

- Submit Complaints
- Track Complaint Status

Wardens can:

- View Complaints
- Update Complaint Status
- Resolve Complaints
- Add Remarks

Complaint statuses include:

- Pending
- In Progress
- Resolved

---

# 🏖️ Leave Management

Students can:

- Apply for Leave
- View Leave Status

Wardens can:

- Approve Leave Requests
- Reject Leave Requests
- Add Remarks

---

# 🍽️ Mess Management

Features include:

- Weekly Mess Menu
- Student Feedback
- Meal Attendance Tracking
- Food Quality Monitoring

---

# 💬 Student-Warden Messaging

The messaging system supports:

- Direct Student-Warden Communication
- Read/Unread Message Tracking
- Real-Time Chat Refresh
- Conversation History

---

# 📈 Analytics Dashboard

The dashboard provides:

- Total Students
- Occupied Rooms
- Available Rooms
- Complaint Statistics
- Attendance Overview
- Leave Statistics

---

# 🔒 Security Features

- Password Hashing
- Session Protection
- Role-Based Access Control
- Input Validation
- Database Constraint Validation
- SQL Injection Prevention

---

# ⚙️ Installation Guide

## Step 1: Clone Repository

```bash
git clone https://github.com/alreshveya-03/hostel-managment-hub.git
cd hostel-managment-hub
```

---

## Step 2: Create Virtual Environment

```bash
python -m venv venv
```

---

## Step 3: Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 5: Create Database

```sql
CREATE DATABASE hostel_hub;
```

---

## Step 6: Import Database Schema

```bash
mysql -u root -p hostel_hub < schema.sql
```

---

## Step 7: Configure Database

Update database credentials in:

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

## Step 8: Run Application

```bash
python app.py
```

---

## Step 9: Open Browser

```text
http://127.0.0.1:5000
```

---

# 🚀 Future Enhancements

- Mobile Application
- Push Notifications
- Email Notifications
- Face Recognition Attendance
- QR Code Attendance
- AI Complaint Classification
- Predictive Room Allocation
- Cloud Deployment

---

# 👩‍💻 Developer

**AL RESHVEYA RAMJANI S**

B.Tech Artificial Intelligence and Data Science

Rathinam Technical Campus

---

# 📜 License

This project is developed for educational, academic, and learning purposes.
