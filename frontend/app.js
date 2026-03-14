/**
 * CityPulse AI - Shared Frontend Utilities
 */

// API Base URL
const API_BASE = window.location.origin;

// Utility Functions
const utils = {
    // Format date
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Format time
    formatTime: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Get category emoji
    getCategoryEmoji: (category) => {
        const emojis = {
            garbage: '🗑️',
            roads: '🛣️',
            water: '💧',
            electricity: '⚡',
            streetlight: '💡',
            parks: '🌳',
            noise: '🔊',
            other: '📋'
        };
        return emojis[category.toLowerCase()] || '📋';
    },

    // Get status color
    getStatusClass: (status) => {
        const classes = {
            submitted: 'status-submitted',
            in_progress: 'status-in_progress',
            resolved: 'status-resolved',
            reopened: 'status-reopened',
            closed: 'status-closed'
        };
        return classes[status] || 'status-submitted';
    },

    // Get priority color
    getPriorityClass: (priority) => {
        const classes = {
            high: 'priority-high',
            medium: 'priority-medium',
            low: 'priority-low'
        };
        return classes[priority?.toLowerCase()] || 'priority-medium';
    },

    // Show toast notification
    showToast: (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#6366f1'};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // API request wrapper
    apiRequest: async (endpoint, options = {}) => {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                ...options,
                headers: {
                    ...options.headers
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Truncate text
    truncate: (text, length = 50) => {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    },

    // Validate mobile number
    isValidMobile: (mobile) => {
        return /^[6-9]\d{9}$/.test(mobile);
    },

    // Format mobile number
    formatMobile: (mobile) => {
        if (!mobile) return '';
        return mobile.replace(/(\d{5})(\d{5})/, '$1 $2');
    },

    // Get relative time
    getRelativeTime: (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        return utils.formatDate(dateString);
    },

    // Local storage helpers
    storage: {
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.error('Storage error:', e);
            }
        },
        get: (key) => {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            } catch (e) {
                console.error('Storage error:', e);
                return null;
            }
        },
        remove: (key) => {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.error('Storage error:', e);
            }
        },
        clear: () => {
            try {
                localStorage.clear();
            } catch (e) {
                console.error('Storage error:', e);
            }
        }
    }
};

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export utils
if (typeof module !== 'undefined' && module.exports) {
    module.exports = utils;
}