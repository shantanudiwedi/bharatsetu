import sys
with open('tests/test_suggested_tenders.py', 'r') as f:
    content = f.read()

content = content.replace('file_name="gst.pdf"', 'filename="gst.pdf", file_hash="hash123"')
content = content.replace('file_name="pan.pdf"', 'filename="pan.pdf", file_hash="hash456"')

content = content.replace('verified=True)', 'verified=True, status="SUCCESS")')
content = content.replace('verified=False)', 'verified=False, status="FAILED")')

with open('tests/test_suggested_tenders.py', 'w') as f:
    f.write(content)
print('Fixed Document and Verification constructors.')
