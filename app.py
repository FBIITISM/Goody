"""Goody – Food Ordering Application (Flask backend)."""
import os
import json
import random
import string
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort, send_file
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from dotenv import load_dotenv

from config import Config
from database import db, User, Category, MenuItem, Order, OrderingWindow, SiteSetting
from utils.auth import role_required
from utils.qr_generator import generate_order_qr, order_qr_base64
from utils.notifications import notify_order_received, notify_order_status

load_dotenv()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_order_number():
    """Generate a short unique order number."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return f"{letters}{digits}"


def is_ordering_open():
    """Return True if an ordering window is active right now (or admin forced open)."""
    enabled = SiteSetting.get('orders_enabled', 'true')
    if enabled == 'false':
        return False

    windows = OrderingWindow.query.filter_by(is_active=True).all()
    if not windows:
        return True  # No restrictions configured

    now = datetime.now()
    current_time = now.strftime('%H:%M')
    current_dow = now.weekday()  # 0=Mon

    for w in windows:
        if w.day_of_week is not None and w.day_of_week != current_dow:
            continue
        if w.open_time <= current_time <= w.close_time:
            return True
    return False


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        if current_user.role == 'kitchen':
            return redirect(url_for('kitchen_dashboard'))
        return redirect(url_for('customer_menu'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            remember = request.form.get('remember') == 'on'
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'danger')
    return render_template('index.html', show_login=True)


@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('index'))

    if User.query.filter_by(email=email).first():
        flash('Email already registered. Please log in.', 'warning')
        return redirect(url_for('index'))

    user = User(name=name, email=email, phone=phone, role='customer')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    flash(f'Welcome to Goody, {name}! 🎉', 'success')
    return redirect(url_for('customer_menu'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Customer routes
# ---------------------------------------------------------------------------

@app.route('/menu')
def customer_menu():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    featured = MenuItem.query.filter_by(is_featured=True, is_available=True).limit(6).all()
    ordering_open = is_ordering_open()
    restaurant_name = SiteSetting.get('restaurant_name', app.config['RESTAURANT_NAME'])
    tagline = SiteSetting.get('restaurant_tagline', 'Good Food, Fast & Fresh')
    return render_template(
        'customer/menu.html',
        categories=categories,
        featured=featured,
        ordering_open=ordering_open,
        restaurant_name=restaurant_name,
        tagline=tagline,
    )


@app.route('/cart')
def customer_cart():
    return render_template('customer/cart.html')


@app.route('/place-order', methods=['POST'])
def place_order():
    if not is_ordering_open():
        flash('Sorry, ordering is currently closed.', 'warning')
        return redirect(url_for('customer_menu'))

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    customer_name = data.get('customer_name', '').strip()
    customer_email = data.get('customer_email', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    notes = data.get('notes', '').strip()
    items = data.get('items', [])

    if not customer_name:
        return jsonify({'success': False, 'error': 'Customer name is required'}), 400
    if not items:
        return jsonify({'success': False, 'error': 'No items in order'}), 400

    # Validate items against DB
    validated_items = []
    total = 0.0
    for item in items:
        mi = MenuItem.query.get(int(item.get('id', 0)))
        if not mi or not mi.is_available:
            continue
        qty = max(1, int(item.get('qty', 1)))
        validated_items.append({
            'id': mi.id,
            'name': mi.name,
            'price': mi.price,
            'qty': qty,
        })
        total += mi.price * qty

    if not validated_items:
        return jsonify({'success': False, 'error': 'No valid items'}), 400

    # Create order
    order_number = generate_order_number()
    while Order.query.filter_by(order_number=order_number).first():
        order_number = generate_order_number()

    order = Order(
        order_number=order_number,
        user_id=current_user.id if current_user.is_authenticated else None,
        customer_name=customer_name,
        customer_email=customer_email or None,
        customer_phone=customer_phone or None,
        total_price=round(total, 2),
        notes=notes or None,
        status='received',
    )
    order.set_items(validated_items)
    db.session.add(order)
    db.session.flush()  # get the id

    # Generate QR code
    try:
        qr_save_dir = os.path.abspath(os.path.join(app.static_folder, 'qr_codes'))
        # Ensure the directory is within the static folder (prevent traversal)
        if not qr_save_dir.startswith(os.path.abspath(app.static_folder)):
            raise ValueError('Invalid QR save directory')
        qr_path, _ = generate_order_qr(order, save_dir=qr_save_dir)
        order.qr_code_path = qr_path
    except Exception as e:
        app.logger.warning(f'QR generation failed: {e}')

    db.session.commit()

    # Send notifications (non-blocking)
    try:
        notify_order_received(app, order)
    except Exception as e:
        app.logger.warning(f'Notification failed: {e}')

    return jsonify({
        'success': True,
        'order_number': order_number,
        'order_id': order.id,
        'total': order.total_price,
    })


@app.route('/order/<order_number>')
def order_status(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    qr_b64 = None
    try:
        qr_b64 = order_qr_base64(order)
    except Exception:
        pass
    return render_template('customer/order.html', order=order, qr_b64=qr_b64)


@app.route('/order/<order_number>/status-json')
def order_status_json(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return jsonify({'status': order.status, 'updated_at': order.updated_at.isoformat()})


@app.route('/history')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/history.html', orders=orders)


# ---------------------------------------------------------------------------
# Kitchen routes
# ---------------------------------------------------------------------------

@app.route('/kitchen')
@login_required
@role_required('kitchen', 'admin')
def kitchen_dashboard():
    active_orders = Order.query.filter(
        Order.status.in_(['received', 'preparing'])
    ).order_by(Order.created_at.asc()).all()
    ready_orders = Order.query.filter_by(status='ready').order_by(Order.created_at.desc()).limit(20).all()
    return render_template('kitchen/dashboard.html', active_orders=active_orders, ready_orders=ready_orders)


@app.route('/kitchen/orders')
@login_required
@role_required('kitchen', 'admin')
def kitchen_orders_json():
    """Polling endpoint for live kitchen updates."""
    since_str = request.args.get('since')
    query = Order.query.filter(Order.status.in_(['received', 'preparing', 'ready']))
    if since_str:
        try:
            since_dt = datetime.fromisoformat(since_str)
            query = query.filter(Order.updated_at >= since_dt)
        except ValueError:
            pass
    orders = query.order_by(Order.created_at.asc()).all()
    return jsonify([{
        'id': o.id,
        'order_number': o.order_number,
        'customer_name': o.customer_name,
        'status': o.status,
        'items': o.get_items(),
        'total': o.total_price,
        'notes': o.notes,
        'created_at': o.created_at.isoformat(),
        'updated_at': o.updated_at.isoformat(),
    } for o in orders])


@app.route('/kitchen/order/<int:order_id>')
@login_required
@role_required('kitchen', 'admin')
def kitchen_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    qr_b64 = None
    try:
        qr_b64 = order_qr_base64(order)
    except Exception:
        pass
    return render_template('kitchen/order_detail.html', order=order, qr_b64=qr_b64)


@app.route('/kitchen/order/<int:order_id>/update', methods=['POST'])
@login_required
@role_required('kitchen', 'admin')
def kitchen_update_order(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status') or request.get_json(silent=True, force=True).get('status')
    allowed = ['received', 'preparing', 'ready', 'delivered']
    if new_status not in allowed:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    try:
        notify_order_status(app, order)
    except Exception as e:
        app.logger.warning(f'Status notification failed: {e}')
    return jsonify({'success': True, 'status': order.status})


@app.route('/kitchen/order/<int:order_id>/print')
@login_required
@role_required('kitchen', 'admin')
def kitchen_print_order(order_id):
    order = Order.query.get_or_404(order_id)
    qr_b64 = None
    try:
        qr_b64 = order_qr_base64(order)
    except Exception:
        pass
    return render_template('kitchen/print_order.html', order=order, qr_b64=qr_b64)


@app.route('/kitchen/scan-deliver', methods=['POST'])
@login_required
@role_required('kitchen', 'admin')
def kitchen_scan_deliver():
    """Mark order as delivered via QR scan."""
    data = request.get_json(silent=True) or {}
    raw = data.get('qr_data', '')
    try:
        info = json.loads(raw)
        order_number = info.get('order_number')
    except Exception:
        order_number = raw.strip()

    order = Order.query.filter_by(order_number=order_number).first()
    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    order.status = 'delivered'
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'order_number': order_number})


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route('/admin')
@login_required
@role_required('admin')
def admin_dashboard():
    total_orders = Order.query.count()
    today = datetime.utcnow().date()
    today_orders = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    today_revenue = db.session.query(db.func.sum(Order.total_price)).filter(
        db.func.date(Order.created_at) == today
    ).scalar() or 0.0
    total_revenue = db.session.query(db.func.sum(Order.total_price)).scalar() or 0.0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    pending_orders = Order.query.filter(Order.status.in_(['received', 'preparing'])).count()
    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        today_orders=today_orders,
        today_revenue=today_revenue,
        total_revenue=total_revenue,
        recent_orders=recent_orders,
        pending_orders=pending_orders,
    )


@app.route('/admin/menu')
@login_required
@role_required('admin')
def admin_menu():
    categories = Category.query.order_by(Category.sort_order).all()
    items = MenuItem.query.order_by(MenuItem.category_id, MenuItem.name).all()
    return render_template('admin/menu_manage.html', categories=categories, items=items)


@app.route('/admin/menu/item/add', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_item():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price = float(request.form.get('price', 0))
    category_id = int(request.form.get('category_id', 0))
    is_available = 'is_available' in request.form
    is_featured = 'is_featured' in request.form
    mi = MenuItem(
        name=name, description=description, price=price,
        category_id=category_id, is_available=is_available, is_featured=is_featured
    )
    db.session.add(mi)
    db.session.commit()
    flash(f'"{name}" added to menu.', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/item/<int:item_id>/edit', methods=['POST'])
@login_required
@role_required('admin')
def admin_edit_item(item_id):
    mi = MenuItem.query.get_or_404(item_id)
    mi.name = request.form.get('name', mi.name).strip()
    mi.description = request.form.get('description', mi.description or '').strip()
    mi.price = float(request.form.get('price', mi.price))
    mi.category_id = int(request.form.get('category_id', mi.category_id))
    mi.is_available = 'is_available' in request.form
    mi.is_featured = 'is_featured' in request.form
    db.session.commit()
    flash(f'"{mi.name}" updated.', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/item/<int:item_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_item(item_id):
    mi = MenuItem.query.get_or_404(item_id)
    name = mi.name
    db.session.delete(mi)
    db.session.commit()
    flash(f'"{name}" removed from menu.', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/category/add', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', '🍽️').strip()
    if name:
        cat = Category(name=name, icon=icon)
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{name}" added.', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_settings():
    windows = OrderingWindow.query.all()
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'toggle_orders':
            current = SiteSetting.get('orders_enabled', 'true')
            SiteSetting.set('orders_enabled', 'false' if current == 'true' else 'true')
            flash('Ordering status updated.', 'success')

        elif action == 'save_info':
            SiteSetting.set('restaurant_name', request.form.get('restaurant_name', ''))
            SiteSetting.set('restaurant_tagline', request.form.get('restaurant_tagline', ''))
            flash('Restaurant info saved.', 'success')

        elif action == 'add_window':
            name = request.form.get('win_name', '').strip()
            open_t = request.form.get('open_time', '08:00')
            close_t = request.form.get('close_time', '22:00')
            dow = request.form.get('day_of_week')
            dow = int(dow) if dow and dow.isdigit() else None
            if name:
                window = OrderingWindow(name=name, open_time=open_t, close_time=close_t, day_of_week=dow)
                db.session.add(window)
                db.session.commit()
                flash('Ordering window added.', 'success')

        elif action == 'delete_window':
            win_id = int(request.form.get('window_id', 0))
            win = OrderingWindow.query.get(win_id)
            if win:
                db.session.delete(win)
                db.session.commit()
                flash('Window deleted.', 'success')

        elif action == 'toggle_window':
            win_id = int(request.form.get('window_id', 0))
            win = OrderingWindow.query.get(win_id)
            if win:
                win.is_active = not win.is_active
                db.session.commit()
                flash('Window updated.', 'success')

        return redirect(url_for('admin_settings'))

    orders_enabled = SiteSetting.get('orders_enabled', 'true') == 'true'
    restaurant_name = SiteSetting.get('restaurant_name', app.config['RESTAURANT_NAME'])
    tagline = SiteSetting.get('restaurant_tagline', '')
    return render_template(
        'admin/settings.html',
        windows=windows,
        orders_enabled=orders_enabled,
        restaurant_name=restaurant_name,
        tagline=tagline,
    )


@app.route('/admin/analytics')
@login_required
@role_required('admin')
def admin_analytics():
    # Last 7 days revenue
    from sqlalchemy import text
    daily = db.session.execute(text(
        "SELECT date(created_at) as day, COUNT(*) as cnt, SUM(total_price) as rev "
        "FROM orders WHERE created_at >= date('now', '-7 days') "
        "GROUP BY day ORDER BY day"
    )).fetchall()

    # Top items
    all_orders = Order.query.all()
    item_counts = {}
    for o in all_orders:
        for item in o.get_items():
            k = item['name']
            item_counts[k] = item_counts.get(k, 0) + item['qty']
    top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Status breakdown
    statuses = db.session.execute(text(
        "SELECT status, COUNT(*) as cnt FROM orders GROUP BY status"
    )).fetchall()

    return render_template(
        'admin/analytics.html',
        daily=daily,
        top_items=top_items,
        statuses=statuses,
    )


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

@app.route('/api/menu')
def api_menu():
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    result = []
    for cat in categories:
        items = [
            {'id': i.id, 'name': i.name, 'description': i.description,
             'price': i.price, 'is_available': i.is_available, 'is_featured': i.is_featured}
            for i in cat.items if i.is_available
        ]
        if items:
            result.append({'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'items': items})
    return jsonify(result)


@app.route('/api/ordering-status')
def api_ordering_status():
    return jsonify({'open': is_ordering_open()})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page not found'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='Access forbidden'), 403


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-seed if empty
        if not User.query.first():
            from seed_data import seed
            seed()
    app.run(debug=True, host='0.0.0.0', port=5000)
