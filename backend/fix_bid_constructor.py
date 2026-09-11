import sys
with open('tests/test_suggested_tenders.py', 'r') as f:
    content = f.read()

content = content.replace('bid = Bid(bid_id=f"BID-{uid}", tender_id=tender.id, vendor_id=vendor.id)', 'bid = Bid(bid_id=f"BID-{uid}", tender_id=tender.id, vendor_id=vendor.id, category="Software", bid_amount="₹1,00,000")')
content = content.replace('bid2 = Bid(bid_id="OTHER-BID", tender_id=tender.id, vendor_id=vendor2.id)', 'bid2 = Bid(bid_id="OTHER-BID", tender_id=tender.id, vendor_id=vendor2.id, category="Software", bid_amount="₹1,00,000")')

with open('tests/test_suggested_tenders.py', 'w') as f:
    f.write(content)
print('Updated test_suggested_tenders.py')
