# In app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Note: The imports for 'photos' and 'configure_uploads' 
# are REMOVED from here and moved into create_app()

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # --- MOVED IMPORTS AND CONFIGURATION BLOCK ---
    # These imports MUST happen here to avoid the circular dependency loop
    from .routes import photos 
    from flask_uploads import configure_uploads

    # This configuration must be done after app.config is loaded.
    with app.app_context():
        configure_uploads(app, photos)
    # ----------------------------------------------
    
    # Import and register blueprints
    from . import routes, models
    app.register_blueprint(routes.bp)
    
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