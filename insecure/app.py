from flask import Flask, jsonify, request, render_template
import sqlite3
import logging

#Initialize app
app = Flask(__name__, template_folder='templates')


#insecure session manager
session = {}


# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database setup
DATABASE = 'storefront.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

@app.route('/')
def serve_frontend():
    # Serve the updated storefront HTML file
    return render_template('storefront.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        confirm_password = request.json.get('confirm_password')

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already exists'}), 400
        finally:
            conn.close()

        return jsonify({'message': 'Registration successful'}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username,password)).fetchone()
        conn.close()

        if user is None:
            return jsonify({'error': 'Invalid username or password'}), 401
            

        # Set the session for the logged-in user
        session['user_id'] = user['id']
        session['username'] = user['username']

        # Return a redirect response to the home page
        return jsonify({'message': 'Login successful', 'redirect_url': '/'}), 200



@app.route('/products', methods=['GET'])
def fetch_products():
    #get all products from the db and return them as is
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    product_list = [dict(product) for product in products]

    return jsonify(product_list)

#not specifying integer
@app.route('/product/<product_id>', methods=['GET'])
def fetch_product(product_id):
    #get a specific product from the db and return it as is
    conn = get_db_connection()
    try:
        #sql injection vulnerability
        query = f"SELECT * FROM products WHERE id = '{product_id}'"
        products = conn.execute(query).fetchall()

        #check if any products were found
        if not products:
            return jsonify({'error': 'No product found'}), 404

        # stored xss vulnerability
        product_list = [dict(product) for product in products]
        return jsonify(product_list)

    except Exception as e:
        app.logger.error(f"Error fetching product: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()

@app.route('/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    #update a product in the database with user input
    updated_product = request.get_json()
    product_name = updated_product.get('product_name')
    description = updated_product.get('description')
    price = updated_product.get('price')
    stock = updated_product.get('stock')

    conn = get_db_connection()
    #sql injection vulnerability
    conn.execute(
        f"UPDATE products SET product_name = '{product_name}', description = '{description}', price = {price}, stock = {stock} WHERE id = {product_id}"
    )
    conn.commit()
    conn.close()

    response = jsonify(updated_product)
    response.status_code = 200

    return response

@app.route('/purchase/<int:product_id>', methods=['POST'])
def purchase_product(product_id):
    conn = get_db_connection()
    
    try:

        product = fetch_product(product_id).get_json()

        request_data = request.get_json()
        if not request_data or 'price' not in request_data:
            return jsonify({'error': 'Price is required in the request body'}), 400
        #allows user to manipulate the price
        provided_price = request_data['price']
        if product is None:
            return jsonify({'error': 'Product not found'}), 404


        # Check if stock is available
        if product[0]['stock'] <= 0:
            return jsonify({'error': 'Product is out of stock'}), 400


        # Reduce stock by 1
        new_stock = product[0]['stock'] - 1
        conn.execute(f'UPDATE products SET stock = {new_stock} WHERE id = {product_id}')
        conn.commit()

        # Prepare the response
        response = jsonify({
            'message': 'Purchase successful',
            'product': {
                'id': product[0]['id'],
                'product_name': product[0]['product_name'],
                'description': product[0]['description'],
                'price': provided_price,
                'stock': new_stock
            }
        })
        response.status_code = 200

        return response

    except Exception as e:
        app.logger.error(f"Error in purchase_product: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        conn.close()


if __name__ == '__main__':
    # Create the database and add sample data if it doesn't exist
    conn = sqlite3.connect(DATABASE)
    conn.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY, 
        product_name TEXT NOT NULL, 
        description TEXT, 
        price REAL NOT NULL, 
        stock INTEGER NOT NULL
    );""")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT NOT NULL, 
        password TEXT NOT NULL
    );""")
    conn.commit()
    conn.close()

    # Run the app
    app.run(debug=True)
