/**
 * ProSpeak AI - Session Tracker
 * Handles session counting and dashboard updates across all practice modules
 */

// Track session completion
async function trackSessionCompletion() {
    try {
        console.log('Tracking session completion...');
        
        // Call API to increment session count
        const response = await api.request('/dashboard/increment-session', {
            method: 'POST'
        });
        
        if (response.success) {
            console.log('Session tracked successfully:', response.stats);
            
            // Update any visible counters on the current page
            updatePageCounters(response.stats, response.goals);
            
            // Show achievement notifications
            showSessionAchievements(response.stats);
            
            return response;
        }
    } catch (error) {
        console.error('Failed to track session:', error);
        return null;
    }
}

// Update counters on the current page
function updatePageCounters(stats, goals) {
    // Update header session count if present
    const headerSessions = document.getElementById('headerSessions');
    if (headerSessions) {
        headerSessions.textContent = stats.total_sessions;
    }
    
    // Update any other visible counters
    const totalSessionElements = document.querySelectorAll('[data-counter="total-sessions"]');
    totalSessionElements.forEach(el => {
        el.textContent = stats.total_sessions;
    });
    
    const todaySessionElements = document.querySelectorAll('[data-counter="today-sessions"]');
    todaySessionElements.forEach(el => {
        el.textContent = stats.today_sessions;
    });
    
    const streakElements = document.querySelectorAll('[data-counter="streak"]');
    streakElements.forEach(el => {
        el.textContent = `${stats.current_streak} Day${stats.current_streak !== 1 ? 's' : ''}`;
    });
}

// Show achievement notifications
function showSessionAchievements(stats) {
    const todayCount = stats.today_sessions;
    const totalCount = stats.total_sessions;
    
    // Daily achievements
    if (todayCount === 1) {
        showNotification('Great start! First session of the day completed! 🎉', 'success');
    } else if (todayCount === 3) {
        showNotification('Daily goal achieved! 3 sessions completed today! 🎯', 'success');
    } else if (todayCount === 5) {
        showNotification('Excellent! 5 sessions completed today! 🔥', 'success');
    }
    
    // Milestone achievements
    const milestones = [10, 25, 50, 100, 200, 500];
    if (milestones.includes(totalCount)) {
        setTimeout(() => {
            showMilestoneModal(totalCount);
        }, 1000);
    }
    
    // Streak achievements
    const streak = stats.current_streak;
    if (streak === 7) {
        showNotification('7-day streak! You\'re building a great habit! 🌟', 'success');
    } else if (streak === 14) {
        showNotification('2-week streak! Incredible consistency! 💪', 'success');
    } else if (streak === 30) {
        showNotification('30-day streak! You\'re a champion! 🏆', 'success');
    }
}

// Show milestone modal
function showMilestoneModal(sessions) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-8 max-w-md mx-4 text-center animate-bounce-in">
            <div class="text-6xl mb-4">🎉</div>
            <h3 class="text-2xl font-bold text-primary mb-2">Milestone Achieved!</h3>
            <p class="text-lg text-text-primary mb-4">${sessions} Sessions Completed!</p>
            <p class="text-text-secondary mb-6">You're making incredible progress on your English learning journey!</p>
            <button class="btn-primary" onclick="this.closest('.fixed').remove()">
                Continue Learning
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 10000);
}

// Show notification
function showNotification(message, type = 'info') {
    // Use existing notification system if available
    if (window.notifications) {
        if (type === 'success') {
            window.notifications.success(message);
        } else if (type === 'error') {
            window.notifications.error(message);
        } else {
            window.notifications.info(message);
        }
        return;
    }
    
    // Fallback notification
    const notification = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// Make function globally available
window.trackSessionCompletion = trackSessionCompletion;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { trackSessionCompletion };
}
