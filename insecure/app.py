from flask import Flask, jsonify, request, render_template
import sqlite3
import logging

# Initialize Flask app
app = Flask(__name__, template_folder='templates')


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


@app.route('/products', methods=['GET'])
def fetch_products():
    #get all products from the db and return them as is
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()

    product_list = [dict(product) for product in products]

    return jsonify(product_list)

@app.route('/product/<int:product_id>', methods=['GET'])
def fetch_product(product_id):
    #get a specific product from the db and return it as is
    conn = get_db_connection()
    #sql injection vulnerability
    product = conn.execute(f'SELECT * FROM products WHERE id = {product_id}').fetchone()
    conn.close()

    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    
    #stored xss vulnerability
    return jsonify(dict(product))

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
        if product['stock'] <= 0:
            return jsonify({'error': 'Product is out of stock'}), 400

        # Reduce stock by 1
        new_stock = product['stock'] - 1
        conn.execute(f'UPDATE products SET stock = {new_stock} WHERE id = {product_id}')
        conn.commit()

        # Prepare the response
        response = jsonify({
            'message': 'Purchase successful',
            'product': {
                'id': product['id'],
                'product_name': product['product_name'],
                'description': product['description'],
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
    conn.commit()
    conn.close()

    # Run the app
    app.run(debug=True)
