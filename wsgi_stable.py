"""
WSGI for stable app
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_stable import app

if __name__ == '__main__':
    app.run()