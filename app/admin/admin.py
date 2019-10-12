#!/usr/bin/env python3

import csv
import os
import os.path as op
import logging
from logging.handlers import RotatingFileHandler

from datetime import datetime
from sqlalchemy import func, or_, and_
from sqlalchemy.event import listens_for
from jinja2 import Markup

from flask import Flask, url_for, redirect, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy

import flask_admin as admin

from flask_admin import form
from flask_admin import helpers as admin_helpers
from flask_admin.contrib import sqla

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, current_user
from flask_security.utils import encrypt_password

# Create application
app = Flask(__name__, static_folder='uploads')
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

#  logging
logger = logging.getLogger('flask_admin')
logger.setLevel(logging.INFO)
flask_admin_logs_handler = RotatingFileHandler(
    'flask_admin.log', maxBytes=2000, backupCount=10)
logger.addHandler(flask_admin_logs_handler)

#  gunicorn logging
#  gunicorn --workers=0 --bind=0.0.0.0:8000 --log-level=warning app:app
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

#  Migration
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

#  Create directory for file fields to use
file_path = op.join(op.dirname(__file__), 'uploads')
try:
    os.mkdir(file_path)
except OSError:
    pass

#  Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String(255))
    username = db.Column(db.String, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    orders = db.relationship('Order', backref='owner')
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return "{}, {}".format(self.user_id, self.username)

    def __repr__(self):
        return "{}: {}".format(self.id, self.__str__())


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
    phone = db.Column(db.String)
    cart = db.Column(db.String)
    date = db.Column(db.DateTime(timezone=True), server_default=func.now())
    address = db.Column(db.String)
    payment_type = db.Column(db.String)
    status = db.Column(db.String)
    price = db.Column(db.Float)

    def __str__(self):
        return str(self.id)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    category = db.Column(db.String)
    subcategory = db.Column(db.String)
    price = db.Column(db.Float)
    weight = db.Column(db.String)
    composition = db.Column(db.String)
    img_name = db.Column(db.Unicode(64))
    img_path = db.Column(db.Unicode(128))

    def __unicode__(self):
        return self.name


# Delete hooks for models, delete files if models are getting deleted
@listens_for(Product, 'after_delete')
def del_image(mapper, connection, target):
    if target.path:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path,
                              form.thumbgen_filename(target.path)))
        except OSError:
            pass


# Flask views
@app.route('/')
def index():
    return render_template('index.html')


class UserAdmin(sqla.ModelView):
    action_disallowed_list = ['delete', ]
    column_display_pk = True
    column_list = [
        'user_id',
        'username',
        'first_name',
        'phone',
        'date_of_birth',
        'date',
        'orders'
    ]
    column_default_sort = [('last_name', False), ('first_name', False)]  # sort on multiple columns
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'xls']

    # setup create & edit forms so that only 'available' pets can be selected
    def create_form(self):
        return self._use_filtered_parent(
            super(UserAdmin, self).create_form()
        )

    def edit_form(self, obj):
        return self._use_filtered_parent(
            super(UserAdmin, self).edit_form(obj)
        )

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
                )

    def _use_filtered_parent(self, form):
        form.orders.query_factory = self._get_parent_list
        return form

    def _get_parent_list(self):
        # only show available pets in the form
        # return Order.query.filter_by(available=True).all()
        return Order.query.all()


class OrderAdmin(sqla.ModelView):
    action_disallowed_list = ['delete', ]
    column_list = [
        'id',
        'user_id',
        'phone',
        'address',
        'date',
        'cart',
        'price',
        'payment_type',
        'status'
    ]
    column_display_pk = True
    column_default_sort = [('user_id', False), ('date', False)]  # sort on multiple columns
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'xls']

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
                )


class ProductAdmin(sqla.ModelView):
    action_disallowed_list = ['delete', ]
    column_list = [
        'id',
        'title',
        'category',
        'subcategory',
        'price',
        'weight',
        'composition',
        'img_path'
    ]
    column_display_pk = True
    can_export = True
    export_max_rows = 1000
    export_types = ['csv', 'xls']

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
                )

    def _list_thumbnail(view, context, model, name):
        if not model.img_path:
            return ''

        return Markup('<img src="%s">' % url_for('static',
                                                 filename=form.thumbgen_filename(model.img_path)))

    column_formatters = {
        'img_path': _list_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'img_path': form.ImageUploadField(
            'Image',
            base_path=file_path,
            thumbnail_size=(40, 40, True))
    }


class RoleView(sqla.ModelView):
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')
                )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


# Create admin
admin = admin.Admin(
    app,
    name='Tutaka',
    base_template='my_master.html',
    template_mode='bootstrap3'
    )

# Add views
admin.add_view(UserAdmin(User, db.session))
admin.add_view(OrderAdmin(Order, db.session))
admin.add_view(ProductAdmin(Product, db.session))
admin.add_view(RoleView(Role, db.session))


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

# ===========================  DB wrapper ===========================
# ============================  Usage =============================

# Source https://github.com/pybites/pytip/tree/master/tips


def export_orders_to_file():
    outfile = open('orders.csv', 'w')
    outcsv = csv.writer(outfile)
    records = db.session.query(Order).all()
    [outcsv.writerow([getattr(curr, column.name) for column in Order.__mapper__.columns]) for curr in records]
    outfile.close()


def get_categories():
    categories = db.session.query(Product.category).group_by(Product.category).all()
    categories = [r for r, in categories]
    return categories


def get_subcategories(category):
    subcats = db.session.query(Product.subcategory).filter(Product.category == category).group_by(Product.subcategory).all()
    subcats = [r for r, in subcats]
    return subcats


def get_products_by_category(category):
    # TODO make this function work with categories and subcategories
    products = db.session.query(Product.title).filter(or_(
        Product.category == category,
        Product.subcategory == category
    )).all()
    products = [r for r, in products]
    return products


def get_user(user_id):
    user = db.session.query(User).filter(User.user_id == user_id).first()
    return user


def get_all_users():
    users = db.session.query(User).all()
    return users


def add_user(user):
    db.session.add(User(
        user_id=user['id'],
        username=user['username'],
        first_name=user['first_name'],
        last_name=user['last_name'],
        date=datetime.now()
    ))
    db.session.commit()
    db.session.close()


def update_user(user_id, column_name, value):
    db.session.query(User).filter(User.user_id == user_id).update({column_name: value})
    db.session.commit()
    db.session.close()


def build_sample_db():
    db.drop_all()
    db.create_all()

    with app.app_context():
        user_role = Role(name='user')
        super_user_role = Role(name='superuser')
        db.session.add(user_role)
        db.session.add(super_user_role)
        db.session.commit()

        test_user = user_datastore.create_user(
            first_name='Admin',
            email='admin',
            password=encrypt_password('dukiforever'),
            roles=[user_role, super_user_role]
        )

        db.session.commit()


def add_products(product_list):
    for p in product_list:
        db.session.add(Product(
            title=p[0],
            category=p[1],
            subcategory=p[2],
            price=p[3],
            weight=p[4],
            composition=p[5],
            img_name=p[6],
            img_path=p[6]
            ))
    db.session.commit()


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
    db.session.add(order)
    db.session.flush()
    db.session.refresh(order)
    order_id = order.id
    db.session.commit()
    db.session.close()
    return order_id


def update_order(order_id, column_name, value):
    db.session.query(Order).filter(Order.id == order_id).update({column_name: value})
    db.session.commit()
    db.session.close()


def is_existing_category(text):
    cat = db.session.query(Product).filter(
        or_(
            Product.category == text,
            Product.subcategory == text
            )
    ).first()
    return True if cat else False


def get_product(product, category):
    return db.session.query(Product).filter(and_(
        Product.title == product,
        or_(
            Product.category == category,
            Product.subcategory == category
            )
    )).first()


def get_product_by_id(id):
    p = db.session.query(Product).filter(Product.id == id).first()
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


# ============================  Usage =============================

if __name__ == '__main__':
    app_dir = op.realpath(os.path.dirname(__file__))
    database_path = op.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()
        add_products(product_list)

    # Start app
    app.run(port=5001)
