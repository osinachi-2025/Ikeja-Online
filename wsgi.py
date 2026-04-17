"""
WSGI entry point for production deployment.
This file is used by Gunicorn/Render to start the Flask application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Import the Flask app
from app import app, db, init_db

# Initialize database on app startup
with app.app_context():
    try:
        db.create_all()
        init_db()
        print("[WSGI] Database tables initialized successfully")
    except Exception as e:
        print(f"[WSGI] Error initializing database: {str(e)}")

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the app (for local development only - Gunicorn will handle this in production)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Always False in production
    )
