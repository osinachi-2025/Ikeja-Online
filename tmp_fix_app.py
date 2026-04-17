from pathlib import Path

path = Path('app.py')
text = path.read_text(encoding='utf-8')

old = '''        # Create order
        order = Orders(
            customer_id=customer.id,
            reference_number=reference_number,
            total_amount=total_amount,
            status='pending'
        )'''
new = '''        # Create order
        order = Orders(
            customer_id=customer.id,
            delivery_address_id=delivery_address_id,
            reference_number=reference_number,
            total_amount=total_amount,
            status='pending'
        )'''

if old not in text:
    raise RuntimeError('Old order block not found')
text = text.replace(old, new)

oldpdf = '''    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Invoice #: {order.reference_number}', ln=True)
    pdf.cell(0, 8, f'Date: {order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else "N/A"}', ln=True)
    pdf.cell(0, 8, f'Status: {order.status or "pending"}', ln=True)
    pdf.cell(0, 8, f'Shipping Status: {order.shipping_status or "pending"}', ln=True)
    pdf.ln(5)
'''
newpdf = '''    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Invoice #: {order.reference_number}', ln=True)
    invoice_date = order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else 'N/A'
    pdf.cell(0, 8, f'Date: {invoice_date}', ln=True)
    pdf.cell(0, 8, f'Status: {order.status or "pending"}', ln=True)
    pdf.cell(0, 8, f'Shipping Status: {order.shipping_status or "pending"}', ln=True)
    pdf.ln(5)
'''

if oldpdf in text:
    text = text.replace(oldpdf, newpdf)
else:
    import re
    pattern = re.compile(r"    pdf\.set_font\('Arial', 'B', 12\)\n    pdf\.cell\(0, 8, f'Invoice #: \{order\.reference_number\}', ln=True\)\n    pdf\.cell\(0, 8, f'Date: \{order\.created_at\.strftime\(\"%Y-%m-%d %H:%M:%S\"\) if order\.created_at else \"N/A\"\}', ln=True\)\n    pdf\.cell\(0, 8, f'Status: \{order\.status or \"pending\"\}', ln=True\)\n    pdf\.cell\(0, 8, f'Shipping Status: \{order\.shipping_status or \"pending\"\}', ln=True\)\n    pdf\.ln\(5\)\n")
    text, count = pattern.subn(newpdf, text)
    if count == 0:
        raise RuntimeError('Old PDF lines not found')

path.write_text(text, encoding='utf-8')
print('patched')
