import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'goody-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///goody.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_FROM = os.environ.get('MAIL_FROM', '')
    KITCHEN_EMAIL = os.environ.get('KITCHEN_EMAIL', '')

    # Twilio settings
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    KITCHEN_WHATSAPP = os.environ.get('KITCHEN_WHATSAPP', '')

    # App settings
    RESTAURANT_NAME = os.environ.get('RESTAURANT_NAME', 'Goody Kitchen')
    RESTAURANT_PHONE = os.environ.get('RESTAURANT_PHONE', '')
    RESTAURANT_ADDRESS = os.environ.get('RESTAURANT_ADDRESS', '')
    ORDERS_ENABLED = True
