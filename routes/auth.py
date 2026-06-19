"""routes/auth.py"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import fetch_one, insert_and_get_id
from auth_utils import hash_password, check_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    return render_template('index.html')


# ── Student ───────────────────────────────────────────────────

@auth_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pw    = request.form.get('password', '')
        student = fetch_one(
            "SELECT student_id AS id, name, password FROM students WHERE email=%s", (email,))
        if student and check_password(pw, student['password']):
            session.clear()
            session['user_id'] = student['id']
            session['name']    = student['name']
            session['role']    = 'student'
            return redirect(url_for('student.dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('student_login.html')


@auth_bp.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        f = request.form
        # Basic validation
        if fetch_one("SELECT student_id AS id FROM students WHERE email=%s", (f['email'],)):
            flash('Email already registered.', 'danger')
            return render_template('student_register.html')
        if fetch_one("SELECT student_id AS id FROM students WHERE register_number=%s", (f['reg_number'],)):
            flash('Registration number already exists.', 'danger')
            return render_template('student_register.html')
        hpw = hash_password(f['password'])
        insert_and_get_id(
            """INSERT INTO students
               (name,register_number,email,password,phone,department,year,gender,address)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (f['name'].strip(), f['reg_number'].strip(), f['email'].strip(), hpw,
             f.get('phone',''), f.get('department',''), int(f.get('year',1)),
             f.get('gender','Male'), f.get('address',''))
        )
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.student_login'))
    return render_template('student_register.html')


# ── Warden ────────────────────────────────────────────────────

@auth_bp.route('/warden/login', methods=['GET', 'POST'])
def warden_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pw    = request.form.get('password', '')
        warden = fetch_one(
            "SELECT warden_id AS id, name, password FROM wardens WHERE email=%s", (email,))
        if warden and check_password(pw, warden['password']):
            session.clear()
            session['user_id'] = warden['id']
            session['name']    = warden['name']
            session['role']    = 'warden'
            return redirect(url_for('warden.dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('warden_login.html')


@auth_bp.route('/warden/register', methods=['GET', 'POST'])
def warden_register():
    if request.method == 'POST':
        f = request.form
        if fetch_one("SELECT warden_id AS id FROM wardens WHERE email=%s", (f['email'],)):
            flash('Email already registered.', 'danger')
            return render_template('warden_register.html')
        phone = f.get('phone', '').strip()
        if len(phone) < 10:
            flash('Phone number must be at least 10 digits.', 'danger')
            return render_template('warden_register.html')
        hostel_block = f.get('hostel_block', '').strip()
        if hostel_block not in ('Block A', 'Block B', 'Block C'):
            flash('Please select a valid hostel block (Block A, B, or C).', 'danger')
            return render_template('warden_register.html')
        hpw = hash_password(f['password'])
        res = fetch_one("SELECT warden_id FROM wardens ORDER BY warden_id DESC LIMIT 1")
        if res and res['warden_id'].startswith('WD'):
            try:
                num = int(res['warden_id'][2:])
                next_id = f"WD{num+1:03d}"
            except ValueError:
                next_id = "WD004"
        else:
            next_id = "WD001"
        insert_and_get_id(
            "INSERT INTO wardens (warden_id,name,email,password,phone,hostel_block) VALUES (%s,%s,%s,%s,%s,%s)",
            (next_id, f['name'].strip(), f['email'].strip(), hpw, phone, hostel_block)
        )
        flash('Warden account created! Please log in.', 'success')
        return redirect(url_for('auth.warden_login'))
    return render_template('warden_register.html')


@auth_bp.route('/logout')
def logout():
    role = session.get('role')
    session.clear()
    if role == 'warden':
        return redirect(url_for('auth.warden_login'))
    return redirect(url_for('auth.student_login'))
