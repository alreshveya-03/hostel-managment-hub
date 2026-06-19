"""
auth_utils.py – bcrypt helpers + route decorators
"""
from functools import wraps
from flask import session, redirect, url_for, flash

try:
    import bcrypt
    def hash_password(pw: str) -> str:
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    def check_password(pw: str, hashed: str) -> bool:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
except ImportError:
    import hashlib, os
    def hash_password(pw: str) -> str:
        salt = os.urandom(16).hex()
        h = hashlib.sha256((pw + salt).encode()).hexdigest()
        return f"{salt}${h}"
    def check_password(pw: str, hashed: str) -> bool:
        parts = hashed.split('$')
        if len(parts) != 2:
            return False
        salt, h = parts
        return hashlib.sha256((pw + salt).encode()).hexdigest() == h


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            flash('Please log in as a student.', 'warning')
            return redirect(url_for('auth.student_login'))
        return f(*args, **kwargs)
    return decorated


def warden_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'warden':
            flash('Please log in as a warden.', 'warning')
            return redirect(url_for('auth.warden_login'))
        return f(*args, **kwargs)
    return decorated
