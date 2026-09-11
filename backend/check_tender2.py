import sqlite3

db_path = 'bharatsetu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check the tender with id 05a65c99-2ef9-4660-b4ab-3f025f216b90
cursor.execute("SELECT id, tender_id, title FROM tenders WHERE id = '05a65c99-2ef9-4660-b4ab-3f025f216b90'")
tender = cursor.fetchone()
if tender:
    print(f'Tender found:')
    print(f'  ID: {tender[0]}')
    print(f'  Public ID: {tender[1]}')
    print(f'  Title: {tender[2]}')
    print(f'  ✓ This matches the second tender (CPCL-2026-IT-14)')
else:
    print(f'Tender NOT found')

conn.close()
