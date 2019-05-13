from datetime import date
from datetime import datetime
from sqlalchemy import create_engine, func, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy import Table, Column, String, Integer, Date, MetaData, ForeignKey, Float

engine = create_engine(
    'sqlite:///db.sqlite',
    connect_args={'check_same_thread': False})
# Session = sessionmaker(bind=engine)
Session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    date = Column(Date)

    # def __init__(self, id, login, first_name, last_name, phone, date_of_birth, date):
    #     self.id = id
    #     self.login = login
    #     self.first_name = first_name
    #     self.last_name = last_name
    #     self.phone = phone
    #     self.date_of_birth = date_of_birth
    #     self.date = date


users_orders_association = Table(
    'users_orders', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('order_id', Integer, ForeignKey('orders.id'))
)


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    # user = relationship("User", secondary=users_orders_association)
    user = Column(String)
    cart = Column(String)
    date = Column(Date)
    address = Column(String)
    payment_type = Column(String)
    status = Column(String)
    price = Column(Float)

    # def __init__(self, cart, date, address, payment_type, status):
    #     self.cart = cart
    #     self.date = date
    #     self.address = address
    #     self.payment_type = payment_type
    #     self.status = status


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    category = Column(String)
    subcategory = Column(String)
    price = Column(Float)
    weight = Column(String)
    composition = Column(String)
    image_url = Column(String)

    # def __init__(self, title, category, subcategory, price, weight, composition, image_url):
    #     self.title = title
    #     self.category = category
    #     self.subcategory = subcategory
    #     self.price = price
    #     self.weight = weight
    #     self.composition = composition
    #     self.image_url = image_url

# ===========================  DB wrapper ===========================
# ===========================  Examples ===========================

# https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/#SQLAlchemy-in-Practice
# https://www.youtube.com/watch?v=YWFqtmGK0fk

# Base.metadata.create_all(engine)

# session = Session()

# user_1 = User(1234, 'mu_login', 'first_name', 'last-name', '', date(2019, 4, 11), date(2019, 4, 19))
# user_2 = User(45678, 'mu_login_2', 'first_name 2', 'last-name 2', '', date(2019, 4, 12), date(2019, 4, 20))

# order_1 = Order('текст корзины товаров', date(2019, 4, 18), 'Lida', 'terminal', 'status')
# order_2 = Order('текст корзины товаров 2', date(2019, 4, 20), 'Lida 2', 'terminal 2', 'status 2')

# order_1.user = [user_1]
# order_2.user = [user_2]

# session.add(user_1)
# session.add(user_2)
# session.add(order_1)
# session.add(order_2)

# ================

# users = session.query(User).all()

# for user in users:
#     print(f'{user.id} {user.first_name} was added {user.date}')

# ===============

# orders that 'first_name' made
# my_orders = session.query(Order) \
#     .join(User, Order.user) \
#     .filter(User.first_name == 'first_name') \
#     .all()

# for order in my_orders:
#     print(f'{order.id} {order.address} was added {order.date}')

# ==============

# get orders after 15-01-01
# orders = session.query(Order) \
#     .filter(Order.date > date(2019, 4, 19)) \
#     .all()

# for order in orders:
#     print(f'{order.id} {order.address} was made {order.date}')

# ==============

# session.commit()
# session.close()

# ===========================  Examples ===========================
# ============================  Usage =============================

# Source https://github.com/pybites/pytip/tree/master/tips


def _create_session():
    db_url = 'sqlite:///db.sqlite'

    # if 'pytest' in sys.argv[0]:
    #     db_url += '_test'

    # if not db_url:
    #     raise EnvironmentError('Need to set (TEST_)DATABASE_URL')

    engine = create_engine(
        db_url,
        connect_args={'check_same_thread': False},
        echo=False)
    Base.metadata.create_all(engine)
    create_session = sessionmaker(bind=engine)
    return create_session()


session = _create_session()


def get_categories():
    categories = session.query(Product.category).group_by(Product.category).all()
    categories = [r for r, in categories]
    return categories


def get_subcategories(category):
    subcats = session.query(Product.subcategory).filter(Product.category == category).group_by(Product.subcategory).all()
    subcats = [r for r, in subcats]
    return subcats


def get_products_by_category(category):
    # TODO make this function work with categories and subcategories
    products = session.query(Product.title).filter(or_(
        Product.category == category,
        Product.subcategory == category
    )).all()
    products = [r for r, in products]
    return products


def get_user(user_id):
    user = session.query(User).filter(User.id == user_id).first()
    return user


def add_user(user):
    session.add(User(
        id=user['id'],
        username=user['username'],
        first_name=user['first_name'],
        last_name=user['last_name'],
        date=datetime.now()
    ))
    session.commit()
    session.close()


def update_user(user_id, column_name, value):
    session.query(User).filter(User.id == user_id).update({column_name: value})
    session.commit()
    session.close()


def add_products(product_list):
    for p in product_list:
        session.add(Product(
            title=p[0],
            category=p[1],
            subcategory=p[2],
            price=p[3],
            weight=p[4],
            composition=p[5],
            image_url=p[6]
            ))
    session.commit()
    session.close()


def add_order(order):
    order = Order(
        user=order['user_id'],
        cart=order['cart'],
        date=datetime.now(),
        address=order['address'],
        payment_type=order['payment_type'],
        status=order['status'],
        price=order['price']
    )
    session.add(order)
    session.flush()
    session.refresh(order)
    order_id = order.id
    session.commit()
    session.close()
    return order_id


def update_order(order_id, column_name, value):
    session.query(Order).filter(Order.id == order_id).update({column_name: value})
    session.commit()
    session.close()


def is_existing_category(text):
    cat = session.query(Product).filter(
        or_(
            Product.category == text,
            Product.subcategory == text
            )
    ).first()
    return True if cat else False


def get_product(product, category):
    return session.query(Product).filter(and_(
        Product.title == product,
        or_(
            Product.category == category,
            Product.subcategory == category
            )
    )).first()


def get_product_by_id(id):
    p = session.query(Product).filter(Product.id == id).first()
    p = dict(p.__dict__)
    p.pop('_sa_instance_state', None)
    return p


product_list = (
    ('Пицца Маргарита', 'Пиццы', '30см', 7.50, '430', 'св. помидоры, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Маргарита', 'Пиццы', '45см', 13.00, 530, 'св. помидоры, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Барбекина', 'Пиццы', '30см', 11.00, 530, 'куриная грудка в/к, бекон в/к, св. помидоры, кон. огурцы, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Барбекина', 'Пиццы', '45см', 20.00, 1060, 'куриная грудка в/к, бекон в/к, св. помидоры, кон. огурцы, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Вегетарианская', 'Пиццы', '30см', 9.00, 480, 'куриная грудка в/к, бекон в/к, св. помидоры, кон. огурцы, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Вегетарианская', 'Пиццы', '45см', 16.00, 960, 'св. перец, св. шампиньоны,  св. помидоры, лук-порей, маслины, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Гаваи', 'Пиццы', '30см', 10.00, 490, 'Ветчина в/к, куриная грудка в/к, кон. ананасы, маслины, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Гаваи', 'Пиццы', '45см', 18.00, 980, 'Ветчина в/к, куриная грудка в/к, кон. ананасы, маслины, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Деревенская', 'Пиццы', '30см', 10.00, 480, 'колбаса салями, бекон в/к, кон. огурцы, лук порей, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Деревенская', 'Пиццы', '45см', 18.00, 960, 'колбаса салями, бекон в/к, кон. огурцы, лук порей, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Морская', 'Пиццы', '30см', 16.50, 470, 'семга с/с, мясо креветок, св. перец, маслины, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Морская', 'Пиццы', '45см', 30.00, 940, 'семга с/с, мясо креветок, св. перец, маслины, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Капричиоза', 'Пиццы', '30см', 11.00, 520, 'Ветчина в/к, колбаса "Кабаносы", св. шампиньоны, кон. огурец', 'https://picsum.photos/200/300/?random'),
    ('Пицца Капричиоза', 'Пиццы', '45см', 20.00, 940, 'Ветчина в/к, колбаса "Кабаносы", св. шампиньоны, кон. огурец', 'https://picsum.photos/200/300/?random'),
    ('Пицца Мясное ассорти', 'Пиццы', '30см', 13.00, 530, 'Ветчина в/к, куриная грудка в/к, колбаса салями, бекон в/к, лук порей, сыр моцарелла', 'https://picsum.photos/200/300/?random'),
    ('Пицца Мясное ассорти', 'Пиццы', '45см', 24.00, 1060, 'Ветчина в/к, куриная грудка в/к, колбаса салями, бекон в/к, лук порей, сыр моцарелла', 'https://picsum.photos/200/300/?random'),

    ('Ролл Канада', 'Роллы', '4шт', 8.00, 125, 'сыр сл., угорь жареный в соусе, огурец, авакадо, кунжут', 'https://picsum.photos/200/300/?random'),
    ('Ролл Канада', 'Роллы', '8шт', 15.00, 250, 'сыр сл., угорь жареный в соусе, огурец, авакадо, кунжут', 'https://picsum.photos/200/300/?random'),
    ('Ролл Филладельфия', 'Роллы', '4шт', 8.00, 125, 'сыр сл., семга с/с, авокадо', 'https://picsum.photos/200/300/?random'),
    ('Ролл Филладельфия', 'Роллы', '8шт', 15.00, 250, 'сыр сл., семга с/с, авокадо', 'https://picsum.photos/200/300/?random'),
    ('Ролл Аризона', 'Роллы', '4шт', 4.00, 100, 'сыр сл., мясо креветки, авокадо, кунжут', 'https://picsum.photos/200/300/?random'),
    ('Ролл Аризона', 'Роллы', '8шт', 7.50, 200, 'сыр сл., мясо креветки, авокадо, кунжут', 'https://picsum.photos/200/300/?random'),
    ('Ролл Ямато', 'Роллы', '4шт', 2.90, 100, 'сыр сл., семга с/с п/к, имбирь мар., редька мар.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Ямато', 'Роллы', '8шт', 5.40, 200, 'сыр сл., семга с/с п/к, имбирь мар., редька мар.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Такуан кунсей', 'Роллы', '4шт', 3.50, 100, 'сыр сл., семга с/с п/к, салат чука, огурец, редька мар.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Такуан кунсей', 'Роллы', '8шт', 6.50, 200, 'сыр сл., семга с/с п/к, салат чука, огурец, редька мар.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Гаваи', 'Роллы', '4шт', 2.70, 100, 'куриная грудка в/к, ананас мар., редька мар., сыр чеддер', 'https://picsum.photos/200/300/?random'),
    ('Ролл Гаваи', 'Роллы', '8шт', 5.00, 200, 'куриная грудка в/к, ананас мар., редька мар., сыр чеддер', 'https://picsum.photos/200/300/?random'),
    ('Ролл Риоку', 'Роллы', '4шт', 3.60, 100, 'сыр сл., огурец, семга с/с, икра чер., помидор ', 'https://picsum.photos/200/300/?random'),
    ('Ролл Риоку', 'Роллы', '8шт', 6.70, 200, 'сыр сл., огурец, семга с/с, икра чер., помидор ', 'https://picsum.photos/200/300/?random'),
    ('Ролл Банзай маки', 'Роллы', '4шт', 2.70, 100, 'сыр сл., огурец, семга с/с, икра кр.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Банзай маки', 'Роллы', '8шт', 5.00, 200, 'сыр сл., огурец, семга с/с, икра кр.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Окинава', 'Роллы', '4шт', 2.70, 100, 'сыр сл., огурец, семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Окинава', 'Роллы', '8шт', 5.00, 200, 'сыр сл., огурец, семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Бонито маки', 'Роллы', '4шт', 3.40, 100, 'сыр сл., салат чука, семга с/с, хлопья тунца коп.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Бонито маки', 'Роллы', '8шт', 6.30, 200, 'сыр сл., салат чука, семга с/с, хлопья тунца коп.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Эби каппа маки', 'Роллы', '4шт', 2.90, 100, 'сыр сл., огурец, мясо креветки', 'https://picsum.photos/200/300/?random'),
    ('Ролл Эби каппа маки', 'Роллы', '8шт', 5.30, 200, 'сыр сл., огурец, мясо креветки', 'https://picsum.photos/200/300/?random'),
    ('Ролл Сяке маки', 'Роллы', '4шт', 3.30, 100, 'сыр сл., семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Сяке маки', 'Роллы', '8шт', 6.10, 200, 'сыр сл., семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Вакоме маки', 'Роллы', '4шт', 4.50, 100, 'сыр сл., семга с/с, помидор, салат чука', 'https://picsum.photos/200/300/?random'),
    ('Ролл Вакоме маки', 'Роллы', '8шт', 8.50, 200, 'сыр сл., семга с/с, помидор, салат чука', 'https://picsum.photos/200/300/?random'),
    ('Ролл Вегетеринский', 'Роллы', '4шт', 3.00, 100, 'сыр сл., помидор, авокадо, перец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Вегетеринский', 'Роллы', '8шт', 5.50, 200, 'сыр сл., помидор, авокадо, перец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Сяке Хеяши маки', 'Роллы', '4шт', 3.60, 100, 'сыр сл., семга с/с, салат чука', 'https://picsum.photos/200/300/?random'),
    ('Ролл Сяке Хеяши маки', 'Роллы', '8шт', 6.70, 200, 'сыр сл., семга с/с, салат чука', 'https://picsum.photos/200/300/?random'),
    ('Ролл Косе маки', 'Роллы', '4шт', 2.70, 100, 'сыр сл., перец, семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Косе маки', 'Роллы', '8шт', 5.00, 200, 'сыр сл., перец, семга с/с', 'https://picsum.photos/200/300/?random'),
    ('Ролл Грин маки', 'Роллы', '4шт', 3.20, 100, 'сыр сл., семга с/с п/к, перец, укроп', 'https://picsum.photos/200/300/?random'),
    ('Ролл Грин маки', 'Роллы', '8шт', 6.00, 200, 'сыр сл., семга с/с п/к, перец, укроп', 'https://picsum.photos/200/300/?random'),
    ('Ролл Киото', 'Роллы', '4шт', 3.00, 100, 'сыр сл., семга с/с, перец, огурец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Киото', 'Роллы', '8шт', 5.50, 200, 'сыр сл., семга с/с, перец, огурец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Унаги маки', 'Роллы', '4шт', 4.50, 100, 'угорь жар. в соусе, огурец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Унаги маки', 'Роллы', '8шт', 8.50, 200, 'угорь жар. в соусе, огурец', 'https://picsum.photos/200/300/?random'),
    ('Ролл Калифорния', 'Роллы', '4шт', 2.70, 100, 'сыр сл., крабовые палочки, огурец, икра кр.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Калифорния', 'Роллы', '8шт', 5.00, 200, 'сыр сл., крабовые палочки, огурец, икра кр.', 'https://picsum.photos/200/300/?random'),
    ('Ролл Аляска', 'Роллы', '4шт', 4.50, 100, 'сыр сл., угорь жар. в соусе, огурец, икра кр., кунжут', 'https://picsum.photos/200/300/?random'),
    ('Ролл Аляска', 'Роллы', '8шт', 8.50, 200, 'сыр сл., угорь жар. в соусе, огурец, икра кр., кунжут', 'https://picsum.photos/200/300/?random'),

    ('Бургер Гамбургер', 'Бургеры', None, 2.00, 130, 'Булочка, говяжья котлета, огурец кон., кетчуп', 'https://picsum.photos/200/300/?random'),
    ('Бургер Чизбургер', 'Бургеры', None, 2.80, 180, 'Булочка, говяжья котлета, огурец кон., помидор св., салат, сыр чедер, соус 1000 островов.', 'https://picsum.photos/200/300/?random'),
    ('Бургер Чикенбургер', 'Бургеры', None, 2.80, 190, 'Булочка, куриная котлета, огурец св., помидор св., салат, сыр чедер, горчичный соус', 'https://picsum.photos/200/300/?random'),
    ('Бургер Мехико', 'Бургеры', None, 3.00, 180, 'Булочка, говяжья котлета, огурец кон., св. помидор, перец халапеньо, соус сальса', 'https://picsum.photos/200/300/?random'),
    ('Бургер Барбекю', 'Бургеры', None, 3.00, 180, 'Булочка, куриная котлета, огурец кон., лук мар., салат, бекон, сыр чедер, соус 1000 островов', 'https://picsum.photos/200/300/?random'),
    ('Бургер Фишбургер', 'Бургеры', None, 3.00, 180, 'Булочка, филе хека в понировке, салат, помидор св., сосус тар-тар', 'https://picsum.photos/200/300/?random'),
    ('Бургер Дабл биф', 'Бургеры', None, 6.50, None, 'Булочка, говяжья котлета, помидо св., салат, сыр чедер, соус гриль', 'https://picsum.photos/200/300/?random'),
    ('Бургер Дабл чикен', 'Бургеры', None, 6.50, None, 'Булочка, куриная котлета, помидор св., салат, сыр чедер, соус гриль', 'https://picsum.photos/200/300/?random'),

    ('Драник С курицей', 'Драник', None, 3.20, 220, 'картофельные оладьи, куриная котлета, помидор св., соус тар-тар', 'https://picsum.photos/200/300/?random'),
    ('Драник С говядиной', 'Драник', None, 3.20, 210, 'картофельные оладьи, говяжья котлета, помидор св., соус тар-тар', 'https://picsum.photos/200/300/?random'),
    ('Драник С семгой', 'Драник', None, 4.00, 200, 'картофельные оладьи, семга с/с, помидор св., соус тар-тар', 'https://picsum.photos/200/300/?random'),

    ('Картофель фри большой', 'Закуски', None, 2.40, 150, 'картофель фри', 'https://picsum.photos/200/300/?random'),
    ('Картофель фри малый', 'Закуски', None, 2.00, 100, 'картофель фри', 'https://picsum.photos/200/300/?random'),
    ('Картофельные шарики большие', 'Закуски', None, 2.40, 150, 'картофельные шарики', 'https://picsum.photos/200/300/?random'),
    ('Картофельные шарики малые', 'Закуски', None, 2.00, 100, 'картофельные шарики', 'https://picsum.photos/200/300/?random'),
    ('Наггетсы большие', 'Закуски', None, 5.00, 150, 'наггетсы', 'https://picsum.photos/200/300/?random'),
    ('Наггетсы малые', 'Закуски', None, 4.00, 100, 'наггетсы', 'https://picsum.photos/200/300/?random'),

    ('Квас ж/б 0,5', 'Напитки', None, 1.50, 500, None, 'https://picsum.photos/200/300/?random'),
    ('Квас 0,5', 'Напитки', None, 1.50, 500, None, 'https://picsum.photos/200/300/?random'),
    ('Pepsi 0,5', 'Напитки', None, 1.50, 500, None, 'https://picsum.photos/200/300/?random'),
    ('Mirinda 0,5', 'Напитки', None, 1.50, 500, None, 'https://picsum.photos/200/300/?random'),
    ('7up 0,5', 'Напитки', None, 1.50, 500, None, 'https://picsum.photos/200/300/?random'),
    ('Pepsi 0,33', 'Напитки', None, 1.30, 330, None, 'https://picsum.photos/200/300/?random'),
    ('Mirinda 0,33', 'Напитки', None, 1.30, 330, None, 'https://picsum.photos/200/300/?random'),
    ('7up 0,33', 'Напитки', None, 1.30, 330, None, 'https://picsum.photos/200/300/?random'),
    ('Pepsi 0,25', 'Напитки', None, 1.30, 250, None, 'https://picsum.photos/200/300/?random'),
    ('Mirinda 0,25', 'Напитки', None, 1.30, 250, None, 'https://picsum.photos/200/300/?random'),
    ('7up 0,25', 'Напитки', None, 1.30, 250, None, 'https://picsum.photos/200/300/?random'),
    ('Сок 1л', 'Напитки', None, 3.50, 1000, None, 'https://picsum.photos/200/300/?random'),
    ('Сок 0,2л', 'Напитки', None, 1.50, 200, None, 'https://picsum.photos/200/300/?random'),
    ('Молочные коктейли', 'Напитки', None, 2.80, 200, None, 'https://picsum.photos/200/300/?random'),
    ('Чай и кофе', 'Напитки', None, 2.00, 200, None, 'https://picsum.photos/200/300/?random')
)


# categories = get_categories()
# add_products(product_list)

# ============================  Usage =============================
