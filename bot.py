import config
import logging
import utils
import bot_db as db

from datetime import datetime
from telegram import ReplyKeyboardMarkup, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          CallbackQueryHandler, Filters,
                          RegexHandler, ConversationHandler, PicklePersistence)

# Enable logging
logging.basicConfig(
    filename='bot.log',
    filemode='a+',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

INITIAL, NAME, PHONE, BIRTHDAY, CHOOSING_CATEGORY, CHOOSING_SUBCATEGORY, CHOOSING_PRODUCT, TYPING_QUONTITY, EDITING_CART, ORDERING, CHOOSING_PAYMENT = range(11)


def start(update, context):
    chat = utils.get_chat(context, update)
    chat_id = chat.effective_chat.id
    user = update.message.from_user

    if utils.is_new_user(user.id):
        db.add_user(user)
        update.message.reply_text(
            f"Добрый день!\n"
            f"Добро пожаловать в виртуальный помощник службы доставки еды")
        update.message.reply_text(
            f"Давайте пройдем быструю регистрацию.\n"
            f"Как Вас зовут? (в формате ФИО)"
        )
        return NAME
    else:
        update.message.reply_text(
            config.text['select_menu'],
            reply_markup=utils.get_start_kb()
            )
    context.user_data.clear()

    return CHOOSING_CATEGORY


def cart_handler(update, context):

    if 'cart' not in context.user_data:
        update.message.reply_text(
            config.text['empty_card']
        )
        return start(update, context)
    else:
        update.message.reply_text(
            utils.generate_cart_reply_text(context.user_data),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=utils.get_cart_kb(context.user_data['cart'])
        )
    return EDITING_CART


def user_name_handler(update, context):
    name = update.message.text
    user = update.message.from_user
    utils.validate_name(name)
    db.update_user(user['id'], 'first_name', name)
    update.message.reply_text(
            f"Какой у Вас номер {name}?\n"
            f"Отправьте или введите ваш номер телефона: +375 ** *** ****")
    return PHONE


def user_phone_handler(update, context):
    # TODO add phone number validation
    # +998 66 123 1234
    phone = update.message.text
    user = update.message.from_user
    name = db.get_user(user['id']).first_name
    db.update_user(user['id'], 'phone', phone)

    update.message.reply_text(
        f"🎂 {name}, когда Вас поздравить с днем рождения?\n"
        f"Введите в формате дд.мм.гггг:"
    )
    return BIRTHDAY


def user_birthday_handler(update, context):
    # TODO add birth_date validation
    user = update.message.from_user
    date_of_birth = update.message.text
    try:
        date_of_birth = datetime.strptime(date_of_birth, '%d.%m.%Y')
        db.update_user(user['id'], 'date_of_birth', date_of_birth)
        update.message.reply_text(
            config.text['select_menu'],
            reply_markup=utils.get_start_kb()
        )
        return CHOOSING_CATEGORY

    except Exception as ex:
        logger.warning(ex)
        update.message.reply_text(
            'Введите в формате дд.мм.гггг:'
        )
        return BIRTHDAY


def select_category(update, context):
    user_data = context.user_data

    if utils.is_category(update.message.text):
        user_data.update({'category': update.message.text})

    try:
        if utils.has_subcategory(user_data['category']):
            update.message.reply_text(
                f'Это подкатегория!\n'
                f'Выбери тип',
                reply_markup=utils.get_categories_kb(user_data['category'])
            )
            return CHOOSING_CATEGORY
        else:
            update.message.reply_text(
                f'{update.message.text}\n'
                f'Выбери блюдо',
                reply_markup=utils.get_products_kb(user_data['category'])
            )
            return CHOOSING_PRODUCT

    except Exception as ex:
        print(f'{ex}')


def show_product(update, context):
    try:
        product = db.get_product(update.message.text, context.user_data['category'])
        context.user_data.update(
            product=product
            )
        desc = f'*{product.title}*\n\n'\
               f'{product.composition}\n'\
               f'{product.price} {config.text["currency"]}\n\n'\
               f'Выберите количество'
        update.message.reply_photo(
            photo=open(utils.get_image_path(product.image_url), 'rb'),
            caption=desc,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=utils.get_quontity_kb()
        )
        return TYPING_QUONTITY
    except Exception as ex:
        print(f'{ex}')


def add_to_cart_handler(update, context):
    # TODO check if quontity is INT

    if 'cart' not in context.user_data:
        context.user_data.update({'cart': []})
    try:
        context.user_data['cart'].append({
            'product_id': context.user_data['product'].id,
            'quontity': int(update.message.text)
            })
    except Exception as ex:
        logger.warning(ex)

    update.message.reply_text(
            f'Добавлено в корзину\n',
            reply_markup=utils.get_start_kb()
        )
    return CHOOSING_CATEGORY


def delete_item_handler(update, context):
    item = update.message.text
    cart = context.user_data['cart']

    cart = utils.delete_cart_item(cart, item)

    context.user_data.update(cart=cart)

    cart_handler(update, context)

    # return CHOOSING_CATEGORY


def clear_cart_handler(update, context):
    context.user_data['cart'].clear()
    update.message.reply_text(
        config.text['cleaned_cart']
    )
    start(update, context)


def order_handler(update, context):
    update.message.reply_text(
        config.text['select_order_type'],
        reply_markup=utils.get_order_type_kb()
    )
    return ORDERING


def delivery_handler(update, context):
    context.user_data.update(
        delivery_type=config.text['delivery'])
    update.message.reply_text(
        config.text['enter_address'],
        reply_markup=utils.get_delivery_kb()
    )
    return ORDERING


def self_pick_handler(update, context):
    context.user_data.update(
        delivery_type=config.text['self_pick'])
    update.message.reply_text(
        config.text['select_payment_type'],
        reply_markup=utils.get_payment_type_kb()
    )
    return ORDERING


def order_confirmation_handler(update, context):
    chat = utils.get_chat(context, update)
    chat_id = chat.effective_chat.id
    context.user_data.update(payment_type=update.message.text)
    update.message.reply_text(
        utils.generate_full_order_info(context.user_data, chat_id),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=utils.get_confirm_order_kb()
    )
    return ORDERING


def location_handler(update, context):
    if update.message.location:
        context.user_data.update(address=update.message.location)
    else:
        context.user_data.update(address=update.message.text)
    update.message.reply_text(
        config.text['select_payment_type'],
        reply_markup=utils.get_payment_type_kb()
    )
    return ORDERING


def cancel_order_handler(update, context):
    update.message.reply_text(
        'cancel_order_handler'
    )
    return INITIAL


def submit_order_handler(update, context):
    chat = utils.get_chat(context, update)
    chat_id = chat.effective_chat.id
    order_id = utils.add_order(context.user_data, chat_id)
    context.user_data.update(
        order_id=order_id)
    utils.send_message_to_admin(
        context.bot,
        utils.generate_full_order_info(context.user_data, chat_id),
        True,
        chat_id)
    update.message.reply_text(
        utils.generate_order_confirmation(
            context.user_data
        ),
        reply_markup=utils.get_start_kb()
    )
    done(update, context)


def delivery_time_handler(update, context):
    chat = utils.get_chat(context, update)
    chat_id = chat.effective_chat.id
    context.bot.send_message(
        chat_id=utils.get_user_id_from_callback(chat.callback_query.data),
        text=f'Ваш заказ будет доставлен в течении ' \
             f'{utils.get_delivery_time_from_callback(chat.callback_query.data)} ' \
             f'минут',
        reply_markup=utils.get_ok_ko_markup()
    )


def order_confirm_handler(update, context):
    message = utils.get_message(update, context)
    bot = utils.get_bot(update, context)

    bot.delete_message(
                chat_id=message.chat_id,
                message_id=message.message_id
                )
    message.reply_text(config.text['thank_you'])
    utils.send_message_to_admin(
        context.bot,
        f"Заказ {context.user_data['order_id']} *подтвержден*")
    utils.update_order_status(
        context.user_data['order_id'],
        'confirmed'
    )
    context.user_data.clear()


def order_cancel_handler(update, context):
    message = utils.get_message(update, context)
    bot = utils.get_bot(update, context)

    bot.delete_message(
                chat_id=message.chat_id,
                message_id=message.message_id
                )
    message.reply_text('Ваш заказ отменен')
    utils.send_message_to_admin(
        context.bot,
        f"Заказ {context.user_data['order_id']} *отменен*")
    utils.update_order_status(
        context.user_data['order_id'],
        'cancelled'
    )
    context.user_data.clear()


def done(update, context):
    user_data = context.user_data

    # user_data.clear()
    # return ConversationHandler.END
    return INITIAL


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    persistence = PicklePersistence(filename='conversation')
    updater = Updater(
        config.BOT_TOKEN,
        persistence=persistence,
        use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start)],

        states={
            INITIAL: [
                MessageHandler(
                    Filters.regex(config.text['cart']), cart_handler),
                MessageHandler(
                    Filters.text, start)
                ],
            NAME: [MessageHandler(Filters.text, user_name_handler)],
            PHONE: [MessageHandler(Filters.text, user_phone_handler)],
            BIRTHDAY: [MessageHandler(Filters.text, user_birthday_handler)],
            CHOOSING_CATEGORY: [
                MessageHandler(
                    Filters.regex(config.text['back']), start),
                MessageHandler(
                    Filters.regex(config.text['cart']), cart_handler),
                MessageHandler(
                    Filters.text, select_category)
                ],
            CHOOSING_PRODUCT: [
                MessageHandler(
                    Filters.regex(config.text['back']), start),
                MessageHandler(
                    Filters.text & (
                        ~ Filters.regex(config.text['back']) | ~Filters.regex(config.text['cart'])),
                    show_product)
                ],
            TYPING_QUONTITY: [
                MessageHandler(
                    Filters.regex(config.text['back']), start),
                MessageHandler(
                    Filters.text & (~ Filters.regex(config.text['cart'])),
                    add_to_cart_handler)
                ],
            EDITING_CART: [
                MessageHandler(
                    Filters.text & Filters.regex('^❌\s.*'),
                    delete_item_handler),
                MessageHandler(
                    Filters.text & Filters.regex(config.text['clear']),
                    clear_cart_handler),
                MessageHandler(
                    Filters.text & Filters.regex(config.text['order']),
                    order_handler)
            ],
            ORDERING: [
                MessageHandler(
                    Filters.regex(config.text['delivery']),
                    delivery_handler),
                MessageHandler(
                    Filters.regex(config.text['self_pick']),
                    self_pick_handler),
                MessageHandler(
                    Filters.regex(config.text['terminal']),
                    order_confirmation_handler),
                MessageHandler(
                    Filters.regex(config.text['cash']),
                    order_confirmation_handler),
                MessageHandler(
                    Filters.regex(config.text['confirm']),
                    submit_order_handler),
                MessageHandler(
                    Filters.regex(config.text['cancel']),
                    cancel_order_handler),
                MessageHandler(
                    Filters.regex(config.text['back']),
                    cart_handler),
                MessageHandler(
                    Filters.text | Filters.location, location_handler)
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(
                    Filters.text, done, pass_user_data=True)
                    ]
        },

        fallbacks=[
            MessageHandler(
                    Filters.text & Filters.regex(config.text['order']),
                    order_handler),
            MessageHandler(Filters.regex(config.text['back']), start),
            MessageHandler(Filters.regex(config.text['cart']), cart_handler),
            MessageHandler(Filters.regex('^❌\s.*'), delete_item_handler),
            CallbackQueryHandler(
                    delivery_time_handler,
                    pattern='^.*delivery_time.*$',
                    pass_user_data=True),
            CallbackQueryHandler(
                    order_confirm_handler,
                    pattern='^.*order_confirm.*$'),
            CallbackQueryHandler(
                    order_cancel_handler,
                    pattern='^.*order_cancel.*$'),
            ],
        name="my_conversation",
        persistent=True,
        allow_reentry=True
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', start))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
