from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .db import connection


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if "id" in session:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        print(email)
        password = request.form.get('password1')
        conn = connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, email, password FROM customer
            WHERE email = ?
            ''',
            email
        )
        data = cursor.fetchall()
        print(data)
        if data:
            if password == data[0][2]:
                session["id"] = data[0][0]
                print(session)
                flash('Login successful!', category='info')
                conn.close()
                return redirect(url_for('views.home'))
            else:
                flash('Wrong password!')

        if not data:
            flash('Wrong email!', category='warning')

        conn.close()

    return render_template('login.html')


@auth.route('/logout')
def logout():
    session.pop("id", None)
    session.pop("cart", None)
    return redirect(url_for('views.home'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if "id" in session:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        print(email)
        name = request.form.get('name')
        phone = request.form.get('phone')
        password1 = request.form.get('password1')
        print(password1)
        password2 = request.form.get('password2')

        conn = connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT email from customer
            '''
        )

        for row in cursor.fetchall():
            if email == row[0]:
                flash('Email already exist!', category='warning')
                conn.close()
                return render_template('signup.html')


        print(email)
        if len(password1) < 8:
            flash('Password must contain at least 8 characters!', category='error')
        elif password1 != password2:
            flash('Password confirmation does not match!', category='error')
        else:
            cursor.execute(
                '''
                INSERT INTO customer(customer_name, phone_number, email, password)
                VALUES(?, ?, ?, ?)
                INSERT INTO customer_payment(customer_id)
                SELECT id FROM customer WHERE email = ?
                ''',
                name,
                phone,
                email,
                password1,
                email
            )

            conn.commit()
            conn.close()
            flash('Signed up successfully!')
            return redirect(url_for('views.home'))

    return render_template('signup.html')
