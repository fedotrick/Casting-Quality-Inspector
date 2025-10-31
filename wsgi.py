#!/usr/bin/env python3
"""
WSGI entry point for the Quality Control application.
Uses the app factory pattern with SQLAlchemy data layer.
"""
import os
import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # Run development server
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 5005)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
