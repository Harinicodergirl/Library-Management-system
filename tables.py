from db import conn, cur

def create_tables():

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books(
        book_id SERIAL PRIMARY KEY,
        title VARCHAR(200),
        author VARCHAR(200),
        quantity INT,
        available BOOLEAN
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS members(
        member_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(user_id),
        due INT DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS librarians(
        librarian_id SERIAL PRIMARY KEY,
        user_id INT REFERENCES users(user_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS borrowed_books(
        borrow_id SERIAL PRIMARY KEY,
        member_id INT REFERENCES members(member_id),
        book_id INT REFERENCES books(book_id),
        borrowed_date DATE,
        returned_date DATE,
        quantity INT
    )
    """)

    conn.commit()

    print("All tables created successfully")