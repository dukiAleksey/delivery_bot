import bot_db as db
import config

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode

# ==============================  Database  ==============================


def get_product_list_by_category(category):
    return list('Твар - 1', 'Товар - 2')

# ==============================  Database  ==============================
# ==============================  Keyboards ==============================


def get_start_kb():
    return ReplyKeyboardMarkup(get_main_keyboard())


def get_cart_kb(cart):
    return ReplyKeyboardMarkup(get_cart_keyboard(cart))


def get_categories_kb(category):
    return ReplyKeyboardMarkup(get_categories_keyboard(category))


def get_products_kb(category):
    return ReplyKeyboardMarkup(get_products_keyboard(category))


def get_quontity_kb():
    return ReplyKeyboardMarkup(get_quontity_keyboard())


def get_order_type_kb():
    return ReplyKeyboardMarkup(get_order_type_keyboard())


def get_delivery_kb():
    return ReplyKeyboardMarkup(get_delivery_keyboard())


def get_payment_type_kb():
    return ReplyKeyboardMarkup(get_payment_type_keyboard())


def get_confirm_order_kb():
    return ReplyKeyboardMarkup(get_confirm_order_keyboard())


def get_skip_kb():
    return ReplyKeyboardMarkup(get_skip_keyboard())


# ==============================  Keyboards ==============================
# ===============================  Helpers ===============================


def get_main_keyboard():
    categories = db.get_categories()
    cats_buttons = list(group(categories))
    cats_buttons.append([config.text['cart']])
    return cats_buttons


def get_cart_keyboard(cart):
    # cart_buttons = []
    cart_buttons = list(group(
        get_items_in_cart(cart), 1))
    cart_buttons.append([config.text['back'], config.text['clear']])
    cart_buttons.append([config.text['order']])
    return cart_buttons


def get_products_keyboard(category=None):
    products = db.get_products_by_category(category)
    products_kb = list(group(products))
    products_kb.append([config.text['back']])
    return products_kb


def get_categories_keyboard(category=None):
    cats = db.get_subcategories(category)
    cats_kb = list(group(cats))
    cats_kb.append([config.text['back']])
    return cats_kb


def get_quontity_keyboard():
    quontity_kb = [['1', '2', '3', '4', '5'],
                   ['6', '7', '8', '9', '10'],
                   [config.text['back'], config.text['cart']]]
    return quontity_kb


def get_order_type_keyboard():
    order_type_kb = [[config.text['delivery'],
                      config.text['self_pick']],
                     [config.text['back'], config.text['cart']]]
    return order_type_kb


def get_delivery_keyboard():
    delivery_kb = [
        # [KeyboardButton(config.text['my_location'], request_location=True)],
                   [config.text['back'], config.text['menu']]]
    return delivery_kb


def get_payment_type_keyboard():
    payment_type_kb = [[config.text['cash'], config.text['terminal']],
                       [config.text['back'], config.text['menu']]]
    return payment_type_kb


def get_confirm_order_keyboard():
    payment_type_kb = [[config.text['confirm']],
                       [config.text['cancel']]]
    return payment_type_kb


def get_skip_keyboard():
    skip_kb = [[config.text['skip']]]
    return skip_kb


def group(lst, n=2):
    for i in range(0, len(lst), n):
        val = lst[i:i+n]
        # if len(val) == n:
        #     yield val
        # else:
        yield val


def get_query(context, update):
    if hasattr(update, 'callback_query'):
        return update.callback_query
    elif hasattr(context, 'callback_query'):
        return context.callback_query


def get_chat(context, update):
    if hasattr(update, 'effective_chat'):
        return update
    elif hasattr(context, 'effective_chat'):
        return context


def get_message(context, update):
    query = get_query(context, update)
    chat = get_chat(context, update)
    if hasattr(query, 'message'):
        return query.message
    else:
        return chat.message


def get_bot(context, update):
    if hasattr(context, 'bot'):
        return context.bot
    else:
        return update.bot


def is_new_user(user_id):
    return False if db.get_user(user_id) is not None else True


def validate_name(name):
    # TODO name validation
    return True


def get_user_data(user):
    chat = effective_chat.chat
    user = {}
    user.update({'id': chat.id})
    user.update({'first_name': chat.first_name}) if chat.first_name else user.update({'first_name': None})
    user.update({'last_name': chat.last_name}) if chat.last_name else user.update({'last_name': None})
    user.update({'username': chat.username}) if chat.username else user.update({'username': None})
    return user


def is_category(str):
    return db.is_existing_category(str)


def has_subcategory(category):
    # TODO get category and check for inner categories...
    cats = db.get_subcategories(category)
    cats = [x for x in cats if x is not None]  # removing [None] in list
    if cats:
        return True
    else:
        False


def calculate_cart_price(cart):
    total = [item['price'] * item['quontity'] for item in cart]
    return sum(total)


def calculate_delivery_price(order_price):
    if order_price >= config.free_delivery_price_level:
        return 0
    else:
        return config.delivery_price


def generate_cart_reply_text(data):

    if not data['cart']:
        return config.text['empty_card']

    for item in data['cart']:
        item.update(db.get_product_by_id(item['product_id']))

    cart_price = calculate_cart_price(data['cart'])
    delivery_price = 0
    cart_text = f'{config.text["cart"]}\n'

    for item in data['cart']:
        # f'I am {num:{".2f" if ppl else ""}}'
        cart_text += f'\n*{item["title"]}* {item["subcategory"] if item["subcategory"] else ""}\n' \
                     f'{item["quontity"]} x {item["price"]} = {item["quontity"] * item["price"]} ' \
                     f'{config.text["currency"]}\n'

    try:
        if data['delivery_type'] is not None:
            delivery_price = calculate_delivery_price(cart_price)
            cart_text += f'\n*Доставка* {delivery_price} {config.text["currency"]}\n'
    except KeyError:
        pass

    cart_text += f'\nИтого: {cart_price + delivery_price} {config.text["currency"]}'

    return cart_text


def delete_cart_item(cart, item):
    return list(filter(lambda i: i['title'] not in item, cart))


def get_items_in_cart(cart):
    items = []
    for item in cart:
        items.append(f'❌ {item["title"]} {item["subcategory"] if item["subcategory"] else ""}')
    return items


def add_order(data, chat_id):
    price = calculate_cart_price(data['cart']) + calculate_delivery_price(
        calculate_cart_price(data['cart'])
    )
    order_data = {}
    order_data['user_id'] = chat_id
    # order_data['cart'] = data['cart']
    order_data['delivery_type'] = data['delivery_type']
    order_data['address'] = data['address'] if 'address' in data else None
    order_data['payment_type'] = data['payment_type']
    order_data['status'] = 'initial'
    order_data['price'] = price
    order_data['cart'] = f''
    for item in data['cart']:
        order_data['cart'] += f'{item["title"]} '
        order_data['cart'] += f'{item["category"]} '
        order_data['cart'] += f'{item["subcategory"]} '
        order_data['cart'] += f'x {str(item["quontity"])} '
        order_data['cart'] += f' || '
    return db.add_order(order_data)


def generate_full_order_info(user_data, user_id):
    # TODO if delivery -> add address
    user = db.get_user(user_id)
    text = f'Ваш заказ:\n' \
           f'Телефон: {user.phone}\n' \
           f'Способ оплаты: {user_data["payment_type"]}\n' \
           f'Тип заказа: {user_data["delivery_type"]}\n'
    try:
        text += f'Address: {user_data["address"]}\n' if user_data["address"] else f''
    except:
        pass
    try:
        text += f'Координаты: {user_data["location"]}\n' if user_data["location"] else f''
    except:
        pass
    text += f'\n'
    cart_text = generate_cart_reply_text(user_data)
    return text + cart_text


def generate_order_confirmation(data):
    text = f'Ваш заказ #47014 передан на обработку.\n' \
           f'Сейчас Вам вышлют препологаемое время доставки.'
    return text


def update_order_status(order_id, status):
    db.update_order(order_id, 'status', status)


def generate_time_suggest_reply_keyb(chat_id):
    keyb_time_suggestion = [
            [InlineKeyboardButton("30 минут", callback_data=f'delivery_time_30_{chat_id}'),
             InlineKeyboardButton("45 минут", callback_data=f'delivery_time_45_{chat_id}'),
             InlineKeyboardButton("60 минут", callback_data=f'delivery_time_60_{chat_id}')]
        ]
    return keyb_time_suggestion


def send_message_to_admin(bot, message, time_keys=False, chat_id=False):
    if time_keys and chat_id is not False:
        markup_time_suggestion = InlineKeyboardMarkup(generate_time_suggest_reply_keyb(chat_id))
    else:
        markup_time_suggestion = None

    bot.send_message(
        chat_id=config.admin_chat_id,
        text=message,
        reply_markup=markup_time_suggestion,
        parse_mode=ParseMode.MARKDOWN,)


def get_delivery_time_from_callback(data):
    return data.split('_')[-2]


def get_user_id_from_callback(data):
    return data.split('_')[-1]


def get_ok_ko_markup():
    ok_ko_markup = [
            [InlineKeyboardButton("OK", callback_data='order_confirm'),
             InlineKeyboardButton("Отменить заказ", callback_data='order_cancel')]
        ]
    ok_ko_markup = InlineKeyboardMarkup(ok_ko_markup)
    return ok_ko_markup


def get_image_path(filename):
    from pathlib import Path
    data_folder = Path('resources/menu')
    file_to_open = data_folder / filename
    return str(file_to_open.resolve())


# ===============================  Helpers ===============================
