#!/usr/bin/env python
"""
Debug database configuration
"""
import os

print("=== Database Configuration Debug ===")
print(f"DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")
print(f"DATABASE_URL value: {os.environ.get('DATABASE_URL', 'NOT SET')[:50]}...")  # First 50 chars
print(f"RENDER env var: {os.environ.get('RENDER', 'NOT SET')}")
print(f"Current directory: {os.getcwd()}")
print("\n=== Testing Config ===")

try:
    from app.config import Config
    config = Config()
    print(f"SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI[:50]}...")
except Exception as e:
    print(f"Error loading config: {e}")

print("\n=== Environment Variables ===")
for key, value in os.environ.items():
    if 'DATABASE' in key or 'POSTGRES' in key or 'SQL' in key:
        print(f"{key}: {value[:50]}...")