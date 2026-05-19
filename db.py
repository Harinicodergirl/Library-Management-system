import psycopg2
from psycopg2 import OperationalError

DB_CONFIG = dict(
    host="localhost",
    database="library_db",
    user="postgres",
    password="Harini123$"
)


def _connect_db():
    return psycopg2.connect(**DB_CONFIG)


# create initial global connection and cursor
try:
    conn = _connect_db()
    cur = conn.cursor()
    print("Database connection established successfully")
except Exception as e:
    conn = None
    cur = None
    print("Could not establish DB connection:", e)


def ensure_connection():
    """Ensure global `conn` and `cur` are available and re-connect if closed."""
    global conn, cur
    try:
        if conn is None or getattr(conn, 'closed', 1):
            conn = _connect_db()
            cur = conn.cursor()
            print("Re-established DB connection")
    except OperationalError as e:
        print("DB ensure_connection failed:", e)
        raise


def close_connection():
    """Close global connection cleanly."""
    global conn, cur
    try:
        if conn is not None and not getattr(conn, 'closed', 1):
            conn.commit()
            conn.close()
            print("Database connection closed")
    except Exception as e:
        print("Error closing DB connection:", e)
    finally:
        conn = None
        cur = None