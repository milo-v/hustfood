from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .db import connection

views = Blueprint('views', __name__)


@views.route('/', methods=["GET", "POST"])
def home():
    if request.method == 'POST':
        query = request.form['q']
        if not query:
            return render_template('index.html')

        return redirect(url_for("views.search_result", query=query))
    else:
        return render_template('index.html')


@views.route('/carsales')
def carsales():
    cars = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu_item")
    for row in cursor.fetchall():
        cars.append({"id": row[0], "name": row[1]})

    conn.close()
    return render_template('carsales.html', cars=cars)


@views.route("/search-result?q=<query>")
def search_result(query):
    user_input = '%' + query + '%'
    print(query)
    print(user_input)
    restaurants = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, restaurant_name, restaurant_address
        FROM restaurant
        WHERE restaurant_name LIKE ?
        OR id IN(
            SELECT restaurant_id FROM menu_item
            WHERE item_name LIKE ?
            OR category_name LIKE ?
        )
        ''',
        user_input,
        user_input,
        user_input
    )
    for row in cursor.fetchall():
        restaurants.append({"id": row[0], "name": row[1], "address": row[2]})

    conn.close()
    print(restaurants)
    return render_template('search_result.html', restaurants=restaurants, query=query)


@views.route('/restaurant?id=<rid>')
def restaurant(rid):
    print(session)
    restaurant = []
    items = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT restaurant_name, restaurant_address FROM restaurant WHERE id = ?', rid)
    for row in cursor.fetchall():
        restaurant.append({"name": row[0], "address": row[1]})

    cursor.execute(
        '''
        SELECT id, item_name, price
        FROM menu_item
        WHERE restaurant_id = ?
        ''',
        rid
    )
    for row in cursor.fetchall():
        items.append({"id": row[0], "name": row[1], "price": row[2]})

    conn.close()
    return render_template('restaurant.html', restaurant=restaurant[0], items=items)


@views.route('/user')
def user():
    if "id" in session:
        print(session["id"])
        data = []
        conn = connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, customer_name, phone_number, email
            FROM customer
            WHERE id = ?
            ''',
            session["id"]
        )
        for row in cursor.fetchall():
            data.append({"id": row[0], "name": row[1],
                        "phone": row[2], "email": row[3]})
            print(data)

    else:
        return redirect(url_for('auth.login'))

    return render_template('user.html', data=data)


@views.route('/payment?uid=<uid>', methods=["GET", "POST"])
def payment(uid):
    data = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT payment_type FROM customer_payment
        WHERE customer_id = ?
        ''',
        uid
    )
    for row in cursor.fetchall():
        data.append({"method": row[0]})

    options = ['MOMO','ZALOPAY', 'VTMONEY', 'SHOPEEPAY']
    for option in options:
        for dat in data:
            if option == dat["method"]:
                options.remove(option)


    if request.method == "POST":
        select = request.form.get('payment-method')
        cursor.execute(
            '''
            INSERT INTO customer_payment(customer_id, payment_type)
            VALUES(?, ?)
            ''',
            uid,
            select
        )
        conn.commit()
        conn.close()
        return render_template('payment.html', payments=data, options=options)
    
    conn.close()

    return render_template('payment.html', payments=data, options=options)


@views.route('/base')
def base():
    return render_template('base.html')

@views.route('/cart?pid=<pid>')
def cart(pid):
    print(session)
    items = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT item_name, item_price, quantity, in_order.price
        FROM menu_item FULL JOIN in_order ON menu_item.id = menu_item_id
        WHERE placed_order_id = ?
        ''',
        pid
    )
    for row in cursor.fetchall():
        items.append({"name": row[0], "price": row[1], "quantity": row[2], "total": row[3]})

    final = []
    cursor.execute(
        '''
        SELECT final_price, restaurant_id FROM placed_order
        WHERE id = ?
        ''',
        pid
    )
    for row in cursor.fetchall():
        final.append({"value": row[0], "rid": row[1]})

    print(final)

    payments = []
    cursor.execute(
        '''
        SELECT payment_type FROM customer_payment
        WHERE customer_id = ?
        ''',
        session["id"]
    )
    for row in cursor.fetchall():
        payments.append({"type": row[0]})

    conn.close()
    return render_template('cart.html', items = items, final=final, payments=payments)

@views.route('/item?id=<id>', methods=["GET", "POST"])
def item(id):
    print(session)
    data = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, restaurant_id, item_name, price
        FROM menu_item
        WHERE id = ?
        ''',
        id
    )
    for row in cursor.fetchall():
        data.append({"id": row[0], "rid": row[1], "name": row[2], "price": row[3]})

    if request.method == "POST":
        amount = int(request.form.get('amount'))
        placed_order_id = []
        if not "cart" in session:
            cursor.execute(
                '''
                INSERT INTO placed_order(customer_id, restaurant_id, price, final_price, delivered)
                VALUES(?, ?, 0, 0, 0)
                ''',
                session["id"],
                data[0]["rid"]
            )
            conn.commit()
            cursor.execute(
                '''
                SELECT TOP 1 id
                FROM placed_order
                ORDER BY id DESC
                '''
            )
            for row in cursor.fetchall():
                placed_order_id.append({"value": row[0]})

            session["cart"] = placed_order_id[0]["value"]

        cursor.execute(
            '''
            SELECT TOP 1 id
            FROM placed_order
            ORDER BY id DESC
            '''
        )
        for row in cursor.fetchall():
            placed_order_id.append({"value": row[0]})

        cursor.execute(
            '''
            INSERT INTO order_status(placed_order_id, time_order, order_status, payment_status)
            VALUES(?, GETDATE(), 'ADDED_TO_CART', 'NOT_CONFIRMED')
            ''',
            placed_order_id[0]["value"]
        )
        conn.commit()
        conn.execute(
            '''
            INSERT INTO in_order(placed_order_id, menu_item_id, quantity, offer_id, item_price, price)
            VALUES(?, ?, ?, 1, ?, ?)
            ''',
            placed_order_id[0]["value"],
            data[0]["id"],
            amount,
            data[0]["price"],
            data[0]["price"] * amount
        )

        conn.commit()
        cursor.execute(
            '''
            UPDATE placed_order
            SET price = (
                SELECT SUM(price) FROM in_order
                WHERE placed_order_id = ?
            ),
            final_price = (
                SELECT SUM(price) FROM in_order
                WHERE placed_order_id = ?
            )
            WHERE id = ?
            ''',
            placed_order_id[0]["value"],
            placed_order_id[0]["value"],
            placed_order_id[0]["value"]
        )

        conn.commit()
        print(placed_order_id[0]["value"])
        conn.close()
        return redirect(url_for('views.cart', pid = placed_order_id[0]["value"]))

    conn.close()
    return render_template('item.html', item=data)