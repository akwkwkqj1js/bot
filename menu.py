from aiogram import types
from utils.mydb import *


main_menu_btn = [
    '🛒 Каталог',
    '👤 Профиль',
    '/adm'
]

admin_sending_btn = [
    '✅ Начать', # 0
    '🔧 Отложить', # 1
    '❌ Отменить' # 2
]

to_close = types.InlineKeyboardMarkup(row_width=3)
to_close.add(
    types.InlineKeyboardButton(text='❌', callback_data='to_close')
)


def pact():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='Согласен ✅', callback_data='pact_accept'),
    )

    return markup


def admin_sending_info(all_msg, good, bad):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='⚪️Всего: %s' % all_msg, callback_data='sending'),
        types.InlineKeyboardButton(text='✅GOOD: %s' % good, callback_data='sending'),
        types.InlineKeyboardButton(text='❌BAD: %s' % bad, callback_data='sending'),
    )

    return markup


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(main_menu_btn[0], main_menu_btn[1])

    conn, cursor = connect()

    cursor.execute(f'SELECT * FROM buttons')
    base = cursor.fetchall()

    x1 = 0
    x2 = 1
    try:
        for i in range(len(base)):
            markup.add(
                base[x1][0],
                base[x2][0],
            )

            x1 += 2
            x2 += 2
    except Exception as e:
        try:
            markup.add(
                base[x1][0],
            )
        except:
            return markup

    return markup


def dep_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='Пополнить | QIWI ', callback_data='qiwi'),
    )

    return markup


def payment_menu(url):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='👉 Перейти к оплате 👈', url=url),
    )

    return markup


def admin_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='ℹ️ Информация о сервере', callback_data='admin_info_server'),
        types.InlineKeyboardButton(text='ℹ️ Информация', callback_data='admin_info'),
        types.InlineKeyboardButton(text='🔧 Изменить баланс', callback_data='give_balance'),
        types.InlineKeyboardButton(text='⚙️ Управление каталогами/товарами', callback_data='admin_main_settings'),
        #types.InlineKeyboardButton(text='⚙️ Настройки бота', callback_data='admin_settings'),
        types.InlineKeyboardButton(text='⚙️ Рассылка', callback_data='email_sending'),
        types.InlineKeyboardButton(text='⚙️ Кнопки', callback_data='admin_buttons'),
        types.InlineKeyboardButton(text='⚙️ Cоздать купон', callback_data='create_cupons'),
        )

    return markup


def admin_main_settings():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='⚙️ Каталоги', callback_data='admin_catalogs'),
        types.InlineKeyboardButton(text='⚙️ Подкаталоги', callback_data='admin_subdirectories'),
        types.InlineKeyboardButton(text='⚙️ Товар', callback_data='admin_products'),
        types.InlineKeyboardButton(text='« Назад', callback_data='back_to_admin_menu'),
        )

    return markup


def admin_subdirectories():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='🔧 Добавить', callback_data='admin_subdirectory_add'),
        types.InlineKeyboardButton(text='🔧 Удалить', callback_data='admin_subdirectory_del'),
        types.InlineKeyboardButton(text='« Назад', callback_data='admin_main_settings'),
    )

    return markup


def admin_catalogs():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='🔧 Добавить', callback_data='admin_catalog_add'),
        types.InlineKeyboardButton(text='🔧 Удалить', callback_data='admin_catalog_del'),
        types.InlineKeyboardButton(text='« Назад', callback_data='admin_main_settings'),
        )

    return markup


def admin_products(admin_flag=True):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(text='🔧 Загрузить товар', callback_data='admin_product_upload'),
        types.InlineKeyboardButton(text='🔧 Добавить', callback_data='admin_product_add'),
        types.InlineKeyboardButton(text='🔧 Удалить', callback_data='admin_product_del'),
        )
    if admin_flag:
        markup.add(types.InlineKeyboardButton(text='« Назад', callback_data='admin_main_settings'))

    return markup


def email_sending():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add( 
        types.InlineKeyboardButton(text='✔️ Рассылка(только текст)', callback_data='email_sending_text'), 
        types.InlineKeyboardButton(text='✔️ Рассылка(текст + фото)', callback_data='email_sending_photo'),
        types.InlineKeyboardButton(text='ℹ️ Информация о выделениях', callback_data='email_sending_info')
    )

    return markup


def admin_sending():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        admin_sending_btn[0],
        admin_sending_btn[1],
        admin_sending_btn[2],
    )

    return markup


def admin_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='🔧 Добавить', callback_data='admin_buttons_add'),
        types.InlineKeyboardButton(text='🔧 Удалить', callback_data='admin_buttons_del'),
        types.InlineKeyboardButton(text='« Назад', callback_data='back_to_admin_menu')
    )

    return markup


def buy(product, catalog):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='Купить', callback_data=f'buy_{product}'),
        types.InlineKeyboardButton(text='Назад', callback_data=f'catalog:{catalog}'),
    )

    return markup


def download(product_code):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(text='Скачать', callback_data=f'download_{product_code}'),
    )

    return markup


def profile():
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='💳 Пополнить баланс', callback_data='deposit_profile'),
         types.InlineKeyboardButton(text='🤑 Вывод средств', callback_data='withdraw')],
        [types.InlineKeyboardButton(text='🤝 Начать сделку', callback_data='search_seller')],
        [types.InlineKeyboardButton(text='🛍 Мои покупки', callback_data='profile_my_purchase'),
         types.InlineKeyboardButton(text='👥 Реферальная сеть', callback_data='ref')],
        [types.InlineKeyboardButton(text='🎁 Халява', callback_data='activate_promocode')],
    ])

    return markup


def trust_user(user_id, product_id, catalog_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="Одобрить", callback_data=f'agree:{user_id}'),
        types.InlineKeyboardButton(text="Отклонить", callback_data=f'decline:{user_id}:{product_id}:{catalog_id}')
    ]])


def manage_seller(user_id, product_id, catalog_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Удалить товар", callback_data=f'del_product:{product_id}:{catalog_id}')],
        [types.InlineKeyboardButton(text="Отменить продавца", callback_data=f'del_seller:{user_id}')]
    ])


def cancel_button(back=False):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=f"<< {'Отмена' if not back else 'Назад'}", callback_data='admin_products')
    ]])


def choose_role():
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="Я продавец", callback_data='search_seller_'),
        types.InlineKeyboardButton(text="Я покупатель", callback_data='search_seller_0')
    ]])


def prepare_dealing(dealing_id, init=True, is_clarify=False):
    if init:
        return types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="Отменить сделку", callback_data=f'dealing_cancel_{dealing_id}')
        ]])
    else:
        markup = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="Одобрить", callback_data=f"dealing_accept_{dealing_id}"),
            types.InlineKeyboardButton(text="Отклонить", callback_data=f'dealing_cancel_{dealing_id}')
        ]])
        if not is_clarify:
            markup.add(types.InlineKeyboardButton(text="Уточнить условия", callback_data=f'dealing_clarify_{dealing_id}'))
        return markup


def open_dealing(dealing_id, is_seller=True):
    if not is_seller:
        return types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="Написать сообщение", callback_data=f'dealing_message_{dealing_id}')
        ]])
    else:
        return types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text="Написать сообщение", callback_data=f'dealing_message_{dealing_id}'),
            types.InlineKeyboardButton(text="Условия выполнены!", callback_data=f'dealing_confirmcond_{dealing_id}')
        ]])


def confirm_dealing(dealing_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="Да, соглашусь", callback_data=f'dealing_success_{dealing_id}'),
        types.InlineKeyboardButton(text="Нет, поспорю", callback_data=f'dealing_suspend_{dealing_id}')
    ]])


def cancel_clarify_button(dealing_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="<< Назад", callback_data=f'dealing_{dealing_id}')
    ]])


def dealing_update_button(dealing_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="Обновить", callback_data=f'dealing_update_{dealing_id}')
    ]])


def dealing_link_button(dealing_id):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Назначить обсуждения", callback_data=f'dealing_link_{dealing_id}')],
        [types.InlineKeyboardButton(text="Закрыть сделку", callback_data=f'dealing_success_{dealing_id}')]
    ])


def withdraw(cancel=False):
    return types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="Киви", callback_data='withdraw_qiwi'),
    ]]) if not cancel else types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="<< Назад", callback_data='withdraw')
    ]])
