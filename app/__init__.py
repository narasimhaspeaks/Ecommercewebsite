# In app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail

# Note: The imports for 'photos' and 'configure_uploads' 
# are REMOVED from here and moved into create_app()

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Import and register blueprints
    from . import routes, models
    app.register_blueprint(routes.bp)
    # Create DB tables and seed initial data in development environment
    with app.app_context():
        db.create_all()
        try:
            models.seed_data()
        except Exception:
            pass
        # Ensure 'order_code' column exists in Order table (for existing DBs)
        try:
            # Use PRAGMA to inspect columns in SQLite
            res = db.engine.execute("PRAGMA table_info('order')").fetchall()
            col_names = [r[1] for r in res]
            if 'order_code' not in col_names:
                # Add nullable column for existing DB
                db.engine.execute('ALTER TABLE "order" ADD COLUMN order_code VARCHAR(32)')
                # Populate codes for existing orders
                from .models import Order
                import secrets, string

                def _generate_code(length=10):
                    alphabet = string.ascii_uppercase + string.digits
                    return ''.join(secrets.choice(alphabet) for _ in range(length))

                orders = Order.query.all()
                for o in orders:
                    o.order_code = _generate_code(10)
                db.session.commit()
        except Exception:
            # If anything fails here, don't block app startup
            pass
    
    return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

# Error Handler
login_manager.login_view = 'main.login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"