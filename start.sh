#!/bin/bash
# Startup script for Render deployment

echo "🚀 Starting Bonhoeffer CRM Backend..."

# Install dependencies (already done by Render, but just in case)
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create database tables
echo "🗄️  Creating database tables..."
python -c "
from database import engine, Base
print('Creating all database tables...')
Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
"

# Check if we need to seed initial data
echo "🌱 Checking for initial data..."
python -c "
from database import SessionLocal, User
db = SessionLocal()
try:
    user_count = db.query(User).count()
    if user_count == 0:
        print('No users found. Database needs seeding.')
        exit(1)
    else:
        print(f'Found {user_count} users. Database already seeded.')
        exit(0)
except Exception as e:
    print(f'Error checking users: {e}')
    exit(1)
finally:
    db.close()
"

# If exit code is 1, run seed data
if [ $? -eq 1 ]; then
    echo "🌱 Seeding initial data..."
    python seed_data.py
    echo "✅ Initial data seeded successfully!"
fi

echo "🎉 Database setup complete!"
echo "🚀 Starting the application..."

# Start the application
uvicorn main:app --host 0.0.0.0 --port $PORT
