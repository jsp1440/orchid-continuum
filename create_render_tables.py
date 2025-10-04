import os
import sys

# Set Render database URL
os.environ['DATABASE_URL'] = "postgresql://orchid_user:4WVfquT9ZRvuc0PeHxyAvoGYPbdmIbq8@dpg-d390i5mmcj7s738lpqig-a.oregon-postgres.render.com/orchid_contnuum"

# Now import app and models
from app import app, db

print("🔨 Creating all database tables on Render...")
print(f"📍 Database: {os.environ['DATABASE_URL'][:50]}...\n")

with app.app_context():
    # Import all models to register them
    import models
    
    # Create all tables
    db.create_all()
    
    print("✅ All tables created successfully!")
    print("\n📊 Tables created:")
    
    # List all tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    
    for table in sorted(table_names):
        print(f"   ✓ {table}")
    
    print(f"\n🎉 Total: {len(table_names)} tables created")
