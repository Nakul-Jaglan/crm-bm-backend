#!/bin/bash

# Create data directory
mkdir -p data

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}