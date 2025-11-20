/**
 * ProSpeak AI - Notification System
 * Simple, elegant notifications for user feedback
 */

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 4000) {
        const notification = this.createNotification(message, type, duration);
        this.container.appendChild(notification);
        this.notifications.push(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full', 'opacity-0');
        }, 100);

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.remove(notification);
            }, duration);
        }

        return notification;
    }

    createNotification(message, type, duration) {
        const notification = document.createElement('div');
        notification.className = `
            transform translate-x-full opacity-0 transition-all duration-300 ease-out
            max-w-sm w-full bg-white border border-gray-200 rounded-lg shadow-lg p-4
            ${this.getTypeClasses(type)}
        `;

        const icon = this.getIcon(type);
        const progressBar = duration > 0 ? this.createProgressBar(duration) : '';

        notification.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <i class="${icon} text-lg"></i>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900">${message}</p>
                    ${progressBar}
                </div>
                <div class="ml-4 flex-shrink-0">
                    <button class="text-gray-400 hover:text-gray-600 transition-colors" onclick="window.notifications.remove(this.closest('.transform'))">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        return notification;
    }

    createProgressBar(duration) {
        return `
            <div class="mt-2 bg-gray-200 rounded-full h-1">
                <div class="bg-current h-1 rounded-full transition-all ease-linear" 
                     style="width: 100%; animation: shrink ${duration}ms linear forwards;"></div>
            </div>
        `;
    }

    getTypeClasses(type) {
        const classes = {
            success: 'border-green-200 text-green-600',
            error: 'border-red-200 text-red-600',
            warning: 'border-yellow-200 text-yellow-600',
            info: 'border-blue-200 text-blue-600'
        };
        return classes[type] || classes.info;
    }

    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    remove(notification) {
        if (!notification || !notification.parentNode) return;

        // Animate out
        notification.classList.add('translate-x-full', 'opacity-0');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            // Remove from array
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }

    success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 6000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }

    // Persistent notification (no auto-remove)
    persistent(message, type = 'info') {
        return this.show(message, type, 0);
    }

    // Clear all notifications
    clear() {
        this.notifications.forEach(notification => {
            this.remove(notification);
        });
    }
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shrink {
        from { width: 100%; }
        to { width: 0%; }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// Initialize global notification system
window.notifications = new NotificationSystem();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSystem;
}