-- =============================================================
--  HOSTEL HUB — SEED / DEMO DATA
--  Run this AFTER schema.sql
--  All passwords are stored as bcrypt hashes.
--
--  PLAIN TEXT PASSWORDS (for testing):
--    All wardens  → warden123
--    All students → student123
--
--  These hashes below are real bcrypt hashes generated
--  by Python:  bcrypt.hashpw(b"warden123", bcrypt.gensalt())
--  You can replace them with fresh hashes from your app.
-- =============================================================

USE hostel_hub;

-- =============================================================
-- WARDENS (3 wardens, one per block)
-- =============================================================
INSERT INTO wardens (warden_id, name, hostel_block, phone, email, password) VALUES
(
    'WD001',
    'Dr. Ramesh Kumar',
    'Block A',
    '9876543210',
    'ramesh.kumar@hostel.edu',
    -- plain: warden123
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhcCnOmGf8KzDQNVjVqxXm'
),
(
    'WD002',
    'Mrs. Priya Sundaram',
    'Block B',
    '9876543211',
    'priya.sundaram@hostel.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhcCnOmGf8KzDQNVjVqxXm'
),
(
    'WD003',
    'Mr. Senthil Murugan',
    'Block C',
    '9876543212',
    'senthil.murugan@hostel.edu',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMqJqhcCnOmGf8KzDQNVjVqxXm'
);


-- =============================================================
-- ROOMS
-- Block A: Rooms A101–A105 (Floor 1), A201–A205 (Floor 2)
-- Block B: Rooms B101–B105
-- Block C: Rooms C101–C103
-- =============================================================
INSERT INTO rooms (room_no, block, floor, capacity, occupied, room_type, ac_available) VALUES
-- Block A, Floor 1
('A101', 'Block A', 1, 3, 3, 'Standard',  FALSE),
('A102', 'Block A', 1, 3, 2, 'Standard',  FALSE),
('A103', 'Block A', 1, 3, 1, 'Standard',  FALSE),
('A104', 'Block A', 1, 3, 0, 'Standard',  FALSE),
('A105', 'Block A', 1, 2, 2, 'Premium',   TRUE),
-- Block A, Floor 2
('A201', 'Block A', 2, 3, 3, 'Standard',  FALSE),
('A202', 'Block A', 2, 3, 2, 'Standard',  FALSE),
('A203', 'Block A', 2, 2, 1, 'Premium',   TRUE),
('A204', 'Block A', 2, 1, 1, 'Deluxe',    TRUE),
('A205', 'Block A', 2, 3, 0, 'Standard',  FALSE),
-- Block B, Floor 1
('B101', 'Block B', 1, 3, 3, 'Standard',  FALSE),
('B102', 'Block B', 1, 3, 2, 'Standard',  FALSE),
('B103', 'Block B', 1, 3, 1, 'Standard',  FALSE),
('B104', 'Block B', 1, 2, 2, 'Premium',   TRUE),
('B105', 'Block B', 1, 3, 0, 'Standard',  FALSE),
-- Block C, Floor 1
('C101', 'Block C', 1, 3, 3, 'Standard',  FALSE),
('C102', 'Block C', 1, 3, 1, 'Standard',  FALSE),
('C103', 'Block C', 1, 2, 0, 'Premium',   TRUE);


-- =============================================================
-- STUDENTS (15 students across blocks/rooms/depts)
-- plain password for all: student123
-- =============================================================
INSERT INTO students
    (name, register_number, department, year, room_no, phone, email, password, gender, food_preference, address)
VALUES
-- Block A students (CSE / AIDS)
(
    'Arun Prakash',       '21CS001', 'CSE',   3, 'A101', '9600001001',
    'arun.prakash@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '12, Gandhi Street, Coimbatore'
),
(
    'Karthik Selvan',     '21CS002', 'CSE',   3, 'A101', '9600001002',
    'karthik.selvan@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '45, Nehru Nagar, Tirupur'
),
(
    'Vijay Anand',        '21CS003', 'CSE',   3, 'A101', '9600001003',
    'vijay.anand@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '8, Anna Nagar, Salem'
),
(
    'Deepak Raj',         '21CS004', 'CSE',   3, 'A102', '9600001004',
    'deepak.raj@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '22, Bharathi Street, Erode'
),
(
    'Suresh Babu',        '21CS005', 'CSE',   3, 'A102', '9600001005',
    'suresh.babu@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '67, Rajaji Road, Madurai'
),
(
    'Ravi Shankar',       '21AIDS01', 'AIDS', 2, 'A103', '9600002001',
    'ravi.shankar@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '3, Thiruvalluvar Street, Vellore'
),
(
    'Manoj Kumar',        '21AIDS02', 'AIDS', 2, 'A201', '9600002002',
    'manoj.kumar@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '14, Kamaraj Nagar, Chennai'
),
(
    'Naveen Krishnan',    '21AIDS03', 'AIDS', 2, 'A201', '9600002003',
    'naveen.krishnan@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '9, MGR Colony, Trichy'
),
(
    'Arjun Nair',         '21AIDS04', 'AIDS', 2, 'A201', '9600002004',
    'arjun.nair@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '31, Patel Road, Coimbatore'
),
-- Block B students (IT / ECE)
(
    'Rahul Verma',        '21IT001', 'IT',    1, 'B101', '9600003001',
    'rahul.verma@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '5, Subash Street, Madurai'
),
(
    'Sanjay Patel',       '21IT002', 'IT',    1, 'B101', '9600003002',
    'sanjay.patel@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '88, Lake View Road, Chennai'
),
(
    'Dinesh Babu',        '21IT003', 'IT',    1, 'B101', '9600003003',
    'dinesh.babu@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '12, Periyar Nagar, Trichy'
),
(
    'Aakash Menon',       '21ECE01', 'ECE',   4, 'B102', '9600004001',
    'aakash.menon@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '77, Marina Road, Chennai'
),
(
    'Surya Dev',          '21ECE02', 'ECE',   4, 'B102', '9600004002',
    'surya.dev@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Veg',
    '2, Velachery Main Road, Chennai'
),
-- Block C student (MECH)
(
    'Pradeep Reddy',      '21MECH1', 'MECH',  2, 'C101', '9600005001',
    'pradeep.reddy@college.edu',
    '$2b$12$eImiTXuWVxfM37uY9pEPGO5VjGZqhlKi5XGVJ7mBhZqJQ8pOJjMDu',
    'Male', 'Non-Veg',
    '43, Indira Nagar, Coimbatore'
);


-- =============================================================
-- COMPLAINTS (sample complaints with varied categories/priorities)
-- =============================================================
INSERT INTO complaints (student_id, complaint_text, category, priority, status, warden_remarks, filed_date, resolved_date) VALUES
(1, 'The tube light in our room has been fused for 3 days. Replacement needed urgently.',
    'Electrical', 'Normal', 'In Progress', 'Electrician assigned', '2025-05-01', NULL),

(2, 'Water tap in bathroom is leaking continuously. Floor is always wet.',
    'Plumbing', 'Urgent', 'Pending', NULL, '2025-05-03', NULL),

(3, 'WiFi signal is very weak in room A101. Cannot attend online classes.',
    'Internet', 'Normal', 'Pending', NULL, '2025-05-05', NULL),

(4, 'Saw an electrical spark near the switchboard last night. Very dangerous.',
    'Electrical', 'Emergency', 'In Progress', 'Electrician dispatched immediately', '2025-05-06', NULL),

(5, 'Room not cleaned for the past week. Garbage is piling up.',
    'Cleaning', 'Normal', 'Resolved', 'Cleaning done on 08-May', '2025-05-02', '2025-05-08'),

(6, 'Bed frame in my room is broken. Cannot sleep properly.',
    'Furniture', 'Normal', 'Pending', NULL, '2025-05-07', NULL),

(7, 'Hot water not available in Block A bathrooms since Monday.',
    'Plumbing', 'Urgent', 'In Progress', 'Plumber working on boiler', '2025-05-04', NULL),

(8, 'Common area lights on floor 2 are not working since 3 days.',
    'Electrical', 'Normal', 'Resolved', 'Fixed by electrician', '2025-04-28', '2025-05-01'),

(9, 'Internet router in Block A floor 1 reboots every 30 minutes.',
    'Internet', 'Urgent', 'Pending', NULL, '2025-05-08', NULL),

(10, 'Drain in bathroom is completely blocked. Water not draining.',
    'Plumbing', 'Urgent', 'In Progress', 'Drain cleaning scheduled', '2025-05-07', NULL);


-- =============================================================
-- LEAVE REQUESTS
-- =============================================================
INSERT INTO leave_requests (student_id, reason, from_date, to_date, status, warden_remarks) VALUES
(1, 'Going home for family function - sister\'s engagement ceremony.',         '2025-05-10', '2025-05-13', 'Approved',  'Approved. Return by 13th evening.'),
(2, 'Medical appointment - dental surgery scheduled at city hospital.',        '2025-05-09', '2025-05-10', 'Approved',  'Approved for medical leave.'),
(3, 'Need to attend cousin\'s wedding in Madurai.',                            '2025-05-15', '2025-05-17', 'Pending',   NULL),
(4, 'Father is unwell. Need to go home to Erode for care.',                    '2025-05-08', '2025-05-11', 'Approved',  'Emergency leave granted.'),
(5, 'Attending inter-college hackathon at Anna University.',                   '2025-05-20', '2025-05-21', 'Pending',   NULL),
(6, 'Going home for summer vacation.',                                         '2025-05-25', '2025-06-01', 'Pending',   NULL),
(7, 'Passport renewal appointment in Chennai.',                                '2025-05-12', '2025-05-12', 'Approved',  'Single day leave approved.'),
(8, 'Attending college sports meet at another campus.',                        '2025-05-18', '2025-05-19', 'Rejected',  'Rejected - exam preparation week.'),
(9, 'Attending relative\'s function in Vellore.',                              '2025-05-22', '2025-05-24', 'Pending',   NULL),
(10,'Medical emergency - need to visit government hospital.',                  '2025-05-09', '2025-05-09', 'Approved',  'Approved.');


-- =============================================================
-- ATTENDANCE (last 7 days for student 1–5 as sample)
-- =============================================================
INSERT INTO attendance (student_id, att_date, status, marked_by) VALUES
-- Student 1
(1, '2025-05-02', 'Present', 'WD001'),
(1, '2025-05-03', 'Present', 'WD001'),
(1, '2025-05-04', 'Absent',  'WD001'),
(1, '2025-05-05', 'Present', 'WD001'),
(1, '2025-05-06', 'Present', 'WD001'),
(1, '2025-05-07', 'Leave',   'WD001'),
(1, '2025-05-08', 'Present', 'WD001'),
-- Student 2
(2, '2025-05-02', 'Present', 'WD001'),
(2, '2025-05-03', 'Present', 'WD001'),
(2, '2025-05-04', 'Present', 'WD001'),
(2, '2025-05-05', 'Present', 'WD001'),
(2, '2025-05-06', 'Leave',   'WD001'),
(2, '2025-05-07', 'Leave',   'WD001'),
(2, '2025-05-08', 'Present', 'WD001'),
-- Student 3
(3, '2025-05-02', 'Present', 'WD001'),
(3, '2025-05-03', 'Absent',  'WD001'),
(3, '2025-05-04', 'Absent',  'WD001'),
(3, '2025-05-05', 'Present', 'WD001'),
(3, '2025-05-06', 'Present', 'WD001'),
(3, '2025-05-07', 'Present', 'WD001'),
(3, '2025-05-08', 'Present', 'WD001'),
-- Student 4
(4, '2025-05-02', 'Present', 'WD001'),
(4, '2025-05-03', 'Present', 'WD001'),
(4, '2025-05-04', 'Present', 'WD001'),
(4, '2025-05-05', 'Absent',  'WD001'),
(4, '2025-05-06', 'Present', 'WD001'),
(4, '2025-05-07', 'Present', 'WD001'),
(4, '2025-05-08', 'Present', 'WD001'),
-- Student 5
(5, '2025-05-02', 'Present', 'WD001'),
(5, '2025-05-03', 'Present', 'WD001'),
(5, '2025-05-04', 'Present', 'WD001'),
(5, '2025-05-05', 'Present', 'WD001'),
(5, '2025-05-06', 'Present', 'WD001'),
(5, '2025-05-07', 'Absent',  'WD001'),
(5, '2025-05-08', 'Present', 'WD001');


-- =============================================================
-- ANNOUNCEMENTS
-- =============================================================
INSERT INTO announcements (title, description, ann_type, posted_by) VALUES
(
    'Water Supply Interruption – 10th May',
    'Due to maintenance work, water supply in Block A will be interrupted from 10 AM to 2 PM on 10th May 2025. Please store water in advance. We apologize for the inconvenience.',
    'General', 'WD001'
),
(
    'Emergency: Power Outage Expected Tonight',
    'TNEB has informed us about planned power maintenance tonight from 11 PM to 2 AM. All students are advised to charge their devices before 10 PM. Generators will not be available during this period.',
    'Emergency', 'WD001'
),
(
    'Mess Menu Update – This Week',
    'Special menu this week! Friday dinner will have Biryani. Saturday lunch will include Paneer Special. Sunday breakfast will have Poori with Channa Masala. All students are encouraged to attend.',
    'Mess Update', 'WD002'
),
(
    'Hostel Day Celebration – 20th May',
    'Annual Hostel Day celebrations will be held on 20th May 2025. Cultural programs, sports events, and a special dinner are planned. All students must attend. Registration opens from 12th May.',
    'General', 'WD001'
),
(
    'Holiday Announcement – Pongal',
    'The hostel office will remain closed on 14th and 15th January. Mess will serve special Pongal breakfast on 14th January. Students who wish to go home must submit leave applications by 12th January.',
    'Holiday', 'WD003'
),
(
    'Strict Curfew Reminder',
    'All students must return to the hostel premises by 9:30 PM on weekdays and 10:00 PM on weekends. Violations will be reported to the college administration. Cooperation is expected.',
    'General', 'WD001'
);


-- =============================================================
-- MESS MENU (last 7 days)
-- =============================================================
INSERT INTO mess_menu (menu_date, breakfast, lunch, snacks, dinner) VALUES
('2025-05-02', 'Idli, Sambar, Coconut Chutney, Tea',
               'Rice, Dal Fry, Mixed Veg Curry, Pickle, Papad',
               'Bread Butter, Banana, Tea',
               'Chapati, Paneer Butter Masala, Rice, Dal, Salad'),

('2025-05-03', 'Dosa, Tomato Chutney, Sambar, Coffee',
               'Rice, Rasam, Potato Curry, Curd, Papad',
               'Biscuits, Bajji, Tea',
               'Chapati, Egg Curry / Paneer Curry, Rice, Dal'),

('2025-05-04', 'Pongal, Sambar, Vada, Tea',
               'Rice, Sambar, Beans Poriyal, Pickle, Papad',
               'Fruit Bowl, Tea',
               'Fried Rice, Gobi Manchurian / Chicken Gravy, Raita'),

('2025-05-05', 'Poori, Channa Masala, Tea',
               'Rice, Dal Tadka, Cabbage Curry, Curd, Pickle',
               'Murukku, Tea',
               'Chapati, Dal Makhani, Rice, Salad'),

('2025-05-06', 'Upma, Coconut Chutney, Boiled Egg / Banana, Tea',
               'Veg Biryani / Chicken Biryani, Raita, Pickle',
               'Samosa, Tea',
               'Chapati, Kadai Paneer / Mutton Curry, Rice, Dal'),

('2025-05-07', 'Idiyappam, Coconut Milk, Boiled Egg / Banana, Tea',
               'Rice, Lemon Rasam, Drumstick Curry, Curd, Papad',
               'Cake Slice, Tea',
               'Chapati, Veg Korma, Rice, Dal, Salad'),

('2025-05-08', 'Paratha, Curd, Pickle, Tea',
               'Rice, Sambar, Aloo Gobi, Papad, Pickle',
               'Bajji, Tea',
               'Chapati, Egg Bhurji / Paneer Bhurji, Rice, Dal');


-- =============================================================
-- MEAL ATTENDANCE (students 1–5 for last 3 days)
-- =============================================================
INSERT INTO meal_attendance (student_id, meal_date, meal_type, attended) VALUES
-- 2025-05-06
(1, '2025-05-06', 'Breakfast', TRUE),
(1, '2025-05-06', 'Lunch',     TRUE),
(1, '2025-05-06', 'Snacks',    FALSE),
(1, '2025-05-06', 'Dinner',    TRUE),
(2, '2025-05-06', 'Breakfast', TRUE),
(2, '2025-05-06', 'Lunch',     FALSE),
(2, '2025-05-06', 'Snacks',    TRUE),
(2, '2025-05-06', 'Dinner',    TRUE),
(3, '2025-05-06', 'Breakfast', FALSE),
(3, '2025-05-06', 'Lunch',     TRUE),
(3, '2025-05-06', 'Snacks',    TRUE),
(3, '2025-05-06', 'Dinner',    FALSE),
-- 2025-05-07
(1, '2025-05-07', 'Breakfast', TRUE),
(1, '2025-05-07', 'Lunch',     TRUE),
(1, '2025-05-07', 'Snacks',    TRUE),
(1, '2025-05-07', 'Dinner',    TRUE),
(2, '2025-05-07', 'Breakfast', TRUE),
(2, '2025-05-07', 'Lunch',     TRUE),
(2, '2025-05-07', 'Snacks',    FALSE),
(2, '2025-05-07', 'Dinner',    TRUE),
(4, '2025-05-07', 'Breakfast', FALSE),
(4, '2025-05-07', 'Lunch',     TRUE),
(4, '2025-05-07', 'Snacks',    TRUE),
(4, '2025-05-07', 'Dinner',    TRUE),
-- 2025-05-08
(1, '2025-05-08', 'Breakfast', TRUE),
(1, '2025-05-08', 'Lunch',     FALSE),
(1, '2025-05-08', 'Snacks',    TRUE),
(1, '2025-05-08', 'Dinner',    TRUE),
(5, '2025-05-08', 'Breakfast', TRUE),
(5, '2025-05-08', 'Lunch',     TRUE),
(5, '2025-05-08', 'Snacks',    FALSE),
(5, '2025-05-08', 'Dinner',    FALSE);


-- =============================================================
-- FOOD FEEDBACK
-- =============================================================
INSERT INTO food_feedback (student_id, feedback_text, sentiment, rating, meal_type, feedback_date) VALUES
(1, 'Breakfast idli was soft and sambar was very tasty today. Really enjoyed it.',    'Positive', 5, 'Breakfast', '2025-05-08'),
(2, 'Lunch was okay. Rice was fine but dal could have been spicier.',                 'Neutral',  3, 'Lunch',     '2025-05-08'),
(3, 'Dinner chapati was too hard and the paneer curry was bland. Not satisfied.',     'Negative', 2, 'Dinner',    '2025-05-07'),
(4, 'The biryani on Tuesday was excellent! Best meal this month.',                    'Positive', 5, 'Lunch',     '2025-05-06'),
(5, 'Snacks samosa was cold and stale. Please serve fresh food.',                    'Negative', 1, 'Snacks',    '2025-05-06'),
(6, 'Food quality has improved this week. Breakfast was good.',                       'Positive', 4, 'Breakfast', '2025-05-07'),
(7, 'Dinner was decent. Could add more variety to the menu.',                         'Neutral',  3, 'Dinner',    '2025-05-08'),
(8, 'Overall good food this week. Rasam was especially tasty on Wednesday.',          'Positive', 4, 'Lunch',     '2025-05-07'),
(9, 'Bread butter breakfast is boring. Please include eggs more often.',              'Neutral',  3, 'Breakfast', '2025-05-07'),
(10,'Mutton curry on Friday was the highlight of the week! More non-veg please.',     'Positive', 5, 'Dinner',    '2025-05-06');
