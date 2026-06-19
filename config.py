import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hostel-hub-secret-2024-change-in-prod')
    # MySQL connection
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER     = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'rashvi@0311')
    MYSQL_DB       = os.environ.get('MYSQL_DB', 'hostel_hub')
    # Upload folder
    UPLOAD_FOLDER  = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
