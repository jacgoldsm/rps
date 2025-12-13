# Rock Paper Scissors - Architecture & Repository Structure

This document provides a comprehensive overview of the Rock Paper Scissors web application architecture, codebase structure, and key implementation details.

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Core Features](#core-features)
- [Database Schema](#database-schema)
- [Socket Events](#socket-events)
- [Game Flow](#game-flow)
- [Key Implementation Details](#key-implementation-details)

---

## Overview

This is a real-time multiplayer Rock Paper Scissors game built with Flask and Socket.IO. Players can compete against each other with an ELO rating system, live matchmaking, and a 30-second turn timer.

## Tech Stack

**Backend:**
- Flask (Python web framework)
- Flask-SocketIO (WebSocket support for real-time communication)
- Flask-Login (User authentication and session management)
- SQLAlchemy (ORM for database)
- SQLite (Database)

**Frontend:**
- HTML5/Jinja2 templates
- CSS3 with custom animations
- Vanilla JavaScript (ES6+)
- Socket.IO client

---

## Repository Structure

```
rps/
├── app/                          # Main application package
│   ├── __init__.py              # App factory and initialization
│   ├── auth.py                  # Authentication routes and logic
│   ├── game.py                  # Game routes (lobby, play, leaderboard)
│   ├── models.py                # Database models (User, Game)
│   ├── socket_handlers.py       # Socket.IO event handlers
│   ├── static/                  # Static assets
│   │   ├── css/
│   │   │   └── style.css       # All application styles
│   │   └── js/
│   │       ├── game.js         # Game logic and Socket.IO client
│   │       └── lobby.js        # Lobby presence management
│   └── templates/               # Jinja2 HTML templates
│       ├── base.html           # Base template with navigation
│       ├── login.html          # Login page
│       ├── register.html       # Registration page
│       ├── lobby.html          # Game lobby
│       ├── game.html           # Game room
│       └── leaderboard.html    # ELO rankings
├── config.py                    # Application configuration
├── run.py                       # Application entry point
├── init_db.py                   # Database initialization script
├── migrate_db.py                # Database migration script
├── add_elo_fields.py            # Migration for ELO fields
└── CLAUDE.md                    # This file
```

---

## Architecture

### Application Pattern
The application follows a **modular Flask architecture** with blueprints:

1. **Auth Blueprint** (`auth.py`) - Handles user authentication
2. **Game Blueprint** (`game.py`) - Handles game-related routes
3. **Socket Handlers** (`socket_handlers.py`) - Real-time game communication

### Communication Architecture

```
┌─────────────┐         WebSocket          ┌─────────────┐
│   Client    │◄──────────────────────────►│   Server    │
│  (Browser)  │         Socket.IO          │   (Flask)   │
└─────────────┘                            └─────────────┘
      │                                            │
      │                                            │
      ├─ game.js (game logic)                     ├─ socket_handlers.py
      ├─ lobby.js (presence)                      ├─ models.py (ORM)
      └─ Socket.IO client                         └─ SQLite database
```

### Real-Time Communication Flow

1. **Client connects** → Server tracks session in `active_users` dict
2. **Client joins lobby** → Server broadcasts to other lobby users
3. **Client requests game** → Server creates/joins game, starts timers
4. **Player makes choice** → Server receives, validates, determines winner
5. **Game ends** → Server updates ELO, broadcasts results to both players

---

## Core Features

### 1. Authentication System
- **Registration**: Username, email, password with hashing (Werkzeug)
- **Login**: Session-based authentication with Flask-Login
- **Sessions**: Persistent login with `remember_me` functionality

### 2. Matchmaking System
- **Quick Play**: Random matchmaking with waiting games
- **Game States**: `waiting` → `active` → `completed` or `cancelled`
- **Lobby Presence**: Real-time online user list with Socket.IO

### 3. ELO Rating System
- **Starting Rating**: 1200 ELO
- **K-Factor**: 10 (rating volatility)
- **Formula**: Standard ELO calculation
  ```python
  expected_score = 1 / (1 + 10^((opponent_rating - player_rating) / 400))
  new_rating = old_rating + K * (actual_score - expected_score)
  ```
- **Win Rate**: Calculated as `wins / (wins + losses)` (excludes ties)

### 4. Turn Timer System
- **Duration**: 30 seconds per turn
- **Server-side**: Threading.Timer enforces timeout
- **Client-side**: Visual countdown with progress bar
- **Automatic Loss**: Player who times out loses with full ELO penalty
- **Visual Feedback**:
  - Green (30-11s)
  - Yellow + pulse animation (10-6s)
  - Red + shake animation (5-0s)

### 5. Disconnect Handling
- **In Lobby**: Auto-removes from online list
- **In Game**: Cancels game without ELO changes
- **Timer Cleanup**: All timers cancelled on disconnect
- **Opponent Notification**: Real-time alert when opponent leaves

### 6. Play Again Feature
- **Instant Rematch**: Creates new game with same players
- **Seamless**: Both players auto-redirect to new game
- **Timer Reset**: Fresh 30-second timer for new round

---

## Database Schema

### User Model
```python
User:
  - id: Integer (Primary Key)
  - username: String(80) (Unique)
  - email: String(120) (Unique)
  - password_hash: String(200)
  - elo_rating: Integer (Default: 1200)
  - games_played: Integer (Default: 0)
  - games_won: Integer (Default: 0)
  - games_lost: Integer (Default: 0)
  - games_tied: Integer (Default: 0)
  - created_at: DateTime

  Properties:
  - win_rate: Computed as (wins / (wins + losses)) * 100
```

### Game Model
```python
Game:
  - id: Integer (Primary Key)
  - player1_id: Integer (Foreign Key → User)
  - player2_id: Integer (Foreign Key → User, Nullable)
  - player1_choice: String(10) ['rock'|'paper'|'scissors'|'timeout']
  - player2_choice: String(10) ['rock'|'paper'|'scissors'|'timeout']
  - winner_id: Integer (Foreign Key → User, Nullable)
  - status: String(20) ['waiting'|'active'|'completed'|'cancelled']
  - is_quickplay: Boolean (Default: False)
  - player1_elo_change: Integer (Default: 0)
  - player2_elo_change: Integer (Default: 0)
  - created_at: DateTime
  - completed_at: DateTime (Nullable)
```

---

## Socket Events

### Client → Server

| Event | Data | Description |
|-------|------|-------------|
| `connect` | - | Client connects, server tracks session |
| `join_lobby` | - | Join lobby room for presence |
| `leave_lobby` | - | Leave lobby room |
| `join_game` | `{game_id}` | Join specific game room |
| `make_choice` | `{game_id, choice}` | Submit rock/paper/scissors |
| `play_again` | `{game_id}` | Request rematch with same opponent |
| `disconnect` | - | Client disconnects, cleanup timers |

### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `user_joined_lobby` | `{user_id, username}` | User joined lobby |
| `user_left_lobby` | `{user_id, username}` | User left lobby |
| `player_joined` | `{player_id, username, opponent_username, game_active, timer_seconds}` | Player joined game |
| `waiting_for_opponent` | `{message}` | Waiting for player 2 |
| `choice_made` | `{player_id}` | Opponent made choice (hidden) |
| `game_result` | `{player1_choice, player2_choice, winner_id, player1_elo_change, player2_elo_change}` | Game completed normally |
| `game_timeout` | `{winner_id, loser_id, winner_username, loser_username, player1_elo_change, player2_elo_change}` | Game ended by timeout |
| `opponent_disconnected` | `{message}` | Opponent left, game cancelled |
| `new_game_created` | `{game_id, player1_username, player2_username}` | Rematch ready |

---

## Game Flow

### 1. Matchmaking Flow
```
User clicks "Play Game"
    ↓
Server searches for waiting game
    ↓
Found? → Join as player2 → Start game with timers
    ↓
Not found? → Create new game as player1 → Wait
```

### 2. Game Play Flow
```
Both players join
    ↓
Server starts 30s timers for both
    ↓
Client displays timer countdown
    ↓
Player clicks choice (rock/paper/scissors)
    ↓
Server cancels that player's timer
    ↓
Both made choice? → Determine winner → Update ELO → Broadcast result
    ↓
One times out? → Other player wins → Update ELO → Broadcast timeout result
```

### 3. Game Result Determination
```python
def determine_winner(game):
    if p1_choice == p2_choice:
        return None  # Tie

    winning_combinations = {
        ('rock', 'scissors'): player1,
        ('paper', 'rock'): player1,
        ('scissors', 'paper'): player1,
        # ... reverse for player2
    }

    return winning_combinations.get((p1_choice, p2_choice))
```

---

## Key Implementation Details

### 1. Session Management
- **Server-side dict**: `active_users = {session_id: {user_id, room}}`
- **Purpose**: Track which room each user is in (lobby or game)
- **Cleanup**: Removed on disconnect

### 2. Timer Management
- **Server-side dict**: `game_timers = {game_id: {player1_timer, player2_timer}}`
- **Implementation**: Python `threading.Timer`
- **Lifecycle**:
  - Start when both players join
  - Cancel when player makes choice
  - Cancel all on disconnect or game end
  - Auto-expire executes `handle_timer_expire()`

### 3. Room Management
- **Lobby Room**: `'lobby'` - All players in lobby
- **Game Rooms**: `f'game_{game_id}'` - Two players per game
- **Socket.IO**: Automatic room broadcasting

### 4. State Synchronization
- **Server is source of truth**: All game logic on server
- **Client displays state**: Updates from socket events
- **No client-side validation**: Choices sent directly to server
- **Timer sync**: Client timer is visual only, server enforces

### 5. Disconnect Scenarios

| Scenario | Action | ELO Change? |
|----------|--------|-------------|
| Player disconnects in lobby | Remove from online list | No |
| Player disconnects during game (no choices) | Cancel game | No |
| Player disconnects during game (after choice) | Cancel game | No |
| Player disconnects after both chose | Game completes normally | Yes |
| Player times out | Opponent wins | Yes |

### 6. Security Considerations
- **Password hashing**: Werkzeug with salt
- **Session protection**: Flask-Login with secret key
- **CSRF protection**: Built into Flask forms
- **SQL Injection**: Protected by SQLAlchemy ORM
- **Choice validation**: Server-side only
- **Timer enforcement**: Server-side, client display only

### 7. Scalability Limitations
- **In-memory state**: `active_users` and `game_timers` in process memory
- **Not horizontally scalable**: Can't run multiple Flask instances
- **Database**: SQLite (single file, not concurrent-write optimized)
- **For production**: Need Redis for session/timer state, PostgreSQL for DB

---

## Development Setup

### Prerequisites
```bash
python 3.8+
pip install flask flask-socketio flask-login flask-sqlalchemy
```

### Initialize Database
```bash
python init_db.py
```

### Run Application
```bash
python run.py
```

Access at: `http://localhost:5000`

### Migrate ELO Fields (if needed)
```bash
python add_elo_fields.py
```

---

## Future Enhancements

**Suggested improvements:**
1. **Redis integration**: Store `active_users` and `game_timers` in Redis for horizontal scaling
2. **Game history**: Add view to see past games and choices
3. **Best of N**: Support best-of-3 or best-of-5 series
4. **Private matches**: Allow challenging specific users
5. **Spectator mode**: Watch live games
6. **Chat system**: In-game messaging
7. **Achievements**: Badges for win streaks, ELO milestones, etc.
8. **Mobile responsive**: Enhanced mobile UI
9. **Sound effects**: Add audio feedback
10. **Reconnection logic**: Resume game if player temporarily disconnects

---

## Troubleshooting

### Common Issues

**Timer not showing:**
- Check browser console for JavaScript errors
- Verify `timer_seconds` is included in `player_joined` event
- Ensure `timer-container` div exists in template

**Disconnect not working:**
- Verify Socket.IO client is connected
- Check server logs for disconnect events
- Ensure `active_users` dict is populated on connect

**ELO not updating:**
- Confirm `update_elo_ratings()` is called after winner determined
- Check `db.session.commit()` is executed
- Verify `player1_elo_change` and `player2_elo_change` columns exist

**Play Again not working:**
- Ensure both players are still connected
- Check `new_game_created` event is emitted to old game room
- Verify client redirects to new game URL

---

## Contact & Contributions

This is a learning project demonstrating real-time web game development with Flask and Socket.IO. Feel free to extend and modify for your own use.

**Key learning concepts demonstrated:**
- WebSocket communication with Socket.IO
- Real-time multiplayer game state management
- ELO rating system implementation
- Timer-based game mechanics
- User authentication and sessions
- ORM with SQLAlchemy
- Modern CSS with animations

---

*Last updated: December 2024*
