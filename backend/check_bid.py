import sqlite3

db_path = 'bharatsetu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get schema for bids table
cursor.execute("PRAGMA table_info(bids)")
columns = cursor.fetchall()
print('Bids table schema:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Check for bid with amount 1234567
cursor.execute("SELECT * FROM bids WHERE bid_amount = 1234567 OR bid_amount = '1234567'")
rows = cursor.fetchall()
if rows:
    print('\nFound bid(s) with amount 1234567:')
    for row in rows:
        print(f'  {row}')
else:
    print('\nNo bid found with amount 1234567')
    # List recent bids
    cursor.execute("SELECT * FROM bids ORDER BY ROWID DESC LIMIT 5")
    print('\nLast 5 bids:')
    for row in cursor.fetchall():
        print(f'  {row}')

conn.close()
