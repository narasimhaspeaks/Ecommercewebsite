import sqlite3
import os
import secrets, string
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
db = os.path.join(basedir, 'ecommerce.db')
print('DB file:', db, 'exists=', os.path.exists(db))
if not os.path.exists(db):
    print('Database missing')
    raise SystemExit(1)
con = sqlite3.connect(db)
cur = con.cursor()
cur.execute("PRAGMA table_info('order')")
cols = [r[1] for r in cur.fetchall()]
print('Columns before:', cols)
if 'order_code' not in cols:
    print('Adding order_code column...')
    cur.execute('ALTER TABLE "order" ADD COLUMN order_code VARCHAR(32)')
    con.commit()
    cur.execute("PRAGMA table_info('order')")
    print('Columns after:', [r[1] for r in cur.fetchall()])
else:
    print('order_code already exists')

# Populate rows without order_code
cur.execute("SELECT id, order_code FROM 'order'")
rows = cur.fetchall()
alphabet = string.ascii_uppercase + string.digits
for row in rows:
    oid, code = row
    if not code:
        # generate unique code (naive)
        newc = ''.join(secrets.choice(alphabet) for _ in range(10))
        cur.execute("UPDATE 'order' SET order_code=? WHERE id=?", (newc, oid))
con.commit()
print('Populated order_code for existing rows')
con.close()
