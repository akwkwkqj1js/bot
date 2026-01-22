from datetime import datetime
from random import randint

from utils.mydb import *
import config


class Dealing:

    @staticmethod
    def new_dealing(seller_id, customer_id, condition, price):
        conn, cursor = connect()
        dealing_id = f'd{randint(0, 99999999999)}'
        cursor.execute("insert into dealings(dealing_id, seller_id, customer_id, condition, price, date) "
                       "values (?, ?, ?, ?, ?, ?)",
                       (dealing_id, seller_id, customer_id, condition, price, datetime.now()))
        conn.commit()
        return dealing_id

    def __init__(self, dealing_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM dealings WHERE dealing_id = "{dealing_id}"')
        deal = cursor.fetchone()
        self.dealing_id = dealing_id
        self.seller_id = deal[1]
        self.customer_id = deal[2]
        self.condition = deal[3]
        self.price = float(deal[4])
        self.status = deal[6]
        self.date = deal[5]
        self.init = deal[7]

    def update_status(self, status):
        conn, cursor = connect()
        cursor.execute(f"update dealings set status = \"{status}\" where dealing_id = \"{self.dealing_id}\"")
        conn.commit()
        return True

    def update_condition(self, condition, is_seller):
        conn, cursor = connect()
        condition = f'\n\n<b><i>Уточнение условий от {"продавца" if is_seller else "покупателя"}:</i></b>\n' + condition
        cursor.execute(f"update dealings set condition = \"{self.condition + condition}\" "
                       f"where dealing_id = \"{self.dealing_id}\"")
        conn.commit()
        return True

    def check_init(self, user_id):
        return (user_id == self.seller_id and self.init == 'seller') \
               or (user_id == self.customer_id and self.init == 'customer')

    def delete_dealing(self):
        conn, cursor = connect()
        cursor.execute(f"delete from dealings where dealing_id = \"{self.dealing_id}\"")
        conn.commit()
        return True

