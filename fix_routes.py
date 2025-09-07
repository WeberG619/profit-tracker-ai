"""
Script to verify routes are registered
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.app import app

print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.endpoint}: {rule.rule}")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")