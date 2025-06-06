#!/bin/bash
# Deployment script for Render
echo "Starting deployment..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Database migrations completed!"
echo "Starting the application..."
