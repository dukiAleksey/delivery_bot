import csv

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
    user_id = Column(String)
    phone = Column(String)
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


def export_orders_to_file():
    outfile = open('orders.csv', 'w')
    outcsv = csv.writer(outfile)
    records = session.query(Order).all()
    [outcsv.writerow([getattr(curr, column.name) for column in Order.__mapper__.columns]) for curr in records]
    outfile.close()


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
        user_id=order['user_id'],
        phone=order['user_phone'],
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
    ('Пицца Маргарита', 'Пиццы', '30см', 7.50, '430', 'св. помидоры, сыр моцарелла', 'pizza_margarita.jpg'),
    ('Пицца Маргарита', 'Пиццы', '45см', 13.00, 530, 'св. помидоры, сыр моцарелла', 'pizza_margarita.jpg'),
    ('Пицца Барбекина', 'Пиццы', '30см', 11.00, 530, 'куриная грудка в/к, бекон в/к, св. помидоры, кон. огурцы, сыр моцарелла', 'pizza_barbekina.jpg'),
    ('Пицца Барбекина', 'Пиццы', '45см', 20.00, 1060, 'куриная грудка в/к, бекон в/к, св. помидоры, кон. огурцы, сыр моцарелла', 'pizza_barbekina.jpg'),
    ('Пицца Вегетарианская', 'Пиццы', '30см', 9.00, 480, 'св. перец, св. шампиньоны,  св. помидоры, лук-порей, маслины, сыр моцарелла', 'pizza_vagatarianskaya.jpg'),
    ('Пицца Вегетарианская', 'Пиццы', '45см', 16.00, 960, 'св. перец, св. шампиньоны,  св. помидоры, лук-порей, маслины, сыр моцарелла', 'pizza_vagatarianskaya.jpg'),
    ('Пицца Гаваи', 'Пиццы', '30см', 10.00, 490, 'Ветчина в/к, куриная грудка в/к, кон. ананасы, маслины, сыр моцарелла', 'pizza_gavai.jpg'),
    ('Пицца Гаваи', 'Пиццы', '45см', 18.00, 980, 'Ветчина в/к, куриная грудка в/к, кон. ананасы, маслины, сыр моцарелла', 'pizza_gavai.jpg'),
    ('Пицца Деревенская', 'Пиццы', '30см', 10.00, 480, 'колбаса салями, бекон в/к, кон. огурцы, лук порей, сыр моцарелла', 'pizza_derevenskaya.jpg'),
    ('Пицца Деревенская', 'Пиццы', '45см', 18.00, 960, 'колбаса салями, бекон в/к, кон. огурцы, лук порей, сыр моцарелла', 'pizza_derevenskaya.jpg'),
    ('Пицца Морская', 'Пиццы', '30см', 16.50, 470, 'семга с/с, мясо креветок, св. перец, маслины, сыр моцарелла', 'pizza_morskaya.jpg'),
    ('Пицца Морская', 'Пиццы', '45см', 30.00, 940, 'семга с/с, мясо креветок, св. перец, маслины, сыр моцарелла', 'pizza_morskaya.jpg'),
    ('Пицца Капричиоза', 'Пиццы', '30см', 11.00, 520, 'Ветчина в/к, колбаса "Кабаносы", св. шампиньоны, кон. огурец', 'pizza_kaprichoza.jpg'),
    ('Пицца Капричиоза', 'Пиццы', '45см', 20.00, 940, 'Ветчина в/к, колбаса "Кабаносы", св. шампиньоны, кон. огурец', 'pizza_kaprichoza.jpg'),
    ('Пицца Мясное ассорти', 'Пиццы', '30см', 13.00, 530, 'Ветчина в/к, куриная грудка в/к, колбаса салями, бекон в/к, лук порей, сыр моцарелла', 'pizza_myasnoe_assorti.jpg'),
    ('Пицца Мясное ассорти', 'Пиццы', '45см', 24.00, 1060, 'Ветчина в/к, куриная грудка в/к, колбаса салями, бекон в/к, лук порей, сыр моцарелла', 'pizza_myasnoe_assorti.jpg'),
    ('Пицца С ветчиной', 'Пиццы', '30см', 8.00, 430, 'ветчина в/к, сыр моцарелла', 'pizza_s_vetchinoy.jpg'),
    ('Пицца С ветчиной', 'Пиццы', '45см', 14.50, 860, 'ветчина в/к, сыр моцарелла', 'pizza_s_vetchinoy.jpg'),
    ('Пицца С колбасой', 'Пиццы', '30см', 9.00, 430, 'колбаса салями, сыр моцарелла', 'pizza_s_kilbasoy.jpg'),
    ('Пицца С колбасой', 'Пиццы', '45см', 16.00, 860, 'колбаса салями, сыр моцарелла', 'pizza_s_kilbasoy.jpg'),
    ('Пицца Диабло', 'Пиццы', '30см', 11.00, 500, 'колбаса салями, св. шампиньоны, перец халапеньо, соус сальса, сыр моцарелла', 'pizza_diablo.jpg'),
    ('Пицца Диабло', 'Пиццы', '45см', 20.00, 1000, 'колбаса салями, св. шампиньоны, перец халапеньо, соус сальса, сыр моцарелла', 'pizza_diablo.jpg'),
    ('Пицца Закрытая', 'Пиццы', '30см', 13.00, 650, 'Ветчина в/к, колбаса салями, кон. огурцы, сыр моцарелла', 'pizza_zakrytaya.jpg'),
    ('Пицца Закрытая', 'Пиццы', '45см', 24.00, 1300, 'Ветчина в/к, колбаса салями, кон. огурцы, сыр моцарелла', 'pizza_zakrytaya.jpg'),
    ('Пицца Тутака', 'Пиццы', '30см', 11.00, 560, 'куриная грудка в/к, св. помидоры, св. шампиньоны, св. укроп, сыр моцарелла', 'pizza_tutaka.jpg'),
    ('Пицца Тутака', 'Пиццы', '45см', 20.00, 1120, 'куриная грудка в/к, св. помидоры, св. шампиньоны, св. укроп, сыр моцарелла', 'pizza_tutaka.jpg'),
    ('Пицца Кватро', 'Пиццы', '30см', 11.00, 510, 'ветчина в/к, св. перец, св. шампиньоны, маслины, сыр моцарелла', 'pizza_kvatro.jpg'),
    ('Пицца Кватро', 'Пиццы', '45см', 20.00, 1020, 'ветчина в/к, св. перец, св. шампиньоны, маслины, сыр моцарелла', 'pizza_kvatro.jpg'),
    ('Пицца Бургер', 'Пиццы', '30см', 11.00, 530, 'фарш гов., бекон в/к, св. помидоры, кон. огурец, соус гриль, соус "Гриль" сыр моцарелла', 'pizza_burger.jpg'),
    ('Пицца Бургер', 'Пиццы', '45см', 20.00, 1060, 'фарш гов., бекон в/к, св. помидоры, кон. огурец, соус гриль, соус "Гриль" сыр моцарелла', 'pizza_burger.jpg'),
    ('Пицца Яркая', 'Пиццы', '30см', 11.00, 490, 'ветчина в/к, колбаса салями, св. перец, маслины, св. огурец, сыр моцарелла', 'pizza_yarkaya.jpg'),
    ('Пицца Яркая', 'Пиццы', '45см', 20.00, 980, 'ветчина в/к, колбаса салями, св. перец, маслины, св. огурец, сыр моцарелла', 'pizza_yarkaya.jpg'),
    ('Пицца Баварская', 'Пиццы', '30см', 11.00, 490, 'колбаса "Кабаносы", св. перец, св. шампиньоны, сыр моцарелла', 'pizza_bavarskaya.jpg'),
    ('Пицца Баварская', 'Пиццы', '45см', 20.00, 980, 'колбаса "Кабаносы", св. перец, св. шампиньоны, сыр моцарелла', 'pizza_bavarskaya.jpg'),
    ('Пицца Суприм', 'Пиццы', '30см', 11.00, 470, 'Ветчина в/к, колбаса "Кабаносы", св. перец, кон. огурец, лук порей, соус "1000 островов", сыр моцарелла', 'pizza_suprim.jpg'),
    ('Пицца Суприм', 'Пиццы', '45см', 20.00, 940, 'Ветчина в/к, колбаса "Кабаносы", св. перец, кон. огурец, лук порей, соус "1000 островов", сыр моцарелла', 'pizza_suprim.jpg'),

    ('Ролл Канада', 'Роллы', '4шт', 8.00, 125, 'сыр сл., угорь жареный в соусе, огурец, авакадо, кунжут', 'sushi_kanada.jpg'),
    ('Ролл Канада', 'Роллы', '8шт', 15.00, 250, 'сыр сл., угорь жареный в соусе, огурец, авакадо, кунжут', 'sushi_kanada.jpg'),
    ('Ролл Филладельфия', 'Роллы', '4шт', 8.00, 125, 'сыр сл., семга с/с, авокадо', 'sushi_filadelfia.jpg'),
    ('Ролл Филладельфия', 'Роллы', '8шт', 15.00, 250, 'сыр сл., семга с/с, авокадо', 'sushi_filadelfia.jpg'),
    ('Ролл Аризона', 'Роллы', '4шт', 4.00, 100, 'сыр сл., мясо креветки, авокадо, кунжут', 'sushi_arizona.jpg'),
    ('Ролл Аризона', 'Роллы', '8шт', 7.50, 200, 'сыр сл., мясо креветки, авокадо, кунжут', 'sushi_arizona.jpg'),
    ('Ролл Ямато', 'Роллы', '4шт', 2.90, 100, 'сыр сл., семга с/с п/к, имбирь мар., редька мар.', 'sushi_yamato.jpg'),
    ('Ролл Ямато', 'Роллы', '8шт', 5.40, 200, 'сыр сл., семга с/с п/к, имбирь мар., редька мар.', 'sushi_yamato.jpg'),
    ('Ролл Такуан кунсей', 'Роллы', '4шт', 3.50, 100, 'сыр сл., семга с/с п/к, салат чука, огурец, редька мар.', 'sushi_takuan_kunsey.jpg'),
    ('Ролл Такуан кунсей', 'Роллы', '8шт', 6.50, 200, 'сыр сл., семга с/с п/к, салат чука, огурец, редька мар.', 'sushi_takuan_kunsey.jpg'),
    ('Ролл Гаваи', 'Роллы', '4шт', 2.70, 100, 'куриная грудка в/к, ананас мар., редька мар., сыр чеддер', 'sushi_gavai.jpg'),
    ('Ролл Гаваи', 'Роллы', '8шт', 5.00, 200, 'куриная грудка в/к, ананас мар., редька мар., сыр чеддер', 'sushi_gavai.jpg'),
    ('Ролл Риоку', 'Роллы', '4шт', 3.60, 100, 'сыр сл., огурец, семга с/с, икра чер., помидор ', 'sushi_rioku.jpg'),
    ('Ролл Риоку', 'Роллы', '8шт', 6.70, 200, 'сыр сл., огурец, семга с/с, икра чер., помидор ', 'sushi_rioku.jpg'),
    ('Ролл Банзай маки', 'Роллы', '4шт', 2.70, 100, 'сыр сл., огурец, семга с/с, икра кр.', 'sushi_banzai_maki.jpg'),
    ('Ролл Банзай маки', 'Роллы', '8шт', 5.00, 200, 'сыр сл., огурец, семга с/с, икра кр.', 'sushi_banzai_maki.jpg'),
    ('Ролл Окинава', 'Роллы', '4шт', 2.70, 100, 'сыр сл., огурец, семга с/с', 'sushi_okinava.jpg'),
    ('Ролл Окинава', 'Роллы', '8шт', 5.00, 200, 'сыр сл., огурец, семга с/с', 'sushi_okinava.jpg'),
    ('Ролл Бонито маки', 'Роллы', '4шт', 3.40, 100, 'сыр сл., салат чука, семга с/с, хлопья тунца коп.', 'sushi_bonito_maki.jpg'),
    ('Ролл Бонито маки', 'Роллы', '8шт', 6.30, 200, 'сыр сл., салат чука, семга с/с, хлопья тунца коп.', 'sushi_bonito_maki.jpg'),
    ('Ролл Эби каппа маки', 'Роллы', '4шт', 2.90, 100, 'сыр сл., огурец, мясо креветки', 'sushi_ebi_kappa_maki.jpg'),
    ('Ролл Эби каппа маки', 'Роллы', '8шт', 5.30, 200, 'сыр сл., огурец, мясо креветки', 'sushi_ebi_kappa_maki.jpg'),
    ('Ролл Сяке маки', 'Роллы', '4шт', 3.30, 100, 'сыр сл., семга с/с', 'sushi_syake_maki.jpg'),
    ('Ролл Сяке маки', 'Роллы', '8шт', 6.10, 200, 'сыр сл., семга с/с', 'sushi_syake_maki.jpg'),
    ('Ролл Вакоме маки', 'Роллы', '4шт', 4.50, 100, 'сыр сл., семга с/с, помидор, салат чука', 'sushi_vakome_maki.jpg'),
    ('Ролл Вакоме маки', 'Роллы', '8шт', 8.50, 200, 'сыр сл., семга с/с, помидор, салат чука', 'sushi_vakome_maki.jpg'),
    ('Ролл Вегетеринский', 'Роллы', '4шт', 3.00, 100, 'сыр сл., помидор, авокадо, перец', 'sushi_vagatarianskiy.jpg'),
    ('Ролл Вегетеринский', 'Роллы', '8шт', 5.50, 200, 'сыр сл., помидор, авокадо, перец', 'sushi_vagatarianskiy.jpg'),
    ('Ролл Сяке Хеяши маки', 'Роллы', '4шт', 3.60, 100, 'сыр сл., семга с/с, салат чука', 'sushi_syake_heyashi_maki.jpg'),
    ('Ролл Сяке Хеяши маки', 'Роллы', '8шт', 6.70, 200, 'сыр сл., семга с/с, салат чука', 'sushi_syake_heyashi_maki.jpg'),
    ('Ролл Косе маки', 'Роллы', '4шт', 2.70, 100, 'сыр сл., перец, семга с/с', 'sushi_kose_maki.jpg'),
    ('Ролл Косе маки', 'Роллы', '8шт', 5.00, 200, 'сыр сл., перец, семга с/с', 'sushi_kose_maki.jpg'),
    ('Ролл Грин маки', 'Роллы', '4шт', 3.20, 100, 'сыр сл., семга с/с п/к, перец, укроп', 'sushi_grin_maki.jpg'),
    ('Ролл Грин маки', 'Роллы', '8шт', 6.00, 200, 'сыр сл., семга с/с п/к, перец, укроп', 'sushi_grin_maki.jpg'),
    ('Ролл Киото', 'Роллы', '4шт', 3.00, 100, 'сыр сл., семга с/с, перец, огурец', 'sushi_kioto.jpg'),
    ('Ролл Киото', 'Роллы', '8шт', 5.50, 200, 'сыр сл., семга с/с, перец, огурец', 'sushi_kioto.jpg'),
    ('Ролл Унаги маки', 'Роллы', '4шт', 4.50, 100, 'угорь жар. в соусе, огурец', 'sushi_unagii_maki.jpg'),
    ('Ролл Унаги маки', 'Роллы', '8шт', 8.50, 200, 'угорь жар. в соусе, огурец', 'sushi_unagii_maki.jpg'),
    ('Ролл Калифорния', 'Роллы', '4шт', 2.70, 100, 'сыр сл., крабовые палочки, огурец, икра кр.', 'sushi_kaliforniya.jpg'),
    ('Ролл Калифорния', 'Роллы', '8шт', 5.00, 200, 'сыр сл., крабовые палочки, огурец, икра кр.', 'sushi_kaliforniya.jpg'),
    ('Ролл Аляска', 'Роллы', '4шт', 4.50, 100, 'сыр сл., угорь жар. в соусе, огурец, икра кр., кунжут', 'sushi_alaska.jpg'),
    ('Ролл Аляска', 'Роллы', '8шт', 8.50, 200, 'сыр сл., угорь жар. в соусе, огурец, икра кр., кунжут', 'sushi_alaska.jpg'),

    ('Бургер Гамбургер', 'Бургеры', None, 2.00, 130, 'Булочка, говяжья котлета, огурец кон., кетчуп', 'burger_hamburger.jpg'),
    ('Бургер Чизбургер', 'Бургеры', None, 2.80, 180, 'Булочка, говяжья котлета, огурец кон., помидор св., салат, сыр чедер, соус 1000 островов.', 'burger_chizburger.png'),
    ('Бургер Чикенбургер', 'Бургеры', None, 2.80, 190, 'Булочка, куриная котлета, огурец св., помидор св., салат, сыр чедер, горчичный соус', 'burger_chikenburger.png'),
    ('Бургер Мехико', 'Бургеры', None, 3.00, 180, 'Булочка, говяжья котлета, огурец кон., св. помидор, перец халапеньо, соус сальса', 'burger_mehiko.jpg'),
    ('Бургер Барбекю', 'Бургеры', None, 3.00, 180, 'Булочка, куриная котлета, огурец кон., лук мар., салат, бекон, сыр чедер, соус 1000 островов', 'burger_barbq.jpg'),
    ('Бургер Фишбургер', 'Бургеры', None, 3.00, 180, 'Булочка, филе хека в понировке, салат, помидор св., сосус тар-тар', 'burger_fishburger.jpg'),
    ('Бургер Дабл биф', 'Бургеры', None, 6.50, None, 'Булочка, говяжья котлета, помидо св., салат, сыр чедер, соус гриль', 'burger_dubl_beef.jpg'),
    ('Бургер Дабл чикен', 'Бургеры', None, 6.50, None, 'Булочка, куриная котлета, помидор св., салат, сыр чедер, соус гриль', 'burger_dabl_chiken.jpg'),

    ('Драник С курицей', 'Драник', None, 3.20, 220, 'картофельные оладьи, куриная котлета, помидор св., соус тар-тар', 'dranik_s_kuritsey.jpg'),
    ('Драник С говядиной', 'Драник', None, 3.20, 210, 'картофельные оладьи, говяжья котлета, помидор св., соус тар-тар', 'dranik_s_govuadinoy.jpg'),
    ('Драник С семгой', 'Драник', None, 4.00, 200, 'картофельные оладьи, семга с/с, помидор св., соус тар-тар', 'dranik_s_semgoy.jpg'),

    ('Картофель фри большой', 'Закуски', None, 2.40, 150, 'картофель фри', 'snacks_kartofel_free.jpg'),
    ('Картофель фри малый', 'Закуски', None, 2.00, 100, 'картофель фри', 'snacks_kartofel_free.jpg'),
    ('Картофельные шарики большие', 'Закуски', None, 2.40, 150, 'картофельные шарики', 'snacks_shariki.jpg'),
    ('Картофельные шарики малые', 'Закуски', None, 2.00, 100, 'картофельные шарики', 'snacks_shariki.jpg'),
    ('Наггетсы большие', 'Закуски', None, 5.00, 150, 'наггетсы', 'snacks_naggetsy.jpg'),
    ('Наггетсы малые', 'Закуски', None, 4.00, 100, 'наггетсы', 'snacks_naggetsy.jpg'),

    ('Квас ж/б 0,5', 'Напитки', None, 1.50, 500, None, 'pepsicola.jpg'),
    ('Квас 0,5', 'Напитки', None, 1.50, 500, None, 'pepsicola.jpg'),
    ('Pepsi 0,5', 'Напитки', None, 1.50, 500, None, 'pepsicola.jpg'),
    ('Mirinda 0,5', 'Напитки', None, 1.50, 500, None, 'pepsicola.jpg'),
    ('7up 0,5', 'Напитки', None, 1.50, 500, None, 'pepsicola.jpg'),
    ('Pepsi 0,33', 'Напитки', None, 1.30, 330, None, 'pepsicola.jpg'),
    ('Mirinda 0,33', 'Напитки', None, 1.30, 330, None, 'pepsicola.jpg'),
    ('7up 0,33', 'Напитки', None, 1.30, 330, None, 'pepsicola.jpg'),
    ('Pepsi 0,25', 'Напитки', None, 1.30, 250, None, 'pepsicola.jpg'),
    ('Mirinda 0,25', 'Напитки', None, 1.30, 250, None, 'pepsicola.jpg'),
    ('7up 0,25', 'Напитки', None, 1.30, 250, None, 'pepsicola.jpg'),
    ('Сок 1л', 'Напитки', None, 3.50, 1000, None, 'pepsicola.jpg'),
    ('Сок 0,2л', 'Напитки', None, 1.50, 200, None, 'pepsicola.jpg'),
    ('Молочные коктейли', 'Напитки', None, 2.80, 200, None, 'coctail.jpg'),
    ('Чай и кофе', 'Напитки', None, 2.00, 200, None, 'tea_coffee.jpg')
)


# categories = get_categories()
# add_products(product_list)

# ============================  Usage =============================
