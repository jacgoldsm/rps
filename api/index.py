"""
Vercel serverless function entry point
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, socketio

# Create the Flask application
app = create_app()

# Vercel requires the app to be exported
# For Socket.IO on Vercel, we need to use the WSGI app
# Note: WebSocket transport may not work on Vercel, will fallback to polling
handler = socketio.WSGIApp(socketio, app)

# This is what Vercel will use
def application(environ, start_response):
    return handler(environ, start_response)
