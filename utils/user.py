from utils.mydb import *
import config


class User():

    def __init__(self, user_id):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM users WHERE user_id = "{user_id}"')
        user = cursor.fetchone()

        self.user_id = user[0]
        self.first_name = user[1]
        self.username = user[2]
        self.balance = float(user[3])
        self.who_invite = user[4]
        self.date = user[5]
        self.pact = user[6]
        self.trusted = user[7]

    def update_balance(self, value, deal=False):
        conn, cursor = connect()

        cursor.execute(f'UPDATE users SET balance = {float(self.balance) + float(value)} WHERE user_id = "{self.user_id}"')
        if deal:
            cursor.execute(f'update users set dealings = dealings + 1 where user_id = "{self.user_id}";')
        conn.commit()

        return True

    async def give_money(self, bot, user_id, amount):
        if self.balance - self.give_all_dealing_prices() >= amount:
            self.update_balance(-amount)

            user = User(user_id)
            user.update_balance(amount)

            await bot.send_message(chat_id=user_id, text=f'✅ {self.first_name} перевел вам {amount} ₽')
            await bot.send_message(chat_id=self.user_id, text=f'✅ Вы перевели {amount} ₽ пользователю {user.first_name}')

            try:
                await bot.send_message(chat_id=config.config('CHAT_ID'), text=f'✅ {self.first_name} успешно перевел {amount} ₽ пользователю {user.first_name}')
            except: pass
        else:
            try:
                await bot.send_message(chat_id=config.config('CHAT_ID'), text=f'❌ {self.first_name} на балансе недостатачно средств')
            except: pass

    @staticmethod
    def give_trust(user_id, value):
        try:
            conn, cursor = connect()
            cursor.execute(f"update users set trusted={value} where user_id = {user_id};")
            conn.commit()
            return True
        except Exception as e:
            print(str(e))

    @staticmethod
    def admin4ek(user_id):
        return None if str(user_id) in str(config.config('admin_id_own')) else user_id

    def give_all_dealing_prices(self):
        _, cursor = connect()

        cursor.execute(f'SELECT SUM(price) FROM dealings WHERE customer_id = "{self.user_id}" '
                       f'and status not in ("success", "close")')
        res = cursor.fetchone()
        return float(res[0]) if res and res[0] else 0
