#!/usr/bin/env python3
"""Test script to verify basic functionality"""

print("Testing deployment...")

# Test Flask import
try:
    import flask
    print(f"✓ Flask {flask.__version__} imported successfully")
except Exception as e:
    print(f"✗ Flask import failed: {e}")

# Test app import
try:
    from app_ultra_minimal import app
    print("✓ App imported successfully")
except Exception as e:
    print(f"✗ App import failed: {e}")

# Test routes
try:
    with app.test_client() as client:
        # Test health endpoint
        response = client.get('/health')
        print(f"✓ Health endpoint: {response.status_code}")
        
        # Test home page
        response = client.get('/')
        print(f"✓ Home page: {response.status_code}")
        
        # Test login page
        response = client.get('/login')
        print(f"✓ Login page: {response.status_code}")
        
    print("\nAll tests passed!")
except Exception as e:
    print(f"\n✗ Route tests failed: {e}")