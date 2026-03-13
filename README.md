# 🍔 Goody Kitchen – Food Ordering App

A complete, production-ready food ordering web application built with Python Flask, SQLite, Bootstrap, and QR codes.

## Features

- **Customer Interface** – Browse menu, add to cart, place orders, track status in real-time
- **Kitchen Dashboard** – View live orders, update status (Received → Preparing → Ready), print orders with QR
- **Admin Panel** – Manage menu items, ordering windows (time-based), analytics
- **QR Codes** – Auto-generated for each order, scannable to mark delivered
- **Notifications** – Email (Gmail SMTP) + WhatsApp (Twilio) notifications
- **Role-based access** – Customer, Kitchen Staff, Admin

## Quick Start (Local)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings (email, Twilio, etc.)
```

### 3. Run the app

```bash
python app.py
```

The app auto-creates the SQLite database and seeds sample data on first run.

Open: **http://localhost:5000**

### 4. Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@goody.com | admin123 |
| Kitchen | kitchen@goody.com | kitchen123 |
| Customer | customer@goody.com | customer123 |

## Configuration (.env)

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask secret key (change this!) |
| `MAIL_USERNAME` | Gmail address |
| `MAIL_PASSWORD` | Gmail App Password (not your regular password) |
| `KITCHEN_EMAIL` | Email for kitchen notifications |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `KITCHEN_WHATSAPP` | Kitchen WhatsApp number (e.g. `whatsapp:+1234567890`) |
| `RESTAURANT_NAME` | Your restaurant name |

### Gmail Setup
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate an App Password for "Mail"
4. Use that password as `MAIL_PASSWORD`

### Twilio WhatsApp Setup (Free)
1. Sign up at [twilio.com](https://twilio.com)
2. Join the WhatsApp Sandbox (free): `twilio.com/try-twilio`
3. Copy your Account SID and Auth Token

## Project Structure

```
Goody/
├── app.py              # Main Flask application
├── config.py           # Configuration
├── database.py         # SQLAlchemy models
├── seed_data.py        # Sample data seeder
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── static/
│   ├── css/style.css
│   ├── js/
│   │   ├── customer.js   # Cart management
│   │   ├── kitchen.js    # Live order updates
│   │   └── qr-scanner.js # QR scan to deliver
│   └── images/
├── templates/
│   ├── base.html
│   ├── index.html        # Login/Register
│   ├── customer/         # Menu, Cart, Order tracking, History
│   ├── kitchen/          # Dashboard, Order detail, Print
│   └── admin/            # Dashboard, Menu, Settings, Analytics
└── utils/
    ├── auth.py           # Role-based access decorator
    ├── qr_generator.py   # QR code generation
    └── notifications.py  # Email + WhatsApp
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/menu` | GET | Get full menu as JSON |
| `/api/ordering-status` | GET | Check if ordering is open |
| `/place-order` | POST | Submit an order |
| `/order/<number>/status-json` | GET | Get order status |
| `/kitchen/orders` | GET | Live order list (kitchen) |
| `/kitchen/order/<id>/update` | POST | Update order status |
| `/kitchen/scan-deliver` | POST | Mark delivered via QR scan |

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full instructions on deploying to Render, Railway, or other platforms.
