import os
from flask import Flask, abort, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask_cors import CORS


load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://127.0.0.1:5500","http://127.0.0.1:5501","http://127.0.0.1:5501/index.html","https://library-front-end-50h2.onrender.com"]}})


@app.route('/', methods=['GET',"POST"])
def show_books():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT book_id AS id, title, author, published_year, image_url, available FROM books;')
    books = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(books)

@app.route('/<int:index>', methods=['DELETE'])
def delete_book(index):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Execute the DELETE SQL command
        cur.execute("DELETE FROM books WHERE book_id = %s RETURNING *;", (index,))
        deleted_book = cur.fetchone()
        
        # Check if the book was found and deleted
        if deleted_book is None:
            cur.close()
            abort(404, description=f"Book with id {index} not found.")
        
        # Commit the transaction
        conn.commit()
        cur.close()
        
        # Return a success message
        return jsonify({"message": f"Book with id {index} deleted successfully."}), 200

    except Exception as e:
        conn.rollback()  # Roll back the transaction on error
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
