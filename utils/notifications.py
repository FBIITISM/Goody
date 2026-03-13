"""Notification utilities – Email (Gmail SMTP) + WhatsApp (Twilio)."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def _send_email(app, to_address, subject, body_html):
    """Send an email via Gmail SMTP. Silently fails if not configured."""
    if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
        app.logger.info(f'[Email] Not configured – would send to {to_address}: {subject}')
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_FROM'] or app.config['MAIL_USERNAME']
        msg['To'] = to_address
        msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.sendmail(msg['From'], to_address, msg.as_string())
        app.logger.info(f'[Email] Sent to {to_address}: {subject}')
        return True
    except Exception as e:
        app.logger.error(f'[Email] Failed: {e}')
        return False


def _send_whatsapp(app, to_number, message):
    """Send a WhatsApp message via Twilio. Silently fails if not configured."""
    sid = app.config.get('TWILIO_ACCOUNT_SID')
    token = app.config.get('TWILIO_AUTH_TOKEN')
    if not sid or not token:
        app.logger.info(f'[WhatsApp] Not configured – would send to {to_number}: {message}')
        return False
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        client.messages.create(
            from_=app.config['TWILIO_WHATSAPP_FROM'],
            to=to_number,
            body=message,
        )
        app.logger.info(f'[WhatsApp] Sent to {to_number}')
        return True
    except Exception as e:
        app.logger.error(f'[WhatsApp] Failed: {e}')
        return False


def notify_order_received(app, order):
    """Notify customer and kitchen that a new order was received."""
    restaurant = app.config.get('RESTAURANT_NAME', 'Goody Kitchen')
    items = order.get_items()
    items_html = ''.join([
        f"<tr><td>{i['name']}</td><td>{i['qty']}</td><td>${i['price']:.2f}</td></tr>"
        for i in items
    ])
    items_text = '\n'.join([f"  {i['qty']}x {i['name']} – ${i['price']:.2f}" for i in items])

    # --- Customer email ---
    if order.customer_email:
        subject = f"✅ Order #{order.order_number} Received – {restaurant}"
        body = f"""
        <h2>Thank you, {order.customer_name}!</h2>
        <p>Your order <strong>#{order.order_number}</strong> has been received and is being prepared.</p>
        <table border="1" cellpadding="6" style="border-collapse:collapse">
          <thead><tr><th>Item</th><th>Qty</th><th>Price</th></tr></thead>
          <tbody>{items_html}</tbody>
        </table>
        <p><strong>Total: ${order.total_price:.2f}</strong></p>
        {'<p><strong>Notes:</strong> ' + order.notes + '</p>' if order.notes else ''}
        <p>We'll notify you when your order is ready!</p>
        <p>– {restaurant}</p>
        """
        _send_email(app, order.customer_email, subject, body)

    # --- Kitchen email ---
    kitchen_email = app.config.get('KITCHEN_EMAIL')
    if kitchen_email:
        subject = f"🔔 New Order #{order.order_number} – {order.customer_name}"
        body = f"""
        <h2>New Order #{order.order_number}</h2>
        <p><strong>Customer:</strong> {order.customer_name}</p>
        <p><strong>Phone:</strong> {order.customer_phone or 'N/A'}</p>
        <table border="1" cellpadding="6" style="border-collapse:collapse">
          <thead><tr><th>Item</th><th>Qty</th><th>Price</th></tr></thead>
          <tbody>{items_html}</tbody>
        </table>
        <p><strong>Total: ${order.total_price:.2f}</strong></p>
        {'<p><strong>Notes:</strong> ' + order.notes + '</p>' if order.notes else ''}
        """
        _send_email(app, kitchen_email, subject, body)

    # --- Kitchen WhatsApp ---
    kitchen_wa = app.config.get('KITCHEN_WHATSAPP')
    if kitchen_wa:
        msg = (
            f"🔔 New Order #{order.order_number}\n"
            f"Customer: {order.customer_name}\n"
            f"Items:\n{items_text}\n"
            f"Total: ${order.total_price:.2f}\n"
            f"Notes: {order.notes or 'None'}"
        )
        _send_whatsapp(app, kitchen_wa, msg)


def notify_order_status(app, order):
    """Notify customer of order status update."""
    restaurant = app.config.get('RESTAURANT_NAME', 'Goody Kitchen')
    status_labels = {
        'preparing': 'Being Prepared 👨‍🍳',
        'ready': 'Ready for Pickup! 🎉',
        'delivered': 'Delivered ✅',
    }
    status_label = status_labels.get(order.status, order.status)

    if order.customer_email:
        subject = f"Order #{order.order_number} – {status_label}"
        body = f"""
        <h2>Hi {order.customer_name}!</h2>
        <p>Your order <strong>#{order.order_number}</strong> status has been updated:</p>
        <h3 style="color:#e67e22">{status_label}</h3>
        {'<p>🎉 Please come to the counter to pick up your order!</p>' if order.status == 'ready' else ''}
        <p>– {restaurant}</p>
        """
        _send_email(app, order.customer_email, subject, body)

    if order.customer_phone and order.status == 'ready':
        wa_to = f"whatsapp:{order.customer_phone}"
        msg = (
            f"🎉 {restaurant}: Your order #{order.order_number} is READY for pickup! "
            f"Please come to the counter."
        )
        _send_whatsapp(app, wa_to, msg)
