from utils.mydb import *
from aiogram import types
from random import randint

class Catalog():

    async def get_info(self, catalog_id=None, subdirectory_id=None):
        conn, cursor = connect()

        if catalog_id is not None:
            cursor.execute(f'SELECT * FROM catalogs WHERE catalog_id = "{catalog_id}"')
            self.catalog = cursor.fetchone()

            self.catalog_id = self.catalog[0]
            self.catalog_name = self.catalog[1]
            self.catalog_photo = self.catalog[2]
        elif subdirectory_id is not None:
            cursor.execute(f'SELECT * FROM subdirectories WHERE subdirectory_id = "{subdirectory_id}"')
            self.subdirectory = cursor.fetchone()

            self.subdirectory_id = self.subdirectory[1]
            self.subdirectory_name = self.subdirectory[2]
            self.subdirectory_photo = self.subdirectory[3]


    async def get_menu(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        #  for i in self.catalogs:
        #     markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'catalog:{i[0]}'))

        x1 = 0
        x2 = 1
        try:
            for i in range(len(self.catalogs)):
                markup.add(
                    types.InlineKeyboardButton(text=f'{self.catalogs[x1][1]}',
                                               callback_data=f'catalog:{self.catalogs[x1][0]}'),
                    types.InlineKeyboardButton(text=f'{self.catalogs[x2][1]}',
                                               callback_data=f'catalog:{self.catalogs[x2][0]}')
                )

                x1 += 2
                x2 += 2
        except Exception as e:
            try:
                markup.add(
                    types.InlineKeyboardButton(text=f'{self.catalogs[x1][1]}',
                                               callback_data=f'catalog:{self.catalogs[x1][0]}'),
                )
            except:
                pass

        markup.add(types.InlineKeyboardButton(text='⚙️ Управление товарами', callback_data='admin_products'))
        return markup

    async def get_all_catalogs(self):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM catalogs')
        self.catalogs = cursor.fetchall()

    async def create_catalog(self, name, file_name):
        conn, cursor = connect()

        catalog_id = f"c{randint(0, 999999)}"

        cursor.execute(f'INSERT INTO catalogs VALUES ("{catalog_id}", "{name}", "{file_name}")')
        conn.commit()

        try:
            cursor.execute(f'CREATE TABLE {catalog_id} (product_id TEXT, name TEXT, price DECIMAL(10, 2), description '
                           f'TEXT, user_id TEXT, photo TEXT)')
            conn.commit()
        except:
            pass

    async def create_subdirectory(self, catalog_id, name, file_name):
        conn, cursor = connect()

        subdirectory_id = f"subdirectory{randint(0, 999999)}"

        cursor.execute(f'INSERT INTO subdirectories VALUES ("{catalog_id}", "{subdirectory_id}", "{name}", "{file_name}")')
        conn.commit()

        try:
            cursor.execute(
                f'CREATE TABLE {subdirectory_id} (product_id TEXT, name TEXT, price DECIMAL(10, 2), description TEXT)')
            conn.commit()
        except:
            pass

    async def get_menu_del_catalogs(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'del_catalog:{i[0]}'))

        return markup

    async def del_catalog(self, catalog_id):
        conn, cursor = connect()

        cursor.execute(f'DELETE FROM catalogs WHERE catalog_id = "{catalog_id}"')
        conn.commit()

    async def get_menu_add_subdirectory(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'add_subdirectory:{i[0]}'))

        return markup

    async def get_menu_add_product(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'add_product_catalog:{i[0]}'))

        markup.add(types.InlineKeyboardButton(text="<< Назад", callback_data='admin_products'))

        return markup

    async def get_menu_del_product(self, subdirectories=None):
        if subdirectories is None:
            await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs if subdirectories is None else subdirectories:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}' if subdirectories is None else f'{i[2]}',
                                                  callback_data=f'del_product_menu:{i[0]}' if subdirectories is None else f'del_product_menu_2_subdirectory:{i[1]}'))

        markup.add(types.InlineKeyboardButton(text="<< Назад", callback_data='admin_products'))

        return markup

    async def get_menu_upload_product(self):
        await self.get_all_catalogs()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in self.catalogs:
            markup.add(types.InlineKeyboardButton(text=f'{i[1]}', callback_data=f'upload_catalog:{i[0]}'))

        markup.add(types.InlineKeyboardButton(text="<< Назад", callback_data='admin_products'))

        return markup

    async def get_catalog_photo(self, catalog_id=None, subdirectory_id=None):
        if catalog_id is not None:
            await self.get_info(catalog_id=catalog_id)
        elif subdirectory_id is not None:
            await self.get_info(subdirectory_id=subdirectory_id)

        return self.catalog_photo if catalog_id is not None else self.subdirectory_photo if subdirectory_id is not None else None

    async def check_subdirectory_in_catalog(self, subdirectories):
        if len(subdirectories) > 0:
            return True
        else:
            return False

    async def get_menu_add_product_choosing(self, catalog_id):
        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(
                text=f'Добавить товар в этот каталог',
                callback_data=f'add_product_in_catalog:{catalog_id}'),
            types.InlineKeyboardButton(
                text=f'Добавить товар в подкаталог',
                callback_data=f'add_product_get_menu_subdirectory:{catalog_id}'),
            types.InlineKeyboardButton(
                text="<< Назад",
                callback_data='admin_products')
        )

        return markup

    async def get_menu_add_product_subdirectory(self, subdirectory):

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in subdirectory:
            markup.add(types.InlineKeyboardButton(text=f'{i[2]}', callback_data=f'add_product_in_subdirectory:{i[1]}'))

        markup.add(types.InlineKeyboardButton(text="<< Назад", callback_data='admin_products'))

        return markup

    async def get_menu_del_subdirectory(self):
        conn, cursor = connect()

        cursor.execute(f'SELECT * FROM subdirectories')
        rows = cursor.fetchall()

        markup = types.InlineKeyboardMarkup(row_width=2)

        for i in rows:
            await self.get_info(i[0])
            markup.add(types.InlineKeyboardButton(text=f'{i[2]} | {self.catalog_name}', callback_data=f'del_subdirectory:{i[1]}'))

        return markup

    async def del_subdirectory(self, subdirectory_id):
        conn, cursor = connect()

        cursor.execute(f'DELETE FROM subdirectories WHERE subdirectory_id = "{subdirectory_id}"')
        conn.commit()

        cursor.execute(f'SELECT * FROM {subdirectory_id}')
        rows = cursor.fetchall()

        for i in rows:
            cursor.execute(f'DROP TABLE {i[0]}')

        cursor.execute(f'DROP TABLE {subdirectory_id}')