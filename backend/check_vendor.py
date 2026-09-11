import sqlite3

db_path = 'bharatsetu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get schema for vendors table
cursor.execute("PRAGMA table_info(vendors)")
columns = cursor.fetchall()
print('Vendors table schema:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Check vendor with id d34e33e8-5791-4aa4-b8a3-40140c065085
vendor_id = 'd34e33e8-5791-4aa4-b8a3-40140c065085'
cursor.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
vendor = cursor.fetchone()
if vendor:
    print(f'\nVendor record:')
    for i, col in enumerate(columns):
        print(f'  {col[1]} = {vendor[i]}')
else:
    print(f'\nNo vendor found with id {vendor_id}')

# Check all vendors
cursor.execute("SELECT id, name FROM vendors")
print('\nAll vendors:')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
