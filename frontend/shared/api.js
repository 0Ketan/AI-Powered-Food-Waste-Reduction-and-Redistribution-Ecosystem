/**
 * AnnaSetu AI - Shared API Client
 * Single fetch wrapper with 10s timeout, JSON parsing, visible error banners, and submit locking.
 */

const API_BASE = '/api';
const DEFAULT_TIMEOUT_MS = 10000;

/**
 * Show a visible red error message at the top of the page (never silent).
 */
export function showError(message) {
    let banner = document.getElementById('global-error-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'global-error-banner';
        banner.className = 'error-banner';
        banner.setAttribute('role', 'alert');
        const main = document.querySelector('main') || document.body;
        main.insertBefore(banner, main.firstChild);
    }
    banner.innerHTML = `
        <span class="error-banner-text"></span>
        <button type="button" class="error-banner-close" aria-label="Dismiss error">&times;</button>
    `;
    banner.querySelector('.error-banner-text').textContent = `Error: ${message}`;
    banner.querySelector('.error-banner-close').addEventListener('click', () => {
        banner.style.display = 'none';
    });
    banner.style.display = 'flex';
}

export function clearError() {
    const banner = document.getElementById('global-error-banner');
    if (banner) banner.style.display = 'none';
}

/**
 * Disable submit button(s) while an async request is running (prevents double submits).
 */
export async function withSubmitLock(buttonOrForm, fn) {
    const buttons = [];
    if (buttonOrForm) {
        if (buttonOrForm.tagName === 'FORM') {
            buttons.push(...buttonOrForm.querySelectorAll('button[type="submit"], button:not([type])'));
        } else {
            buttons.push(buttonOrForm);
        }
    }
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.dataset.origText = btn.innerHTML;
        btn.classList.add('is-loading');
    });
    try {
        clearError();
        return await fn();
    } finally {
        buttons.forEach(btn => {
            btn.disabled = false;
            if (btn.dataset.origText) {
                btn.innerHTML = btn.dataset.origText;
                delete btn.dataset.origText;
            }
            btn.classList.remove('is-loading');
        });
    }
}

/**
 * Generic fetch wrapper with 10s timeout and JSON parsing.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        signal: controller.signal,
        ...options
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);
        const rawText = await response.text();
        let data = {};
        if (rawText) {
            try {
                data = JSON.parse(rawText);
            } catch {
                data = { message: rawText };
            }
        }

        if (!response.ok) {
            const msg = data.message || data.detail || `HTTP ${response.status}: ${response.statusText}`;
            const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
            err.status = response.status;
            err.data = data;
            throw err;
        }

        return data;
    } catch (error) {
        if (error.name === 'AbortError') {
            const timeoutErr = new Error(`Request timed out after 10s (${endpoint})`);
            timeoutErr.status = 408;
            if (!options.silent) showError(timeoutErr.message);
            throw timeoutErr;
        }
        console.error(`API Error [${endpoint}]:`, error);
        if (!options.silent) {
            showError(error.message || 'Request failed');
        }
        throw error;
    } finally {
        clearTimeout(timer);
    }
}

// ============================================================================
// CORE ENDPOINTS
// ============================================================================

export async function getHealth() {
    return apiRequest('/health');
}

export async function getDemoClock(options = {}) {
    return apiRequest('/demo/clock', options);
}

export async function advanceDemoClock(minutes) {
    const params = new URLSearchParams({ minutes: String(minutes) });
    return apiRequest(`/demo/advance?${params}`, { method: 'POST' });
}

export async function resetDemoClock() {
    return apiRequest('/demo/reset', { method: 'POST' });
}

export async function getUsers() {
    return apiRequest('/demo/users');
}

// ============================================================================
// FORECAST ENDPOINTS (M2)
// ============================================================================

export async function getForecastOptions() {
    return apiRequest('/forecast/options');
}

export async function getForecastRecommend(payload) {
    return apiRequest('/forecast/recommend', {
        method: 'POST',
        body: payload
    });
}

export async function getForecastMetrics(kitchenId, slot) {
    const params = new URLSearchParams({ kitchen_id: kitchenId, slot });
    return apiRequest(`/forecast/metrics?${params}`);
}

// ============================================================================
// WASTE ENDPOINTS (M2)
// ============================================================================

export async function logWaste(payload) {
    return apiRequest('/waste/logs', {
        method: 'POST',
        body: payload
    });
}

export async function getWasteLogs(kitchenId, limit = 50) {
    const params = new URLSearchParams({ kitchen_id: kitchenId, limit: String(limit) });
    return apiRequest(`/waste/logs?${params}`);
}

export async function getWasteSummary(kitchenId, options = {}) {
    const params = new URLSearchParams({ kitchen_id: kitchenId });
    return apiRequest(`/waste/summary?${params}`, options);
}

// ============================================================================
// SAFETY ENDPOINTS (M1)
// ============================================================================

export async function getSafetyCategories() {
    return apiRequest('/safety/categories');
}

export async function evaluateSafety(payload) {
    return apiRequest('/safety/evaluate', {
        method: 'POST',
        body: payload
    });
}

export async function getSafetyRecords(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/safety/records?${params}`);
}

export async function getSafetyDisposals(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/safety/disposals?${params}`);
}

export async function completeSafetyRecord(recordId, payload) {
    return apiRequest(`/safety/records/${encodeURIComponent(recordId)}/complete`, {
        method: 'POST',
        body: payload
    });
}

// ============================================================================
// MARKETPLACE ENDPOINTS (M3)
// ============================================================================

export async function getMarketplaceListings(donorId = null, status = null) {
    const params = new URLSearchParams();
    if (donorId) params.append('donor_id', donorId);
    if (status) params.append('status', status);
    return apiRequest(`/marketplace/listings?${params}`);
}

export async function createMarketplaceListing(payload) {
    return apiRequest('/marketplace/listings', {
        method: 'POST',
        body: payload
    });
}

export async function getNearbyListings(recipientId) {
    const params = new URLSearchParams({ recipient_id: recipientId });
    return apiRequest(`/marketplace/nearby?${params}`);
}

export async function claimListing(listingId, recipientId) {
    return apiRequest(`/marketplace/listings/${encodeURIComponent(listingId)}/claim`, {
        method: 'POST',
        body: { recipient_id: recipientId },
        silent: true // caller handles 409 custom message
    });
}

export async function pickupListing(listingId, donorId, code) {
    return apiRequest(`/marketplace/listings/${encodeURIComponent(listingId)}/pickup`, {
        method: 'POST',
        body: { donor_id: donorId, code }
    });
}

export async function serveListing(listingId, recipientId, peopleServed) {
    return apiRequest(`/marketplace/listings/${encodeURIComponent(listingId)}/served`, {
        method: 'POST',
        body: { recipient_id: recipientId, people_served: peopleServed }
    });
}

export async function getMarketplaceNeeds(status = null, recipientId = null, forDonorId = null) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (recipientId) params.append('recipient_id', recipientId);
    if (forDonorId) params.append('for_donor_id', forDonorId);
    return apiRequest(`/marketplace/needs?${params}`);
}

export async function createMarketplaceNeed(payload) {
    return apiRequest('/marketplace/needs', {
        method: 'POST',
        body: payload
    });
}

export async function pledgeToNeed(needId, payload) {
    return apiRequest(`/marketplace/needs/${encodeURIComponent(needId)}/pledge`, {
        method: 'POST',
        body: payload
    });
}

export async function getAlerts(userId, since = null, unreadOnly = false) {
    const params = new URLSearchParams({ user_id: userId });
    if (since) params.append('since', since);
    if (unreadOnly) params.append('unread_only', 'true');
    return apiRequest(`/marketplace/alerts?${params}`, { silent: true });
}

export async function markAlertsRead(userId) {
    return apiRequest('/marketplace/alerts/read', {
        method: 'POST',
        body: { user_id: userId },
        silent: true
    });
}

export async function getImpact(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/marketplace/impact?${params}`);
}

export async function getMarketplaceClaims(recipientId = null, donorId = null) {
    const params = new URLSearchParams();
    if (recipientId) params.append('recipient_id', recipientId);
    if (donorId) params.append('donor_id', donorId);
    return apiRequest(`/marketplace/claims?${params}`);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

export function formatDate(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return String(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

export function formatTime(dateString) {
    if (!dateString) return '--';
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return String(dateString);
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

export function formatDateTime(dateString) {
    if (!dateString) return '--';
    return `${formatDate(dateString)} ${formatTime(dateString)}`;
}

export function showToast(message, type = 'info', duration = 3500) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:1000;display:flex;flex-direction:column;gap:0.5rem;max-width:360px;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}
