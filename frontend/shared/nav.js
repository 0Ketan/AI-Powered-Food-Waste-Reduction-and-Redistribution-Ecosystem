/**
 * AnnaSetu AI - Shared Navigation Component
 * Renders the top navigation bar with user info, demo clock, alerts, and role-based navigation.
 */

import { state, getNavItems, logout, formatDemoTime, getUnreadAlertCount, markAlertsRead } from './state.js';
import { showToast } from './api.js';

/**
 * Create and return the navigation bar element
 */
export function createNavBar() {
    const nav = document.createElement('nav');
    nav.className = 'navbar';
    nav.innerHTML = `
        <div class="nav-container">
            <div class="nav-left">
                <a href="index.html" class="nav-brand">
                    <span class="brand-icon">🍲</span>
                    <span class="brand-text">AnnaSetu AI</span>
                </a>
                <div class="nav-divider"></div>
                <div class="nav-menu" id="nav-menu"></div>
            </div>
            <div class="nav-right">
                <div class="nav-clock" id="nav-clock" title="Demo Clock">
                    <span class="clock-icon">⏰</span>
                    <span class="clock-time">--:--:--</span>
                    <span class="clock-label">Demo Time</span>
                </div>
                <button class="nav-alerts" id="nav-alerts" title="Alerts" aria-label="Alerts">
                    <span class="alerts-icon">🔔</span>
                    <span class="alerts-badge" id="alerts-badge" style="display: none;">0</span>
                </button>
                <div class="nav-user" id="nav-user" style="display: none;">
                    <span class="user-avatar" id="user-avatar"></span>
                    <span class="user-name" id="user-name"></span>
                    <span class="user-role" id="user-role"></span>
                    <button class="btn btn-sm btn-logout" id="btn-logout">Logout</button>
                </div>
                <div class="nav-login" id="nav-login" style="display: none;">
                    <button class="btn btn-primary" id="btn-login-kitchen">Kitchen</button>
                    <button class="btn btn-secondary" id="btn-login-ngo">NGO</button>
                    <button class="btn btn-secondary" id="btn-login-mandir">Mandir</button>
                    <button class="btn btn-secondary" id="btn-login-processing">Processing Unit</button>
                </div>
            </div>
        </div>
        <!-- Alerts Dropdown -->
        <div class="alerts-dropdown" id="alerts-dropdown" style="display: none;">
            <div class="dropdown-header">
                <h4>Alerts</h4>
                <button class="btn btn-sm btn-mark-read" id="btn-mark-read">Mark all read</button>
            </div>
            <div class="dropdown-list" id="alerts-list"></div>
        </div>
    `;
    return nav;
}

/**
 * Initialize navigation bar
 */
export function initNavBar(api) {
    const navBar = createNavBar();
    document.body.insertBefore(navBar, document.body.firstChild);

    // Setup event listeners
    setupNavEvents(api);
    updateNavUI();

    // Listen for state changes
    window.addEventListener('democlock-update', () => updateClockDisplay());
    window.addEventListener('alerts-update', () => updateAlertsUI());

    // Start polling
    import('./state.js').then(({ startPolling }) => startPolling(api));
}

/**
 * Setup navigation event listeners
 */
function setupNavEvents(api) {
    // Logout button
    document.getElementById('btn-logout')?.addEventListener('click', () => logout(api));

    // Login buttons
    document.getElementById('btn-login-kitchen')?.addEventListener('click', () => showLoginModal('kitchen'));
    document.getElementById('btn-login-ngo')?.addEventListener('click', () => showLoginModal('ngo'));
    document.getElementById('btn-login-mandir')?.addEventListener('click', () => showLoginModal('mandir'));
    document.getElementById('btn-login-processing')?.addEventListener('click', () => showLoginModal('processing_unit'));

    // Alerts dropdown
    const alertsBtn = document.getElementById('nav-alerts');
    const alertsDropdown = document.getElementById('alerts-dropdown');

    alertsBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleAlertsDropdown();
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!alertsBtn?.contains(e.target) && !alertsDropdown?.contains(e.target)) {
            closeAlertsDropdown();
        }
    });

    // Mark all read
    document.getElementById('btn-mark-read')?.addEventListener('click', async () => {
        await markAlertsRead(api);
        closeAlertsDropdown();
        showToast('All alerts marked as read', 'success');
    });

    // Update clock display initially
    updateClockDisplay();
}

/**
 * Update navigation UI based on login state
 */
export function updateNavUI() {
    const navMenu = document.getElementById('nav-menu');
    const navUser = document.getElementById('nav-user');
    const navLogin = document.getElementById('nav-login');
    const userAvatar = document.getElementById('user-avatar');
    const userName = document.getElementById('user-name');
    const userRole = document.getElementById('user-role');

    if (state.user) {
        // User logged in - show nav menu and user info
        navMenu.style.display = 'flex';
        navUser.style.display = 'flex';
        navLogin.style.display = 'none';

        // Update user info
        userAvatar.textContent = getRoleIcon(state.user.role);
        userName.textContent = state.user.name;
        userRole.textContent = formatRole(state.user.role);

        // Build role-based navigation
        renderNavMenu(navMenu);
    } else {
        // Not logged in
        navMenu.style.display = 'none';
        navUser.style.display = 'none';
        navLogin.style.display = 'flex';
    }
}

/**
 * Render role-based navigation menu
 */
function renderNavMenu(container) {
    const navItems = getNavItems();
    container.innerHTML = navItems.map(item => `
        <a href="${item.href}" class="nav-item" data-page="${item.id}">
            <span class="nav-item-icon">${item.icon}</span>
            <span class="nav-item-label">${item.label}</span>
        </a>
    `).join('');

    // Highlight current page
    const currentPage = getCurrentPageId();
    const activeLink = container.querySelector(`[data-page="${currentPage}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

/**
 * Get current page ID from URL
 */
function getCurrentPageId() {
    const path = window.location.pathname;
    const page = path.split('/').pop().replace('.html', '');
    return page || 'index';
}

/**
 * Update clock display
 */
function updateClockDisplay() {
    const clockTime = document.querySelector('.clock-time');
    if (clockTime) {
        clockTime.textContent = formatDemoTime();
    }
}

/**
 * Update alerts UI
 */
function updateAlertsUI() {
    const badge = document.getElementById('alerts-badge');
    const count = getUnreadAlertCount();

    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }

    // Update dropdown list if open
    const dropdown = document.getElementById('alerts-dropdown');
    if (dropdown.style.display !== 'none') {
        renderAlertsDropdown();
    }
}

/**
 * Toggle alerts dropdown
 */
function toggleAlertsDropdown() {
    const dropdown = document.getElementById('alerts-dropdown');
    const isOpen = dropdown.style.display !== 'none';

    if (isOpen) {
        closeAlertsDropdown();
    } else {
        openAlertsDropdown();
    }
}

/**
 * Open alerts dropdown
 */
function openAlertsDropdown() {
    const dropdown = document.getElementById('alerts-dropdown');
    dropdown.style.display = 'block';
    renderAlertsDropdown();
}

/**
 * Close alerts dropdown
 */
function closeAlertsDropdown() {
    const dropdown = document.getElementById('alerts-dropdown');
    dropdown.style.display = 'none';
}

/**
 * Render alerts in dropdown
 */
function renderAlertsDropdown() {
    const list = document.getElementById('alerts-list');
    const alerts = state.alerts.slice(0, 10); // Show latest 10

    if (alerts.length === 0) {
        list.innerHTML = '<div class="dropdown-empty">No alerts</div>';
        return;
    }

    list.innerHTML = alerts.map(alert => `
        <div class="alert-item ${!alert.read ? 'unread' : ''}" data-alert-id="${alert.id}">
            <div class="alert-icon">${getAlertIcon(alert.type)}</div>
            <div class="alert-content">
                <div class="alert-message">${escapeHtml(alert.message)}</div>
                <div class="alert-time">${formatAlertTime(alert.created_at)}</div>
            </div>
        </div>
    `).join('');

    // Add click handlers to mark as read
    list.querySelectorAll('.alert-item').forEach(item => {
        item.addEventListener('click', () => {
            const alertId = item.dataset.alertId;
            markAlertRead(alertId);
        });
    });
}

/**
 * Mark individual alert as read
 */
function markAlertRead(alertId) {
    const alert = state.alerts.find(a => a.id === alertId);
    if (alert && !alert.read) {
        alert.read = 1;
        state.unreadAlertCount = Math.max(0, state.unreadAlertCount - 1);
        window.dispatchEvent(new CustomEvent('alerts-update', {
            detail: { alerts: state.alerts, unreadCount: state.unreadAlertCount }
        }));
        renderAlertsDropdown();
    }
}

/**
 * Get icon for user role
 */
function getRoleIcon(role) {
    const icons = {
        kitchen: '🍳',
        processing_unit: '🏭',
        ngo: '🤝',
        mandir: '🕉️',
    };
    return icons[role] || '👤';
}

/**
 * Format role for display
 */
function formatRole(role) {
    const labels = {
        kitchen: 'Kitchen',
        processing_unit: 'Processing Unit',
        ngo: 'NGO',
        mandir: 'Mandir',
    };
    return labels[role] || role;
}

/**
 * Get icon for alert type
 */
function getAlertIcon(type) {
    const icons = {
        new_listing: '🍽️',
        claimed: '✅',
        pledge: '🤝',
        expiry_warning: '⚠️',
        expired: '❌',
        disposal: '🗑️',
    };
    return icons[type] || '🔔';
}

/**
 * Format alert time
 */
function formatAlertTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show login modal for role selection
 */
function showLoginModal(role) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal login-modal">
            <h3>Select User</h3>
            <p>Choose a demo account to continue as ${formatRole(role)}</p>
            <div class="user-list" id="user-list"></div>
            <button class="btn btn-secondary modal-close" id="modal-close">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);

    // Fetch users and populate
    fetch('/api/demo/users')
        .then(r => r.json())
        .then(data => {
            const users = data.users.filter(u => u.role === role);
            const list = modal.querySelector('#user-list');
            list.innerHTML = users.map(user => `
                <button class="user-option" data-user-id="${user.id}">
                    <span class="user-option-name">${escapeHtml(user.name)}</span>
                    <span class="user-option-id">${user.id}</span>
                </button>
            `).join('');

            // Add click handlers
            list.querySelectorAll('.user-option').forEach(btn => {
                btn.addEventListener('click', () => {
                    const userId = btn.dataset.userId;
                    const user = users.find(u => u.id === userId);
                    if (user) {
                        import('./state.js').then(({ saveUser }) => saveUser(user));
                        updateNavUI();
                        showToast(`Logged in as ${user.name}`, 'success');
                        modal.remove();
                        // Reload page to initialize page-specific logic
                        window.location.reload();
                    }
                });
            });
        })
        .catch(() => {
            showToast('Failed to load users', 'error');
        });

    // Close modal handlers
    modal.querySelector('#modal-close')?.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Export for use in pages
export { updateNavUI, updateClockDisplay, updateAlertsUI };