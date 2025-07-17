from flask import Flask, jsonify
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Database setup
DATABASE = 'users.db'

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return conn

# Route to fetch user data
@app.route('/users', methods=['GET'])
def fetch_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    # Convert rows to a list of dictionaries
    user_list = [dict(user) for user in users]
    return jsonify(user_list)

# Main entry point
if __name__ == '__main__':
    # Create the database and add sample data if it doesn't exist
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', ('John Doe', 'john@example.com'))
    conn.execute('INSERT INTO users (name, email) VALUES (?, ?)', ('Jane Smith', 'jane@example.com'))
    conn.commit()
    conn.close()
    
    # Run the Flask app
    app.run(debug=True)
