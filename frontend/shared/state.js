/**
 * AnnaSetu AI - Shared State Management
 * Persists user ID in localStorage key `annasetu_user_id` (defaults to first kitchen).
 * Polls demo clock and alerts every 5 seconds.
 */

export const USER_ID_KEY = 'annasetu_user_id';

export const state = {
    users: [],
    user: null,
    demoTime: null,
    offsetMinutes: 0,
    alerts: [],
    unreadAlertCount: 0,
    pollingIntervals: {},
    readyPromise: null,
};

export function isDonorRole(role) {
    return role === 'kitchen' || role === 'processing_unit';
}

export function getHomePageForRole(role) {
    return isDonorRole(role) ? '/kitchen/dashboard.html' : '/recipient/nearby.html';
}

export function getSavedUserId() {
    try {
        return localStorage.getItem(USER_ID_KEY);
    } catch {
        return null;
    }
}

export function saveUser(user) {
    state.user = user;
    try {
        if (user?.id) {
            localStorage.setItem(USER_ID_KEY, String(user.id));
        }
    } catch (e) {
        console.warn('Failed to save annasetu_user_id:', e);
    }
    window.dispatchEvent(new CustomEvent('user-changed', { detail: { user } }));
}

export function getUser() {
    return state.user;
}

export function getUserRole() {
    return state.user?.role || null;
}

/**
 * Load users from /api/demo/users and select saved user or default to first kitchen.
 */
export async function ensureUserLoaded(api) {
    if (state.readyPromise) return state.readyPromise;
    state.readyPromise = (async () => {
        try {
            const res = await api.getUsers();
            state.users = res.users || [];
            const savedId = getSavedUserId();
            let chosen = state.users.find(u => String(u.id) === String(savedId));
            if (!chosen) {
                chosen = state.users.find(u => u.role === 'kitchen') || state.users[0] || null;
            }
            if (chosen) {
                state.user = chosen;
                try {
                    localStorage.setItem(USER_ID_KEY, String(chosen.id));
                } catch {}
            }
        } catch (e) {
            console.warn('Failed to load users:', e);
        }
        return state.user;
    })();
    return state.readyPromise;
}

export function updateDemoClock(demoTime, offsetMinutes) {
    state.demoTime = demoTime;
    state.offsetMinutes = offsetMinutes;
    window.dispatchEvent(new CustomEvent('democlock-update', {
        detail: { demoTime, offsetMinutes }
    }));
}

export function getDemoTime() {
    return state.demoTime ? new Date(state.demoTime) : new Date();
}

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

export async function refreshClock(api) {
    try {
        const data = await api.getDemoClock({ silent: true });
        updateDemoClock(data.demo_time_utc, data.offset_minutes);
    } catch (e) {
        console.warn('Demo clock poll failed:', e);
    }
}

export async function fetchAlerts(api) {
    if (!state.user) return;
    try {
        const alerts = await api.getAlerts(state.user.id);
        state.alerts = Array.isArray(alerts) ? alerts : [];
        state.unreadAlertCount = state.alerts.filter(a => !a.read).length;
        window.dispatchEvent(new CustomEvent('alerts-update', {
            detail: { alerts: state.alerts, unreadCount: state.unreadAlertCount }
        }));
    } catch (e) {
        console.warn('Fetch alerts failed:', e);
    }
}

export async function markAlertsRead(api) {
    if (!state.user) return;
    try {
        await api.markAlertsRead(state.user.id);
        state.alerts.forEach(a => { a.read = 1; });
        state.unreadAlertCount = 0;
        window.dispatchEvent(new CustomEvent('alerts-update', {
            detail: { alerts: state.alerts, unreadCount: 0 }
        }));
    } catch (e) {
        console.warn('Mark alerts read failed:', e);
    }
}

export function startPolling(api) {
    stopPolling();
    refreshClock(api);
    if (state.user) fetchAlerts(api);

    state.pollingIntervals.clock = setInterval(() => refreshClock(api), 5000);
    state.pollingIntervals.alerts = setInterval(() => {
        if (state.user) fetchAlerts(api);
    }, 5000);
}

export function stopPolling() {
    Object.values(state.pollingIntervals).forEach(id => clearInterval(id));
    state.pollingIntervals = {};
}

export function getNavItems() {
    const role = getUserRole();
    const items = [
        { id: 'dashboard', label: 'Dashboard', href: '/kitchen/dashboard.html', icon: '📊', roles: ['kitchen', 'processing_unit'] },
        { id: 'plan', label: 'Plan', href: '/kitchen/plan.html', icon: '🔮', roles: ['kitchen', 'processing_unit'] },
        { id: 'log', label: 'Log Waste', href: '/kitchen/log.html', icon: '📝', roles: ['kitchen', 'processing_unit'] },
        { id: 'post-surplus', label: 'Post Surplus', href: '/kitchen/post-surplus.html', icon: '🏪', roles: ['kitchen', 'processing_unit'] },
        { id: 'listings', label: 'My Listings', href: '/kitchen/listings.html', icon: '📋', roles: ['kitchen', 'processing_unit'] },
        { id: 'nearby', label: 'Nearby Food', href: '/recipient/nearby.html', icon: '🗺️', roles: ['ngo', 'mandir'] },
        { id: 'needs', label: 'My Needs', href: '/recipient/needs.html', icon: '🙏', roles: ['ngo', 'mandir'] },
        { id: 'claims', label: 'My Claims', href: '/recipient/claims.html', icon: '✅', roles: ['ngo', 'mandir'] },
    ];
    return items.filter(item => item.roles.includes(role));
}
