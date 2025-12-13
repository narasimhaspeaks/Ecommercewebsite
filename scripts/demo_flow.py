import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Product, Order, Notification

app = create_app()

with app.app_context():
    client_user = app.test_client()
    client_admin = app.test_client()

    # Ensure there is at least one product and the demo user exists
    demo = User.query.filter_by(email='user@example.com').first()
    admin = User.query.filter_by(email='admin@example.com').first()
    if not demo or not admin:
        print('Required users missing. Check seed_data was run.')
        raise SystemExit(1)
    p = Product.query.first()
    if not p:
        print('No products found.')
        raise SystemExit(1)

    # User login
    r = client_user.post('/login', data={'email': demo.email, 'password': 'user123'}, follow_redirects=True)
    print('User login status code:', r.status_code)

    # Add to cart (for completeness - not used for direct order creation)
    r = client_user.get(f'/add_to_cart/{p.id}', follow_redirects=True)
    print('Add to cart status code:', r.status_code)

    # -- create an order directly (bypass forms/session) --
    from app.routes import generate_order_code
    order = Order(user_id=demo.id, fullname=demo.username, email=demo.email, address='123 Demo St, Demo City', total=p.price)
    order.order_code = generate_order_code(10)
    db.session.add(order)
    db.session.commit()
    # add item
    from app.models import OrderItem
    oi = OrderItem(order_id=order.id, product_id=p.id, name=p.name, price=p.price, quantity=1)
    db.session.add(oi)
    db.session.commit()
    print('Order created:', order.id, order.order_code, order.total)

    # Admin login
    r = client_admin.post('/login', data={'email': admin.email, 'password': 'admin123'}, follow_redirects=True)
    print('Admin login status code:', r.status_code)

    # Cancel the order as admin
    r = client_admin.post(f'/admin/orders/{order.id}/cancel', follow_redirects=True)
    print('Admin cancel status code:', r.status_code)

    # Re-query notifications for demo user
    notes = Notification.query.filter_by(user_id=demo.id).order_by(Notification.created_at.desc()).all()
    print('Notifications for demo user:', [(n.message, n.is_read) for n in notes])

    # Check if order still exists
    order_after = Order.query.get(order.id)
    print('Order after cancel exists:', bool(order_after))
