"""
Profit Tracker AI - Receipt processing and profit tracking for trade businesses
"""

from .create_app import create_app
from .models import db

__all__ = ['create_app', 'db']