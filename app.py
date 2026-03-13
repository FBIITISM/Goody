from flask import Flask, render_template, request, redirect, url_for
from models import db, Order
from utils import generate_qr_code
from email_service import send_email

app = Flask(__name__)

# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///goody.db'
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/order', methods=['POST'])
def order():
    # Process order
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)