# =============================================================
#  database/connection.py
#  Hostel Hub — MySQL Connection Helper
# =============================================================

import mysql.connector
import streamlit as st


def get_connection():
    """
    Returns a live MySQL connection.
    Configure your credentials in Streamlit secrets or
    edit the values below directly for local development.

    Streamlit secrets (~/.streamlit/secrets.toml):
        [mysql]
        host     = "localhost"
        port     = 3306
        user     = "root"
        password = "rashvi@0311"
        database = "hostel_hub"
    """

    # ── Try Streamlit secrets first (production) ──────────────
    try:
        cfg = st.secrets["mysql"]
        return mysql.connector.connect(
            host=cfg["host"],
            port=int(cfg.get("port", 3306)),
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            autocommit=False,
            charset="utf8mb4",
            connect_timeout=10,
        )

    except Exception:
        # Secrets not configured — fall through to dev credentials
        pass

    # ── Fallback: hard-coded dev credentials ──────────────────
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="rashvi@0311",           # ← change for your local setup
        database="hostel_hub",
        autocommit=False,
        charset="utf8mb4",
        connect_timeout=10,
    )
