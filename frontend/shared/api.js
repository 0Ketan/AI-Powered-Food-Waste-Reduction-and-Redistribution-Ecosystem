/**
 * AnnaSetu AI - Shared API Client
 * Centralized API communication with the backend.
 */

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ============================================================================
// CORE ENDPOINTS
// ============================================================================

/** Get health status */
export async function getHealth() {
    return apiRequest('/health');
}

/** Get demo clock time */
export async function getDemoClock() {
    return apiRequest('/demo/clock');
}

/** Advance demo clock by minutes */
export async function advanceDemoClock(minutes) {
    return apiRequest('/demo/advance', {
        method: 'POST',
        body: { minutes }
    });
}

/** Reset demo clock */
export async function resetDemoClock() {
    return apiRequest('/demo/reset', { method: 'POST' });
}

/** Get all users for frontend */
export async function getUsers() {
    return apiRequest('/demo/users');
}

// ============================================================================
// FORECAST ENDPOINTS (M2)
// ============================================================================

/** Get forecast options (kitchens, slots, weather, events) */
export async function getForecastOptions() {
    return apiRequest('/forecast/options');
}

/** Get cooking quantity recommendation */
export async function getForecastRecommend(payload) {
    return apiRequest('/forecast/recommend', {
        method: 'POST',
        body: payload
    });
}

/** Get forecast metrics */
export async function getForecastMetrics(kitchenId, slot) {
    const params = new URLSearchParams({ kitchen_id: kitchenId, slot });
    return apiRequest(`/forecast/metrics?${params}`);
}

// ============================================================================
// WASTE ENDPOINTS (M2)
// ============================================================================

/** Log waste entry */
export async function logWaste(payload) {
    return apiRequest('/waste/log', {
        method: 'POST',
        body: payload
    });
}

/** Get waste logs for a kitchen */
export async function getWasteLogs(kitchenId, limit = 50) {
    const params = new URLSearchParams({ kitchen_id: kitchenId, limit: String(limit) });
    return apiRequest(`/waste/logs?${params}`);
}

/** Get waste summary for a kitchen */
export async function getWasteSummary(kitchenId) {
    const params = new URLSearchParams({ kitchen_id: kitchenId });
    return apiRequest(`/waste/summary?${params}`);
}

// ============================================================================
// SAFETY ENDPOINTS (M1)
// ============================================================================

/** Get food categories */
export async function getSafetyCategories() {
    return apiRequest('/safety/categories');
}

/** Evaluate food safety */
export async function evaluateSafety(payload) {
    return apiRequest('/safety/evaluate', {
        method: 'POST',
        body: payload
    });
}

/** Get safety label for printing */
export async function getSafetyLabel(labelId) {
    return apiRequest(`/safety/label/${labelId}/print`);
}

/** Get safety records for a donor */
export async function getSafetyRecords(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/safety/records?${params}`);
}

/** Get safety records as CSV */
export async function getSafetyRecordsCSV(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    const response = await fetch(`${API_BASE}/safety/records.csv?${params}`);
    return response.text();
}

/** Get safety disposals for a donor */
export async function getSafetyDisposals(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/safety/disposals?${params}`);
}

/** Create safety disposal record */
export async function createSafetyDisposal(payload) {
    return apiRequest('/safety/disposals', {
        method: 'POST',
        body: payload
    });
}

// ============================================================================
// MARKETPLACE ENDPOINTS (M3)
// ============================================================================

/** Get marketplace listings */
export async function getMarketplaceListings(donorId = null, status = null) {
    const params = new URLSearchParams();
    if (donorId) params.append('donor_id', donorId);
    if (status) params.append('status', status);
    return apiRequest(`/marketplace/listings?${params}`);
}

/** Create marketplace listing */
export async function createMarketplaceListing(payload) {
    return apiRequest('/marketplace/listings', {
        method: 'POST',
        body: payload
    });
}

/** Get nearby listings for a recipient */
export async function getNearbyListings(recipientId, maxKm = 10) {
    const params = new URLSearchParams({ recipient_id: recipientId });
    return apiRequest(`/marketplace/nearby?${params}`);
}

/** Claim a listing */
export async function claimListing(listingId, recipientId) {
    return apiRequest(`/marketplace/listings/${listingId}/claim`, {
        method: 'POST',
        body: { recipient_id: recipientId }
    });
}

/** Pickup a listing */
export async function pickupListing(listingId, donorId, code) {
    return apiRequest(`/marketplace/listings/${listingId}/pickup`, {
        method: 'POST',
        body: { donor_id: donorId, code }
    });
}

/** Mark listing as served */
export async function serveListing(listingId, recipientId, peopleServed) {
    return apiRequest(`/marketplace/listings/${listingId}/served`, {
        method: 'POST',
        body: { recipient_id: recipientId, people_served: peopleServed }
    });
}

/** Get marketplace needs */
export async function getMarketplaceNeeds(status = null, recipientId = null, forDonorId = null) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (recipientId) params.append('recipient_id', recipientId);
    if (forDonorId) params.append('for_donor_id', forDonorId);
    return apiRequest(`/marketplace/needs?${params}`);
}

/** Create a need request */
export async function createMarketplaceNeed(payload) {
    return apiRequest('/marketplace/needs', {
        method: 'POST',
        body: payload
    });
}

/** Pledge to a need */
export async function pledgeToNeed(needId, payload) {
    return apiRequest(`/marketplace/needs/${needId}/pledge`, {
        method: 'POST',
        body: payload
    });
}

/** Get alerts for a user */
export async function getAlerts(userId, since = null, unreadOnly = false) {
    const params = new URLSearchParams({ user_id: userId });
    if (since) params.append('since', since);
    if (unreadOnly) params.append('unread_only', 'true');
    return apiRequest(`/alerts?${params}`);
}

/** Mark all alerts as read */
export async function markAlertsRead(userId) {
    return apiRequest('/alerts/read', {
        method: 'POST',
        body: { user_id: userId }
    });
}

/** Get impact statistics for a donor */
export async function getImpact(donorId) {
    const params = new URLSearchParams({ donor_id: donorId });
    return apiRequest(`/impact?${params}`);
}

/** Get marketplace claims */
export async function getMarketplaceClaims(recipientId = null, donorId = null) {
    const params = new URLSearchParams();
    if (recipientId) params.append('recipient_id', recipientId);
    if (donorId) params.append('donor_id', donorId);
    return apiRequest(`/marketplace/claims?${params}`);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/** Format date for display */
export function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

/** Format time for display */
export function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

/** Format datetime for display */
export function formatDateTime(dateString) {
    return `${formatDate(dateString)} ${formatTime(dateString)}`;
}

/** Get relative time string */
export function getRelativeTime(dateString) {
    const now = new Date();
    const then = new Date(dateString);
    const diffMs = then - now;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 0) return 'Expired';
    if (diffMins < 60) return `${diffMins} min left`;
    if (diffHours < 24) return `${diffHours}h ${diffMins % 60}m left`;
    return `${diffDays}d ${diffHours % 24}h left`;
}

/** Calculate minutes until expiry */
export function minutesUntilExpiry(consumeBy) {
    const now = new Date();
    const then = new Date(consumeBy);
    return Math.floor((then - now) / 60000);
}

/** Show toast notification */
export function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    `;
    document.body.appendChild(container);
    return container;
}

/** Format number with commas */
export function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

/** Debounce function */
export function debounce(fn, delay) {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
}