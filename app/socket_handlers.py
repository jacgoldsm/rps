from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from flask import flash, request
from app import socketio
from app.models import Game, db, User
from datetime import datetime
import threading

# Track active users and their current rooms
active_users = {}  # {session_id: {'user_id': id, 'room': 'lobby' or 'game_X'}}

# Track game timers
game_timers = {}  # {game_id: {'player1_timer': Timer, 'player2_timer': Timer}}

# Turn timer duration in seconds
TURN_TIMER_SECONDS = 30

def handle_timer_expire(game_id, player_id):
    """Handle when a player's turn timer expires"""
    game = Game.query.get(game_id)

    if not game or game.status != 'active':
        return

    # Check if player already made a choice
    if player_id == game.player1_id and game.player1_choice:
        return
    if player_id == game.player2_id and game.player2_choice:
        return

    # Player didn't make a choice in time - they lose
    # Determine winner (the other player)
    if player_id == game.player1_id:
        winner_id = game.player2_id
        loser_id = game.player1_id
        # Set a default losing choice for the player who timed out
        game.player1_choice = 'timeout'
        # If opponent hasn't chosen yet, set a default winning choice
        if not game.player2_choice:
            game.player2_choice = 'rock'
    else:
        winner_id = game.player1_id
        loser_id = game.player2_id
        game.player2_choice = 'timeout'
        if not game.player1_choice:
            game.player1_choice = 'rock'

    game.winner_id = winner_id
    game.status = 'completed'
    game.completed_at = datetime.utcnow()

    # Update ELO ratings
    update_elo_ratings(game)

    db.session.commit()

    # Cancel any remaining timers for this game
    cancel_game_timers(game_id)

    # Get player usernames
    winner = User.query.get(winner_id)
    loser = User.query.get(loser_id)

    # Notify both players
    socketio.emit('game_timeout', {
        'winner_id': winner_id,
        'loser_id': loser_id,
        'winner_username': winner.username if winner else 'Unknown',
        'loser_username': loser.username if loser else 'Unknown',
        'player1_elo_change': game.player1_elo_change,
        'player2_elo_change': game.player2_elo_change
    }, room=f'game_{game_id}')

def start_turn_timer(game_id, player_id):
    """Start a timer for a player's turn"""
    if game_id not in game_timers:
        game_timers[game_id] = {}

    timer_key = f'player{player_id}_timer'

    # Cancel existing timer if any
    if timer_key in game_timers[game_id]:
        game_timers[game_id][timer_key].cancel()

    # Create new timer
    timer = threading.Timer(TURN_TIMER_SECONDS, handle_timer_expire, args=[game_id, player_id])
    timer.start()
    game_timers[game_id][timer_key] = timer

def cancel_player_timer(game_id, player_id):
    """Cancel a specific player's timer"""
    if game_id not in game_timers:
        return

    timer_key = f'player{player_id}_timer'
    if timer_key in game_timers[game_id]:
        game_timers[game_id][timer_key].cancel()
        del game_timers[game_id][timer_key]

def cancel_game_timers(game_id):
    """Cancel all timers for a game"""
    if game_id in game_timers:
        for timer in game_timers[game_id].values():
            timer.cancel()
        del game_timers[game_id]

@socketio.on('join_game')
def handle_join_game(data):
    """Player joins a game room"""
    game_id = data['game_id']
    game = Game.query.get(game_id)

    if not game:
        return

    # Join the socket room
    room_name = f'game_{game_id}'
    join_room(room_name)

    # Track user's current room
    session_id = request.sid
    if session_id in active_users:
        active_users[session_id]['room'] = room_name

    # Check current game state and notify accordingly
    if game.status == 'active' and game.player2_id is not None:
        # Game is already active with both players
        # Determine opponent username
        if current_user.id == game.player1_id:
            opponent = User.query.get(game.player2_id)
        else:
            opponent = User.query.get(game.player1_id)

        # Start timers for both players if they haven't made choices
        if not game.player1_choice:
            start_turn_timer(game_id, game.player1_id)
        if not game.player2_choice:
            start_turn_timer(game_id, game.player2_id)

        # Notify all players in the room
        emit('player_joined', {
            'player_id': current_user.id,
            'username': current_user.username,
            'opponent_username': opponent.username if opponent else 'Unknown',
            'game_active': True,
            'timer_seconds': TURN_TIMER_SECONDS
        }, room=room_name)
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
        # Cancel timer for this player
        cancel_player_timer(game_id, game.player1_id)
    elif current_user.id == game.player2_id:
        game.player2_choice = choice
        # Cancel timer for this player
        cancel_player_timer(game_id, game.player2_id)

    # Check if both players have made choices
    if game.player1_choice and game.player2_choice:
        winner_id = determine_winner(game)
        game.winner_id = winner_id
        game.status = 'completed'
        game.completed_at = datetime.utcnow()

        # Update ELO ratings
        update_elo_ratings(game)

        db.session.commit()

        # Cancel all timers for this game
        cancel_game_timers(game_id)

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
    K = 10

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

@socketio.on('play_again')
def handle_play_again(data):
    """Handle play again request - creates new game with same players"""
    old_game_id = data['game_id']
    old_game = Game.query.get(old_game_id)

    if not old_game:
        return

    # Verify the requesting user was part of the previous game
    if current_user.id not in [old_game.player1_id, old_game.player2_id]:
        return

    # Leave the old game room
    leave_room(f'game_{old_game_id}')

    # Create a new game with the same players
    new_game = Game(
        player1_id=old_game.player1_id,
        player2_id=old_game.player2_id,
        status='active',
        is_quickplay=old_game.is_quickplay
    )
    db.session.add(new_game)
    db.session.commit()

    # Get player usernames
    player1 = User.query.get(old_game.player1_id)
    player2 = User.query.get(old_game.player2_id)

    # Notify both players to join the new game
    emit('new_game_created', {
        'game_id': new_game.id,
        'player1_username': player1.username,
        'player2_username': player2.username
    }, room=f'game_{old_game_id}')

@socketio.on('connect')
def handle_connect():
    """Handle user connection"""
    if current_user.is_authenticated:
        session_id = request.sid
        active_users[session_id] = {
            'user_id': current_user.id,
            'room': None
        }
        print(f"User {current_user.username} connected with session {session_id}")

@socketio.on('join_lobby')
def handle_join_lobby():
    """Handle user joining the lobby"""
    if current_user.is_authenticated:
        session_id = request.sid
        join_room('lobby')

        # Update user's current room
        if session_id in active_users:
            active_users[session_id]['room'] = 'lobby'

        # Broadcast updated online users list
        emit('user_joined_lobby', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room='lobby', include_self=False)

@socketio.on('leave_lobby')
def handle_leave_lobby():
    """Handle user leaving the lobby"""
    if current_user.is_authenticated:
        session_id = request.sid
        leave_room('lobby')

        # Update user's current room
        if session_id in active_users:
            active_users[session_id]['room'] = None

        # Broadcast user left
        emit('user_left_lobby', {
            'user_id': current_user.id,
            'username': current_user.username
        }, room='lobby')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    if not current_user.is_authenticated:
        return

    session_id = request.sid

    if session_id not in active_users:
        return

    user_info = active_users[session_id]
    user_id = user_info['user_id']
    current_room = user_info['room']

    print(f"User {current_user.username} disconnected from session {session_id}")

    # Handle disconnect based on current room
    if current_room and current_room.startswith('game_'):
        # User was in a game
        game_id = int(current_room.split('_')[1])
        game = Game.query.get(game_id)

        # Cancel all timers for this game
        cancel_game_timers(game_id)

        if game and game.status in ['waiting', 'active']:
            # End the game without score changes
            if game.status == 'active' and game.player1_choice and game.player2_choice:
                # Both players made choices but disconnected before seeing result
                # Game already completed, don't change anything
                pass
            else:
                # Game in progress or waiting, cancel it
                game.status = 'cancelled'
                game.completed_at = datetime.utcnow()
                db.session.commit()

                # Notify other player if present
                emit('opponent_disconnected', {
                    'message': 'Your opponent has left the game. Game cancelled.'
                }, room=current_room, include_self=False)

    elif current_room == 'lobby':
        # User was in lobby, notify others
        emit('user_left_lobby', {
            'user_id': user_id,
            'username': current_user.username
        }, room='lobby', include_self=False)

    # Remove from active users
    del active_users[session_id]