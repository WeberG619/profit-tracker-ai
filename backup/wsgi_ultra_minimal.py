"""
WSGI for ultra minimal app
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_ultra_minimal import app

if __name__ == '__main__':
    app.run()