import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from app.models import Notification, Order
app = create_app()
with app.app_context():
    notes = Notification.query.all()
    print('Total notifications:', len(notes))
    for n in notes:
        print(n.id, n.user_id, n.message, n.is_read, n.created_at)
    orders = Order.query.all()
    print('Orders:', [(o.id, o.order_code) for o in orders])
