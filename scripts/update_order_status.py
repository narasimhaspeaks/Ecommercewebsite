"""
Migration script to add status column to existing orders
Run this once to update the database schema
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Order

app = create_app()

with app.app_context():
    # Try to add status column if it doesn't exist
    try:
        # Check if column exists by trying to query it
        Order.query.with_entities(Order.status).first()
        print("Status column already exists!")
    except:
        # Column doesn't exist, add it
        print("Adding status column to Order table...")
        
        # Add the column using raw SQL
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE [order] ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
        db.session.commit()
        
        print("Status column added successfully!")
        print("Updating existing orders to 'pending' status...")
        
        # Update all existing orders
        orders = Order.query.all()
        for order in orders:
            if not hasattr(order, 'status') or order.status is None:
                order.status = 'pending'
        
        db.session.commit()
        print(f"Updated {len(orders)} orders.")
    
    print("Database migration complete!")
