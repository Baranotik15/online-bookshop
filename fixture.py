import asyncio
import os
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from books.models import Author, Book
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

BOOK_TITLES = [
    "Тіні забутих предків", "Захар Беркут", "Лісова пісня", "Кайдашева сім'я",
    "Земля", "Місто", "Вир", "Людина і зброя", "Собор", "Тронка",
    "Циклон", "Берег любові", "Диво", "Три листки за вікном", "Вогнепоклонники",
    "Жовтий князь", "Марія", "Чорна рада", "Хіба ревуть воли", "Бур'ян",
    "Майстер корабля", "Вершники", "Мальви", "Смерть і воїн", "Дорогою ціною",
    "Під чужими зорями", "Голос трави", "Рай і люди", "Птахи з невидимого острова",
    "Зачарована Десна", "Ніч перед Різдвом", "Кобзар", "Мартин Боруля",
    "Украдене щастя", "Пісня про рушник", "Мороз", "Поема про море",
    "Сонячна машина", "Місяцева зозуля", "Зимові дерева", "Степ", "Орда",
    "Залізний острів", "Криниця для спраглих", "Дорога", "Листя землі",
    "Чотири броди", "Похорон богів", "Перший удар", "Зелені святки",
    "Щоденник", "Вибране", "На полі крові", "Сімнадцятий патруль", "Холодний яр",
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
    await User.objects.filter(is_superuser=False).adelete()
    print("Готово.\n")


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


async def seed_books(authors, n=50):
    print(f"Створення {n} книг...")
    titles = random.sample(BOOK_TITLES * 2, n)
    books = [
        Book(
            title=title,
            description=random.choice(DESCRIPTIONS),
            price=Decimal(str(round(random.uniform(80, 650), 2))),
            author=random.choice(authors),
            stock=random.randint(0, 100),
        )
        for title in titles
    ]
    await Book.objects.abulk_create(books)
    result = [b async for b in Book.objects.all()]
    print(f"  + {n} книг")
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

    # users і authors незалежні — паралельно
    users, authors = await asyncio.gather(seed_users(50), seed_authors(50))

    books = await seed_books(authors, 50)

    # orders і carts незалежні — паралельно
    await asyncio.gather(seed_orders(users, books, 50), seed_carts(users, books, 50))

    print("\n" + "=" * 40)
    print("БД заповнена успішно!")
    print(f"  Users:      {await User.objects.filter(is_superuser=False).acount()}")
    print(f"  Authors:    {await Author.objects.acount()}")
    print(f"  Books:      {await Book.objects.acount()}")
    print(f"  Orders:     {await Order.objects.acount()}")
    print(f"  OrderItems: {await OrderItem.objects.acount()}")
    print(f"  Carts:      {await Cart.objects.acount()}")
    print(f"  CartItems:  {await CartItem.objects.acount()}")


if __name__ == '__main__':
    asyncio.run(main())
