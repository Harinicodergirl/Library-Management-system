from flask import Flask, render_template, request, redirect, url_for, session, flash
import db
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "change_this_secret"

LOAN_DAYS = 14
FINE_PER_DAY = 1  # currency units per day overdue


@app.before_request
def ensure_db():
    # ensure DB connection is available for every request
    try:
        db.ensure_connection()
    except Exception:
        flash('Database connection error')


def get_user_by_email(email):
    db.cur.execute("SELECT user_id, name, email FROM users WHERE email=%s", (email,))
    return db.cur.fetchone()


def get_member_by_user_id(user_id):
    db.cur.execute("SELECT member_id, user_id, due FROM members WHERE user_id=%s", (user_id,))
    return db.cur.fetchone()


def get_librarian_by_user_id(user_id):
    db.cur.execute("SELECT librarian_id, user_id FROM librarians WHERE user_id=%s", (user_id,))
    return db.cur.fetchone()


@app.route('/')
def index():
    return render_template('index.html')


# ----------------- SIGNUP -----------------
@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        # create user and member
        db.cur.execute("INSERT INTO users(name, email) VALUES(%s,%s) RETURNING user_id", (name, email))
        user_id = db.cur.fetchone()[0]
        db.cur.execute("INSERT INTO members(user_id) VALUES(%s)", (user_id,))
        db.conn.commit()
        # auto-login the new user
        session['role'] = 'user'
        session['user_id'] = user_id
        member = get_member_by_user_id(user_id)
        session['member_id'] = member[0]
        session['name'] = name
        flash('Account created and logged in')
        return redirect(url_for('user_dashboard'))
    return render_template('signup_user.html')


@app.route('/signup/librarian', methods=['GET', 'POST'])
def signup_librarian():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        # create user and librarian
        db.cur.execute("INSERT INTO users(name, email) VALUES(%s,%s) RETURNING user_id", (name, email))
        user_id = db.cur.fetchone()[0]
        db.cur.execute("INSERT INTO librarians(user_id) VALUES(%s)", (user_id,))
        db.conn.commit()
        # auto-login as librarian
        librarian = get_librarian_by_user_id(user_id)
        session['role'] = 'librarian'
        session['user_id'] = user_id
        session['librarian_id'] = librarian[0]
        session['name'] = name
        flash('Librarian account created and logged in')
        return redirect(url_for('librarian_dashboard'))
    return render_template('signup_librarian.html')


# ----------------- LOGIN -----------------
@app.route('/login/user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_by_email(email)
        if not user:
            flash('No user found with that email. Please sign up.')
            return redirect(url_for('signup_user'))

        member = get_member_by_user_id(user[0])
        if not member:
            flash('No member record found. Please sign up.')
            return redirect(url_for('signup_user'))

        session['role'] = 'user'
        session['user_id'] = user[0]
        session['member_id'] = member[0]
        session['name'] = user[1]
        return redirect(url_for('user_dashboard'))

    return render_template('login_user.html')


@app.route('/login/librarian', methods=['GET', 'POST'])
def login_librarian():
    if request.method == 'POST':
        email = request.form.get('email')
        user = get_user_by_email(email)
        if not user:
            flash('No user found with that email.')
            return redirect(url_for('login_librarian'))

        librarian = get_librarian_by_user_id(user[0])
        if not librarian:
            flash('Not a librarian account. Please sign up.')
            return redirect(url_for('signup_librarian'))

        session['role'] = 'librarian'
        session['user_id'] = user[0]
        session['librarian_id'] = librarian[0]
        session['name'] = user[1]
        return redirect(url_for('librarian_dashboard'))

    return render_template('login_librarian.html')


@app.route('/logout')
def logout():
    # close DB connection cleanly when user logs out
    try:
        db.close_connection()
    except Exception:
        pass
    session.clear()
    return redirect(url_for('index'))


# ----------------- COMMON -----------------
@app.route('/books')
def view_books():
    db.cur.execute("SELECT book_id, title, author, quantity FROM books ORDER BY book_id")
    books = db.cur.fetchall()
    return render_template('books.html', books=books)


# ----------------- USER -----------------
@app.route('/user')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('login_user'))

    member_id = session.get('member_id')

    # borrowed books for member
    db.cur.execute("""
    SELECT b.borrow_id, bk.title, bk.author, b.borrowed_date, b.returned_date
    FROM borrowed_books b
    JOIN books bk ON b.book_id = bk.book_id
    WHERE b.member_id = %s
    ORDER BY b.borrow_id DESC
    """, (member_id,))

    borrowed = db.cur.fetchall()

    # compute due dates and fines
    borrowed_info = []
    for row in borrowed:
        borrow_id, title, author, borrowed_date, returned_date = row
        due_date = borrowed_date + timedelta(days=LOAN_DAYS)
        returned = returned_date is not None
        fine = 0
        if returned:
            if returned_date > due_date:
                fine = (returned_date - due_date).days * FINE_PER_DAY
        else:
            if date.today() > due_date:
                fine = (date.today() - due_date).days * FINE_PER_DAY
        borrowed_info.append({
            'borrow_id': borrow_id,
            'title': title,
            'author': author,
            'borrowed_date': borrowed_date,
            'due_date': due_date,
            'returned_date': returned_date,
            'returned': returned,
            'fine': fine
        })

    return render_template('user_dashboard.html', name=session.get('name'), borrowed=borrowed_info)


@app.route('/user/borrow/<int:book_id>', methods=['POST'])
def user_borrow(book_id):
    if session.get('role') != 'user':
        return redirect(url_for('login_user'))

    member_id = session.get('member_id')

    # check availability
    db.cur.execute("SELECT quantity FROM books WHERE book_id=%s", (book_id,))
    row = db.cur.fetchone()
    if not row or row[0] <= 0:
        flash('Book not available')
        return redirect(url_for('view_books'))

    db.cur.execute("INSERT INTO borrowed_books(member_id, book_id, borrowed_date, returned_date, quantity) VALUES(%s,%s,%s,%s,%s)",
                (member_id, book_id, date.today(), None, 1))
    db.cur.execute("UPDATE books SET quantity = quantity - 1 WHERE book_id=%s", (book_id,))
    db.conn.commit()
    flash('Book borrowed successfully')
    return redirect(url_for('user_dashboard'))


@app.route('/user/return/<int:borrow_id>', methods=['POST'])
def user_return(borrow_id):
    if session.get('role') != 'user':
        return redirect(url_for('login_user'))

    # find book_id
    db.cur.execute("SELECT book_id, borrowed_date FROM borrowed_books WHERE borrow_id=%s AND member_id=%s", (borrow_id, session.get('member_id')))
    row = db.cur.fetchone()
    if not row:
        flash('Invalid return request')
        return redirect(url_for('user_dashboard'))

    book_id, borrowed_date = row
    returned_date = date.today()
    db.cur.execute("UPDATE borrowed_books SET returned_date=%s WHERE borrow_id=%s", (returned_date, borrow_id))
    db.cur.execute("UPDATE books SET quantity = quantity + 1 WHERE book_id=%s", (book_id,))
    db.conn.commit()
    flash('Book returned successfully')
    return redirect(url_for('user_dashboard'))


# ----------------- LIBRARIAN -----------------
@app.route('/librarian')
def librarian_dashboard():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    # summary counts
    db.cur.execute("SELECT COUNT(*) FROM books")
    books_count = db.cur.fetchone()[0]
    db.cur.execute("SELECT COUNT(*) FROM members")
    members_count = db.cur.fetchone()[0]
    db.cur.execute("SELECT COUNT(*) FROM borrowed_books WHERE returned_date IS NULL")
    borrowed_count = db.cur.fetchone()[0]

    return render_template('librarian_dashboard.html', name=session.get('name'), books_count=books_count, members_count=members_count, borrowed_count=borrowed_count)


@app.route('/librarian/books')
def librarian_books():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    db.cur.execute("SELECT book_id, title, author, quantity FROM books ORDER BY book_id")
    books = db.cur.fetchall()
    return render_template('books.html', books=books, librarian=True)


@app.route('/librarian/add_book', methods=['GET', 'POST'])
def add_book():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        quantity = int(request.form.get('quantity') or 0)

        # check if exists
        db.cur.execute("SELECT book_id FROM books WHERE title=%s AND author=%s", (title, author))
        r = db.cur.fetchone()
        if r:
            db.cur.execute("UPDATE books SET quantity = quantity + %s WHERE book_id=%s", (quantity, r[0]))
        else:
            db.cur.execute("INSERT INTO books(title, author, quantity, available) VALUES(%s,%s,%s,%s)", (title, author, quantity, quantity > 0))
        db.conn.commit()
        flash('Book added/updated successfully')
        return redirect(url_for('librarian_books'))

    return render_template('add_book.html')


@app.route('/librarian/remove_book/<int:book_id>', methods=['POST', 'GET'])
def remove_book(book_id):
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    # accept both POST (form) and GET (link) for convenience
    try:
        db.cur.execute("DELETE FROM books WHERE book_id=%s", (book_id,))
        db.conn.commit()
        flash('Book removed')
    except Exception as e:
        flash('Error removing book: {}'.format(e))
    return redirect(url_for('librarian_books'))


@app.route('/librarian/members')
def librarian_members():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    db.cur.execute("SELECT m.member_id, u.name, u.email, m.due FROM members m JOIN users u ON m.user_id = u.user_id ORDER BY m.member_id")
    members = db.cur.fetchall()
    return render_template('members.html', members=members)


@app.route('/librarian/add_member', methods=['GET', 'POST'])
def add_member():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        # insert user
        db.cur.execute("INSERT INTO users(name, email) VALUES(%s,%s) RETURNING user_id", (name, email))
        user_id = db.cur.fetchone()[0]
        db.cur.execute("INSERT INTO members(user_id) VALUES(%s)", (user_id,))
        db.conn.commit()
        flash('Member added successfully')
        return redirect(url_for('librarian_members'))

    return render_template('add_member.html')


@app.route('/librarian/remove_member/<int:member_id>', methods=['POST', 'GET'])
def remove_member(member_id):
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    # check for borrowed_books references
    db.cur.execute("SELECT COUNT(*) FROM borrowed_books WHERE member_id=%s", (member_id,))
    cnt = db.cur.fetchone()[0]
    if cnt > 0:
        flash('Cannot remove member: there are borrowed book records referencing this member. Return or clear borrowed books first, or use Force Remove.')
        return redirect(url_for('librarian_members'))

    # remove user and member records (simple cascade)
    db.cur.execute("SELECT user_id FROM members WHERE member_id=%s", (member_id,))
    row = db.cur.fetchone()
    if row:
        user_id = row[0]
        try:
            db.cur.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
            db.cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
            db.conn.commit()
            flash('Member removed')
        except Exception as e:
            db.conn.rollback()
            flash('Error removing member: {}'.format(e))
    else:
        flash('Member not found')
    return redirect(url_for('librarian_members'))


@app.route('/librarian/remove_member_force/<int:member_id>', methods=['POST', 'GET'])
def remove_member_force(member_id):
    """Force remove member by deleting borrowed records first, then member and user."""
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    db.cur.execute("SELECT user_id FROM members WHERE member_id=%s", (member_id,))
    row = db.cur.fetchone()
    if not row:
        flash('Member not found')
        return redirect(url_for('librarian_members'))

    user_id = row[0]
    try:
        # delete borrowed records
        db.cur.execute("DELETE FROM borrowed_books WHERE member_id=%s", (member_id,))
        # remove member and user
        db.cur.execute("DELETE FROM members WHERE member_id=%s", (member_id,))
        db.cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        db.conn.commit()
        flash('Member and their borrowed records removed (force)')
    except Exception as e:
        db.conn.rollback()
        flash('Error during force remove: {}'.format(e))
    return redirect(url_for('librarian_members'))


@app.route('/librarian/borrowed')
def librarian_borrowed():
    if session.get('role') != 'librarian':
        return redirect(url_for('login_librarian'))

    db.cur.execute("""
    SELECT b.borrow_id, u.name, u.email, bk.title, b.borrowed_date, b.returned_date
    FROM borrowed_books b
    JOIN members m ON b.member_id = m.member_id
    JOIN users u ON m.user_id = u.user_id
    JOIN books bk ON b.book_id = bk.book_id
    ORDER BY b.borrow_id DESC
    """)
    rows = db.cur.fetchall()
    borrowed_info = []
    for r in rows:
        borrow_id, name, email, title, borrowed_date, returned_date = r
        due_date = borrowed_date + timedelta(days=LOAN_DAYS)
        fine = 0
        if returned_date:
            if returned_date > due_date:
                fine = (returned_date - due_date).days * FINE_PER_DAY
        else:
            if date.today() > due_date:
                fine = (date.today() - due_date).days * FINE_PER_DAY
        borrowed_info.append({'borrow_id': borrow_id, 'name': name, 'email': email, 'title': title, 'borrowed_date': borrowed_date, 'due_date': due_date, 'returned_date': returned_date, 'fine': fine})

    return render_template('borrowed_list.html', borrowed=borrowed_info)


if __name__ == '__main__':
    app.run(debug=True)