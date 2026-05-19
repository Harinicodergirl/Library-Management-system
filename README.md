# Library Management System (Flask + PostgreSQL)

A full-stack **Library Management Web Application** built using **Python (Flask)**, **PostgreSQL**, and **HTML/CSS **.  
The system supports separate roles for **Users (Members)** and **Librarians (Admin)** with fine calculation and transaction tracking.

---

## Features

### User (Member)
- Secure login system
- Borrow books from available collection
- Return borrowed books
- Automatic fine calculation for late returns
- Pay outstanding fines
- View currently borrowed books

---

### Librarian (Admin)
- Secure librarian login system
- Add new books to the library
- Remove books from system
- Add new members
- Remove existing members
- View member status (borrowed books, fines, activity)
- Track borrowing and return history

---

## Fine System

- Fine is automatically calculated based on overdue days
- Fine is updated when a book is returned
- Users can clear dues via the “Pay Fine” option
- Ensures accountability for late returns

---

## Tech Stack

- **Backend:** Python, Flask  
- **Database:** PostgreSQL  
- **Frontend:** HTML, CSS 
- **Architecture:** Modular Python design  
  - `app.py` → Routes & backend logic  
  - `db.py` → Database connection & queries  
  - `templates/` → HTML UI  
  - `static/` → CSS styling  

---

## Future Improvements

-  Advanced search system (books by title, author, genre)
-  Analytics dashboard (most borrowed books, active users)
-  Borrow history tracking per member
-  Book-wise borrower history
-  Improved UI with Bootstrap/React frontend
-  Deployment on Render / Railway / AWS

