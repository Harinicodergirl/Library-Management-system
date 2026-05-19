import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="library_db",
    user="postgres",
    password=""
)

cur = conn.cursor()
print("Database connection established successfully")