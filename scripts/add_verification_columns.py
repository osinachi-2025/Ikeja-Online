import sqlite3
import os
from pathlib import Path

DB_PATH = Path('instance') / 'ikeja_online.db'
if not DB_PATH.exists():
    print('DB not found:', DB_PATH)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

cols_done = []
try:
    c.execute("ALTER TABLE users ADD COLUMN verification_code VARCHAR(10);")
    print('added verification_code')
    cols_done.append('verification_code')
except Exception as e:
    print('verification_code add error:', e)

try:
    c.execute("ALTER TABLE users ADD COLUMN verification_expires DATETIME;")
    print('added verification_expires')
    cols_done.append('verification_expires')
except Exception as e:
    print('verification_expires add error:', e)

conn.commit()
conn.close()

print('done, columns added:', cols_done)
