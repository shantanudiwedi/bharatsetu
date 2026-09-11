import sqlite3

db_path = 'bharatsetu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if bid with amount 2345678 exists
cursor.execute("SELECT id, bid_id, tender_id, bid_amount, status FROM bids WHERE bid_amount = '2345678'")
rows = cursor.fetchall()
if rows:
    print('Found bid(s) with amount 2345678:')
    for row in rows:
        print(f'  id={row[0]}, bid_id={row[1]}, tender_id={row[2]}, bid_amount={row[3]}, status={row[4]}')
        
        # Verify the tender_id matches a Tender UUID
        cursor.execute("SELECT id, tender_id FROM tenders WHERE id = ?", (row[2],))
        tender = cursor.fetchone()
        if tender:
            print(f'    ✓ Tender found: id={tender[0]}, tender_id={tender[1]}')
        else:
            print(f'    ✗ Tender NOT found with id={row[2]} - this is a BUG!')
else:
    print('No bid found with amount 2345678')

conn.close()
