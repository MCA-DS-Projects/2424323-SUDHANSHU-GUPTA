/* User Dashboard client logic (extracted from inline template)
   - Uses global `api` client (app/static/js/api.js)
   - Safe DOM operations, avoids innerHTML with user data
   - Implements retry/backoff for loadDashboardData
   - Exposes cleanupDashboard and initializeDashboard
*/
(function(window, document){
    'use strict';

    // Configuration: injected by template when included
    const ROUTES = window.__DASHBOARD_ROUTES || {};

    // State
    let retryCount = 0;
    let retryTimer = null;
    const maxRetries = 4;

    // Helpers
    function safeSetText(el, text) {
        if (!el) return;
        el.textContent = text;
    }

    function replaceClassColor(el, newClass) {
        if (!el) return;
        // Remove known color classes (tailwind-ish)
        el.classList.remove('text-green-600','text-yellow-600','text-text-primary','text-orange-600','text-yellow-500','text-green-500','text-red-500');
        el.classList.add(...newClass.split(' '));
    }

    function animateProgressFill(fillEl, percentage) {
        if (!fillEl) return;
        const last = parseFloat(fillEl.dataset.lastWidth || '0');
        const target = Math.max(0, Math.min(100, Number(percentage || 0)));
        if (last === target) return; // no-op
        fillEl.dataset.lastWidth = String(target);

        // Use requestAnimationFrame to avoid layout thrash
        requestAnimationFrame(() => {
            fillEl.style.width = target + '%';
        });
    }

    // Toast/banner utilities
    function showToast(message, opts = {}) {
        const container = document.createElement('div');
        container.className = 'fixed top-4 right-4 z-50';

        const card = document.createElement('div');
        card.className = 'bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-sm';
        card.setAttribute('role', 'status');
        card.textContent = message;

        if (opts.retry) {
            const retryBtn = document.createElement('button');
            retryBtn.className = 'ml-3 text-sm text-primary';
            retryBtn.textContent = 'Retry now';
            retryBtn.addEventListener('click', () => {
                loadDashboardData(true);
                container.remove();
            });
            card.appendChild(retryBtn);
        }

        container.appendChild(card);
        document.body.appendChild(container);

        setTimeout(() => {
            container.remove();
        }, opts.duration || 5000);
    }

    // Loaders
    async function loadDashboardData(force=false) {
        if (!window.api) {
            console.warn('API client not available');
            return;
        }

        try {
            // Reset any retry state when forced
            if (force) retryCount = 0;

            const overview = await window.api.getDashboardOverview();
            updateDashboardStats(overview);

            const stats = await window.api.getDashboardStats();
            updateDetailedStats(stats);

            retryCount = 0; // success
        } catch (err) {
            console.error('Failed to load dashboard data', err);
            showDefaultStats();
            // show toast with retry affordance
            showToast('Could not refresh dashboard data. Will retry automatically.', { retry: true, duration: 8000 });

            // Exponential backoff
            if (retryCount < maxRetries) {
                retryCount += 1;
                const backoff = Math.min(30000, Math.pow(2, retryCount) * 1000);
                clearTimeout(retryTimer);
                retryTimer = setTimeout(() => loadDashboardData(), backoff);
            }
        }
    }

    function showDefaultStats() {
        safeSetText(document.getElementById('overallScoreText'), '--');
        safeSetText(document.getElementById('streakCount'), '-- Days');
        safeSetText(document.getElementById('dailyProgress'), '-/-');
        safeSetText(document.getElementById('totalSessions'), '--');
    }

    function updateDetailedStats(statsData) {
        if (!statsData) return;
        const totalTime = Math.round((statsData.total_practice_time || 0) / 3600);
        document.querySelectorAll('.practice-time').forEach(el => safeSetText(el, totalTime + 'h'));
    }

    function updateCircularProgress(circleId, textId, percentage) {
        const circle = document.getElementById(circleId);
        const text = document.getElementById(textId);
        if (!circle || !text) return;

        const circumference = 2 * Math.PI * 15.9155;
        const offset = circumference - (percentage / 100) * circumference;
        circle.style.strokeDasharray = `${circumference}, ${circumference}`;
        circle.style.strokeDashoffset = circumference;

        requestAnimationFrame(() => {
            circle.style.transition = 'stroke-dashoffset 1.2s ease-in-out';
            circle.style.strokeDashoffset = offset;
        });

        // animate text
        safeSetText(document.getElementById(textId), Math.round(percentage) + '%');

        // color classes
        circle.classList.remove('text-green-500','text-yellow-500','text-red-500');
        if (percentage >= 85) circle.classList.add('text-green-500');
        else if (percentage >= 70) circle.classList.add('text-yellow-500');
        else circle.classList.add('text-red-500');
    }

    function updateDashboardStats(data) {
        if (!data) return;
        const stats = data.stats || {};
        const goals = data.goals || {};
        const performance = data.performance || {};
        const user = data.user || {};

        updateCircularProgress('overallScoreCircle','overallScoreText', stats.recent_average || stats.average_score || 0);

        // improvement
        const improvementEl = document.getElementById('scoreImprovement');
        if (improvementEl) {
            const improvement = performance.improvement_rate || 0;
            if (improvement > 0) { improvementEl.textContent = `+${improvement.toFixed(1)}% this week`; improvementEl.classList.add('text-green-600'); }
            else if (improvement < 0) { improvementEl.textContent = `${improvement.toFixed(1)}% this week`; improvementEl.classList.add('text-red-600'); }
            else { improvementEl.textContent = 'Stable performance'; }
        }

        // streak
        const streakEl = document.getElementById('streakCount');
        if (streakEl) {
            const streak = stats.current_streak || 0;
            safeSetText(streakEl, `${streak} Day${streak !== 1 ? 's' : ''}`);
            if (streak >= 30) replaceClassColor(streakEl, 'text-orange-600');
            else if (streak >= 14) replaceClassColor(streakEl, 'text-yellow-600');
            else if (streak >= 7) replaceClassColor(streakEl, 'text-green-600');
        }

        // daily progress: use goals.daily_progress and goals.daily_goal consistently
        const dailyEl = document.getElementById('dailyProgress');
        if (dailyEl) {
            const today = goals.daily_progress || stats.today_sessions || 0;
            const goal = goals.daily_goal || 3;
            safeSetText(dailyEl, `${today}/${goal}`);
            if (today >= goal) replaceClassColor(dailyEl,'text-green-600');
            else if (today >= goal * 0.7) replaceClassColor(dailyEl,'text-yellow-600');
            else replaceClassColor(dailyEl,'text-text-primary');
        }

        // total sessions
        const totalEl = document.getElementById('totalSessions');
        if (totalEl) { animateNumber(totalEl, stats.total_sessions || 0); updateSessionMilestones(stats.total_sessions || 0); }

        // weekly progress bar
        const fillEl = document.getElementById('weeklyProgressFill');
        if (fillEl) {
            const perc = goals.weekly_percentage || 0;
            animateProgressFill(fillEl, perc);
            safeSetText(document.getElementById('weeklyPercentage'), Math.round(perc) + '%');
            safeSetText(document.getElementById('weeklyProgressText'), `${goals.weekly_progress || 0} of ${goals.weekly_goal || '--'} sessions`);
        }

        updateWelcomeMessage(user, stats);
    }

    function animateNumber(element, targetNumber, suffix = '') {
        const startNumber = parseInt(element.textContent) || 0;
        const duration = 800;
        const startTime = Date.now();

        function updateNumber() {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentNumber = Math.round(startNumber + (targetNumber - startNumber) * easeOut);
            element.textContent = currentNumber + suffix;
            if (progress < 1) requestAnimationFrame(updateNumber);
        }
        updateNumber();
    }

    function updateSessionMilestones(totalSessions) {
        const totalSessionsEl = document.getElementById('totalSessions');
        if (!totalSessionsEl) return;
        const container = totalSessionsEl.parentElement;
        if (!container) return;
        const existing = container.querySelector('.milestone-badge');
        if (existing) existing.remove();
        let badgeText = '';
        let badgeClass = '';
        if (totalSessions >= 100) { badgeText = '🏆 Century!'; badgeClass='bg-yellow-100 text-yellow-800'; }
        else if (totalSessions >= 50) { badgeText = '🎯 Half Century!'; badgeClass='bg-blue-100 text-blue-800'; }
        else if (totalSessions >= 25) { badgeText = '⭐ Quarter Century!'; badgeClass='bg-green-100 text-green-800'; }
        else if (totalSessions >= 10) { badgeText = '🚀 Getting Started!'; badgeClass='bg-purple-100 text-purple-800'; }
        if (badgeText) {
            const badge = document.createElement('div');
            badge.className = `milestone-badge text-xs px-2 py-1 rounded-full ${badgeClass} mt-1`;
            badge.textContent = badgeText;
            container.appendChild(badge);
        }
    }

    function updateWelcomeMessage(user, stats) {
        const welcomeElement = document.getElementById('welcomeMessage');
        if (!welcomeElement || !user) return;
        const firstName = user.name ? user.name.split(' ')[0] : 'there';
        const timeOfDay = getTimeOfDay();
        const streak = stats.current_streak || 0;
        let message = `Good ${timeOfDay}, ${firstName}!`;
        if (streak >= 7) message += ` 🔥 Amazing ${streak}-day streak!`;
        else if (streak >= 3) message += ` 💪 Keep up the momentum!`;
        else message += ` Ready to practice today?`;
        welcomeElement.textContent = message;
    }

    function getTimeOfDay() {
        const hour = new Date().getHours();
        if (hour < 12) return 'morning';
        if (hour < 17) return 'afternoon';
        return 'evening';
    }

    // Session summary: safe DOM creation and removal only if recent
    function showLastSessionSummary() {
        try {
            const summaryData = localStorage.getItem('lastSessionSummary');
            if (!summaryData) return;
            const summary = JSON.parse(summaryData);
            const timeSince = Date.now() - summary.timestamp;
            if (timeSince < 5 * 60 * 1000) {
                // Build banner with safe textContent
                const banner = document.createElement('div');
                banner.className = 'fixed top-20 left-1/2 transform -translate-x-1/2 z-50 animate-fade-in';
                const inner = document.createElement('div');
                inner.className = 'bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-4 rounded-lg shadow-xl max-w-md';
                const title = document.createElement('h3');
                title.className = 'font-bold text-lg mb-1';
                title.textContent = 'Session Completed! 🎉';
                inner.appendChild(title);

                const list = document.createElement('div');
                list.className = 'text-sm space-y-1 opacity-90';
                const ex = document.createElement('div'); ex.textContent = `✅ ${summary.exercises} exercises completed`;
                const tm = document.createElement('div'); tm.textContent = `⏱️ ${formatDuration(summary.duration)}`;
                const ac = document.createElement('div'); ac.textContent = `🏅 ${summary.accuracy}% average accuracy`;
                list.appendChild(ex); list.appendChild(tm); list.appendChild(ac);
                inner.appendChild(list);

                const closeBtn = document.createElement('button');
                closeBtn.className = 'ml-3 text-white hover:text-gray-200 absolute top-2 right-3';
                closeBtn.setAttribute('aria-label','Close session summary');
                closeBtn.textContent = '✕';
                closeBtn.addEventListener('click', () => {
                    banner.remove();
                });
                inner.appendChild(closeBtn);

                banner.appendChild(inner);
                document.body.appendChild(banner);

                setTimeout(() => {
                    banner.remove();
                }, 8000);

                // Only remove storage after showing
                localStorage.removeItem('lastSessionSummary');
            }
        } catch (e) { console.error('Error showing session summary', e); }
    }

    function formatDuration(ms) {
        if (!ms) return '0s';
        const minutes = Math.floor(ms / 60000);
        const seconds = Math.floor((ms % 60000) / 1000);
        return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
    }

    // Celebration overlay with accessibility
    function celebrateStreak(streak) {
        const overlay = document.createElement('div');
        overlay.className = 'fixed inset-0 flex items-center justify-center z-50';
        overlay.setAttribute('role','dialog');
        overlay.setAttribute('aria-live','polite');

        const panel = document.createElement('div');
        panel.className = 'bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-8 py-4 rounded-lg shadow-xl';
        panel.tabIndex = -1;
        panel.innerHTML = `<div class="text-center"><i class="fas fa-fire text-3xl mb-2" aria-hidden="true"></i><h3 class="text-xl font-bold">${streak} Day Streak!</h3><p class="text-sm">You're on fire! Keep it up!</p></div>`;

        const close = document.createElement('button');
        close.className = 'absolute top-4 right-4 text-white';
        close.setAttribute('aria-label','Close celebration');
        close.textContent = '✕';
        close.addEventListener('click', () => { overlay.remove(); });

        overlay.appendChild(panel);
        overlay.appendChild(close);
        document.body.appendChild(overlay);

        // Focus management
        panel.focus();

        setTimeout(() => { if (overlay.parentElement) overlay.remove(); }, 3000);
    }

    // Expose cleanup and initialization
    window.cleanupDashboard = function() {
        console.log('Cleaning up Dashboard...');
        if (retryTimer) clearTimeout(retryTimer);
        retryTimer = null;
        retryCount = 0;
        // Clear any intervals stored on window
        if (window.dashboardRefreshInterval) { clearInterval(window.dashboardRefreshInterval); window.dashboardRefreshInterval = null; }
        window.dashboardInitialized = false;
    };

    window.initializeDashboard = function initializeDashboard() {
        if (window.dashboardInitialized) return;
        showLastSessionSummary();
        loadDashboardData();

        // Animate existing progress fills only if changed
        document.querySelectorAll('.progress-fill').forEach(bar => {
            const width = bar.style.width || bar.dataset.lastWidth || '0%';
            bar.style.width = '0%';
            requestAnimationFrame(() => { bar.style.width = width; });
        });

        // Refresh interval
        window.dashboardRefreshInterval = setInterval(() => {
            loadDashboardData();
        }, 30000);

        // Cleanup hooks
        document.addEventListener('visibilitychange', () => { if (document.hidden) window.cleanupDashboard(); });
        window.addEventListener('beforeunload', window.cleanupDashboard);

        // SPA navigation hook
        if (window.spaNav && typeof window.spaNav === 'object') {
            // listen for custom event 'pageUnload' if SPA triggers it
            document.addEventListener('pageUnload', window.cleanupDashboard);
        }

        window.dashboardInitialized = true;
    };

    // Auto-init when DOM ready
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', window.initializeDashboard);
    else window.initializeDashboard();

})(window, document);
