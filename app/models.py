from . import db, login_manager
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # In-app notifications for the user
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    category = db.Column(db.String(80), default="General")
    stock = db.Column(db.Integer, default=100)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    fullname = db.Column(db.String(140))
    email = db.Column(db.String(140))
    address = db.Column(db.String(300))
    total = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    name = db.Column(db.String(140))
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def seed_data():
    # Called at startup; add demo admin/user/products if none exist
    if User.query.first():
        return
    admin = User(username="admin", email="admin@example.com", is_admin=True)
    admin.set_password("admin123")
    demo = User(username="demo_user", email="user@example.com")
    demo.set_password("user123")
    db.session.add_all([admin, demo])

    # sample products (use actual uploaded images)
    sample_products = [
        Product(name="Bluetooth Headphones", price=49.99,
                description="Wireless over-ear Bluetooth headphones with noise isolation.",
                image_url="/static/uploads/headphones.jpg", category="Headphones", stock=25),
        Product(name="Portable Bluetooth Speaker", price=29.99,
                description="Water-resistant portable speaker with 8h battery.",
                image_url="/static/uploads/speaker.jpg", category="Speakers", stock=40),
        Product(name="Smart Watch", price=119.99,
                description="Fitness-focused smart watch with heart-rate monitor.",
                image_url="/static/uploads/smartwatch.jpg", category="Watches", stock=15),
        Product(name="USB-C Charger", price=15.50,
                description="Fast charging USB-C adapter, 30W.",
                image_url="/static/uploads/chargecable.jpg", category="Accessories", stock=100),
    ]
    db.session.add_all(sample_products)
    db.session.commit()
