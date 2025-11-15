from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Game, User, db

game_bp = Blueprint('game', __name__)

@game_bp.route('/')
@game_bp.route('/lobby')
@login_required
def lobby():
    """Game lobby - show online players"""
    online_users = User.query.all()
    return render_template('lobby.html', users=online_users)

@game_bp.route('/join-random-game', methods=['POST'])
@login_required
def join_random_game():
    """Join or create a random matchmaking game"""
    # First, try to find an existing quickplay game waiting for a player
    # Exclude games where current user is already player1
    available_game = Game.query.filter_by(
        status='waiting',
        is_quickplay=True,
        player2_id=None
    ).filter(
        Game.player1_id != current_user.id
    ).first()

    if available_game:
        # Join the existing game
        available_game.player2_id = current_user.id
        available_game.status = 'active'
        db.session.commit()
        return jsonify({
            'game_id': available_game.id,
            'status': 'matched',
            'message': 'Matched with a player!'
        })
    else:
        # No available game, create a new quickplay game
        game = Game(
            player1_id=current_user.id,
            status='waiting',
            is_quickplay=True
        )
        db.session.add(game)
        db.session.commit()
        return jsonify({
            'game_id': game.id,
            'status': 'waiting',
            'message': 'Waiting for an opponent...'
        })

@game_bp.route('/game/<int:game_id>')
@login_required
def play_game(game_id):
    """Game room for playing"""
    game = Game.query.get_or_404(game_id)
    
    # Check if user is already part of this game
    if game.player1_id == current_user.id or game.player2_id == current_user.id:
        # User is already in the game, just show the page
        pass
    elif game.status == 'waiting' and game.player2_id is None:
        # Add current user as player2
        game.player2_id = current_user.id
        game.status = 'active'
        db.session.commit()
    else:
        # Game is full or user is not part of it
        flash('This game is not available')
        return redirect(url_for('game.lobby'))
    
    return render_template('game.html', game=game)

@game_bp.route('/leaderboard')
def leaderboard():
    """Display ELO leaderboard"""
    # Get search query if provided
    search_query = request.args.get('search', '').strip()
    
    # Base query
    query = User.query
    
    # Apply search filter if provided
    if search_query:
        query = query.filter(User.username.ilike(f'%{search_query}%'))
    
    # Get top players sorted by ELO
    players = query.order_by(User.elo_rating.desc()).all()
    
    return render_template('leaderboard.html', 
                         players=players, 
                         search_query=search_query)