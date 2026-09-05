import sqlite3

conn = sqlite3.connect('tacos.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('Tables:', tables)

for name in tables:
    cur.execute(f'SELECT COUNT(*) FROM {name}')
    count = cur.fetchone()[0]
    cur.execute(f'SELECT * FROM {name} LIMIT 3')
    rows = cur.fetchall()
    cur.execute(f'PRAGMA table_info({name})')
    cols = [c[1] for c in cur.fetchall()]
    print(f'\n--- {name} ({count} rows) ---')
    print('Columns:', cols)
    print('Sample:', rows)

conn.close()
