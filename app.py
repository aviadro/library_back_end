import os
from flask import Flask, abort, jsonify, request
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


@app.route('/', methods=['GET', 'POST'])
def show_books():
    if request.method == 'GET':
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT book_id AS id, title, author, published_year, image_url, available FROM books;')
        books = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(books)
    
    elif request.method == 'POST':
        new_book = request.get_json()
        title = new_book['title']
        author = new_book['author']
        published_year = new_book['published_year']
        image_url = new_book['image_url']
        available = True  # Set default value for available
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO books (title, author, published_year, image_url, available) VALUES (%s, %s, %s, %s, %s) RETURNING book_id, title, author, published_year, image_url, available',
            (title, author, published_year, image_url, available)
        )
        new_book_record = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(new_book_record), 201



@app.route('/<int:index>', methods=['DELETE', 'PUT'])
def modify_book(index):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if request.method == 'DELETE':
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
        
        elif request.method == 'PUT':
            # Get the data for the update
            updated_book = request.get_json()
            title = updated_book.get('title')
            author = updated_book.get('author')
            published_year = updated_book.get('published_year')
            image_url = updated_book.get('image_url')
            available = updated_book.get('available')
            
            # Execute the UPDATE SQL command
            cur.execute(
                '''
                UPDATE books
                SET title = %s, author = %s, published_year = %s, image_url = %s, available = %s
                WHERE book_id = %s RETURNING *;
                ''',
                (title, author, published_year, image_url, available, index)
            )
            updated_book_data = cur.fetchone()

            # Check if the book was found and updated
            if updated_book_data is None:
                cur.close()
                abort(404, description=f"Book with id {index} not found.")
            
            # Commit the transaction
            conn.commit()
            cur.close()

            # Return a success message with the updated book data
            return jsonify({"message": f"Book with id {index} updated successfully.", "book": updated_book_data}), 200

    except Exception as e:
        conn.rollback()  # Roll back the transaction on error
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
