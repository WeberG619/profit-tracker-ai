#!/usr/bin/env python
"""
Force PostgreSQL connection for Render
"""
import os

# Get the DATABASE_URL from environment
database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    print(f"Found DATABASE_URL: {database_url[:30]}...")
    
    # Force it into the environment with the correct name
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        print("Fixed postgres:// to postgresql://")
    
    # Set it explicitly
    os.environ['SQLALCHEMY_DATABASE_URI'] = database_url
    print("Set SQLALCHEMY_DATABASE_URI explicitly")
else:
    print("ERROR: No DATABASE_URL found in environment!")
    print("Available environment variables:")
    for key in sorted(os.environ.keys()):
        if any(x in key.upper() for x in ['DATA', 'POST', 'SQL', 'RENDER']):
            print(f"  {key}: {os.environ[key][:50]}...")