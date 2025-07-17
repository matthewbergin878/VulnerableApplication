from flask import Flask, jsonify
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Database setup
DATABASE = 'users.db'

def add_user(conn, name, ssn):
    #manually concatenating values instead of using paramterized queries
    sql = "INSERT INTO users(name, ssn) VALUES('" + name + "','" + ssn + "')"
    cur = conn.cursor()
    cur.executescript(sql) #executescript allows for multiple sql statements to be run at once
    conn.commit()
def select_user(conn, name):
    #manually concatenating values instead of using paramterized queries
    sql = "SELECT * FROM users WHERE name='" + name + "'"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

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

@app.route('/user/<username>', methods=['GET'])
def fetch_user(username):
    conn = get_db_connection()
    users = select_user(conn, username)
    conn.close()

    user_list = [dict(user) for user in users]
    return jsonify(user_list)

@app.route('/user/<username>/<ssn>', methods=['POST'])
def post_user(username, ssn):
    conn = get_db_connection()
    add_user(conn, username, ssn)
    conn.close()



# Main entry point
if __name__ == '__main__':
    # Create the database and add sample data if it doesn't exist
    conn = sqlite3.connect(DATABASE)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        name text NOT NULL, 
        ssn text
    );""")
    conn.execute('INSERT INTO users (name, ssn) VALUES (?, ?)', ('JohnDoe', '123456789'))
    conn.execute('INSERT INTO users (name, ssn) VALUES (?, ?)', ('JaneSmith', '987654321'))
    conn.commit()
    conn.close()
    
    # Run the Flask app
    app.run(debug=True)
