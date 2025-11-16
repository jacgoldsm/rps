"""
Vercel serverless function entry point
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

# Create the Flask application
app = create_app()

# This is what Vercel will use - just export the app directly
# Flask-SocketIO is already integrated into the app
# Note: WebSocket transport may not work on Vercel, will fallback to polling
