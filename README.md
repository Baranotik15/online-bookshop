# online-bookshop
![Database schema](static/table_schema.png)

# 📚 Bookshop API

REST API for an online book store built with Django REST Framework.

## 📖 Books

- `GET /api/books/` — list all books
- `GET /api/books/{id}/` — get book details (includes genres, author, stock)
- `POST /api/books/` — create a book
- `PUT /api/books/{id}/` — replace a book
- `PATCH /api/books/{id}/` — partial update
- `DELETE /api/books/{id}/` — delete a book

## 👤 Authors

- `GET /api/authors/` — list all authors
- `GET /api/authors/{id}/` — get author details
- `POST /api/authors/` — create an author
- `PUT /api/authors/{id}/` — replace an author
- `PATCH /api/authors/{id}/` — partial update
- `DELETE /api/authors/{id}/` — delete an author

## 🏷️ Genres

- `GET /api/genres/` — list all genres
- `GET /api/genres/{id}/` — get genre details
- `POST /api/genres/` — create a genre `{ "name": "Роман" }`
- `PUT /api/genres/{id}/` — replace a genre
- `PATCH /api/genres/{id}/` — partial update
- `DELETE /api/genres/{id}/` — delete a genre

When creating or updating a book, pass genre IDs via `genre_ids`:
```json
{ "title": "Кобзар", "author_id": 3, "price": "150.00", "genre_ids": [1, 4, 7] }
```

## 📦 Orders

Requires authentication.

- `GET /api/orders/` — list current user's orders
- `GET /api/orders/{id}/` — get order details
- `POST /api/orders/` — create a new order
- `PUT /api/orders/{id}/` — update order status
- `DELETE /api/orders/{id}/` — cancel/delete order

## 🛒 Cart

Single endpoint, requires authentication. All actions use `/api/cart/`.

- `GET /api/cart/` — get current user's cart (items + `total_price`)
- `POST /api/cart/` — add item `{ "book_id": 1, "quantity": 1 }` → returns `{ total_items, total_price }`
- `PATCH /api/cart/` — update quantity `{ "item_id": 5, "quantity": 3 }` → returns `{ subtotal, total }`
- `DELETE /api/cart/` — remove item `{ "item_id": 5 }` → returns `{ total_items, total_price }`

## 🔧 Admin panel

Available at `/admin/`. Built with [django-unfold](https://github.com/unfoldadmin/django-unfold).

**Access levels:**
| Role | Access |
|------|--------|
| Superuser | Full access to everything |
| Staff + group | Can edit models assigned to their group |
| Staff (no group) | Read-only |

**Groups** (create with `python manage.py create_groups`):
| Group | Models |
|-------|--------|
| Edit Books | Book, Author, Genre |
| Edit Orders | Order, OrderItem |
| Edit Users | User |

> Cart is read-only for everyone in the admin panel.

---

## 💻 Local development

**Requirements:** Python 3.12+

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/online-bookshop.git
cd online-bookshop
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Create `.env`:**
```bash
cp env-sample .env
# fill in SECRET_KEY and Stripe keys
```

**5. Apply migrations:**
```bash
python manage.py migrate
```

**6. Create a superuser:**
```bash
python manage.py createsuperuser
```

**7. Create admin groups (once):**
```bash
python manage.py create_groups
```

**8. Seed the database (optional):**
```bash
python fixture.py
```

**9. Run the server:**
```bash
python manage.py runserver
```

The app will be available at **http://localhost:8000**

---

## 🚀 Deployment (EC2 or any Linux host)

**Requirements:** Ubuntu server, Docker, Docker Compose, open port 8000 in firewall/Security Group.

**1. Install Docker:**
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER && newgrp docker
```

**2. Clone the repository:**
```bash
git clone https://github.com/your-username/online-bookshop.git
cd online-bookshop
```

**3. Create and fill `.env`:**
```bash
cp env-sample .env
nano .env
```

Set the following values:
```
SECRET_KEY=           # generate: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DEBUG=false
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**4. Add your domain or IP to `ALLOWED_HOSTS` in `proj/settings.py`:**
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com', 'your-ec2-ip']
```

**5. Build and start:**
```bash
docker compose up --build -d
```

The app will be available at **http://your-domain.com:8000**

**6. Create a superuser:**
```bash
docker exec -it online-bookshop-web-1 python manage.py createsuperuser
```

**7. Create admin groups (once):**
```bash
docker exec online-bookshop-web-1 python manage.py create_groups
```

**8. Seed the database (optional):**
```bash
docker exec online-bookshop-web-1 python fixture.py
```

**Useful commands:**
```bash
docker compose logs -f          # view logs
docker compose down             # stop (data preserved)
docker compose down -v          # stop and delete all data
docker compose up -d            # start after server reboot
```

---

## 💳 Stripe (test payments)

Uses Stripe Sandbox for local development.

**Setup `.env`:**
```
STRIPE_PUBLIC_KEY=pk_test_...   # Publishable key from Stripe Dashboard → Developers → API keys
STRIPE_SECRET_KEY=sk_test_...   # Secret key from Stripe Dashboard → Developers → API keys
STRIPE_WEBHOOK_SECRET=whsec_... # Generated by stripe listen (see below)
```

**Start webhook listener:**
```bash
stripe listen --forward-to localhost:8000/orders/webhook/
```

The command prints:
```
> Ready! Your webhook signing secret is whsec_abc123...
```
Copy `whsec_abc123...` into `STRIPE_WEBHOOK_SECRET` in `.env`, then restart the Django server. Keep this terminal open while testing.

**Test card:**

| Field | Value |
|-------|-------|
| Card number | `4242 4242 4242 4242` |
| Expiry | any future date, e.g. `12/34` |
| CVC | any 3 digits, e.g. `123` |
| Name | anything |

After payment the order status changes from `pending` → `paid` via webhook.
