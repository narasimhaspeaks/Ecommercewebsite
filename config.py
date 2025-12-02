import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_me")
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(basedir, "ecommerce.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- REQUIRED UPLOAD CONFIGURATION ---
    # 1. UPLOADED_PHOTOS_DEST: The file path where images will be saved.
    #    We are setting it to 'app/static/uploads' relative to the base directory.
    #    Note: 'photos' is the name of the UploadSet you defined in routes.py
    UPLOADED_PHOTOS_DEST = os.path.join(basedir, 'app', 'static', 'uploads')
    
    # 2. UPLOADED_PHOTOS_URL: The URL prefix to access the images.
    UPLOADED_PHOTOS_URL = '/static/uploads/'
    # -------------------------------------