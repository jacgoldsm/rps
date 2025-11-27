from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
import os

# Configure SocketIO with options suitable for Railway deployment
socketio_options = {
    'cors_allowed_origins': '*',
    'async_mode': 'eventlet',
    'logger': False,
    'engineio_logger': False,
}

socketio = SocketIO(**socketio_options)
login_manager = LoginManager()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__,
                static_folder='static',
                static_url_path='/static')
    app.config.from_object('config.Config')
    
    # Import db here to avoid circular imports
    from app.models import db
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.game import game_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    
    # Import socket handlers
    from app import socket_handlers

    # Only create tables automatically in local development
    # On Railway/production, use init_db.py script instead
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        with app.app_context():
            try:
                db.create_all()
            except Exception as e:
                app.logger.warning(f"Could not create database tables: {e}")

    return app


@login_manager.user_loader
def load_user(user_id):
    # Import User here to avoid circular imports
    from app.models import User
    return User.query.get(int(user_id))