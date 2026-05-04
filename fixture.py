import asyncio
import os
import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from books.models import Author, Book, Genre
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem

User = get_user_model()

# ─── Data pools ───────────────────────────────────────────────

FIRST_NAMES = [
    "Іван", "Олена", "Микола", "Марія", "Андрій", "Тетяна", "Сергій", "Наталія",
    "Олексій", "Юлія", "Василь", "Оксана", "Дмитро", "Ірина", "Максим", "Людмила",
    "Павло", "Галина", "Роман", "Вікторія", "Тарас", "Христина", "Богдан", "Ліна",
    "Yaroslav", "Sofia", "Mykhailo", "Anna", "Denys", "Khrystyna",
]

LAST_NAMES = [
    "Шевченко", "Коваленко", "Бондаренко", "Ткаченко", "Кравченко", "Іваненко",
    "Мельник", "Савченко", "Марченко", "Поліщук", "Гончаренко", "Тимченко",
    "Романенко", "Павленко", "Олійник", "Литвиненко", "Харченко", "Даниленко",
    "Лисенко", "Захаренко", "Moroz", "Kovalchuk", "Petrenko", "Sydorenko",
    "Zinchenko", "Rudenko", "Horobets", "Karpenko", "Sereda", "Hrytsenko",
]

BOOKS_DATA = [
    {"title": "Хоробний новий світ",       "first_name": "Олдос",         "last_name": "Гакслі",          "image": "01.jpg"},
    {"title": "Кайдашева сім'я",            "first_name": "Іван",          "last_name": "Нечуй-Левицький", "image": "02.jpg"},
    {"title": "Собор Паризької Богоматері", "first_name": "Віктор",        "last_name": "Гюго",            "image": "03.jpg"},
    {"title": "Подорож до центру Землі",    "first_name": "Жюль",          "last_name": "Верн",            "image": "04.jpg"},
    {"title": "Холодний яр",                "first_name": "Юрій",          "last_name": "Горліс-Горський", "image": "05.jpg"},
    {"title": "Прощавай, зброє!",           "first_name": "Ернест",        "last_name": "Хемінгуей",       "image": "06.jpg"},
    {"title": "Маленький принц",            "first_name": "Антуан де",     "last_name": "Сент-Екзюпері",   "image": "07.jpg"},
    {"title": "Гаррі Поттер і філософський камінь", "first_name": "Джоан", "last_name": "Роулінг",         "image": "08.jpg"},
    {"title": "Код да Вінчі",               "first_name": "Ден",           "last_name": "Браун",           "image": "09.jpg"},
    {"title": "Джерело",                    "first_name": "Ден",           "last_name": "Браун",           "image": "10.jpg"},
    {"title": "Хранителі персня",           "first_name": "Джон",          "last_name": "Толкін",          "image": "11.jpg"},
    {"title": "Гобіт",                      "first_name": "Джон",          "last_name": "Толкін",          "image": "12.jpg"},
    {"title": "Кривава меридіана",          "first_name": "Кормак",        "last_name": "Маккарті",        "image": "13.jpg"},
    {"title": "Великий Гетсбі",             "first_name": "Френсіс Скотт", "last_name": "Фіцджеральд",     "image": "14.jpg"},
    {"title": "Убити пересмішника",         "first_name": "Гарпер",        "last_name": "Лі",              "image": "15.jpg"},
    {"title": "П'ять мов любові",           "first_name": "Гері",          "last_name": "Чепмен",          "image": "16.jpg"},
    {"title": "Гра Ендера",                 "first_name": "Орсон Скотт",   "last_name": "Кард",            "image": "17.jpg"},
    {"title": "Записки з підпілля",         "first_name": "Федір",         "last_name": "Достоєвський",    "image": "18.jpg"},
    {"title": "Мертві душі",                "first_name": "Микола",        "last_name": "Гоголь",          "image": "19.jpg"},
    {"title": "Принц і жебрак",             "first_name": "Марк",          "last_name": "Твен",            "image": "20.jpg"},
    {"title": "Нейромант",                  "first_name": "Вільям",        "last_name": "Гібсон",          "image": "21.jpg"},
]

DESCRIPTIONS = [
    "Захоплюючий роман про долю людини у вирі історичних подій.",
    "Глибокий психологічний твір з яскравими образами та живою мовою.",
    "Класичний твір української літератури, обов'язковий для читання.",
    "Поетична проза про красу рідного краю та силу людського духу.",
    "Драматична повість, що змушує переосмислити цінності буття.",
    "Пригодницький роман з несподіваними поворотами сюжету.",
    "Філософський твір про пошук сенсу життя та людської гідності.",
    "Лірична оповідь про кохання, вірність та самопожертву.",
    "Епічна сага про боротьбу народу за свободу та незалежність.",
    "Сатиричний твір, що висміює людські вади та суспільні вади.",
]

GENRES = [
    "Роман", "Повість", "Поезія", "Драма", "Детектив",
    "Фантастика", "Пригоди", "Історичний", "Лірика", "Сатира",
]

STATUSES = ['pending', 'paid', 'shipped', 'cancelled']

HASHED_PW = make_password('password123')


def rand_date(start_year=1920, end_year=1990):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


# ─── Async functions ──────────────────────────────────────────

async def clear_all():
    print("Очищення таблиць...")
    await CartItem.objects.all().adelete()
    await Cart.objects.all().adelete()
    await OrderItem.objects.all().adelete()
    await Order.objects.all().adelete()
    await Book.objects.all().adelete()
    await Author.objects.all().adelete()
    await Genre.objects.all().adelete()
    await User.objects.filter(is_superuser=False).adelete()
    print("Готово.\n")


async def seed_genres():
    print("Створення жанрів...")
    await Genre.objects.abulk_create([Genre(name=g) for g in GENRES])
    result = [g async for g in Genre.objects.all()]
    print(f"  + {len(result)} жанрів")
    return result


async def seed_users(n=50):
    print(f"Створення {n} користувачів...")
    users = [
        User(
            username=f"user{i}",
            email=f"user{i}@bookshop.ua",
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            password=HASHED_PW,
        )
        for i in range(1, n + 1)
    ]
    await User.objects.abulk_create(users)
    result = [u async for u in User.objects.filter(is_superuser=False)]
    print(f"  + {n} користувачів")
    return result


async def seed_authors(n=50):
    print(f"Створення {n} авторів...")
    authors, used = [], set()
    while len(authors) < n:
        first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        if (first, last) in used:
            continue
        used.add((first, last))
        birth = rand_date(1850, 1970)
        death = rand_date(birth.year + 30, min(birth.year + 80, 2020)) if random.random() > 0.4 else None
        authors.append(Author(first_name=first, last_name=last, birth_date=birth, death_date=death))
    await Author.objects.abulk_create(authors)
    result = [a async for a in Author.objects.all()]
    print(f"  + {n} авторів")
    return result


IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images_for_fixture')


def fetch_cover(book, image_filename):
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        return
    try:
        path = os.path.join(IMAGES_DIR, image_filename)
        with open(path, 'rb') as f:
            book.image.save(image_filename, ContentFile(f.read()), save=True)
    except Exception:
        pass


async def seed_books(genres):
    n = len(BOOKS_DATA)
    print(f"Створення {n} книг...")

    books = []
    for data in BOOKS_DATA:
        author, _ = await Author.objects.aget_or_create(
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        books.append(Book(
            title=data['title'],
            description=random.choice(DESCRIPTIONS),
            price=Decimal(str(round(random.uniform(80, 650), 2))),
            author=author,
            stock=random.randint(1, 100),
        ))

    await Book.objects.abulk_create(books)
    result = [b async for b in Book.objects.all()]
    for book in result:
        await book.genres.aset(random.sample(genres, random.randint(1, min(4, len(genres)))))

    print("  Завантаження обкладинок...")
    book_map = {b.title: b for b in result}
    for data in BOOKS_DATA:
        book = book_map.get(data['title'])
        if book:
            fetch_cover(book, data['image'])

    covers = sum(1 for b in result if b.image)
    print(f"  + {n} книг, {covers} обкладинок завантажено")
    return result


async def seed_orders(users, books, n=50):
    print(f"Створення {n} замовлень...")
    orders = [
        Order(user=random.choice(users), total_price=Decimal("0.00"), status=random.choice(STATUSES))
        for _ in range(n)
    ]
    await Order.objects.abulk_create(orders)
    all_orders = [o async for o in Order.objects.all()]

    items = []
    for order in all_orders:
        selected = random.sample(books, random.randint(1, 4))
        total = Decimal("0.00")
        for book in selected:
            qty = random.randint(1, 3)
            items.append(OrderItem(order=order, book=book, quantity=qty, price=book.price))
            total += book.price * qty
        order.total_price = total

    await OrderItem.objects.abulk_create(items)
    await Order.objects.abulk_update(all_orders, ['total_price'])
    print(f"  + {n} замовлень, {len(items)} позицій")


async def seed_carts(users, books, n=50):
    print(f"Створення {n} кошиків...")
    carts = [Cart(user=random.choice(users)) for _ in range(n)]
    await Cart.objects.abulk_create(carts)
    all_carts = [c async for c in Cart.objects.all()]

    items = []
    for cart in all_carts:
        selected = random.sample(books, random.randint(1, 5))
        for book in selected:
            items.append(CartItem(cart=cart, book=book, quantity=random.randint(1, 3)))

    await CartItem.objects.abulk_create(items)
    print(f"  + {n} кошиків, {len(items)} позицій")


async def main():
    await clear_all()

    genres = await seed_genres()
    users = await seed_users(50)

    books = await seed_books(genres)

    # orders і carts незалежні — паралельно
    await asyncio.gather(seed_orders(users, books, 50), seed_carts(users, books, 50))

    print("\n" + "=" * 40)
    print("БД заповнена успішно!")
    print(f"  Users:      {await User.objects.filter(is_superuser=False).acount()}")
    print(f"  Authors:    {await Author.objects.acount()}")
    print(f"  Books:      {await Book.objects.acount()} ({len(BOOKS_DATA)} унікальних)")
    print(f"  Orders:     {await Order.objects.acount()}")
    print(f"  OrderItems: {await OrderItem.objects.acount()}")
    print(f"  Carts:      {await Cart.objects.acount()}")
    print(f"  Genres:     {await Genre.objects.acount()}")
    print(f"  CartItems:  {await CartItem.objects.acount()}")


if __name__ == '__main__':
    asyncio.run(main())
