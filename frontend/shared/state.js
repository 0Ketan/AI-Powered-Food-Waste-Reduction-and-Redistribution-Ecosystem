/**
 * AnnaSetu AI - Shared State Management
 * Handles user session, demo clock, alerts polling, and global state.
 */

const STORAGE_KEY = 'annasetu_user';

/**
 * Current user state
 */
export const state = {
    user: null,
    demoTime: null,
    offsetMinutes: 0,
    alerts: [],
    lastAlertCheck: null,
    unreadAlertCount: 0,
    pollingIntervals: {},
};

/**
 * Initialize state from localStorage
 */
export function initState() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            const parsed = JSON.parse(stored);
            state.user = parsed.user || null;
        }
    } catch (e) {
        console.warn('Failed to load state from localStorage:', e);
    }
}

/**
 * Save current user to localStorage
 */
export function saveUser(user) {
    state.user = user;
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ user }));
    } catch (e) {
        console.warn('Failed to save user to localStorage:', e);
    }
}

/**
 * Clear user session
 */
export function clearUser() {
    state.user = null;
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
        console.warn('Failed to clear localStorage:', e);
    }
}

/**
 * Check if user is logged in
 */
export function isLoggedIn() {
    return state.user !== null;
}

/**
 * Get current user
 */
export function getUser() {
    return state.user;
}

/**
 * Get user role
 */
export function getUserRole() {
    return state.user?.role || null;
}

/**
 * Update demo clock state
 */
export function updateDemoClock(demoTime, offsetMinutes) {
    state.demoTime = demoTime;
    state.offsetMinutes = offsetMinutes;
    // Dispatch event for UI updates
    window.dispatchEvent(new CustomEvent('democlock-update', {
        detail: { demoTime, offsetMinutes }
    }));
}

/**
 * Get demo time as Date object
 */
export function getDemoTime() {
    if (state.demoTime) {
        return new Date(state.demoTime);
    }
    return new Date(); // Fallback to real time
}

/**
 * Format demo time for display
 */
export function formatDemoTime() {
    const dt = getDemoTime();
    return dt.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

/**
 * Start polling for demo clock and alerts
 */
export function startPolling(api) {
    // Stop any existing polling
    stopPolling();

    // Poll demo clock every 5 seconds
    state.pollingIntervals.clock = setInterval(async () => {
        try {
            const data = await api.getDemoClock();
            updateDemoClock(data.demo_time_utc, data.offset_minutes);
        } catch (e) {
            console.warn('Demo clock poll failed:', e);
        }
    }, 5000);

    // Poll alerts every 5 seconds if logged in
    state.pollingIntervals.alerts = setInterval(async () => {
        if (state.user) {
            try {
                const alerts = await api.getAlerts(state.user.id, state.lastAlertCheck, true);
                if (alerts && alerts.length > 0) {
                    state.alerts = [...alerts, ...state.alerts].slice(0, 50);
                    state.unreadAlertCount = alerts.length;
                    state.lastAlertCheck = new Date().toISOString();
                    window.dispatchEvent(new CustomEvent('alerts-update', {
                        detail: { alerts: state.alerts, unreadCount: state.unreadAlertCount }
                    }));
                }
            } catch (e) {
                console.warn('Alerts poll failed:', e);
            }
        }
    }, 5000);

    // Initial fetch
    if (state.user) {
        fetchAlerts(api);
    }
}

/**
 * Stop all polling intervals
 */
export function stopPolling() {
    Object.values(state.pollingIntervals).forEach(id => clearInterval(id));
    state.pollingIntervals = {};
}

/**
 * Fetch alerts for current user
 */
export async function fetchAlerts(api) {
    if (!state.user) return;
    try {
        const alerts = await api.getAlerts(state.user.id);
        state.alerts = alerts || [];
        state.unreadAlertCount = state.alerts.filter(a => !a.read).length;
        state.lastAlertCheck = new Date().toISOString();
        window.dispatchEvent(new CustomEvent('alerts-update', {
            detail: { alerts: state.alerts, unreadCount: state.unreadAlertCount }
        }));
    } catch (e) {
        console.warn('Fetch alerts failed:', e);
    }
}

/**
 * Mark alerts as read
 */
export async function markAlertsRead(api) {
    if (!state.user) return;
    try {
        await api.markAlertsRead(state.user.id);
        state.alerts.forEach(a => a.read = 1);
        state.unreadAlertCount = 0;
        window.dispatchEvent(new CustomEvent('alerts-update', {
            detail: { alerts: state.alerts, unreadCount: 0 }
        }));
    } catch (e) {
        console.warn('Mark alerts read failed:', e);
    }
}

/**
 * Get all alerts
 */
export function getAlerts() {
    return state.alerts;
}

/**
 * Get unread alert count
 */
export function getUnreadAlertCount() {
    return state.unreadAlertCount;
}

/**
 * Add a new alert (from polling or real-time)
 */
export function addAlert(alert) {
    state.alerts.unshift(alert);
    if (state.alerts.length > 50) state.alerts.pop();
    if (!alert.read) state.unreadAlertCount++;
    window.dispatchEvent(new CustomEvent('alerts-update', {
        detail: { alerts: state.alerts, unreadCount: state.unreadAlertCount }
    }));
}

/**
 * Check if current user can access a page based on role
 */
export function canAccessPage(pageRoles) {
    if (!state.user) return false;
    if (!pageRoles || pageRoles.length === 0) return true;
    return pageRoles.includes(state.user.role);
}

/**
 * Get navigation items for current user role
 */
export function getNavItems() {
    const role = getUserRole();
    const baseItems = [
        { id: 'dashboard', label: 'Dashboard', href: 'dashboard.html', icon: '📊', roles: ['kitchen', 'processing_unit'] },
        { id: 'plan', label: 'Plan', href: 'plan.html', icon: '🔮', roles: ['kitchen', 'processing_unit'] },
        { id: 'log', label: 'Log Waste', href: 'log.html', icon: '📊', roles: ['kitchen', 'processing_unit'] },
        { id: 'post-surplus', label: 'Post Surplus', href: 'post-surplus.html', icon: '🏪', roles: ['kitchen', 'processing_unit'] },
        { id: 'listings', label: 'My Listings', href: 'listings.html', icon: '📋', roles: ['kitchen', 'processing_unit'] },
        { id: 'nearby', label: 'Nearby Food', href: 'nearby.html', icon: '🗺️', roles: ['ngo', 'mandir'] },
        { id: 'needs', label: 'My Needs', href: 'needs.html', icon: '📝', roles: ['ngo', 'mandir'] },
        { id: 'claims', label: 'My Claims', href: 'claims.html', icon: '✅', roles: ['ngo', 'mandir'] },
    ];

    return baseItems.filter(item => item.roles.includes(role));
}

/**
 * Logout current user
 */
export function logout(api) {
    stopPolling();
    clearUser();
    window.location.href = 'index.html';
}

// Initialize on load
initState();