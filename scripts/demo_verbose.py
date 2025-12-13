import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from app.models import User, Product, Order, OrderItem, Notification
from app.routes import generate_order_code

app = create_app()

def dump_state(prefix=''):
    print('\n===', prefix, 'STATE DUMP ===')
    orders = Order.query.order_by(Order.id).all()
    for o in orders:
        print('Order:', o.id, getattr(o, 'order_code', None), o.user_id, o.fullname, o.total)
        items = OrderItem.query.filter_by(order_id=o.id).all()
        for it in items:
            print('  Item:', it.id, it.product_id, it.name, it.quantity)
    notes = Notification.query.order_by(Notification.id).all()
    for n in notes:
        print('Notification:', n.id, n.user_id, n.message, n.is_read)
    print('=== END STATE ===\n')

with app.app_context():
    admin = User.query.filter_by(email='admin@example.com').first()
    demo = User.query.filter_by(email='user@example.com').first()
    p = Product.query.first()
    if not admin or not demo or not p:
        print('Required users/products missing. Run seed_data or check DB.')
        sys.exit(1)

    # Clean up any previous demo orders created by these scripts to keep output clear
    print('Cleaning previous demo orders (test-run cleanup)')
    for o in Order.query.filter(Order.fullname.ilike('%Demo%')).all():
        OrderItem.query.filter_by(order_id=o.id).delete()
        db.session.delete(o)
    db.session.commit()

    dump_state('BEFORE')

    # Create a new order for demo user
    order = Order(user_id=demo.id, fullname='Demo User', email=demo.email, address='123 Demo St', total=p.price)
    order.order_code = generate_order_code(10)
    db.session.add(order)
    db.session.commit()
    oi = OrderItem(order_id=order.id, product_id=p.id, name=p.name, price=p.price, quantity=1)
    db.session.add(oi)
    db.session.commit()

    print('Created order:', order.id, order.order_code)
    dump_state('AFTER CREATE')

    # Use test client to login as admin and call cancel route
    client = app.test_client()
    r = client.post('/login', data={'email': admin.email, 'password': 'admin123'}, follow_redirects=True)
    print('Admin login response status:', r.status_code)
    r = client.post(f'/admin/orders/{order.id}/cancel', follow_redirects=True)
    print('Cancel POST status:', r.status_code)

    dump_state('AFTER CANCEL')

    # Show notifications for demo user specifically
    notes = Notification.query.filter_by(user_id=demo.id).order_by(Notification.id.desc()).all()
    print('\nNotifications for demo user:')
    for n in notes:
        print(n.id, n.message, n.is_read, n.created_at)

    # Final check whether order row exists
    order_after = Order.query.get(order.id)
    print('\nOrder after cancel exists?', bool(order_after))
