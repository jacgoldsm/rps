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

    # Create tables automatically if they don't exist
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created/verified successfully")

            # Run migration to make email optional if needed
            run_email_migration(app, db)
        except Exception as e:
            app.logger.error(f"Could not create database tables: {e}")

    return app


def run_email_migration(app, db):
    """Make email field optional - runs automatically on app startup"""
    try:
        # Check if we're using PostgreSQL
        database_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')

        if 'postgresql' in database_uri:
            # PostgreSQL migration
            with db.engine.connect() as conn:
                # Check if email is already nullable
                result = conn.execute(db.text("""
                    SELECT is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'user' AND column_name = 'email'
                """))

                row = result.fetchone()
                if row and row[0] == 'NO':
                    # Email is NOT NULL, need to migrate
                    app.logger.info("Running email migration: making email field optional")

                    trans = conn.begin()
                    try:
                        # Remove NOT NULL constraint
                        conn.execute(db.text('ALTER TABLE "user" ALTER COLUMN email DROP NOT NULL'))

                        # Try to remove UNIQUE constraint
                        try:
                            result = conn.execute(db.text("""
                                SELECT constraint_name
                                FROM information_schema.table_constraints
                                WHERE table_name = 'user'
                                AND constraint_type = 'UNIQUE'
                                AND constraint_name LIKE '%email%'
                            """))

                            constraint = result.fetchone()
                            if constraint:
                                constraint_name = constraint[0]
                                conn.execute(db.text(f'ALTER TABLE "user" DROP CONSTRAINT {constraint_name}'))
                                app.logger.info(f"Removed UNIQUE constraint on email: {constraint_name}")
                        except Exception:
                            pass  # UNIQUE constraint might not exist

                        trans.commit()
                        app.logger.info("✓ Email field migration completed successfully")
                    except Exception as e:
                        trans.rollback()
                        app.logger.error(f"Email migration failed: {e}")
                elif row:
                    app.logger.info("Email field is already nullable - no migration needed")

        elif 'sqlite' in database_uri:
            # SQLite doesn't need migration - db.create_all() will use the new schema
            app.logger.info("SQLite detected - using schema from models.py")

    except Exception as e:
        app.logger.warning(f"Could not check/run email migration: {e}")


@login_manager.user_loader
def load_user(user_id):
    # Import User here to avoid circular imports
    from app.models import User
    return User.query.get(int(user_id))