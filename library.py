from db import conn, cur
from datetime import date


class Library:

    # ---------------- ADD BOOK ----------------

    def add_book(self, title, author, quantity):
        cur.execute("""
        SELECT book_id, quantity FROM books
        WHERE title=%s AND author=%s
        """, (title, author))

        result = cur.fetchone()

        if result:
            book_id, qty = result

            cur.execute("""
            UPDATE books
            SET quantity = quantity + %s
            WHERE book_id = %s
            """, (quantity, book_id))
        else:
            cur.execute("""
            INSERT INTO books(title, author, quantity, available)
            VALUES (%s, %s, %s, %s)
            """, (title, author, quantity, quantity > 0))

            print("New book added")

        print("Book already exists → quantity updated")


        #cur.execute("""
        #INSERT INTO books(title, author, quantity, available)
        #VALUES(%s, %s, %s, %s)
        #""", (title, author, quantity, quantity > 0))

        #conn.commit()

        print("Book added successfully")


    # ---------------- VIEW BOOKS ----------------

    def view_books(self):

        cur.execute("SELECT * FROM books")

        books = cur.fetchall()

        for book in books:
            print(book)


    # ---------------- REMOVE BOOK ----------------

    def remove_book(self, book_id):

        cur.execute("""
        DELETE FROM books
        WHERE book_id = %s
        """, (book_id,))

        conn.commit()

        print("Book removed successfully")


    # ---------------- ADD MEMBER ----------------

    def add_member(self, name, email):

        # insert into users table

        cur.execute("""
        INSERT INTO users(name, email)
        VALUES(%s, %s)
        RETURNING user_id
        """, (name, email))

        user_id = cur.fetchone()[0]

        # insert into members table

        cur.execute("""
        INSERT INTO members(user_id)
        VALUES(%s)
        """, (user_id,))

        conn.commit()

        print("Member added successfully")


    # ---------------- BORROW BOOK ----------------

    def borrow_book(self, member_id, book_id):

        cur.execute("""
        SELECT quantity FROM books
        WHERE book_id = %s
        """, (book_id,))

        quantity = cur.fetchone()[0]

        if quantity > 0:

            cur.execute("""
            INSERT INTO borrowed_books(
                member_id,
                book_id,
                borrowed_date,
                returned_date,
                quantity
            )
            VALUES(%s, %s, %s, %s, %s)
            """, (member_id, book_id, date.today(), None, 1))

            cur.execute("""
            UPDATE books
            SET quantity = quantity - 1
            WHERE book_id = %s
            """, (book_id,))

            conn.commit()

            print("Book borrowed successfully")

        else:
            print("Book not available")
    


    # ---------------- RETURN BOOK ----------------

    def return_book(self, borrow_id):

        cur.execute("""
        SELECT book_id FROM borrowed_books
        WHERE borrow_id = %s
        """, (borrow_id,))

        book_id = cur.fetchone()[0]

        cur.execute("""
        UPDATE borrowed_books
        SET returned_date = %s
        WHERE borrow_id = %s
        """, (date.today(), borrow_id))

        cur.execute("""
        UPDATE books
        SET quantity = quantity + 1
        WHERE book_id = %s
        """, (book_id,))

        conn.commit()

        print("Book returned successfully")