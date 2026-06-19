"""
Hostel Hub Flask Application
"""
import os
from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.warden import warden_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(warden_bp, url_prefix='/warden')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.context_processor
    def inject_unread_messages_count():
        from flask import session
        if 'user_id' in session and 'role' in session:
            user_id = session['user_id']
            role = session['role']
            from database import fetch_one
            if role == 'student':
                try:
                    row = fetch_one("SELECT COUNT(*) AS cnt FROM messages WHERE student_id = %s AND sender_role = 'warden' AND is_read = FALSE", (user_id,))
                    return {'unread_messages_count': row['cnt'] if row else 0}
                except Exception:
                    return {'unread_messages_count': 0}
            elif role == 'warden':
                try:
                    row = fetch_one("SELECT COUNT(*) AS cnt FROM messages WHERE warden_id = %s AND sender_role = 'student' AND is_read = FALSE", (user_id,))
                    return {'unread_messages_count': row['cnt'] if row else 0}
                except Exception:
                    return {'unread_messages_count': 0}
        return {'unread_messages_count': 0}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
