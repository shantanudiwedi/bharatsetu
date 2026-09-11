import sqlite3

db_path = 'bharatsetu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get schema for tenders table
cursor.execute("PRAGMA table_info(tenders)")
columns = cursor.fetchall()
print('Tenders table schema:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Check tender with public id CPCL-2026-IND-09
cursor.execute("SELECT * FROM tenders WHERE tender_id = 'CPCL-2026-IND-09'")
tender = cursor.fetchone()
if tender:
    print(f'\nTender record (tender_id = CPCL-2026-IND-09):')
    for i, col in enumerate(columns):
        print(f'  {col[1]} = {tender[i]}')
else:
    print(f'\nNo tender found with tender_id = CPCL-2026-IND-09')

# List the first 3 tenders
cursor.execute("SELECT id, tender_id, title FROM tenders LIMIT 3")
print('\nFirst 3 tenders:')
for row in cursor.fetchall():
    print(f'  id={row[0]}, tender_id={row[1]}, title={row[2]}')

conn.close()
