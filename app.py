from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Sample menu data
menu_items = [
    {'id': 1, 'name': 'Biryani', 'price': 250, 'category': 'Rice'},
    {'id': 2, 'name': 'Butter Chicken', 'price': 300, 'category': 'Curry'},
    {'id': 3, 'name': 'Naan', 'price': 50, 'category': 'Bread'},
    {'id': 4, 'name': 'Samosa', 'price': 40, 'category': 'Appetizer'},
]

# Sample orders data
orders = []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/menu')
def menu():
    return render_template('menu.html', items=menu_items)

@app.route('/orders')
def view_orders():
    return render_template('orders.html', orders=orders)

@app.route('/kitchen')
def kitchen():
    return render_template('kitchen.html', orders=orders)

@app.route('/admin')
def admin():
    return render_template('admin.html', menu_items=menu_items, orders=orders)

@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = {
        'id': len(orders) + 1,
        'customer': data.get('customer', 'Guest'),
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': 'received'
    }
    orders.append(new_order)
    return jsonify({'success': True, 'order_id': new_order['id']}), 201

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)