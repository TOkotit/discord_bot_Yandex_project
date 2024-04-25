import os
import sqlite3

with open('keywords.txt') as file:
    list_ = [i.strip() for i in file.readlines()]
data_base = sqlite3.connect('database/keywords.db')
cursor = data_base.cursor()
for i in list_:
    cursor.execute(f"""INSERT OR IGNORE INTO keys VALUES(?, ?, ?, ?, ?)""", (i, None, None, None, 'False'))
    data_base.commit()
