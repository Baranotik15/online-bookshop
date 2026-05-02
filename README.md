# online-bookshop
![Database schema](static/table_schema.png)
# 📚 Bookshop API

REST API for an online book store built with Django REST Framework.

## 📖 Books

- `GET /books/` — list all books (short info)
- `GET /books/{id}/` — get book details
- `POST /books/` — create a new book
- `PUT /books/{id}/` — update a book
- `DELETE /books/{id}/` — delete a book

## 👤 Authors

- `GET /authors/` — list all authors
- `GET /authors/{id}/` — get author details
- `POST /authors/` — create an author
- `PUT /authors/{id}/` — update an author
- `DELETE /authors/{id}/` — delete an author

## 📦 Orders

- `GET /orders/` — list user orders
- `GET /orders/{id}/` — get order details
- `POST /orders/` — create a new order
- `PUT /orders/{id}/` — update order status
- `DELETE /orders/{id}/` — cancel/delete order
