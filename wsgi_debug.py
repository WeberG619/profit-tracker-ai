"""
Debug WSGI entry point
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.info("Starting WSGI debug application...")

try:
    from app.app_debug import app
    logger.info("Successfully imported app")
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    # Try alternative import
    try:
        from app.app import app
        logger.info("Successfully imported app using alternative import")
    except ImportError as e2:
        logger.error(f"Failed alternative import: {e2}")
        raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)