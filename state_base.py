import sqlite3


class DB():

    def __init__(self):
        with sqlite3.connect('states.db') as conn:
            c = conn.cursor()
            c.execute(''' CREATE TABLE IF NOT EXISTS state (id integer primary key, key text, value text)''')
            conn.commit()



    def set_value(self, key, value):
        with sqlite3.connect('states.db') as con:
            cursor = con.cursor()
            cursor.execute(''' SELECT value FROM state WHERE key =? ''', (key,))

            ex_result = cursor.fetchall()

            if len(ex_result) == 0:
                cursor.execute(''' INSERT INTO state (key, value) values(?, ?) ''', (key, value))
                con.commit()
            elif len(ex_result) == 1:
                cursor.execute(''' UPDATE state SET value = ? WHERE key = ? ''', (value, key))
                con.commit()

        return True

    def get_value(self, key):
        with sqlite3.connect('states.db') as con:
            cursor = con.cursor()
            cursor.execute(''' SELECT value FROM state WHERE key = ? ''', (key,))
            ex_result = cursor.fetchall()

            if len(ex_result) == 1:
                return ex_result[0][0]

        return None




















