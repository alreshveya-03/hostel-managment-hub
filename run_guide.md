# Hostel Management System – Step-by-Step Run Guide

This guide describes how to configure, run, and interact with the Hostel Management System application.

## Prerequisites

- Python 3.8 or higher
- MySQL Server (configured and running)

## Setup Steps

### 1. Configure the Virtual Environment

Ensure the virtual environment is set up and active. If not already done:

```bash
# Navigate to the project root
cd e:\hostel_hub_flask

# Create a virtual environment if needed
python -m venv venv

# Activate the virtual environment
# On Windows (cmd/powershell):
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Database Configuration

The application queries the MySQL database using parameters defined in `config.py`. You can adjust these settings by setting environment variables or editing `config.py` directly:

- `MYSQL_HOST`: The MySQL hostname (defaults to `localhost`).
- `MYSQL_PORT`: The MySQL port (defaults to `3306`).
- `MYSQL_USER`: The MySQL username (defaults to `root`).
- `MYSQL_PASSWORD`: The MySQL password (defaults to `rashvi@0311`).
- `MYSQL_DB`: The database name (defaults to `hostel_hub`).

### 4. Running the Flask App

Start the Flask development server:

```bash
python app.py
```

By default, the application runs on **`http://127.0.0.1:5000`**.

---

## Database Schema Differences Reference

The application code has been aligned to map directly to the actual running MySQL database schema. The key differences from the initial `schema.sql` are summarized below:

| Entity | codebase `schema.sql` reference | Actual Running MySQL Database Schema |
| :--- | :--- | :--- |
| **Students PK** | `id` (INT) | `student_id` (INT, auto-increment) |
| **Students Reg No** | `reg_number` | `register_number` |
| **Students Room** | `room_id` (INT FK to `rooms.id`) | `room_no` (VARCHAR(10) FK to `rooms.room_no`) |
| **Students Extra** | `is_active`, `guardian_name`, `guardian_phone`, `profile_photo` | *Not present in database* |
| **Wardens PK** | `id` (INT, auto-increment) | `warden_id` (VARCHAR(10), manual input e.g. `WD001`) |
| **Rooms PK** | `id` (INT, auto-increment), `room_number` | `room_no` (VARCHAR(10), primary key) |
| **Rooms Extra** | `amenities`, `is_active` | `ac_available` (TINYINT(1)), *No `is_active`* |
| **Complaints PK** | `id` | `complaint_id` |
| **Complaints Text** | `title` and `description` | `complaint_text` (Combined title + description separated by `\n`) |
| **Complaints Response** | `warden_response` | `warden_remarks` |
| **Complaints Resolved** | `resolved_at` (TIMESTAMP) | `resolved_date` (DATE) |
| **Leave Requests PK** | `id` | `leave_id` |
| **Leave Requests Date** | `created_at` | `applied_on` (TIMESTAMP) |
| **Leave Requests Extra** | `destination`, `contact_during_leave`, `approved_by` | *Not present in database* |
| **Attendance PK** | `id` | `attendance_id` |
| **Attendance Date** | `date` | `att_date` |
| **Mess Menu PK** | `id`, `day_of_week` / `meal_type` combinations | `menu_id` (PK), `menu_date` (DATE, unique key) |
| **Mess Menu Items** | `day_of_week`, `meal_type`, `items`, `calories` | `menu_date`, `breakfast`, `lunch`, `snacks`, `dinner` |
| **Food Feedback PK** | `id` | `feedback_id` |
| **Food Feedback Date** | `date` | `feedback_date` |
| **Announcements PK** | `id` | `announcement_id` |
| **Announcements Content**| `content` | `description` |
| **Announcements Date** | `created_at` | `posted_date` |
| **Announcements Warden**| `warden_id` (INT) | `posted_by` (VARCHAR(10) FK to `wardens.warden_id`) |

No manual migration or database alterations are needed now because all routes and queries have been modified to match the running database. Refer to `migration.sql` for query representations.
