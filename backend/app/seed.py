import random

from app.database import SessionLocal, engine, Base
from app import models, auth

random.seed(42)

PLATFORMS = ["AliExpress", "Alibaba", "Taobao", "Temu", "1688"]
CATEGORIES = [
    "Электроника",
    "Наушники",
    "Смартфоны",
    "Аксессуары",
    "Одежда",
    "Обувь",
    "Дом и сад",
    "Игрушки",
    "Инструменты",
    "Красота и здоровье",
    "Автотовары",
    "Спорт",
]
PRODUCT_WORDS = [
    "Беспроводные наушники",
    "Смарт-часы",
    "USB кабель",
    "Чехол для телефона",
    "Кроссовки",
    "Куртка зимняя",
    "Дрель аккумуляторная",
    "Набор отвёрток",
    "Светодиодная лампа",
    "Рюкзак городской",
    "Power bank 20000",
    "Веб-камера",
    "Игровая мышь",
    "Механическая клавиатура",
    "Фитнес-браслет",
    "Термокружка",
]
COMMENTS_GOOD = [
    "Отличный товар, доставка быстрая, продавец молодец.",
    "Качество на высоте, рекомендую этого продавца.",
    "Пришло раньше срока, всё работает как надо.",
    "Цена-качество супер, заказываю не первый раз.",
]
COMMENTS_MID = [
    "Нормально, но доставка задержалась на пару недель.",
    "Товар ок, упаковка слабовата.",
    "Среднее качество, за свою цену сойдёт.",
]
COMMENTS_BAD = [
    "Долго шло, продавец не отвечал на вопросы.",
    "Качество не очень, ожидал большего.",
    "Доставка очень медленная, товар с дефектом.",
]


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.User).first():
            print("БД уже наполнена — пропускаю seed.")
            return

        # Платформы
        platforms = [models.Platform(name=n) for n in PLATFORMS]
        db.add_all(platforms)
        db.flush()

        # Категории
        categories = [models.Category(name=n) for n in CATEGORIES]
        db.add_all(categories)
        db.flush()

        # Продавцы
        sellers = []
        for i in range(30):
            sellers.append(
                models.Seller(
                    name=f"Seller_{i + 1}",
                    platform_id=random.choice(platforms).id,
                )
            )
        db.add_all(sellers)
        db.flush()

        # Товары
        products = []
        for i in range(100):
            cat = random.choice(categories)
            title = f"{random.choice(PRODUCT_WORDS)} #{i + 1}"
            products.append(
                models.Product(
                    title=title,
                    description=f"{title}. Категория: {cat.name}. Доставка из Китая.",
                    category_id=cat.id,
                    seller_id=random.choice(sellers).id,
                    profile_attrs={"cat": cat.id % 5, "price": random.randint(1, 5)},
                )
            )
        db.add_all(products)
        db.flush()

        # Пользователи для образца MVP (пароль у всех: password123)
        users = []
        pwd = auth.hash_password("password123")
        for i in range(20):
            users.append(
                models.User(
                    email=f"user{i + 1}@example.com",
                    password_hash=pwd,
                    display_name=f"Пользователь {i + 1}",
                    profile_attrs={"region": i % 3, "type": i % 2},
                    crit_weights={
                        "service": 0.25,
                        "seller": 0.25,
                        "product": 0.25,
                        "delivery": 0.25,
                    },
                )
            )
        db.add_all(users)
        db.flush()

        # Отзывы
        reviews = []
        for _ in range(500):
            product = random.choice(products)
            user = random.choice(users)
            tier = random.random()
            if tier > 0.6:
                scores = [random.randint(4, 5) for _ in range(4)]
                comment = random.choice(COMMENTS_GOOD)
            elif tier > 0.3:
                scores = [random.randint(3, 4) for _ in range(4)]
                comment = random.choice(COMMENTS_MID)
            else:
                scores = [random.randint(1, 3) for _ in range(4)]
                comment = random.choice(COMMENTS_BAD)
            reviews.append(
                models.Review(
                    user_id=user.id,
                    product_id=product.id,
                    platform_id=random.choice(platforms).id,
                    seller_id=product.seller_id,
                    score_service=scores[0],
                    score_seller=scores[1],
                    score_product=scores[2],
                    score_delivery=scores[3],
                    score_total=sum(scores) / 4.0,
                    comment_text=f"{product.title}. {comment}",
                )
            )
        db.add_all(reviews)
        db.flush()

        for _ in range(150):
            rv = random.choice(reviews)
            db.add(
                models.Comment(
                    review_id=rv.id,
                    user_id=random.choice(users).id,
                    text=random.choice(
                        [
                            "Спасибо за отзыв!",
                            "А какой размер брали?",
                            "У меня тоже всё хорошо.",
                            "Сколько шла посылка?",
                        ]
                    ),
                )
            )
        for _ in range(200):
            rv = random.choice(reviews)
            db.add(
                models.Feedback(
                    user_id=random.choice(users).id,
                    review_id=rv.id,
                    is_useful=1 if random.random() > 0.3 else 0,
                )
            )

        db.commit()
        print(
            "Seed готов: 5 площадок, 12 категорий, 30 продавцов, "
            "100 товаров, 20 пользователей, 500 отзывов."
        )
        print("   Тестовый вход: user1@example.com / password123")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
