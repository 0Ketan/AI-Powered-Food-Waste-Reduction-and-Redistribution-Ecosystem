/**
 * AnnaSetu AI - Shared Navigation Bar
 * Renders prototype banner, title "AnnaSetu AI — Prototype", user switcher dropdown,
 * demo clock, Demo Guide, +1 Hour, Reset Demo, alerts bell (marks read on open), and role menu.
 */

import * as api from './api.js';
import {
    state,
    ensureUserLoaded,
    saveUser,
    getHomePageForRole,
    getNavItems,
    formatDemoTime,
    startPolling,
    refreshClock,
    markAlertsRead,
} from './state.js';

function createTopShell() {
    const wrapper = document.createElement('div');
    wrapper.id = 'app-shell-header';
    wrapper.innerHTML = `
        <div class="proto-banner">Prototype - simulated data</div>
        <nav class="navbar">
            <div class="nav-container">
                <div class="nav-left">
                    <a href="/index.html" class="nav-brand">
                        <span class="brand-text">AnnaSetu AI</span>
                    </a>
                    <div class="nav-menu" id="nav-menu"></div>
                </div>
                <div class="nav-right">
                    <a href="/index.html" class="btn btn-sm btn-outline" id="btn-demo-guide">Demo Guide</a>
                    <div class="nav-clock" id="nav-clock" title="Demo Clock">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        <span class="clock-time" id="nav-clock-time">--:--</span>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline" id="btn-plus-hour" title="Advance demo clock by 1 hour">+1 Hour</button>
                    <button type="button" class="btn btn-sm btn-danger" id="btn-reset-demo" title="Reset demo database and clock">Reset Demo</button>
                    <div class="alerts-wrapper" style="position:relative;">
                        <button type="button" class="nav-alerts" id="nav-alerts" title="Alerts" aria-label="Alerts">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                            <span class="alerts-badge" id="alerts-badge" style="display:none;">0</span>
                        </button>
                        <div class="alerts-dropdown" id="alerts-dropdown" style="display:none;">
                            <div class="dropdown-header">
                                <h4>Alerts</h4>
                                <span class="text-muted" style="font-size:0.75rem;">Marked read on open</span>
                            </div>
                            <div class="dropdown-list" id="alerts-list">
                                <div class="dropdown-empty">No alerts</div>
                            </div>
                        </div>
                    </div>
                    <div class="user-switcher">
                        <label for="user-switcher-select" class="sr-only">Switch User</label>
                        <select id="user-switcher-select" class="form-select form-select-sm"></select>
                    </div>
                </div>
            </div>
        </nav>
    `;
    return wrapper;
}

function getCurrentPageId() {
    const file = window.location.pathname.split('/').pop() || 'index.html';
    return file.replace('.html', '') || 'index';
}

function renderNavMenu() {
    const container = document.getElementById('nav-menu');
    if (!container) return;
    const items = getNavItems();
    const current = getCurrentPageId();
    container.innerHTML = items.map(item => `
        <a href="${item.href}" class="nav-item ${item.id === current ? 'active' : ''}" data-page="${item.id}">
            <span>${item.label}</span>
        </a>
    `).join('');
}

function renderUserSwitcher() {
    const select = document.getElementById('user-switcher-select');
    if (!select) return;
    if (!state.users.length) {
        select.innerHTML = '<option value="">No users</option>';
        return;
    }
    select.innerHTML = state.users.map(u => {
        const selected = state.user && String(state.user.id) === String(u.id) ? 'selected' : '';
        return `<option value="${api.escapeHtml(u.id)}" ${selected}>${api.escapeHtml(u.name)} (${api.escapeHtml(u.role)})</option>`;
    }).join('');
}

function updateClockDisplay() {
    const el = document.getElementById('nav-clock-time');
    if (el) el.textContent = formatDemoTime();
}

function updateAlertsUI() {
    const badge = document.getElementById('alerts-badge');
    const count = state.unreadAlertCount || 0;
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : String(count);
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
    const dropdown = document.getElementById('alerts-dropdown');
    if (dropdown && dropdown.style.display !== 'none') {
        renderAlertsList();
    }
}

function alertHref(a) {
    const role = state.user?.role;
    const t = (a.type || a.alert_type || '').toLowerCase();
    if (role === 'kitchen' || role === 'processing_unit') {
        if (t === 'log_reminder') {
            return `/kitchen/log.html?slot=${encodeURIComponent(a.slot || 'lunch')}`;
        }
        return '/kitchen/listings.html';
    }
    if (t === 'new_listing') return '/recipient/nearby.html';
    if (t === 'pledge') return '/recipient/needs.html';
    if (t === 'claimed' || t === 'collected') return '/recipient/claims.html';
    return getHomePageForRole(role || 'ngo');
}

function renderAlertsList() {
    const list = document.getElementById('alerts-list');
    if (!list) return;
    const alerts = (state.alerts || []).slice(0, 15);
    if (!alerts.length) {
        list.innerHTML = '<div class="dropdown-empty">No alerts yet</div>';
        return;
    }
    list.innerHTML = alerts.map(a => `
        <a href="${alertHref(a)}" class="alert-item ${!a.read ? 'unread' : ''}" style="text-decoration:none; color:inherit;">
            <div class="alert-content">
                <div class="alert-message">${api.escapeHtml(a.message)}</div>
                <div class="alert-time">${api.formatDateTime(a.created_at)}</div>
            </div>
        </a>
    `).join('');
}

export async function initNavBar() {
    if (document.getElementById('app-shell-header')) return;
    const shell = createTopShell();
    document.body.insertBefore(shell, document.body.firstChild);

    await ensureUserLoaded(api);
    renderUserSwitcher();
    renderNavMenu();
    updateClockDisplay();
    startPolling(api);

    // User switcher -> save to annasetu_user_id & go to that role's home page
    document.getElementById('user-switcher-select')?.addEventListener('change', (e) => {
        const chosen = state.users.find(u => String(u.id) === String(e.target.value));
        if (chosen) {
            saveUser(chosen);
            window.location.href = getHomePageForRole(chosen.role);
        }
    });

    // +1 Hour button
    document.getElementById('btn-plus-hour')?.addEventListener('click', async (e) => {
        await api.withSubmitLock(e.currentTarget, async () => {
            await api.advanceDemoClock(60);
            await refreshClock(api);
            api.showToast('Demo clock advanced by +1 hour', 'success');
            window.dispatchEvent(new CustomEvent('demo-clock-advanced'));
        });
    });

    // Reset Demo button
    document.getElementById('btn-reset-demo')?.addEventListener('click', async (e) => {
        if (!window.confirm('Reset demo database and clock to initial seed state?')) return;
        await api.withSubmitLock(e.currentTarget, async () => {
            await api.resetDemoClock();
            window.location.reload();
        });
    });

    // Alerts bell -> open dropdown and mark read on open
    const alertsBtn = document.getElementById('nav-alerts');
    const dropdown = document.getElementById('alerts-dropdown');
    alertsBtn?.addEventListener('click', async (e) => {
        e.stopPropagation();
        const isOpen = dropdown.style.display !== 'none';
        if (isOpen) {
            dropdown.style.display = 'none';
        } else {
            renderAlertsList();
            dropdown.style.display = 'block';
            if (state.unreadAlertCount > 0) {
                await markAlertsRead(api);
            }
        }
    });

    document.addEventListener('click', (e) => {
        if (!alertsBtn?.contains(e.target) && !dropdown?.contains(e.target)) {
            if (dropdown) dropdown.style.display = 'none';
        }
    });

    window.addEventListener('democlock-update', updateClockDisplay);
    window.addEventListener('alerts-update', updateAlertsUI);
}

// Auto-initialize when imported as <script type="module" src=".../shared/nav.js">
export const navReady = initNavBar();
