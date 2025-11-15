from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import flash
from app import socketio
from app.models import Game, db, User
from datetime import datetime

@socketio.on('join_game')
def handle_join_game(data):
    """Player joins a game room"""
    game_id = data['game_id']
    game = Game.query.get(game_id)
    
    if not game:
        return
    
    # Join the socket room
    join_room(f'game_{game_id}')
    
    # Check current game state and notify accordingly
    if game.status == 'active' and game.player2_id is not None:
        # Game is already active with both players
        # Determine opponent username
        if current_user.id == game.player1_id:
            opponent = User.query.get(game.player2_id)
        else:
            opponent = User.query.get(game.player1_id)
        
        # Notify all players in the room
        emit('player_joined', {
            'player_id': current_user.id,
            'username': current_user.username,
            'opponent_username': opponent.username if opponent else 'Unknown',
            'game_active': True
        }, room=f'game_{game_id}')
    else:
        # Player1 is waiting
        emit('waiting_for_opponent', {
            'message': 'Waiting for another player to join...'
        })

@socketio.on('make_choice')
def handle_choice(data):
    """Handle player's rock/paper/scissors choice"""
    game_id = data['game_id']
    choice = data['choice']  # 'rock', 'paper', or 'scissors'
    
    game = Game.query.get(game_id)
    
    if current_user.id == game.player1_id:
        game.player1_choice = choice
    elif current_user.id == game.player2_id:
        game.player2_choice = choice
    
    # Check if both players have made choices
    if game.player1_choice and game.player2_choice:
        winner_id = determine_winner(game)
        game.winner_id = winner_id
        game.status = 'completed'
        game.completed_at = datetime.utcnow()
        
        # Update ELO ratings
        update_elo_ratings(game)
        
        db.session.commit()
        
        # Broadcast result to both players
        emit('game_result', {
            'player1_choice': game.player1_choice,
            'player2_choice': game.player2_choice,
            'winner_id': winner_id,
            'player1_elo_change': game.player1_elo_change,
            'player2_elo_change': game.player2_elo_change
        }, room=f'game_{game_id}')
    else:
        db.session.commit()
        emit('choice_made', {
            'player_id': current_user.id
        }, room=f'game_{game_id}')

def determine_winner(game):
    """Determine the winner based on choices"""
    p1_choice = game.player1_choice
    p2_choice = game.player2_choice
    
    if p1_choice == p2_choice:
        return None  # Tie
    
    winning_combinations = {
        ('rock', 'scissors'): game.player1_id,
        ('paper', 'rock'): game.player1_id,
        ('scissors', 'paper'): game.player1_id,
        ('scissors', 'rock'): game.player2_id,
        ('rock', 'paper'): game.player2_id,
        ('paper', 'scissors'): game.player2_id
    }
    
    return winning_combinations.get((p1_choice, p2_choice))

def update_elo_ratings(game):
    """Update ELO ratings for both players based on game outcome"""
    player1 = User.query.get(game.player1_id)
    player2 = User.query.get(game.player2_id)
    
    # K-factor: maximum rating change per game
    K = 32
    
    # Expected scores based on current ratings
    expected_p1 = 1 / (1 + 10 ** ((player2.elo_rating - player1.elo_rating) / 400))
    expected_p2 = 1 / (1 + 10 ** ((player1.elo_rating - player2.elo_rating) / 400))
    
    # Actual scores (1 = win, 0.5 = tie, 0 = loss)
    if game.winner_id is None:  # Tie
        score_p1 = 0.5
        score_p2 = 0.5
        player1.games_tied += 1
        player2.games_tied += 1
    elif game.winner_id == game.player1_id:  # Player 1 wins
        score_p1 = 1.0
        score_p2 = 0.0
        player1.games_won += 1
        player2.games_lost += 1
    else:  # Player 2 wins
        score_p1 = 0.0
        score_p2 = 1.0
        player1.games_lost += 1
        player2.games_won += 1
    
    # Calculate rating changes
    elo_change_p1 = round(K * (score_p1 - expected_p1))
    elo_change_p2 = round(K * (score_p2 - expected_p2))
    
    # Update ratings
    player1.elo_rating += elo_change_p1
    player2.elo_rating += elo_change_p2
    
    # Update games played
    player1.games_played += 1
    player2.games_played += 1
    
    # Store ELO changes in game record
    game.player1_elo_change = elo_change_p1
    game.player2_elo_change = elo_change_p2
    
    db.session.add(player1)
    db.session.add(player2)