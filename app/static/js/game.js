// Rock-Paper-Scissors Game Frontend
// This file handles all client-side game interactions and WebSocket communication

// Initialize Socket.IO connection
const socket = io();

// Game state
let gameState = {
    gameId: null,
    currentUserId: null,
    currentUsername: null,
    opponentUsername: null,
    myChoice: null,
    opponentChoice: null,
    waitingForOpponent: false,
    gameActive: false,
    timerSeconds: 30,
    timerInterval: null,
    timeRemaining: 30
};

// DOM elements
const choiceButtons = document.querySelectorAll('.choice-btn');
const statusMessage = document.getElementById('status-message');
const myChoiceDisplay = document.getElementById('my-choice');
const opponentChoiceDisplay = document.getElementById('opponent-choice');
const resultDisplay = document.getElementById('result');
const playAgainBtn = document.getElementById('play-again-btn');
const playerInfo = document.getElementById('player-info');
const timerContainer = document.getElementById('timer-container');
const timerDisplay = document.getElementById('timer-display');
const timerBar = document.getElementById('timer-bar');

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Get game info from page data attributes or hidden inputs
    gameState.gameId = document.getElementById('game-id')?.value;
    gameState.currentUserId = parseInt(document.getElementById('current-user-id')?.value);
    gameState.currentUsername = document.getElementById('current-username')?.value;
    
    // Initialize player info
    initializePlayerInfo();
    
    if (gameState.gameId) {
        joinGame(gameState.gameId);
    }
    
    // Add click handlers to choice buttons
    choiceButtons.forEach(btn => {
        btn.addEventListener('click', handleChoiceClick);
    });
    
    // Play again button
    if (playAgainBtn) {
        playAgainBtn.addEventListener('click', handlePlayAgain);
    }
});

// Join a game room
function joinGame(gameId) {
    socket.emit('join_game', { game_id: gameId });
    updateStatus('Waiting for opponent to join...');
}

// Handle choice button clicks
function handleChoiceClick(e) {
    if (!gameState.gameActive) {
        showNotification('Waiting for another player to join!', 'warning');
        return;
    }
    
    if (gameState.myChoice) {
        showNotification('You already made your choice!', 'info');
        return;
    }
    
    const choice = e.currentTarget.dataset.choice;
    makeChoice(choice);
}

// Send choice to server
function makeChoice(choice) {
    gameState.myChoice = choice;

    socket.emit('make_choice', {
        game_id: gameState.gameId,
        choice: choice
    });

    // Update UI to show choice made
    displayMyChoice(choice);
    disableChoiceButtons();
    updateStatus('Waiting for opponent\'s choice...');
    gameState.waitingForOpponent = true;

    // Stop timer since choice was made
    stopTimer();
}

// Display player's choice
function displayMyChoice(choice) {
    const emoji = getChoiceEmoji(choice);
    myChoiceDisplay.innerHTML = `
        <div class="choice-display animate-choice">
            <div class="choice-emoji">${emoji}</div>
            <div class="choice-label">${capitalizeFirst(choice)}</div>
        </div>
    `;
}

// Display opponent's choice
function displayOpponentChoice(choice) {
    const emoji = getChoiceEmoji(choice);
    opponentChoiceDisplay.innerHTML = `
        <div class="choice-display animate-choice">
            <div class="choice-emoji">${emoji}</div>
            <div class="choice-label">${capitalizeFirst(choice)}</div>
        </div>
    `;
}

// Get emoji for choice
function getChoiceEmoji(choice) {
    const emojis = {
        'rock': '✊',
        'paper': '✋',
        'scissors': '✌️'
    };
    return emojis[choice] || '❓';
}

// Disable choice buttons
function disableChoiceButtons() {
    choiceButtons.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('disabled');
    });
}

// Enable choice buttons
function enableChoiceButtons() {
    choiceButtons.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('disabled');
    });
}

// Update status message
function updateStatus(message) {
    if (statusMessage) {
        statusMessage.textContent = message;
    }
}

// Timer functions
function startTimer(seconds) {
    // Stop any existing timer
    stopTimer();

    gameState.timerSeconds = seconds;
    gameState.timeRemaining = seconds;

    // Show timer
    if (timerContainer) {
        timerContainer.style.display = 'block';
    }

    // Update display immediately
    updateTimerDisplay();

    // Start countdown
    gameState.timerInterval = setInterval(() => {
        gameState.timeRemaining--;

        updateTimerDisplay();

        if (gameState.timeRemaining <= 0) {
            stopTimer();
            // Timer expired - server will handle the loss
        }
    }, 1000);
}

function stopTimer() {
    if (gameState.timerInterval) {
        clearInterval(gameState.timerInterval);
        gameState.timerInterval = null;
    }

    // Hide timer
    if (timerContainer) {
        timerContainer.style.display = 'none';
    }
}

function updateTimerDisplay() {
    if (timerDisplay) {
        timerDisplay.textContent = gameState.timeRemaining;

        // Add warning class when time is low
        if (gameState.timeRemaining <= 10) {
            timerDisplay.classList.add('timer-warning');
        } else {
            timerDisplay.classList.remove('timer-warning');
        }

        // Add critical class when time is very low
        if (gameState.timeRemaining <= 5) {
            timerDisplay.classList.add('timer-critical');
        } else {
            timerDisplay.classList.remove('timer-critical');
        }
    }

    // Update progress bar
    if (timerBar) {
        const percentage = (gameState.timeRemaining / gameState.timerSeconds) * 100;
        timerBar.style.width = percentage + '%';

        // Change color based on time remaining
        if (gameState.timeRemaining <= 5) {
            timerBar.style.backgroundColor = '#dc3545'; // Red
        } else if (gameState.timeRemaining <= 10) {
            timerBar.style.backgroundColor = '#ffc107'; // Yellow
        } else {
            timerBar.style.backgroundColor = '#28a745'; // Green
        }
    }
}

// Socket event handlers

// When a player joins the game
socket.on('player_joined', (data) => {
    console.log('Player joined:', data);
    
    // Update opponent username
    if (data.player_id !== gameState.currentUserId && data.username) {
        gameState.opponentUsername = data.username;
    }
    
    // If opponent_username is provided (for the joining player)
    if (data.opponent_username && !gameState.opponentUsername) {
        gameState.opponentUsername = data.opponent_username;
    }
    
    // Always update the display
    updatePlayerInfo();
    
    // Show notification only if it's the opponent joining
    if (data.player_id !== gameState.currentUserId && data.username) {
        showNotification(`${data.username} joined the game!`, 'success');
    }
    
    // Activate the game if both players are present
    if (data.game_active) {
        gameState.gameActive = true;
        updateStatus('Game started! Make your choice!');
        enableChoiceButtons();

        // Start timer if provided
        if (data.timer_seconds && !gameState.myChoice) {
            startTimer(data.timer_seconds);
        }
    }
});

// When waiting for opponent (player1 only)
socket.on('waiting_for_opponent', (data) => {
    console.log('Waiting for opponent:', data);
    updateStatus(data.message || 'Waiting for opponent to join...');
    gameState.gameActive = false;
});

// When opponent makes a choice
socket.on('choice_made', (data) => {
    if (data.player_id !== gameState.currentUserId) {
        updateStatus('Opponent made their choice! Waiting for result...');
        opponentChoiceDisplay.innerHTML = `
            <div class="choice-display">
                <div class="choice-emoji thinking">🤔</div>
                <div class="choice-label">Thinking...</div>
            </div>
        `;
    }
});

// When game result is determined
socket.on('game_result', (data) => {
    // Stop timer
    stopTimer();

    // Display both choices
    if (data.player1_choice && data.player2_choice) {
        const myActualChoice = gameState.myChoice;
        const opponentActualChoice = data.player1_choice === myActualChoice
            ? data.player2_choice
            : data.player1_choice;

        gameState.opponentChoice = opponentActualChoice;
        displayOpponentChoice(opponentActualChoice);
    }

    // Determine result message and ELO change
    let resultMessage = '';
    let resultClass = '';
    let eloChange = 0;

    // Determine which player's ELO change to show
    if (data.player1_choice === gameState.myChoice) {
        eloChange = data.player1_elo_change;
    } else {
        eloChange = data.player2_elo_change;
    }

    if (data.winner_id === null) {
        resultMessage = "It's a tie! 🤝";
        resultClass = 'tie';
    } else if (data.winner_id === gameState.currentUserId) {
        resultMessage = "You win! 🎉";
        resultClass = 'win';
        playSound('win');
    } else {
        resultMessage = "You lose! 😢";
        resultClass = 'lose';
        playSound('lose');
    }

    // Add ELO change to result message
    const eloChangeText = eloChange >= 0
        ? `<span class="elo-gain">+${eloChange} ELO</span>`
        : `<span class="elo-loss">${eloChange} ELO</span>`;

    // Display result
    if (resultDisplay) {
        resultDisplay.innerHTML = `
            <div class="result-message ${resultClass}">
                ${resultMessage}
                <div class="elo-change">${eloChangeText}</div>
            </div>
        `;
        resultDisplay.classList.add('show');
    }

    updateStatus('Game finished!');

    // Show play again button
    if (playAgainBtn) {
        playAgainBtn.style.display = 'block';
    }

    gameState.gameActive = false;
});

// When game ends due to timeout
socket.on('game_timeout', (data) => {
    // Stop timer
    stopTimer();

    console.log('Game timeout:', data);

    // Determine result message and ELO change
    let resultMessage = '';
    let resultClass = '';
    let eloChange = 0;

    // Determine which player's ELO change to show
    if (gameState.currentUserId === data.winner_id) {
        eloChange = data.player1_elo_change;
    } else {
        eloChange = data.player2_elo_change;
    }

    if (data.winner_id === gameState.currentUserId) {
        resultMessage = `You win! 🎉<br><small>${data.loser_username} ran out of time!</small>`;
        resultClass = 'win';
        playSound('win');
    } else {
        resultMessage = `Time's up! You lose! ⏰<br><small>You didn't make a choice in time.</small>`;
        resultClass = 'lose timeout';
        playSound('lose');
    }

    // Add ELO change to result message
    const eloChangeText = eloChange >= 0
        ? `<span class="elo-gain">+${eloChange} ELO</span>`
        : `<span class="elo-loss">${eloChange} ELO</span>`;

    // Display result
    if (resultDisplay) {
        resultDisplay.innerHTML = `
            <div class="result-message ${resultClass}">
                ${resultMessage}
                <div class="elo-change">${eloChangeText}</div>
            </div>
        `;
        resultDisplay.classList.add('show');
    }

    updateStatus('Game finished!');

    // Disable choice buttons
    disableChoiceButtons();

    // Show play again button
    if (playAgainBtn) {
        playAgainBtn.style.display = 'block';
    }

    gameState.gameActive = false;
});

// Handle connection errors
socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    showNotification('Connection error. Please refresh the page.', 'error');
});

// Handle disconnections
socket.on('disconnect', () => {
    console.log('Disconnected from server');
    gameState.gameActive = false;
    updateStatus('Disconnected from server. Please refresh the page.');
});

// Handle new game created (play again)
socket.on('new_game_created', (data) => {
    console.log('New game created:', data);
    // Redirect to the new game
    window.location.href = `/game/${data.game_id}`;
});

// Handle opponent disconnected
socket.on('opponent_disconnected', (data) => {
    console.log('Opponent disconnected:', data.message);

    // Update UI to show opponent left
    updateStatus('Opponent left the game');
    showNotification(data.message, 'warning');

    // Disable game controls
    disableChoiceButtons();
    gameState.gameActive = false;

    // Show result display
    if (resultDisplay) {
        resultDisplay.innerHTML = `
            <div class="result-message disconnected">
                <div class="disconnect-icon">🚪</div>
                <div class="disconnect-text">
                    <h3>Game Cancelled</h3>
                    <p>Your opponent has left the game.</p>
                    <p class="no-score-change">No rating changes applied.</p>
                </div>
            </div>
        `;
        resultDisplay.classList.add('show');
    }

    // Hide play again button (can't rematch with disconnected player)
    if (playAgainBtn) {
        playAgainBtn.style.display = 'none';
    }
});

// Update player info display
function updatePlayerInfo() {
    if (playerInfo) {
        playerInfo.innerHTML = `
            <div class="player-card">
                <div class="player-name">You: ${gameState.currentUsername}</div>
            </div>
            <div class="vs-divider">VS</div>
            <div class="player-card">
                <div class="player-name">Opponent: ${gameState.opponentUsername || 'Waiting...'}</div>
            </div>
        `;
    }
}

// Initialize player info on page load
function initializePlayerInfo() {
    // Get opponent info from the page if already set
    const opponentNameElement = document.querySelector('.player-card:last-child .player-name');
    if (opponentNameElement) {
        const text = opponentNameElement.textContent;
        const match = text.match(/Opponent:\s*(.+)/);
        if (match && match[1] && match[1] !== 'Waiting...') {
            gameState.opponentUsername = match[1].trim();
            gameState.gameActive = true;
        }
    }
}

// Handle play again button
function handlePlayAgain() {
    // Emit play again event to server
    socket.emit('play_again', {
        game_id: gameState.gameId
    });

    // Show loading message
    updateStatus('Starting new game with same players...');
    showNotification('Creating rematch...', 'info');

    // Disable play again button while waiting
    if (playAgainBtn) {
        playAgainBtn.disabled = true;
        playAgainBtn.textContent = 'Creating rematch...';
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Add to page
    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Make showNotification globally available
window.showNotification = showNotification;

// Play sound effects (optional)
function playSound(type) {
    // You can add actual audio files later
    // For now, this is a placeholder
    console.log(`Playing ${type} sound`);
    
    // Example implementation if you have audio files:
    /*
    const sounds = {
        'win': new Audio('/static/sounds/win.mp3'),
        'lose': new Audio('/static/sounds/lose.mp3'),
        'click': new Audio('/static/sounds/click.mp3')
    };
    
    if (sounds[type]) {
        sounds[type].play();
    }
    */
}

// Utility function to capitalize first letter
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Lobby functions (if on lobby page)
if (window.location.pathname === '/lobby' || window.location.pathname === '/') {
    const joinRandomGameBtn = document.getElementById('join-random-game-btn');

    if (joinRandomGameBtn) {
        joinRandomGameBtn.addEventListener('click', joinRandomGame);
    }
}

// Join random game (matchmaking)
async function joinRandomGame() {
    try {
        // Show loading notification
        showNotification('Finding a match...', 'info');

        const response = await fetch('/join-random-game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.game_id) {
            if (data.status === 'matched') {
                showNotification(data.message, 'success');
            }
            // Redirect to the game room
            window.location.href = `/game/${data.game_id}`;
        } else {
            showNotification('Failed to join game', 'error');
        }
    } catch (error) {
        console.error('Error joining random game:', error);
        showNotification('Error joining game', 'error');
    }
}

// Export for use in other files if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        socket,
        gameState,
        makeChoice,
        joinRandomGame
    };
}