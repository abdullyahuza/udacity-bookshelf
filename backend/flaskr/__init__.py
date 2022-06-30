import os
from flask import Flask, request, abort, jsonify, render_template, url_for, json
from flask_sqlalchemy import SQLAlchemy  # , or_
from flask_cors import CORS
import random

from models import setup_db, Book, db

BOOKS_PER_SHELF = 8

def paginate_books(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * BOOKS_PER_SHELF
    end = start + BOOKS_PER_SHELF

    books = [book.format() for book in selection]
    current_books = books[start:end]

    return current_books


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS,PATCH"
        )
        return response


    @app.route('/books', methods=['GET'])
    def index():

        books = Book.query.order_by(db.desc(Book.id)).all()
        formatted_books = paginate_books(request, books)
        
        if len(formatted_books) == 0:
            abort(404)            

        return jsonify({
            "success": True,
            "books": formatted_books,
            "total_books": len(formatted_books)
        })


    @app.route('/books/<int:book_id>', methods=['PATCH'])
    def update_book_rating(book_id):
        try:
            book = Book.query.get(book_id)
            
            if book is None:
                abort(404)
            
            if 'rating' in request.get_json():
                book.rating = request.get_json()['rating']
            book.update()
            
            return jsonify({
                "success": True,
            })
        except():
            abort(400)


    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        try:
            book = Book.query.get(book_id)

            if book is None:
                abort(404)

            book.delete()
            formatted_books = paginate_books(request, Book.query.order_by(Book.id).all())
            return jsonify({
                'success': True,
                'deleted': book_id,
                'books': formatted_books,
                'total_books': len(Book.query.all())
            })            
        except:
            abort(422)


    @app.route('/books', methods=['POST'])
    def add_book():
        new_book = request.get_json()
        try:
            book = Book(new_book['title'], new_book['author'], new_book['rating'])
            book.insert()
            books = Book.query.order_by(db.desc(Book.id)).all()
            formatted_books = [book.format() for book in books]
            return jsonify({
                "success": True,
                "created": book.id,
                "books": formatted_books,
                "total_books": len(formatted_books)
            })
        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return({
            "success": False,
            "message": "resource not found",
            "error": 404
        }), 404

    @app.errorhandler(422)
    def unprocessible(error):
        return({
            "success": False,
            "message": "unprocessable",
            "error": 422
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return({
            "success": False,
            "message": "bad request",
            "error": 400
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 405, "message": "method not allowed"}),
            405
        )
    return app

# curl http://127.0.0.1:5000/books/8 -X PATCH -H "Content-Type: application/json" -d '{"rating":"1"}'
# curl -X DELETE http://127.0.0.1:5000/books/8 