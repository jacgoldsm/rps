// Lobby-specific JavaScript
// Handles lobby presence and real-time online user updates

// Initialize Socket.IO connection (reuse if already exists from game.js)
const lobbySocket = typeof socket !== 'undefined' ? socket : io();

// Join lobby room when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/lobby' || window.location.pathname === '/') {
        lobbySocket.emit('join_lobby');
        console.log('Joined lobby');
    }
});

// Leave lobby when navigating away
window.addEventListener('beforeunload', () => {
    if (window.location.pathname === '/lobby' || window.location.pathname === '/') {
        lobbySocket.emit('leave_lobby');
    }
});

// Handle user joined lobby
lobbySocket.on('user_joined_lobby', (data) => {
    console.log('User joined lobby:', data.username);
    addPlayerToList(data.user_id, data.username);
    showNotification(`${data.username} joined the lobby`, 'info');
});

// Handle user left lobby
lobbySocket.on('user_left_lobby', (data) => {
    console.log('User left lobby:', data.username);
    removePlayerFromList(data.user_id);
    showNotification(`${data.username} left the lobby`, 'info');
});

// Add player to online players list
function addPlayerToList(userId, username) {
    const playersList = document.querySelector('.players-list');
    if (!playersList) return;

    // Check if player already exists
    if (document.querySelector(`[data-user-id="${userId}"]`)) {
        return;
    }

    // Remove empty state if present
    const emptyState = playersList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    // Create player item
    const playerItem = document.createElement('div');
    playerItem.className = 'player-item';
    playerItem.setAttribute('data-user-id', userId);
    playerItem.innerHTML = `
        <span class="player-avatar">👤</span>
        <span class="player-name">${username}</span>
        <span class="player-status">●</span>
    `;

    playersList.appendChild(playerItem);
}

// Remove player from online players list
function removePlayerFromList(userId) {
    const playersList = document.querySelector('.players-list');
    if (!playersList) return;

    const playerItem = playersList.querySelector(`[data-user-id="${userId}"]`);
    if (playerItem) {
        playerItem.remove();
    }

    // Show empty state if no players left
    const remainingPlayers = playersList.querySelectorAll('.player-item');
    if (remainingPlayers.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = '<p>No other players online</p>';
        playersList.appendChild(emptyState);
    }
}

// Notification function (shared with game.js)
function showNotification(message, type = 'info') {
    // Check if the global function from game.js exists and is different from this one
    if (typeof window.showNotification === 'function' && window.showNotification !== showNotification) {
        // Use the global notification function from game.js if available
        window.showNotification(message, type);
        return;
    }

    // Otherwise create our own
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
