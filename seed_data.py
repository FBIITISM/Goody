"""Seed the database with sample data."""
from app import app
from database import db, User, Category, MenuItem, OrderingWindow, SiteSetting


def seed():
    with app.app_context():
        db.create_all()

        # Admin user
        if not User.query.filter_by(email='admin@goody.com').first():
            admin = User(name='Admin', email='admin@goody.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        # Kitchen user
        if not User.query.filter_by(email='kitchen@goody.com').first():
            kitchen = User(name='Kitchen Staff', email='kitchen@goody.com', role='kitchen')
            kitchen.set_password('kitchen123')
            db.session.add(kitchen)

        # Demo customer
        if not User.query.filter_by(email='customer@goody.com').first():
            cust = User(name='Demo Customer', email='customer@goody.com', role='customer')
            cust.set_password('customer123')
            db.session.add(cust)

        # Categories
        cats = [
            {'name': 'Burgers', 'icon': '🍔', 'sort_order': 1},
            {'name': 'Wraps', 'icon': '🌯', 'sort_order': 2},
            {'name': 'Sides', 'icon': '🍟', 'sort_order': 3},
            {'name': 'Drinks', 'icon': '🥤', 'sort_order': 4},
            {'name': 'Desserts', 'icon': '🍰', 'sort_order': 5},
        ]
        cat_map = {}
        for c in cats:
            existing = Category.query.filter_by(name=c['name']).first()
            if not existing:
                cat = Category(**c)
                db.session.add(cat)
                db.session.flush()
                cat_map[c['name']] = cat.id
            else:
                cat_map[c['name']] = existing.id

        db.session.flush()

        # Re-fetch IDs after flush
        for c in cats:
            cat_obj = Category.query.filter_by(name=c['name']).first()
            if cat_obj:
                cat_map[c['name']] = cat_obj.id

        menu_items = [
            # Burgers
            {'name': 'Classic Goody Burger', 'description': 'Juicy beef patty, lettuce, tomato, pickles, special sauce', 'price': 8.99, 'category': 'Burgers', 'is_featured': True},
            {'name': 'Double Stack', 'description': 'Two beef patties, double cheese, caramelised onions', 'price': 11.99, 'category': 'Burgers', 'is_featured': True},
            {'name': 'Crispy Chicken Burger', 'description': 'Crispy fried chicken, coleslaw, sriracha mayo', 'price': 9.99, 'category': 'Burgers'},
            {'name': 'Veggie Burger', 'description': 'Plant-based patty, avocado, roasted veggies', 'price': 9.49, 'category': 'Burgers'},
            # Wraps
            {'name': 'Grilled Chicken Wrap', 'description': 'Grilled chicken, mixed greens, tzatziki, tomato', 'price': 8.49, 'category': 'Wraps', 'is_featured': True},
            {'name': 'Falafel Wrap', 'description': 'Crispy falafel, hummus, pickled veggies, tahini', 'price': 7.99, 'category': 'Wraps'},
            {'name': 'BBQ Beef Wrap', 'description': 'Pulled beef, BBQ sauce, jalapeños, cheese', 'price': 9.49, 'category': 'Wraps'},
            # Sides
            {'name': 'Goody Fries', 'description': 'Crispy golden fries with sea salt', 'price': 3.99, 'category': 'Sides'},
            {'name': 'Loaded Fries', 'description': 'Fries topped with cheese sauce, bacon bits, sour cream', 'price': 5.99, 'category': 'Sides', 'is_featured': True},
            {'name': 'Onion Rings', 'description': 'Crispy battered onion rings with dipping sauce', 'price': 4.49, 'category': 'Sides'},
            {'name': 'Coleslaw', 'description': 'Creamy homemade coleslaw', 'price': 2.99, 'category': 'Sides'},
            # Drinks
            {'name': 'Soft Drink', 'description': 'Cola, Lemonade, Sprite – your choice', 'price': 2.49, 'category': 'Drinks'},
            {'name': 'Fresh Juice', 'description': 'Orange, Apple, or Watermelon', 'price': 3.99, 'category': 'Drinks'},
            {'name': 'Milkshake', 'description': 'Chocolate, Vanilla, or Strawberry', 'price': 4.99, 'category': 'Drinks', 'is_featured': True},
            {'name': 'Water', 'description': 'Still or Sparkling', 'price': 1.49, 'category': 'Drinks'},
            # Desserts
            {'name': 'Chocolate Brownie', 'description': 'Warm fudge brownie with vanilla ice cream', 'price': 5.49, 'category': 'Desserts', 'is_featured': True},
            {'name': 'Ice Cream Sundae', 'description': 'Three scoops with toppings of your choice', 'price': 4.99, 'category': 'Desserts'},
            {'name': 'Cheesecake Slice', 'description': 'NY-style cheesecake with berry compote', 'price': 5.99, 'category': 'Desserts'},
        ]

        for item in menu_items:
            existing = MenuItem.query.filter_by(name=item['name']).first()
            if not existing:
                cat_id = cat_map.get(item['category'])
                if cat_id:
                    mi = MenuItem(
                        name=item['name'],
                        description=item.get('description', ''),
                        price=item['price'],
                        category_id=cat_id,
                        is_featured=item.get('is_featured', False),
                    )
                    db.session.add(mi)

        # Ordering window (daily 8am-10pm)
        if not OrderingWindow.query.first():
            window = OrderingWindow(
                name='Regular Hours',
                open_time='08:00',
                close_time='22:00',
                is_active=True,
            )
            db.session.add(window)

        # Site settings
        defaults = {
            'orders_enabled': 'true',
            'restaurant_name': 'Goody Kitchen',
            'restaurant_tagline': 'Good Food, Fast & Fresh',
        }
        for k, v in defaults.items():
            if not SiteSetting.query.filter_by(key=k).first():
                db.session.add(SiteSetting(key=k, value=v))

        db.session.commit()
        print("✅ Database seeded successfully!")
        print("  Admin:    admin@goody.com    / admin123")
        print("  Kitchen:  kitchen@goody.com  / kitchen123")
        print("  Customer: customer@goody.com / customer123")


if __name__ == '__main__':
    seed()
