"""QR Code generation utilities."""
import qrcode
import os
import json
import io
import base64
from PIL import Image


def _build_qr_image(order):
    """Build and return a QR code PIL image for the given order."""
    items = order.get_items()
    items_text = ', '.join([f"{i['qty']}x {i['name']}" for i in items])
    qr_data = json.dumps({
        'order_id': order.id,
        'order_number': order.order_number,
        'customer': order.customer_name,
        'items': items_text,
        'total': order.total_price,
    })

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    return qr.make_image(fill_color='black', back_color='white')


def generate_order_qr(order, save_dir='static/qr_codes'):
    """Generate a QR code for an order, save it, and return (filepath, base64)."""
    os.makedirs(save_dir, exist_ok=True)

    img = _build_qr_image(order)

    filename = f"order_{order.order_number}.png"
    filepath = os.path.join(save_dir, filename)
    img.save(filepath)

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return filepath, b64


def order_qr_base64(order):
    """Return a base64-encoded QR image string for inline HTML embedding."""
    img = _build_qr_image(order)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
