from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    elo_rating = db.Column(db.Integer, default=1200)  # Starting ELO rating
    games_played = db.Column(db.Integer, default=0)
    games_won = db.Column(db.Integer, default=0)
    games_lost = db.Column(db.Integer, default=0)
    games_tied = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    games_as_player1 = db.relationship('Game', foreign_keys='Game.player1_id', backref='player1')
    games_as_player2 = db.relationship('Game', foreign_keys='Game.player2_id', backref='player2')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def win_rate(self):
        """Calculate win rate percentage"""
        total_decided_games = self.games_won + self.games_lost
        if total_decided_games == 0:
            return 0.0
        return round((self.games_won / total_decided_games) * 100, 1)


class Game(db.Model):
    """Game model to track matches"""
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    player1_choice = db.Column(db.String(10))  # rock, paper, scissors
    player2_choice = db.Column(db.String(10))
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='waiting')  # waiting, active, completed, cancelled
    is_quickplay = db.Column(db.Boolean, default=False)  # True if random matchmaking game
    player1_elo_change = db.Column(db.Integer, default=0)  # ELO change for player1
    player2_elo_change = db.Column(db.Integer, default=0)  # ELO change for player2
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)