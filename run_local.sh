#!/bin/bash

echo "🚀 Starting Profit Tracker AI locally..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=wsgi.py
export FLASK_ENV=development
export SECRET_KEY="dev-secret-key"

# Initialize database
echo "Setting up database..."
python -c "from app import db; db.create_all()"

# Run the application
echo "Starting server at http://localhost:5000"
python wsgi.py