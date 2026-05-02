# online-bookshop
![Database schema](static/table_schema.png)
# 📚 Bookshop API

REST API for an online book store built with Django REST Framework.

## 📖 Books

- `GET /api/books/` — list all books (short info)
- `GET /api/books/{id}/` — get book details
- `POST /api/books/` — create a new book
- `PUT /api/books/{id}/` — update a book
- `DELETE /api/books/{id}/` — delete a book

## 👤 Authors

- `GET /api/authors/` — list all authors
- `GET /api/authors/{id}/` — get author details
- `POST /api/authors/` — create an author
- `PUT /api/authors/{id}/` — update an author
- `DELETE /api/authors/{id}/` — delete an author

## 📦 Orders

- `GET /api/orders/` — list user orders
- `GET /api/orders/{id}/` — get order details
- `POST /api/orders/` — create a new order
- `PUT /api/orders/{id}/` — update order status
- `DELETE /api/orders/{id}/` — cancel/delete order
