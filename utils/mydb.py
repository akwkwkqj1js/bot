import sqlite3


def connect():
    # conn = mysql.connector.connect(
    #     host='123.45.0.3',
    #     user='root',
    #     password='M0Q2bVpUZ1hQaWg',
    #     database='mark'
    # )
    conn = sqlite3.connect("db.sqlite")

    cursor = conn.cursor()

    return conn, cursor

conn, cursor = connect()

def create_tables():
    try:
        cursor.execute(f'CREATE TABLE users (user_id TEXT, first_name TEXT, username TEXT, balance DECIMAL(10, 2), '
                       f'who_invite TEXT, date TEXT, pact TEXT, trusted INTEGER DEFAULT 0, dealings INTEGER DEFAULT 0)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE check_payment (user_id TEXT, code TEXT, date TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE sending (type TEXT, text TEXT, photo TEXT, date TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE catalogs (catalog_id TEXT, catalog_name TEXT, photo TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE subdirectories (catalog_id TEXT, subdirectory_id TEXT, subdirectory_name TEXT, '
                       f'photo TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE purchase_logs (user_id TEXT, file_name TEXT, amount TEXT, price TEXT, '
                       f'date TEXT, seller_id TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE buttons (name TEXT, info TEXT, photo TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE btc_list (user_id TEXT, code TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE payouts (user_id TEXT, sum TEXT, btc_check TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE payouts_step_0 (user_id TEXT, code TEXT, time TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE deposit_logs (user_id TEXT, type TEXT, sum DECIMAL(10, 2), date TEXT)')
        conn.commit()
    except:
        pass

    try:
        cursor.execute(f'CREATE TABLE deposit_logs (user_id TEXT, type TEXT, sum DECIMAL(10, 2), date TEXT)')
        conn.commit()
    except:
        pass
    try:
        cursor.execute(f'CREATE TABLE btc_list (coupons TEXT, code TEXT)')
        conn.commit()
    except:
        pass
    try:
        cursor.execute(f"CREATE TABLE dealings(dealing_id TEXT PRIMARY KEY, seller_id INTEGER NOT NULL, customer_id "
                       f"INTEGER NOT NULL, condition TEXT NOT NULL, price DECIMAL(10,2), date TEXT, status TEXT "
                       f"DEFAULT 'prepare', init TEXT DEFAULT 'customer');")
        conn.commit()
    except:
        pass

create_tables()
