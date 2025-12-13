import sqlite3
import os
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
db = os.path.join(basedir, 'ecommerce.db')
print('DB file:', db, 'exists=', os.path.exists(db))
if os.path.exists(db):
    con = sqlite3.connect(db)
    cur = con.cursor()
    try:
        cur.execute("PRAGMA table_info('order')")
        rows = cur.fetchall()
        print('PRAGMA table_info(order):')
        for r in rows:
            print(r)
    except Exception as e:
        print('ERROR:', e)
    con.close()
else:
    print('Database not found')
