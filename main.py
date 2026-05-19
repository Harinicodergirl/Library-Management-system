from tables import create_tables
from library import Library
from db import conn

create_tables()

lib = Library()

# add books

lib.add_book(
    "Harry Potter",
    "JK Rowling",
    5
)

lib.add_book(
    "Percy Jackson",
    "Rick Riordan",
    3
)

# view books

lib.view_books()

# add member

lib.add_member(
    "Jack",
    "Jack@gmail.com"
)

# borrow book

lib.borrow_book(
    member_id=2,
    book_id=4
)

# return book

lib.return_book(
    borrow_id=2
)
conn.close()
print("Database connection closed successfully")