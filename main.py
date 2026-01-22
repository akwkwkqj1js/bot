import io
import os

import logging
import types

import requests
from aiogram.utils.exceptions import Throttled

import config
import functions as func
import menu
import texts
import random
import time
import asyncio
import re
import threading
from datetime import datetime

from SystemInfo import SystemInfo
from dealing import Dealing

from states import *
from utils.user import *
from utils.catalog import *
from utils.product import *
from utils.mydb import *

import aiogram.utils.markdown as md

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from ast import literal_eval as leval

from AntiSpam import test, antibot

import traceback

# Configure logging

logging.basicConfig(
    # filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s : %(filename)s line - %(lineno)d : %(funcName)s : %(name)s : %(levelname)s : %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p')

bot = Bot(token=config.config('bot_token'), parse_mode='html')

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

cap4ed_list = {}


@dp.message_handler(commands="cancel", state="*")
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Операция отменена")


@dp.message_handler(commands=['start', 'help'], state='*')
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    if not await test(message, bot):
        return
    try:
        await dp.throttle('start', rate=2)
    except Throttled:
        return
    check = func.first_join(message.chat.id, message.chat.first_name, message.chat.username, message.text)
    if check[0] == True:
        try:
            await bot.send_message(
                chat_id=config.config('channel_id_main_logs'),
                text=f"""
Новый пользователь:
            
first_name : {message.chat.first_name}
username : {message.chat.username}
user_id : {message.chat.id}

Пригласил : {message.text}
    """
            )
        except:
            pass
        resp = requests.get("http://api.fl1yd.su/captcha")
        cap4ed_list[message.from_user.id] = (message.date.timestamp(), resp.headers.get("answer"))
        cap4a = io.BytesIO(resp.content)
        return await message.answer_photo(cap4a, caption='Введи капчу - защита от рейдеров. У тебя минута. Не справишься -   '
                                                         'возвращайся через пару минут 💍')

    if message.from_user.id in cap4ed_list:
        if cap4ed_list[message.from_user.id][0] + 60 < message.date.timestamp():
            func.del_user(message.from_user.id)
            del cap4ed_list[message.from_user.id]
            return await antibot(message, bot)
        return await message.answer("Капчу, сэр..")

    if User(message.from_user.id).pact == 'no':
        await func.pact(message.chat.id, message.message_id)
    else:
        await message.answer_video("https://i.gifer.com/5IUl.gif",
                                     reply_markup=menu.main_menu())


@dp.message_handler(commands=['admin'])
async def admin(message: types.Message):
    if str(message.chat.id) in str(config.config('admin_id_own')) \
            or str(message.chat.id) in [message.chat.id]:
        await message.answer('Панель Всевластия', reply_markup=menu.admin_menu())


@dp.message_handler()
async def send_message(message: types.Message, state: FSMContext):
    status = await test(message, bot)
    if status is False:
        return

    user_id = message.from_user.id
    if user_id in cap4ed_list:
        if cap4ed_list[user_id][0] + 60 < message.date.timestamp():
            func.del_user(user_id)
            del cap4ed_list[user_id]
            return await antibot(message, bot)
        if message.text.lower() != cap4ed_list[user_id][1]:
            return await message.answer(f"Не получилось, попробуй снова\n\nУ тебя осталось  "
                                        f"{int(cap4ed_list[user_id][0] + 60 - message.date.timestamp())} "
                                        f"секунд")
        else:
            del cap4ed_list[user_id]
            await message.answer("Капчу прошел - IQ из 3 цифр, значит можем продолжать")

    try:
        user = User(message.from_user.id)
    except:
        return await send_welcome(message, state)
    if user.pact == 'no':
        await func.pact(message.chat.id, message.message_id)
    else:
        chat_id = message.chat.id
        first_name = message.from_user.first_name
        username = message.from_user.username

        if message.text in func.btn_menu_list():
            await bot.send_message(chat_id=chat_id, text='Стартуем!', reply_markup=menu.main_menu())

            conn, cursor = connect()

            cursor.execute(f'SELECT * FROM buttons WHERE name = "{message.text}"')
            base = cursor.fetchone()

            with open(f'photos/{base[2]}.jpg', 'rb') as photo:
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=base[1], parse_mode='html')

        elif message.text == menu.main_menu_btn[0]:  # catalog
            await bot.send_message(chat_id=chat_id, text='Загрузка!', reply_markup=menu.main_menu())

            text = "Привет, дорогой друг 💍 \nЕсли хочешь видеть другие категории, и у тебя есть информация о ее актуальности, обратись с информацией к @yappy_meaw 🖥"
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=await Catalog().get_menu())

        elif message.text == menu.main_menu_btn[1]:  # profile
            await message.answer_video("https://i.gifer.com/5IUl.gif")

            user = User(chat_id)
            msg = texts.profile.format(
                id=chat_id,
                login=f'@{username}',
                data=user.date[:19],
                balance=round(user.balance, 2)
            )

            await bot.send_message(chat_id=chat_id, text=msg, reply_markup=menu.profile())


        elif '/adm' in message.text:
            if str(chat_id) in config.config('admin_id_own') or chat_id in [chat_id]:
                await bot.send_message(chat_id=chat_id, text='Укажите вариант рассылки',
                                       reply_markup=menu.email_sending())

        elif '/give' in message.text:
            if str(chat_id) in config.config('admin_id_own') or chat_id in [chat_id]:
                try:
                    user_id = message.from_user.id
                    first_name = message.from_user.first_name

                    gid = message.text.split(' ')[1]
                    gsum = float('{:.2f}'.format(float(message.text.split(' ')[2])))

                    if gsum <= 0:
                        await message.answer(text=f'❌ {first_name} неверная сумма')
                    else:
                        await User(user_id).give_money(bot, gid, gsum)

                except Exception as e:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=f'ℹ️ Неверная команда. /give user_id sum - Передать деньги пользователю')

        elif message.text.startswith('/d'):
            if "@" in message.text:
                message.text = message.text.split("@")[0]
            if message.text[2:].isnumeric():
                try:
                    dealing = Dealing(message.text[1:])
                    if User.admin4ek(user_id) \
                            and user_id not in [dealing.seller_id, dealing.customer_id]:
                        raise Exception("пизда")
                except:
                    return await message.answer("Инфа о данной сделке отсутствует в бд")
                markup = None
                if dealing.status == 'prepare':
                    markup = menu.prepare_dealing(dealing.dealing_id, dealing.check_init(user_id))
                elif dealing.status == 'clarify':
                    markup = menu.prepare_dealing(dealing.dealing_id, not dealing.check_init(user_id), True)
                elif dealing.status == 'open':
                    markup = menu.open_dealing(dealing.dealing_id, user_id == dealing.seller_id)
                elif dealing.status == 'confirm' and user_id == dealing.customer_id:
                    markup = menu.confirm_dealing(dealing.dealing_id)
                elif dealing.status == 'suspend' and not User.admin4ek(user_id):
                    markup = menu.dealing_link_button(dealing.dealing_id)
                return await message.answer(texts.dealing_text.format(
                    dealing_id=dealing.dealing_id,
                    seller_name=User(dealing.seller_id).username,
                    customer_name=User(dealing.customer_id).username,
                    condition=dealing.condition,
                    price=dealing.price)
                                            + texts.dealing_extend_text.format(
                    status=func.dealing_status_to_text(dealing.status),
                    date=dealing.date[:19]
                ), reply_markup=markup)

        elif message.text not in [
            menu.main_menu_btn[0],
            menu.main_menu_btn[1]] + func.btn_menu_list() and not re.search(r'BTC_CHANGE_BOT\?start=', message.text):
            if message.chat.id > 0:
                await message.answer('Команда не найдена!')

        # if message.text == '/test':
        #     x = await bot.send_message(chat_id=chat_id, text='testing')
        #     print(x['message_id'])


@dp.callback_query_handler()
async def handler_call(call: types.CallbackQuery, state: FSMContext):
    chat_id = call.from_user.id
    message_id = call.message.message_id
    first_name = call.from_user.first_name
    username = call.from_user.username

    logging.info(f' @{username} - {call.data}')

    if call.data == 'ref':
        user = User(chat_id)

        await bot.send_message(
            chat_id=chat_id,
            text=texts.ref.format(
                config.config("bot_login"),
                chat_id,
                0,
                0,
                config.config("ref_percent")
            ),
            reply_markup=menu.main_menu(),
            parse_mode='html', reply_to_message_id=message_id
        )

    if call.data == 'to_close':
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'admin_info_server':
        await bot.send_message(chat_id=chat_id, text='Данные загружаются, примерное время загрузки - хз')
        await bot.send_message(chat_id=chat_id, text=SystemInfo.get_info_text(),
                               parse_mode='html', reply_to_message_id=message_id)

    if call.data == 'profile_my_purchase':
        text, markup = await Product().get_data_purchases(chat_id)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, reply_to_message_id=message_id)

    if call.data[:13] == 'search_seller':
        data = call.data[13:]
        if data:
            is_seller = True if data != '_0' else False
            if is_seller and User(call.from_user.id).trusted != 1:
                await state.finish()
                await call.message.answer("Ты ещё не продавец, подай заявку или дождись её одобрения, если подал!")
                await call.message.delete()
            else:
                await state.set_data({'is_seller': is_seller})
                await SearchSeller.next()
                await call.message.answer(f"Введи юзернейм/айди {'продавца' if data == '_0' else 'покупателя'}, чтобы "
                                          f"начать с ним сделку.")
        else:
            await call.message.answer("Выбери свою роль в будущей сделке", reply_markup=menu.choose_role())

    if call.data == 'deposit_profile':
        await bot.send_message(
            chat_id=chat_id,
            text='Выберите способ пополнения\n\nЕсли не имеете возможности пополнить баланс через действующие методы,пишите мне в ЛС. Контакт: @yappy_meaw ',
            reply_markup=menu.dep_menu(),
            parse_mode='html',
            reply_to_message_id=message_id)

    if call.data.startswith('withdraw'):
        user = User(call.from_user.id)
        if user.balance - user.give_all_dealing_prices() <= 0:
            await call.message.answer("Недостаточно средств для вывода.")
        else:
            call_parts = call.data.split("_")
            if len(call_parts) == 1:
                await call.message.edit_text("Выбери предпочтительный способ вывода денежных средств:",
                                             reply_markup=menu.withdraw())
            if len(call_parts) == 2:
                if call_parts[1] == 'qiwi':
                    await Withdraw.qiwi.set()
                    await call.message.edit_text("Введи номер кошелька киви\n\nЧерез некоторое время после отправки "
                                                 "админ выведет средства с баланса по указанному номеру.",
                                                 reply_markup=menu.withdraw(True))


    if call.data == 'back_to_catalog':
        text = "Перед покупкой читай правила.\nЧтобы избежать технических проблем. "
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=await Catalog().get_menu())
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    if call.data == 'qiwi':
        response = func.deposit_qiwi(chat_id)

        date = str(datetime.now())[:19]

        await bot.send_message(
            chat_id=chat_id,
            text=texts.check_payment.format(
                config.config('qiwi_number'),
                response[0],
                date,
                '{:.0f}'.format(3600 - (time.time() - response[1]))
            ),
            reply_markup=response[2],
            parse_mode='html', reply_to_message_id=message_id
        )


    if call.data.split(':')[0] == 'download':
        try:
            with open(call.data.split(':')[1], 'rb') as txt:
                await bot.send_message(chat_id=chat_id, text='Жди загрузку товара')

                await bot.send_document(chat_id=chat_id, document=txt)
        except:
            await bot.send_message(chat_id=chat_id, text='Ошибка загрузки')

    if call.data.split(':')[0] == 'pay':
        # await Pay.confirm.set()

        # async with state.proxy() as data:
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])

        user = User(chat_id)
        product = Product()
        await product.get_info(product_id, catalog_id, None)

        if price <= user.balance - user.give_all_dealing_prices():
            await product.get_amount_products(product_id)

            if amount <= product.amount_products:
                # user.update_balance(-price)
                # if User.admin4ek(product.user_id):
                #     User(product.user_id).update_balance(price, deal=True)
                dealing_id = Dealing.new_dealing(product.user_id, chat_id, "Купля/продажа товара", price)
                dealing = Dealing(dealing_id)
                dealing.update_status("confirm")

                file_name = await product.get_products(product_id, amount)
                print(file_name)

                with open(file_name, 'rb') as txt:
                    await call.message.answer_video(
                        "https://i.gifer.com/5IUl.gif"
                    )

                    await bot.send_document(chat_id=chat_id, document=txt, reply_to_message_id=message_id)
                    await bot.send_message(chat_id, """🥳 Cпасибо за покупку!
По покупке товара создана сделка /{}

Очени качество товара и ответь нажатием на одну из кнопок ниже, считаешь ли данную сделку завершённой?""".format(dealing_id),
                                           reply_markup=menu.confirm_dealing(dealing_id))

                await product.purchases_log(file_name, chat_id, price, amount, product.user_id, dealing_id)
            else:
                await bot.send_message(chat_id=chat_id, text='❕ Товара в таком количестве больше нет',
                                       reply_to_message_id=message_id)
        else:
            await bot.send_message(chat_id=chat_id, text='Пополни баланс', reply_to_message_id=message_id)

            # await bot.send_message(chat_id=chat_id, text='Для подтверждения покупке отправьте Ок')

    if call.data.split(':')[0] == 'buy_menu_update':
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])
        update = int(call.data.split(':')[5])

        product = Product()
        await product.get_amount_products(product_id)

        if amount + update > 0:
            if product.amount_products >= amount + update:
                markup = await product.get_buy_menu(product_id, catalog_id, amount, price, update)

                await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)
            else:
                await call.answer('❕ Такого количества товара больше нет')
        else:
            await call.answer('❕ Минимальное количество для покупки 1 шт.')

    if call.data.split(':')[0] == 'buy':
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        amount = int(call.data.split(':')[3])
        price = float(call.data.split(':')[4])

        product = Product()

        text = await product.get_payment_text(product_id, catalog_id, amount, price)
        markup = await product.get_payment_menu(product_id, catalog_id, amount, price)

        await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, reply_markup=markup)

    if call.data == 'amount_product':
        await call.answer('♻️ Это количество товара')

    if call.data.split(':')[0] == 'preview_buy_menu':
        product = Product()
        await product.get_info(call.data.split(':')[1], call.data.split(':')[2], None)
        amount = await product.get_amount_products(call.data.split(':')[1])

        if int(amount) >= 1:
            markup = await Product().get_buy_menu(call.data.split(':')[1], call.data.split(':')[2])

            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=markup)
        else:
            await bot.send_message(chat_id=chat_id, text='Товар закончился, напишите ' +
                                                         ('в тех.поддержку' if not User.admin4ek(product.user_id)
                                                          else f'<a href="tg://user?id={product.user_id}">продавцу</a>'),
                                   reply_to_message_id=message_id)

    if call.data.split(':')[0] == 'product':
        subdirectory_id = None if len(call.data.split(':')) <= 3 else call.data.split(':')[3]
        product = Product()
        await product.get_info(call.data.split(':')[1], call.data.split(':')[2], subdirectory_id)
        text, photo = await Product().get_preview_text(call.data.split(':')[1], call.data.split(':')[2],
                                                       subdirectory_id=subdirectory_id)
        markup = await Product().get_preview_menu(call.data.split(':')[1], call.data.split(':')[2],
                                                  subdirectory_id=subdirectory_id,
                                                  user_id=User.admin4ek(product.user_id))

        await bot.send_photo(chat_id=chat_id, photo=open(photo, 'rb'), caption=text, reply_markup=markup)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data.split(':')[0] == 'catalog':
        markup = await Product().get_menu_products(call.data.split(':')[1])
        photo = await Catalog().get_catalog_photo(call.data.split(':')[1])

        with open(photo, 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=chat_id, caption='Выберите товар', reply_markup=markup)
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

        # await bot.send_message(chat_id=chat_id, text='Выберите товар', reply_markup=markup)
        # await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data.split(':')[0] == 'subdirectory':
        markup = await Product().get_menu_products(catalog_id=call.data.split(':')[2],
                                                   subdirectory_id=call.data.split(':')[1],
                                                   type_directory='subdirectory')
        photo = await Catalog().get_catalog_photo(subdirectory_id=call.data.split(':')[1])

        with open(photo, 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=chat_id, caption='Выберите товар', reply_markup=markup)
            await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'pact_accept':
        await func.pact_accept(chat_id)

        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        await bot.send_animation(animation='https://i.gifer.com/5IUl.gif',
                                 chat_id=chat_id, reply_markup=menu.main_menu())

    if call.data == 'cancel_payment':
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text='❕ Добро пожаловать!')

    if call.data == 'check_payment':
        check = func.check_payment(chat_id)
        if check[0] == 1:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                        text=f'✅ Оплата прошла\nСумма - {check[1]} руб')

        if check[0] == 0:
            await bot.send_message(chat_id=chat_id, text='❌ Оплата не найдена', reply_markup=menu.to_close,
                                   reply_to_message_id=message_id)

    if call.data == 'admin_info':
        await bot.send_message(
            chat_id=chat_id,
            text=func.admin_info(),
            reply_markup=menu.admin_menu()
        )
        await bot.delete_message(chat_id=chat_id, message_id=message_id)

    if call.data == 'give_balance':
        await Admin_give_balance.user_id.set()
        await bot.send_message(chat_id=chat_id, text='Введите ID человека, которому будет изменён баланс',
                               reply_to_message_id=message_id)

    if call.data == 'email_sending':
        await bot.send_message(chat_id=chat_id, text='Укажите вариант рассылки', reply_markup=menu.email_sending(),
                               reply_to_message_id=message_id)

    if call.data == 'email_sending_photo':
        await Email_sending_photo.photo.set()
        await bot.send_message(chat_id=chat_id, text='Отправьте фото боту, только фото!',
                               reply_to_message_id=message_id)

    if call.data == 'email_sending_text':
        await Admin_sending_messages.text.set()
        await bot.send_message(chat_id=chat_id, text='Введите текст рассылки', reply_to_message_id=message_id)

    if call.data == 'email_sending_info':
        await bot.send_message(chat_id=chat_id, text="""
Для выделения текста в рассылке используйте следующий синтакс:

1 | <b>bold</b>, <strong>bold</strong>
2 | <i>italic</i>, <em>italic</em>
3 | <u>underline</u>, <ins>underline</ins>
4 | <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
5 | <b>bold <i>italic bold <s>italic bold strikethrough</s> <u>underline italic bold</u></i> bold</b>
6 | <a href="http://www.example.com/">inline URL</a>
7 | <a href="tg://user?id=123456789">inline mention of a user</a>
8 | <code>inline fixed-width code</code>
9 | <pre>pre-formatted fixed-width code block</pre>
10 | <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
""", parse_mode='None', reply_to_message_id=message_id)
        await bot.send_message(chat_id=chat_id, text="""
Так это будет выглядить в рассылке:

1 | <b>bold</b>, <strong>bold</strong>
2 | <i>italic</i>, <em>italic</em>
3 | <u>underline</u>, <ins>underline</ins>
4 | <s>strikethrough</s>, <strike>strikethrough</strike>, <del>strikethrough</del>
5 | <b>bold <i>italic bold <s>italic bold strikethrough</s> <u>underline italic bold</u></i> bold</b>
6 | <a href="http://www.example.com/">inline URL</a>
7 | <a href="tg://user?id=123456789">inline mention of a user</a>
8 | <code>inline fixed-width code</code>
9 | <pre>pre-formatted fixed-width code block</pre>
10 | <pre><code class="language-python">pre-formatted fixed-width code block written in the Python programming language</code></pre>
""",
                               )

    if call.data == 'create_cupons':
        await Admin_create_cupons.admin_create_cupons.set()
        await bot.send_message(chat_id=chat_id, text='Введите данные в таком формате:\nНазвание купона\nФайл с логами',
                               reply_to_message_id=message_id)

    if call.data == 'activate_promocode':
        await activate_promocode(call.message)

    if call.data == 'admin_buttons':
        await bot.send_message(chat_id=chat_id, text='Настройки кнопок', reply_markup=menu.admin_buttons(),
                               reply_to_message_id=message_id)

    if call.data == 'admin_buttons_del':
        await Admin_buttons.admin_buttons_del.set()
        await bot.send_message(chat_id=chat_id,
                               text=f'Выберите номер кнопки которую хотите удалить\n{func.list_btns()}',
                               reply_to_message_id=message_id)

    if call.data == 'admin_buttons_add':
        await Admin_buttons.admin_buttons_add.set()
        await bot.send_message(chat_id=chat_id, text='Введите название кнопки',
                               reply_to_message_id=message_id)

    if call.data == 'admin_main_settings':
        await bot.send_message(chat_id=chat_id, text='⚙️ Основные настройки', reply_markup=menu.admin_main_settings())
        await call.message.delete()

    if call.data == 'admin_catalogs':
        await bot.send_message(chat_id=chat_id, text='⚙️ Настройка каталогов', reply_markup=menu.admin_catalogs())
        await call.message.delete()

    if call.data == 'admin_subdirectories':
        await bot.send_message(chat_id=chat_id, text='⚙️ Настройка каталогов', reply_markup=menu.admin_subdirectories())
        await call.message.delete()

    if call.data == 'admin_products':
        admin_flag = not bool(User.admin4ek(chat_id))
        if not admin_flag and User(chat_id).trusted == -1:
            await call.message.answer("Ты подал свою заявку на одобрение и она ещё не одобрена, дождись этого...")
        else:
            await bot.send_message(chat_id=chat_id, text='⚙️ Настройка продуктов',
                                   reply_markup=menu.admin_products(admin_flag))
        await call.message.delete()

    if call.data == 'admin_subdirectory_add':
        markup = await Catalog().get_menu_add_subdirectory()
        await bot.send_message(chat_id=chat_id, text='Укажите каталог в который хотите добавить товар',
                               reply_markup=markup, reply_to_message_id=message_id)

    if call.data.split(':')[0] == 'add_subdirectory':
        await AdminAddSubdirectory.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Введите название подкаталога', reply_to_message_id=message_id)

    if call.data == 'back_to_admin_menu':
        await bot.send_message(chat_id=chat_id, text='Меню админа', reply_markup=menu.admin_menu(),
                               reply_to_message_id=message_id)

    if call.data == 'admin_catalog_add':
        await AdminCatalogAdd.name.set()
        await bot.send_message(chat_id=chat_id, text='Введите название каталога', reply_to_message_id=message_id)

    if call.data == 'admin_catalog_del':
        markup = await Catalog().get_menu_del_catalogs()
        await bot.send_message(chat_id=chat_id, text='Укажите каталог который хотите удалить', reply_markup=markup,
                               reply_to_message_id=message_id)

    if call.data == 'admin_subdirectory_del':
        markup = await Catalog().get_menu_del_subdirectory()
        await bot.send_message(chat_id=chat_id, text='Укажите подкаталог', reply_markup=markup,
                               reply_to_message_id=message_id)

    if call.data.split(':')[0] == 'del_subdirectory':
        await AdminDelSubdirectory.confirm.set()

        async with state.proxy() as data:
            data['subdirectory_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Для подтверждения удаления подкаталога отправьте Ок',
                               reply_to_message_id=message_id)

    if call.data.split(':')[0] == 'del_catalog':
        await AdminCatalogDel.confirm.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

        await bot.send_message(chat_id=chat_id, text='Для подтверждения удаления каталога отправьте Ок',
                               reply_to_message_id=message_id)

    if call.data == 'admin_product_add':
        markup = await Catalog().get_menu_add_product()
        await bot.send_message(chat_id=chat_id, text='Укажите каталог в который хотите добавть товар',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'add_product_catalog':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup = await Catalog().get_menu_add_product_choosing(call.data.split(':')[1])
            await bot.send_message(chat_id=chat_id, text='В каталоге есть подкаталоги, Укажите дальнейшие действия',
                                   reply_markup=markup)
        else:
            await AdminAddProduct.name.set()

            async with state.proxy() as data:
                data['catalog_id'] = call.data.split(':')[1]

                await bot.send_message(chat_id=chat_id, text='Введите название товара',
                                       reply_markup=menu.cancel_button())
        await call.message.delete()

    if call.data.split(':')[0] == 'add_product_get_menu_subdirectory':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        markup = await Catalog().get_menu_add_product_subdirectory(product.subdirectories)
        await bot.send_message(chat_id=chat_id, text='Укажите подкаталог в который хотите добавить товар',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'add_product_in_subdirectory':
        await AdminAddProduct.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

            await bot.send_message(chat_id=chat_id, text='Введите название товара',
                                   reply_markup=menu.cancel_button())
            await call.message.delete()

    if call.data.split(':')[0] == 'add_product_in_catalog':
        await AdminAddProduct.name.set()

        async with state.proxy() as data:
            data['catalog_id'] = call.data.split(':')[1]

            await bot.send_message(chat_id=chat_id, text='Введите название товара',
                                   reply_markup=menu.cancel_button())
            await call.message.delete()

    if call.data == 'admin_product_del':
        markup = await Catalog().get_menu_del_product()
        await bot.send_message(chat_id=chat_id, text='Укажите каталог в котором хотите удалить товар',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'del_product_menu':
        markup = await Product().get_menu_del_product(call.data.split(':')[1],
                                                      user_id=User.admin4ek(chat_id))

        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup.add(types.InlineKeyboardButton(text='💫 ПОДКАТАЛОГИ 💫',
                                                  callback_data=f'del_product_menu_subdirectory:{call.data.split(":")[1]}'))

        await bot.send_message(chat_id=chat_id, text='Укажите товар который хотите удалить',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'del_product_menu_subdirectory':
        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        markup = await Catalog().get_menu_del_product(product.subdirectories)

        await bot.send_message(chat_id=chat_id, text='Укажите подкаталог',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'del_product_menu_2_subdirectory':
        markup = await Product().get_menu_del_product_subdirectories(call.data.split(':')[1],
                                                                     user_id=User.admin4ek(chat_id))

        await bot.send_message(chat_id=chat_id, text='Укажите товар который хотите удалить',
                               reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'del_product':
        product_id = call.data.split(':')[1]
        catalog_id = call.data.split(':')[2]
        if call.message.chat.id < 0 and not User.admin4ek(chat_id):
            await Product().del_product(product_id, catalog_id)
            await call.message.edit_caption(call.message.html_text + "\n\n<b>Удалено</b>")
        else:
            await AdminDelProduct.confirm.set()

            async with state.proxy() as data:
                data['product_id'] = product_id
                data['catalog_id'] = catalog_id

                await bot.send_message(chat_id=chat_id, text='Для подтверждения отправьте Ок')
        await call.message.delete()

    if call.data.split(':')[0] == 'del_seller':
        if call.message.chat.id < 0 and not User.admin4ek(chat_id):
            user_id = call.data.split(':')[1]
            User.give_trust(user_id, 0)
            await call.message.edit_caption(call.message.html_text + "\n\n<b>Разрешение торговать отозвано успешно</b>")
            await bot.send_message(user_id, "Сожалею, но теперь ты не можешь заниматься торговлей ввиду нарушений. "
                                            "Вопросы и жалобы - к администрации бота")

    if call.data == 'admin_product_upload':
        markup = await Catalog().get_menu_upload_product()
        await bot.send_message(chat_id=chat_id, text='Укажите каталог', reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'upload_catalog':
        markup = await Product().get_menu_upload_product(call.data.split(':')[1],
                                                         user_id=User.admin4ek(call.from_user.id))

        product = Product()
        await product.get_all_subdirectory_in_catalog(call.data.split(':')[1])

        if await Catalog().check_subdirectory_in_catalog(product.subdirectories):
            markup.add(types.InlineKeyboardButton(text='💫 ПОДКАТАЛОГИ 💫',
                                                  callback_data=f'upload_subdirectory:{call.data.split(":")[1]}'))

        await bot.send_message(chat_id=chat_id, text='Укажите товар', reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'upload_subdirectory':
        markup = await Product().get_menu_upload_subdirectory(call.data.split(':')[1])
        await bot.send_message(chat_id=chat_id, text='Укажите подкаталог', reply_markup=markup)
        await call.message.delete()

    if call.data.split(':')[0] == 'get_menu_upload_subdirectory':
        markup = await Product().get_menu_upload_product(catalog_id=call.data.split(':')[1],
                                                         subdirectory_id=call.data.split(':')[1],
                                                         user_id=User.admin4ek(call.from_user.id))
        await bot.send_message(chat_id=chat_id, text='Укажите товар', reply_markup=markup)

        await call.message.delete()

    if call.data.split(':')[0] == 'upload_product':
        await AdminUploadProduct.upload.set()

        async with state.proxy() as data:
            data['product_id'] = call.data.split(':')[1]
            data['catalog_id'] = call.data.split(':')[2]

        await bot.send_message(chat_id=chat_id, text='Отправьте файл с товаром\n\n1 строка = 1 товар',
                               reply_markup=menu.cancel_button())
        await call.message.delete()

    if call.data.split(':')[0] == 'agree':
        user_id = call.data.split(':')[1]
        ret = User.give_trust(int(user_id), 1)
        if ret:
            await call.message.edit_caption(call.message.html_text + "\n\n<b>Одобрено</b>")
            try:
                await bot.send_message(user_id,
                                       "Поздравляю, теперь ты можешь управлять своими товарами в этом боте!",
                                       reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                                           types.InlineKeyboardButton(text='⚙️ Управление товарами',
                                                                      callback_data='admin_products')
                                       ]]))
            except:
                pass

    if call.data.split(':')[0] == 'decline':
        user_id = call.data.split(':')[1]
        product_id = call.data.split(':')[2]
        catalog_id = call.data.split(':')[3]
        ret = User.give_trust(int(user_id), 0)
        if ret:
            await Product().del_product(product_id, catalog_id)
            await call.message.edit_caption(call.message.html_text + "\n\n<b>Отклонено</b>")
            try:
                await bot.send_message(user_id, "Твой запрос на управление товарами отклонён. Попробуй в другой раз "
                                                "Имей терпение и проверь свою заявку на правильность")
            except:
                pass

    if call.data.split(':')[0] == 'seller':
        user_id = call.data.split(':')[1]
        user = User(user_id)
        msg = texts.seller.format(
            id=user_id,
            login=f'{user.username}',
            data=user.date[:19],
        )
        await bot.send_message(chat_id=chat_id, text=msg, reply_to_message_id=message_id)

    if call.data.startswith("dealing_"):
        call_parts = call.data.split('_')
        if len(call_parts) == 2:
            message = call.message
            message.text = '/' + call_parts[-1]
            await send_message(message)
        if len(call_parts) == 3:
            dealing = Dealing(call_parts[-1])
            if call_parts[1] == 'update':
                try:
                    await call.message.edit_text(config.config("channel_id_main_logs"), texts.dealing_text.format(
                        dealing_id=dealing.dealing_id,
                        seller_name=User(dealing.seller_id).username,
                        customer_name=User(dealing.customer_id).username,
                        condition=dealing.condition,
                        price=dealing.price)
                                           + texts.dealing_extend_text.format(
                        status=func.dealing_status_to_text("prepare"),
                        date=dealing.date[:19]
                    ), reply_markup=menu.dealing_update_button(dealing.dealing_id))
                except:
                    return await call.answer("Ничего не поменялось")
            if call_parts[1] == 'accept' and dealing.status in ['prepare', 'clarify']:
                if dealing.status == 'prepare' and dealing.customer_id == call.from_user.id:
                    customer = User(dealing.customer_id)
                    if customer.balance - customer.give_all_dealing_prices() < dealing.price:
                        return await bot.send_message(dealing.customer_id, "Недостаточно средств на балансе, пополни его "
                                                                           "либо отмени сделку.")
                dealing.update_status("open")
                await bot.send_message(dealing.seller_id,
                                       f"Прекрасно, теперь тебе необходимо выполнить условия сделки /{dealing.dealing_id} и "
                                       f"нажать соответствующую кнопку...",
                                       reply_markup=menu.open_dealing(dealing.dealing_id))
                await bot.send_message(dealing.customer_id,
                                       f"Отлично, теперь необходимо дождаться выполнения условий сделки /{dealing.dealing_id}.\n"
                                       f"Ещё можно обмениваться сообщениями с покупателем, не выходя из бота...",
                                       reply_markup=menu.open_dealing(dealing.dealing_id, False))
            elif call_parts[1] == 'cancel' and dealing.status in ['prepare', 'clarify']:
                dealing.delete_dealing()
                ans = f"Сделка /{dealing.dealing_id} отменена"
                await bot.send_message(dealing.seller_id, ans)
                await bot.send_message(dealing.customer_id, ans)
            elif call_parts[1] == 'clarify' and dealing.status == 'prepare':
                await ClarifyCondition.clarify.set()
                await state.set_data({"dealing_id": dealing.dealing_id})
                await call.message.answer("Введи уточнения и/или дополнения к условиям сделки. Сделай это с толком, "
                                          "с чувством, с расстановкой...",
                                          reply_markup=menu.cancel_clarify_button(dealing.dealing_id))
            elif call_parts[1] == 'message' and dealing.status == 'open':
                await MessageDealing.message.set()
                await state.set_data({"dealing_id": dealing.dealing_id})
                await call.message.answer(f"Отправь одно сообщение {'продавцу' if call.from_user.id == dealing.customer_id else 'покупателю'}",
                                          reply_markup=menu.cancel_clarify_button(dealing.dealing_id))
            elif call_parts[1] == 'confirmcond' and dealing.status == 'open':
                dealing.update_status("confirm")
                await bot.send_message(dealing.customer_id, f"Продавец считает, что условия сделки /{dealing.dealing_id}"
                                                            f" выполнены. Согласишься с этим?",
                                       reply_markup=menu.confirm_dealing(dealing.dealing_id))
                await bot.send_message(dealing.seller_id, f"Условия сделки /{dealing.dealing_id} отмечены как "
                                                          f"выполненные. Осталось только подтверждение от покупателя, "
                                                          f"жди!")
            elif call_parts[1] == 'suspend' and dealing.status == 'confirm':
                dealing.update_status('suspend')
                await call.message.answer("Вот это поворот! Что ж, ожидай гаранта и ссылку на приватную беседу от "
                                          "него для урегулирования спора.")
                await bot.send_message(dealing.seller_id, f"Покупатель сделки /{dealing.dealing_id} считает, что условия"
                                                          f" выполнены не в полном объёме. Жди ссылку на приватную "
                                                          f"беседу от гаранта для урегулирования спора.")
                await bot.send_message(config.config("channel_id_main_logs"),
                                       f"Покупатель сделки /{dealing.dealing_id} считает, что условия"
                                       f" выполнены не в полном объёме. Создай приватный чат и отправь фигурантам "
                                       f"сделки ссылку на него.",
                                       reply_markup=menu.dealing_link_button(dealing.dealing_id))
            elif call_parts[1] == 'success' and dealing.status in ['confirm', 'suspend']:
                dealing.update_status("success")
                User(dealing.customer_id).update_balance(-dealing.price)
                User(dealing.seller_id).update_balance(dealing.price)
                ans = f"Сделка /{dealing.dealing_id} проведена успешно!"
                await call.message.answer(ans)
                await bot.send_message(dealing.seller_id, ans)
                await bot.send_message(config.config("channel_id_main_logs"), ans)
            elif call_parts[1] == 'link' and dealing.status == 'suspend':
                await LinkDealing.link.set()
                await state.set_data({"dealing_id": dealing.dealing_id})
                await call.message.answer(f"Отправь ссылку на чат для обсуждений спора по сделке /{dealing.dealing_id}")
        await call.message.delete()

    await bot.answer_callback_query(call.id)


@dp.callback_query_handler(lambda c: c.data in ["admin_products", 'withdraw'] or c.data.startswith("dealing_"), state='*')
async def admin_products_callback(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    call.message.from_user = call.from_user
    await handler_call(call, state)


@dp.message_handler(state=AdminAddSubdirectory.name)
async def admin_subdirectory_add_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    async with state.proxy() as data:
        data['name'] = message.text

    await AdminAddSubdirectory.next()
    await bot.send_message(chat_id=chat_id, text='Отправьте фото подкаталога')


@dp.message_handler(state=AdminAddSubdirectory.photo, content_types=['photo'])
async def admin_subdirectory_add_photo(message: types.Message, state: FSMContext):
    try:
        file_name = f'photos/subdirectory_{random.randint(0, 9999)}.jpg'
        await message.photo[-1].download(file_name)

        async with state.proxy() as data:
            name = data['name']
            catalog_id = data['catalog_id']

            await Catalog().create_subdirectory(catalog_id, name, file_name)

            await message.answer('✅ Подкаталог создан')

        await state.finish()
    except Exception as e:
        print(e)
        await state.finish()
        await message.answer(str(e))


@dp.message_handler(state=AdminUploadProduct.upload, content_types=['document'])
async def admin_upload(message: types.Message, state: FSMContext):
    try:
        file_name = f'docs/upload_{random.randint(0, 999999999999999)}.txt'
        await message.document.download(file_name)

        async with state.proxy() as data:
            data['file_name'] = file_name

        await AdminUploadProduct.next()
        await message.answer('Для подтверждения загрузки отправьте Ок')
    except:
        await state.finish()
        await  message.answer('Ошибка загрузки, принемаются только файлы')


@dp.message_handler(state=AdminUploadProduct.confirm)
async def admin_upload_confirm(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            data = await Product().upload_product(data['product_id'], data['file_name'])

            await message.answer(
                f'❕ Вы успешно загрузили товар\n\n✅ Успешно загружено строк: {data[0]}\n❌ Строк с ошибками: {data[1]}',
                reply_markup=menu.cancel_button(True))

            await bot.send_message(config.config("channel_id_main_logs"), )
    else:
        await message.answer('Вы отменили загрузку товара', reply_markup=menu.cancel_button(True))

    await state.finish()


@dp.message_handler(state=AdminDelProduct.confirm)
async def admin_del_product_confirm(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            await Product().del_product(data['product_id'], data['catalog_id'])

            await message.answer('Вы успешно удалили товар', reply_markup=menu.cancel_button(True))
    else:
        await message.answer('Вы отменили удаление', reply_markup=menu.cancel_button(True))

    await state.finish()


@dp.message_handler(state=AdminAddProduct.name)
async def admin_add_product_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

        await AdminAddProduct.next()

        await message.answer('Отправьте фото товара', reply_markup=menu.cancel_button())


@dp.message_handler(state=AdminAddProduct.photo, content_types=['photo'])
async def admin_add_product_photo(message: types.Message, state: FSMContext):
    try:
        file_name = f'photos/product_{random.randint(0, 9999)}.jpg'
        await message.photo[-1].download(file_name)

        async with state.proxy() as data:
            data['photo'] = file_name

            await AdminAddProduct.next()

            await message.answer('Введите описание товара', reply_markup=menu.cancel_button())
    except Exception as e:
        await state.finish()
        await message.answer(str(e))


@dp.message_handler(state=AdminAddProduct.description)
async def admin_add_product_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text

        await AdminAddProduct.next()

        await message.answer('Введите цену товара', reply_markup=menu.cancel_button())


@dp.message_handler(state=AdminAddProduct.price)
async def admin_add_product_price(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['price'] = float(message.text)

            await AdminAddProduct.next()

            await message.answer_photo(photo=open(data["photo"], 'rb'), caption=f"""
НАЗВАНИЕ: {data['name']}

ОПИСАНИЕ: {data['description']}

ЦЕНА: {data['price']} руб

Для подтверждения создания отправьте Ок""")

    except:
        await state.finish()
        await message.answer('Неверная цена', reply_markup=menu.cancel_button())


@dp.message_handler(state=AdminAddProduct.confirm)
async def admin_add_product_confirm(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            product_id = await Product().create_product(
                data['catalog_id'],
                data['name'],
                data['photo'],
                data['description'],
                data['price'],
                message.from_user.id
            )
            chat_id = message.from_user.id
            admin_flag = not bool(User.admin4ek(chat_id))
            if not admin_flag:
                if User(chat_id).trusted == 0:
                    User.give_trust(chat_id, -1)
                    await bot.send_photo(chat_id=config.config('channel_id_main_logs'),
                                         photo=open(data['photo'], 'rb'),
                                         caption=f"""
<a href='tg://user?id={chat_id}'>Юзверь</a> #id{chat_id} хочет торговать своим добром.

НАЗВАНИЕ: {data['name']}
ОПИСАНИЕ: {data['description']}
ЦЕНА: {data['price']} руб""",
                                         reply_markup=menu.trust_user(chat_id, product_id, data['catalog_id']))
                    await message.answer("Заявка на создание товара и в целом торговлю подана, жди, ожидай!")
                elif User(chat_id).trusted == 1:
                    await bot.send_photo(chat_id=config.config('channel_id_main_logs'),
                                         photo=open(data['photo'], 'rb'),
                                         caption=f"""
<a href='tg://user?id={chat_id}'>Юзверь</a> #id{chat_id} - новый товар.

НАЗВАНИЕ: {data['name']}
ОПИСАНИЕ: {data['description']}
ЦЕНА: {data['price']} руб""",
                                         reply_markup=menu.manage_seller(chat_id, product_id, data['catalog_id']))
                    await message.answer('Вы успешно добавили товар', reply_markup=menu.cancel_button(True))
                else:
                    await message.answer("Ты уже подал заявку на торговлю, жди одобрения...")
            else:
                await message.answer('Вы успешно добавили товар', reply_markup=menu.cancel_button(True))
    else:
        await message.answer('Создание отменено', reply_markup=menu.cancel_button())

    await state.finish()


@dp.message_handler(state=AdminCatalogDel.confirm)
async def admin_catalog_del(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            await Catalog().del_catalog(data['catalog_id'])

            await message.answer('Вы успешно удалили каталог', reply_markup=menu.cancel_button(True))
    else:
        await message.answer('Удаление каталога отменено', reply_markup=menu.cancel_button(True))

    await state.finish()


@dp.message_handler(state=AdminCatalogAdd.name)
async def admin_catalog_add_name(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    async with state.proxy() as data:
        data['name'] = message.text

    await AdminCatalogAdd.next()
    await bot.send_message(chat_id=chat_id, text='Отправьте фото каталога')


@dp.message_handler(state=AdminCatalogAdd.photo, content_types=['photo'])
async def admin_catalog_add_photo(message: types.Message, state: FSMContext):
    try:
        file_name = f'photos/catalog_{random.randint(0, 9999)}.jpg'
        await message.photo[-1].download(file_name)

        async with state.proxy() as data:
            name = data['name']

            await Catalog().create_catalog(name, file_name)

            await message.answer('✅ Каталог создан')

        await state.finish()
    except Exception as e:
        await state.finish()
        await message.answer(str(e))


@dp.message_handler(state=Pay.confirm)
async def pay_confirm(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if message.text == 'Ок':
        user = User(chat_id)
        product = Product()

        async with state.proxy() as data:
            if data['price'] <= user.balance - user.give_all_dealing_prices():
                await product.get_amount_products(data['product_id'])

                if data['amount'] <= product.amount_products:
                    # user.update_balance(-data['price'])

                    file_name = await product.get_products(data['product_id'], data['amount'])

                    with open(file_name, 'r', encoding='UTF-8') as txt:
                        await message.answer('Жди загрузку товара')

                        await bot.send_document(chat_id=chat_id, document=txt)

                    await product.purchases_log(file_name, chat_id, data['price'], data['amount'])
                else:
                    await message.answer('❕ Товара в таком количестве больше нет')
            else:
                await message.answer('Пополни баланс')
    else:
        await message.answer('Покупка отменена')

    await state.finish()


@dp.message_handler(state=Admin_give_balance.user_id)
async def admin_give_balance_1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.text

    await Admin_give_balance.next()
    await message.answer('Введите сумму на которую будет изменен баланс')


@dp.message_handler(state=Admin_give_balance.balance)
async def admin_give_balance_2(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['balance'] = float(message.text)

            await Admin_give_balance.next()
            await message.answer(f"""
ID: {data['user_id']}
Баланс изменится на: {round(data['balance'], 2)}

Для подтверждения отправьте Ок
""")
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_give_balance.confirm)
async def admin_give_balance_3(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            try:
                func.give_balance(data)
            except:
                await state.finish()
                return await message.answer("Такого юзверя нет в базе")

            await bot.send_message(chat_id=message.chat.id, text='✅ Баланс успешно изменен',
                                   reply_markup=menu.admin_menu())
    else:
        await message.answer('⚠️ Изменение баланса отменено')

    await state.finish()


@dp.message_handler(state=Email_sending_photo.photo, content_types=['photo'])
async def email_sending_photo_1(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['photo'] = random.randint(111111111, 999999999)

        await message.photo[-1].download(f'photos/{data["photo"]}.jpg')
        await Email_sending_photo.next()
        await message.answer('Введите текст рассылки')
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.text)
async def email_sending_photo_2(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['text'] = message.text

            with open(f'photos/{data["photo"]}.jpg', 'rb') as photo:
                await message.answer_photo(photo, data['text'])

            await Email_sending_photo.next()
            await message.answer('Укажи дальнейшее действие', reply_markup=menu.admin_sending())
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.action)
async def email_sending_photo_3(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        if message.text in menu.admin_sending_btn:
            if message.text == menu.admin_sending_btn[0]:  # Начать

                users = func.get_users_list()

                start_time = time.time()
                amount_message = 0
                amount_bad = 0
                async with state.proxy() as data:
                    photo_name = data["photo"]
                    text = data["text"]

                await state.finish()

                try:
                    m = await bot.send_message(
                        chat_id=config.config('admin_id_manager').split(':')[0],
                        text=f'✅ Рассылка в процессе',
                        reply_markup=menu.admin_sending_info(0, 0, 0))
                    msg_id = m['message_id']
                except:
                    pass

                for i in range(len(users)):
                    try:
                        with open(f'photos/{photo_name}.jpg', 'rb') as photo:
                            await bot.send_photo(
                                chat_id=users[i][0],
                                photo=photo,
                                caption=text,
                                reply_markup=menu.to_close
                            )
                        amount_message += 1
                    except Exception as e:
                        amount_bad += 1

                try:
                    await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                message_id=msg_id,
                                                text='✅ Рассылка завершена',
                                                reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                     amount_message,
                                                                                     amount_bad))
                except:
                    pass
                sending_time = time.time() - start_time

                try:
                    await bot.send_message(
                        chat_id=config.config('admin_id_manager').split(':')[0],
                        text=f'✅ Рассылка окончена\n'
                             f'👍 Отправлено: {amount_message}\n'
                             f'👎 Не отправлено: {amount_bad}\n'
                             f'🕐 Время выполнения рассылки - {sending_time} секунд'

                    )
                except:
                    pass

            elif message.text == menu.admin_sending_btn[1]:  # Отложить
                await Email_sending_photo.next()

                await bot.send_message(
                    chat_id=chat_id,
                    text="""
Введите дату начала рассылке в формате: ГОД-МЕСЯЦ-ДЕНЬ ЧАСЫ:МИНУТЫ

Например 2020-09-13 02:28 - рассылка будет сделана 13 числа в 2:28
"""
                )

            elif message.text == menu.admin_sending_btn[2]:
                await state.finish()

                await bot.send_message(
                    message.chat.id,
                    text='Рассылка отменена',
                    reply_markup=menu.main_menu()
                )

                await bot.send_message(
                    message.chat.id,
                    text='Меню админа',
                    reply_markup=menu.admin_menu()
                )
        else:
            await bot.send_message(
                message.chat.id,
                text='Не верная команда, повторите попытку',
                reply_markup=menu.admin_sending())

    except Exception as e:
        await state.finish()
        await bot.send_message(
            chat_id=message.chat.id,
            text='⚠️ ERROR ⚠️'
        )


@dp.message_handler(state=Email_sending_photo.set_down_sending)
async def email_sending_photo_4(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['date'] = message.text
            date = datetime.fromisoformat(data['date'])

            await Email_sending_photo.next()

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Для подтверждения рассылки в {date} отправьте Ок'
            )
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Email_sending_photo.set_down_sending_confirm)
async def email_sending_photo_5(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            data['type_sending'] = 'photo'

            func.add_sending(data)

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Рассылка запланирована в {data["date"]}',
                reply_markup=menu.admin_menu()
            )
    else:
        await bot.send_message(message.chat.id, text='Рассылка отменена', reply_markup=menu.admin_menu())

    await state.finish()


@dp.message_handler(state=Admin_sending_messages.text)
async def admin_sending_messages_1(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text

        await message.answer(data['text'])

        await Admin_sending_messages.next()
        await bot.send_message(
            chat_id=message.chat.id,
            text='Укажите дальнейшее действие',
            reply_markup=menu.admin_sending()
        )


@dp.message_handler(state=Admin_sending_messages.action)
async def admin_sending_messages_2(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    if message.text in menu.admin_sending_btn:
        if message.text == menu.admin_sending_btn[0]:  # Начать

            users = func.get_users_list()

            start_time = time.time()
            amount_message = 0
            amount_bad = 0

            async with state.proxy() as data:
                text = data['text']

            await state.finish()

            try:
                m = await bot.send_message(
                    chat_id=config.config('admin_id_manager').split(':')[0],
                    text=f'✅ Рассылка в процессе',
                    reply_markup=menu.admin_sending_info(0, 0, 0))
                msg_id = m['message_id']
            except Exception as e:
                print(str(e))

            for i in range(len(users)):
                try:
                    await bot.send_message(users[i][0], text, reply_markup=menu.to_close)
                    amount_message += 1
                except Exception as e:
                    amount_bad += 1

            try:
                await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                            message_id=msg_id,
                                            text='✅ Рассылка завершена',
                                            reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                 amount_message,
                                                                                 amount_bad))
            except:
                pass

            sending_time = time.time() - start_time

            try:
                await bot.send_message(
                    chat_id=config.config('admin_id_manager').split(':')[0],
                    text=f'✅ Рассылка окончена\n'
                         f'👍 Отправлено: {amount_message}\n'
                         f'👎 Не отправлено: {amount_bad}\n'
                         f'🕐 Время выполнения рассылки - {sending_time} секунд',
                    reply_markup=types.ReplyKeyboardRemove()
                )
            except:
                print('ERROR ADMIN SENDING')

        elif message.text == menu.admin_sending_btn[1]:  # Отложить
            await Admin_sending_messages.next()

            await bot.send_message(
                chat_id=chat_id,
                text="""
Введите дату начала рассылке в формате: ГОД-МЕСЯЦ-ДЕНЬ ЧАСЫ:МИНУТЫ

Например 2020-09-13 02:28 - рассылка будет сделана 13 числа в 2:28
"""
            )

        elif message.text == menu.admin_sending_btn[2]:
            await bot.send_message(
                message.chat.id,
                text='Рассылка отменена',
                reply_markup=menu.main_menu()
            )
            await bot.send_message(
                message.chat.id,
                text='Меню админа',
                reply_markup=menu.admin_menu()
            )
            await state.finish()
        else:
            await bot.send_message(
                message.chat.id,
                text='Не верная команда, повторите попытку',
                reply_markup=menu.admin_sending())


@dp.message_handler(state=Admin_sending_messages.set_down_sending)
async def admin_sending_messages_3(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['date'] = message.text
            date = datetime.fromisoformat(data['date'])

            await Admin_sending_messages.next()

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Для подтверждения рассылки в {date} отправьте Ок'
            )
    except:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_sending_messages.set_down_sending_confirm)
async def admin_sending_messages_4(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            data['type_sending'] = 'text'
            data['photo'] = random.randint(111111, 9999999)

            func.add_sending(data)

            await bot.send_message(
                chat_id=message.chat.id,
                text=f'Рассылка запланирована в {data["date"]}',
                reply_markup=menu.admin_menu()
            )
    else:
        await bot.send_message(message.chat.id, text='Рассылка отменена', reply_markup=menu.admin_menu())

    await state.finish()


@dp.message_handler(state=Admin_create_cupons.admin_create_cupons, content_types=['document'])
async def admin_create_cupons(message: types.Message, state: FSMContext):
    try:
        file_name = f'docs/promo_{random.randint(0, 999999999999999)}.txt'
        await message.document.download(file_name)
        await message.answer('Загружаем....')
        func.admin_add_cupons(message.caption, file_name)
        await message.answer('Купон добавлен, название: ' + message.text.split("\n")[0], reply_markup=menu.admin_menu())
    except Exception as e:
        print(e)
        await message.answer('Купон добавлен, название: ' + message.text.split("\n")[0], reply_markup=menu.admin_menu())
        await state.finish()


async def activate_promocode(message: types.Message):
    try:
        if os.path.exists("bonuses.txt"):
            with open("bonuses.txt", 'r') as f: bonuses = f.readlines()
        if re.fullmatch(r'\b\[.+\]', bonuses[0]):
            uids = leval(bonuses.pop(0))
        else:
            uids = []
        if message.chat.id in uids:
            return await message.answer("Вы уже забрали свой бонус, ждите новой раздачи.")
        else:
            answer = ''
            while not re.findall(r'\w+', answer): answer = bonuses.pop(0)
            uids.append(message.chat.id)
            with open("bonuses.txt", 'w') as f:
                f.write(str(uids) + '\n' + ''.join(bonuses))
            return await message.answer(answer)
    except Exception as e:
        print(e)
    await message.answer("В данный момент раздачи бонусов нет, Жди...")


@dp.message_handler(state=Admin_buttons.admin_buttons_del)
async def admin_buttons_del(message: types.Message, state: FSMContext):
    try:
        func.admin_del_btn(message.text)

        await message.answer('Кнопка удалена', reply_markup=menu.admin_menu())
        await state.finish()
    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add)
async def admin_buttons_add(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['name'] = message.text

        await Admin_buttons.next()
        await message.answer('Введите текст кнопки')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_text)
async def admin_buttons_add_text(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['text'] = message.text

        await Admin_buttons.next()
        await message.answer('Отправьте фото для кнопки')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_photo, content_types=['photo'])
async def admin_buttons_add_photo(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['photo'] = random.randint(111111111, 999999999)

        await message.photo[-1].download(f'photos/{data["photo"]}.jpg')

        with open(f'photos/{data["photo"]}.jpg', 'rb') as photo:
            await message.answer_photo(photo, data['text'])

        await Admin_buttons.next()
        await message.answer('Для создания кнопки напишите Ок')

    except Exception as e:
        await state.finish()
        await message.answer('⚠️ ERROR ⚠️')


@dp.message_handler(state=Admin_buttons.admin_buttons_add_confirm)
async def admin_buttons_add_confirm(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            func.admin_add_btn(data["name"], data["text"], data["photo"])

            await message.answer('Кнопка создана', reply_markup=menu.admin_menu())
    else:
        await message.answer('Создание кнопки отменено')

    await state.finish()


@dp.message_handler(state=AdminDelSubdirectory.confirm)
async def admin_subdirectory_del(message: types.Message, state: FSMContext):
    if message.text == 'Ок':
        async with state.proxy() as data:
            await Catalog().del_subdirectory(data['subdirectory_id'])

            await message.answer('Вы успешно удалили подкаталог')
    else:
        await message.answer('Удаление каталога отменено')

    await state.finish()


@dp.message_handler(state=SearchSeller.user)
async def search_seller_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        is_seller = data.get("is_seller")
    if not message.text:
        return await message.answer("Я жду от тебя текстового сообщения, попробуй снова" + texts.cancel_text)
    entity = message.text
    if not entity.isnumeric():
        resp = requests.get(f"https://murix.ru/ua/api/getEntity?e={entity}")
        if not resp or resp.json().get("_") != 'User':
            return await message.answer("Я не знаю юзера с таким юзернеймом/айди, попробуй ещё" + texts.cancel_text)
        entity = resp.json().get("id")
    try:
        user = User(int(entity))
        if not is_seller and not user.trusted:
            raise Exception("хуй")
    except:
        return await message.answer(f"Такого {'продавца' if not is_seller else 'покупателя'} нет в бд бота, попробуй "
                                    f"другой юзер/айди" + texts.cancel_text)
    await state.update_data({"user_id": user.user_id})
    await SearchSeller.next()
    await message.answer(texts.seller.format(
        id=user.user_id,
        login=user.username,
        data=user.date[:19]
    ) + 'Теперь введи условия сделки.\nТребуется одно текстовое сообщение.\nОпиши условия максимально '
        'грамотно, это важно.' + texts.cancel_text)


@dp.message_handler(state=SearchSeller.condition)
async def search_seller_condition(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Я жду от тебя текстового сообщения, попробуй снова" + texts.cancel_text)
    await state.update_data({'condition': message.html_text})
    await SearchSeller.next()
    await message.answer("Отлично, осталось лишь ввести сумму сделки в рублях, введи её." + texts.cancel_text)


@dp.message_handler(state=SearchSeller.price)
async def search_seller_price(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Я жду от тебя сумму сделки в виде числа, попробуй снова" + texts.cancel_text)
    try:
        price = float(message.text)
    except:
        return await message.answer("Я жду от тебя сумму сделки в виде числа, попробуй снова" + texts.cancel_text)
    async with state.proxy() as data:
        is_seller = data.get('is_seller')
        user_id = data.get("user_id")
        condition = data.get("condition")
    user = User(message.from_user.id)
    if not is_seller and user.balance - user.give_all_dealing_prices() - price < 0:
        return await message.answer("Введённая сумма сделки больше, чем у тебя лежит на балансе, попробуй другое число"
                                    + texts.cancel_text)
    seller_id = message.from_user.id if is_seller else user_id
    customer_id = user_id if is_seller else message.from_user.id
    dealing_id = Dealing.new_dealing(seller_id, customer_id, condition, price)
    answer_text = texts.dealing_text.format(dealing_id=dealing_id,
                                            seller_name=User(seller_id).username,
                                            customer_name=User(customer_id).username,
                                            condition=condition,
                                            price=price)
    await state.finish()
    try:
        await bot.send_message(user_id, answer_text, reply_markup=menu.prepare_dealing(dealing_id, False))
    except:
        return await message.answer("Похоже, второй участник сделки закрыл бота, такое бывает.")
    await message.answer(answer_text + texts.dealing_init_text, reply_markup=menu.prepare_dealing(dealing_id))
    await bot.send_message(config.config("channel_id_main_logs"), texts.dealing_text.format(
                    dealing_id=dealing_id,
                    seller_name=User(seller_id).username,
                    customer_name=User(customer_id).username,
                    condition=condition,
                    price=price)
                                            + texts.dealing_extend_text.format(
                    status=func.dealing_status_to_text("prepare"),
                    date=str(datetime.now())[:19]
                ), reply_markup=menu.dealing_update_button(dealing_id))


@dp.message_handler(state=ClarifyCondition.clarify)
async def clarify_condition_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        dealing_id = data.get("dealing_id")
    if not message.text:
        return await message.answer("Я ожидаю текстового сообщения, попробуй снова",
                                    reply_markup=menu.cancel_clarify_button(dealing_id))
    dealing = Dealing(dealing_id)
    is_seller = message.from_user.id == dealing.seller_id
    dealing.update_condition(message.html_text, is_seller)
    dealing.update_status("clarify")
    user_id = dealing.seller_id if not is_seller else dealing.customer_id
    await bot.send_message(user_id,
                           f"Есть уточнения по сделке /{dealing.dealing_id}:\n\n{message.text}\n\nПринимаешь их?",
                           reply_markup=menu.prepare_dealing(dealing.dealing_id, not dealing.check_init(user_id), True))
    await message.answer(f"Уточнения по сделке /{dealing.dealing_id} отправлены "
                         f"{'продавцу' if not is_seller else 'покупателю'}")
    await state.finish()


@dp.message_handler(state=MessageDealing.message)
async def message_dealing_text(message: types.Message, state):
    async with state.proxy() as data:
        dealing_id = data.get("dealing_id")
    dealing = Dealing(dealing_id)
    await bot.send_message(dealing.seller_id if message.from_user.id == dealing.customer_id else dealing.customer_id,
                           f"Сообщение от {'продавца' if message.from_user.id == dealing.seller_id else 'покупателя'} "
                           f" сделки /{dealing_id}:\n\n{message.html_text}")
    await state.finish()
    await message.answer("Сообщение доставлено до второго участника сделки")
    message.text = '/' + dealing_id
    await send_message(message)


@dp.message_handler(state=LinkDealing.link)
async def link_dealing_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        dealing_id = data.get("dealing_id")
    if not message.text.startswith("https://t.me/+") and not message.text.startswith("https://t.me/joinchat/"):
        return await message.answer("Неправильный формат ссылки, пробуй ещё раз.")
    dealing = Dealing(dealing_id)
    ans = f"Для обсуждений спора по сделке /{dealing_id} следуй в приватный чат:\n\n{message.text}"
    for x in [dealing.seller_id, dealing.customer_id, message.chat.id]:
        await bot.send_message(x, ans)
    await state.finish()


@dp.message_handler(state=Withdraw.qiwi)
async def withdraw_qiwi_text(message: types.Message, state: FSMContext):
    if not message.text.isnumeric() and not message.text[1:].isnumeric():
        return await message.answer("Неверно указан номер, попробуй снова.", reply_markup=menu.withdraw(True))
    user = User(message.from_user.id)
    await bot.send_message(config.config("channel_id_main_logs"),
                           texts.withdraw_text.format(
        chat_id=message.from_user.id,
        method='киви',
        amount=user.balance - user.give_all_dealing_prices(),
        link=message.text
    ))
    await message.answer("Номер принят, заявка на вывод будет рассмотрена в ближайшее время.")
    await state.finish()



async def sending_check(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        try:
            info = func.sending_check()

            if info != False:
                users = func.get_users_list()

                start_time = time.time()
                amount_message = 0
                amount_bad = 0

                if info[0] == 'text':
                    try:
                        m = await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка в процессе',
                            reply_markup=menu.admin_sending_info(0, 0, 0))
                        msg_id = m['message_id']
                    except:
                        pass

                    for i in range(len(users)):
                        try:
                            await bot.send_message(users[i][0], info[1], reply_markup=menu.to_close)
                            amount_message += 1
                        except Exception as e:
                            amount_bad += 1

                    try:
                        await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                    message_id=msg_id,
                                                    text='✅ Рассылка завершена',
                                                    reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                         amount_message,
                                                                                         amount_bad))
                    except:
                        pass
                    sending_time = time.time() - start_time

                    try:
                        await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка окончена\n'
                                 f'👍 Отправлено: {amount_message}\n'
                                 f'👎 Не отправлено: {amount_bad}\n'
                                 f'🕐 Время выполнения рассылки - {sending_time} секунд'

                        )
                    except:
                        print('ERROR ADMIN SENDING')

                elif info[0] == 'photo':
                    try:
                        m = await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка в процессе',
                            reply_markup=None)
                        msg_id = m['message_id']
                    except:
                        pass

                    for i in range(len(users)):
                        try:
                            with open(f'photos/{info[2]}.jpg', 'rb') as photo:
                                await bot.send_photo(
                                    chat_id=users[i][0],
                                    photo=photo,
                                    caption=info[1],
                                    reply_markup=menu.to_close
                                )
                            amount_message += 1
                        except:
                            amount_bad += 1

                    try:
                        await bot.edit_message_text(chat_id=config.config('admin_id_manager').split(':')[0],
                                                    message_id=msg_id,
                                                    text='✅ Рассылка завершена',
                                                    reply_markup=menu.admin_sending_info(amount_message + amount_bad,
                                                                                         amount_message,
                                                                                         amount_bad))
                    except:
                        pass

                    sending_time = time.time() - start_time

                    try:
                        await bot.send_message(
                            chat_id=config.config('admin_id_manager').split(':')[0],
                            text=f'✅ Рассылка окончена\n'
                                 f'👍 Отправлено: {amount_message}\n'
                                 f'👎 Не отправлено: {amount_bad}\n'
                                 f'🕐 Время выполнения рассылки - {sending_time} секунд'

                        )
                    except:
                        print('ERROR ADMIN SENDING')

            else:
                pass
        except Exception as e:
            print(str(e))


async def check_qiwi(wait_for):
    while True:
        try:
            data = func.get_payments_history()
            payment_code_list = func.get_list_payments_code()

            for i in range(len(data)):
                for j in payment_code_list:
                    if time.time() - float(j[2]) > 3600:
                        func.del_purchase_ticket(j[0])
                    elif data[i]['comment'] == j[1]:
                        if str(data[i]['sum']['currency']) == '643':
                            deposit = float(data[i]["sum"]["amount"])
                            func.del_purchase_ticket(j[0])

                            User(j[0]).update_balance(deposit)
                            try:
                                User(j[0]).give_ref_reward(float(deposit))
                            except:
                                print('pizdos2')

                            conn, cursor = connect()

                            try:
                                cursor.execute(
                                    f'INSERT INTO deposit_logs VALUES ("{j[0]}", "qiwi", "{deposit}", "{datetime.now()}")')
                                conn.commit()
                            except Exception as e:
                                print('e2 ')

                            try:
                                chat = User(j[0])
                                await bot.send_message(chat_id=config.config('channel_id_main_logs'),
                                                       text=texts.logs.format(
                                                           'QIWI',
                                                           chat.first_name,
                                                           f'@{chat.username}',
                                                           j[0],
                                                           datetime.now(),
                                                           f'❕ Кошелек: +{data[i]["personId"]}\n❕ Комментарий: {data[i]["comment"]}',
                                                           deposit
                                                       ))
                            except Exception as e:
                                print('e 3')

                            try:
                                await bot.send_message(
                                    chat_id=j[0],
                                    text=f'✅ Вам зачислено +{deposit}'
                                )
                            except Exception as e:
                                pass

        except Exception as e:
            print(str(e))

        await asyncio.sleep(wait_for)


async def check_payouts(wait_for):
    while True:
        try:
            await asyncio.sleep(wait_for)

            conn, cursor = connect()

            cursor.execute(f'SELECT * FROM payouts')
            payouts = cursor.fetchall()

            if len(payouts) > 0:
                for i in payouts:
                    if i[1] == 'bad':
                        cursor.execute(f'DELETE FROM payouts WHERE user_id = "{i[0]}"')
                        conn.commit()

                        await bot.send_message(chat_id=i[0], text=f'✅ Ваш чек проверен, на ваш баланс начислено 0 ₽',
                                               reply_markup=menu.to_close)
                    else:
                        cursor.execute(f'DELETE FROM payouts WHERE user_id = "{i[0]}"')
                        conn.commit()

                        User(i[0]).update_balance(i[1])
                        try:
                            User(i[0]).give_ref_reward(float(i[1]))
                        except:
                            pass
                        await bot.send_message(chat_id=i[0],
                                               text=f'✅ Ваш чек проверен, на ваш баланс начислено +{i[1]} ₽',
                                               reply_markup=menu.to_close)

                        try:
                            await bot.send_message(chat_id=config.config('channel_id_main_logs'),
                                                   text=texts.logs.format(
                                                       'BANKER',
                                                       User(i[0]).first_name,
                                                       User(i[0]).username,
                                                       i[0],
                                                       datetime.now(),
                                                       f'❕ Чек: {i[2]}',
                                                       i[1]
                                                   ))
                        except:
                            pass
        except:
            pass


if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    loop.create_task(sending_check(10))
    loop.create_task(check_payouts(5))

    executor.start_polling(dp, skip_updates=True)
