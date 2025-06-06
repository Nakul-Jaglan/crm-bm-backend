#!/usr/bin/env python3
"""
Database Health Check Script
Run this to test database connectivity and setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, User, Base
from config import settings
import traceback

def test_database_connection():
    """Test basic database connectivity"""
    try:
        print(f"🔗 Testing database connection...")
        print(f"📊 Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"🌍 Environment: {settings.ENVIRONMENT}")
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("✅ Database connection successful!")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        traceback.print_exc()
        return False

def test_tables():
    """Test if tables exist and can be queried"""
    try:
        print(f"🗄️  Testing database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified!")
        
        # Test user table
        db = SessionLocal()
        try:
            user_count = db.query(User).count()
            print(f"👥 Found {user_count} users in database")
            
            if user_count > 0:
                # Get first user as test
                first_user = db.query(User).first()
                print(f"👤 Sample user: {first_user.email} ({first_user.role})")
            else:
                print("⚠️  No users found - database needs seeding")
                
        finally:
            db.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        traceback.print_exc()
        return False

def main():
    print("🩺 Bonhoeffer CRM Database Health Check")
    print("=" * 50)
    
    # Test connection
    if not test_database_connection():
        print("💥 Database connection failed - cannot proceed")
        sys.exit(1)
    
    print()
    
    # Test tables
    if not test_tables():
        print("💥 Database tables test failed")
        sys.exit(1)
    
    print()
    print("🎉 All database health checks passed!")
    print("✅ Your database is ready for the CRM application")

if __name__ == "__main__":
    main()
