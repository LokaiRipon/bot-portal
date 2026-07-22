const API_BASE = 'https://web-production-9b431.up.railway.app';
let authToken = localStorage.getItem('admin_token');
let currentLicenses = [];

const ICON_COPY = '<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.3"><rect x="5.5" y="5.5" width="8" height="8" rx="1"/><path d="M3 9.5V3.5A1 1 0 0 1 4 2.5h6"/></svg>';

const TIER_HINTS = {
    BASIC: '150 messages / day',
    BRONZE: '300 messages / day',
    PREMIUM: '500 messages / day'
};

// Check auth on load
if (!authToken) {
    window.location.href = 'index.html';
}

// Navigation
function showSection(sectionName, evt) {
    evt = evt || window.event;
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    document.getElementById(`${sectionName}-section`).classList.add('active');
    if (evt && evt.target) {
        const navItem = evt.target.closest('.nav-item');
        if (navItem) navItem.classList.add('active');
    }

    if (sectionName === 'dashboard') loadDashboard();
    if (sectionName === 'licenses') loadLicenses();
    if (sectionName === 'analytics') loadAnalytics();
}

// Load Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/dev/api/stats`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        const lic = data.data.licenses;
        const chats = data.data.chats;

        document.getElementById('total-licenses').textContent = lic.total;
        document.getElementById('active-licenses').textContent = lic.active;
        document.getElementById('messages-today').textContent = chats.messages_today;
        document.getElementById('total-messages').textContent = chats.total_logs;
        document.getElementById('active-users').textContent = chats.active_sessions;
        document.getElementById('active-sessions').textContent = chats.active_sessions;

        const pct = lic.total > 0 ? Math.round((lic.active / lic.total) * 100) : 0;
        const bar = document.getElementById('licenses-bar');
        if (bar) bar.style.setProperty('--pct', pct + '%');
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

// Load Licenses
async function loadLicenses() {
    try {
        const response = await fetch(`${API_BASE}/admin/api/check_keys`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        currentLicenses = data.keys;
        renderLicenses(currentLicenses);
    } catch (error) {
        console.error('Failed to load licenses:', error);
    }
}

// Placeholder for chart rendering (wired up separately against usage history)
function loadAnalytics() {}

// Render Licenses Table
function renderLicenses(licenses) {
    const tbody = document.getElementById('licenses-table');

    if (!licenses || !licenses.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-row">No license keys match. Generate one, or adjust your search.</td></tr>`;
        return;
    }

    tbody.innerHTML = licenses.map(key => {
        const pct = key.message_limit ? Math.min(100, Math.round((key.messages_used / key.message_limit) * 100)) : 0;
        const meterState = pct >= 100 ? 'full' : pct >= 80 ? 'high' : 'normal';
        const statusLed = key.status === 'active' ? 'led-active' : key.status === 'expired' ? 'led-expired' : 'led-pending';

        return `
        <tr>
            <td>
                <div class="key-cell">
                    <span class="key-mono">···· ${key.key.slice(-8)}</span>
                    <button class="icon-btn" onclick="copyToClipboard('${key.key}')" title="Copy full key">${ICON_COPY}</button>
                </div>
            </td>
            <td><span class="jack jack-${key.tier.toLowerCase()}">${key.tier}</span></td>
            <td><span class="led ${statusLed}"></span><span class="status-label">${key.status}</span></td>
            <td>
                <div class="usage-cell">
                    <span class="usage-mono">${key.messages_used}/${key.message_limit}</span>
                    <div class="usage-bar"><span class="usage-fill usage-${meterState}" style="width:${pct}%"></span></div>
                </div>
            </td>
            <td class="cell-mono">${key.expiry_date}</td>
            <td class="cell-actions">
                <button class="btn-ghost btn-small" onclick="copyToClipboard('${key.key}')">Copy</button>
                <button class="btn-ghost btn-small btn-danger" onclick="revokeKey('${key.key}')">Revoke</button>
            </td>
        </tr>`;
    }).join('');
}

// Copy to Clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('License key copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

// Show Toast Notification
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Filter Licenses
function filterLicenses() {
    const searchTerm = document.getElementById('license-search').value.toLowerCase();
    const filtered = currentLicenses.filter(key =>
        key.key.toLowerCase().includes(searchTerm) ||
        key.user_email?.toLowerCase().includes(searchTerm)
    );
    renderLicenses(filtered);
}

// Tier segmented switch (stands in for a native <select>)
function setTier(el, value) {
    el.closest('.switch-group').querySelectorAll('.switch-opt').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    document.getElementById('key-tier').value = value;
    const hint = document.getElementById('tier-hint');
    if (hint) hint.textContent = TIER_HINTS[value] || '';
}

// Generate License Key
async function generateLicenseKey(event) {
    event.preventDefault();

    const tier = document.getElementById('key-tier').value;
    const duration = document.getElementById('key-duration').value;
    const email = document.getElementById('key-email').value;

    try {
        const response = await fetch(`${API_BASE}/admin/api/issue_key`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                user_email: email,
                data: { tier: tier, duration_days: duration }
            })
        });

        const data = await response.json();

        showModal('Key Generated', `
            <div class="success-panel">
                <div class="success-row">
                    <span class="success-label">Key</span>
                    <span class="success-mono">${data.key}</span>
                </div>
                <div class="success-row">
                    <span class="success-label">Tier</span>
                    <span class="jack jack-${tier.toLowerCase()}">${tier}</span>
                </div>
                <div class="success-row">
                    <span class="success-label">Expires</span>
                    <span class="success-mono">${new Date(data.expiry_date).toLocaleString()}</span>
                </div>
                <button class="btn-solid" style="width:100%" onclick="copyToClipboard('${data.key}'); closeModal();">
                    ${ICON_COPY} Copy Key
                </button>
            </div>
        `);

        loadLicenses();
    } catch (error) {
        console.error('Failed to generate key:', error);
        alert('Failed to generate license key');
    }
}

// Revoke Key
async function revokeKey(key) {
    if (!confirm(`Are you sure you want to revoke license key ...${key.slice(-8)}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}${localStorage.getItem('admin_path')}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                action: 'revoke_key',
                data: { key: key }
            })
        });

        const data = await response.json();
        if (data.status === 'success') {
            showToast('License key revoked');
            loadLicenses();
        } else {
            alert(`Failed to revoke key: ${data.message}`);
        }
    } catch (error) {
        console.error('Failed to revoke key:', error);
        alert('Failed to revoke key');
    }
}

// Drawer form markup (shared between initial open and reset-after-close)
function drawerFormHTML() {
    return `
        <div class="drawer-head">
            <h3>New License Key</h3>
            <button class="icon-btn" onclick="closeModal()" aria-label="Close">✕</button>
        </div>
        <form onsubmit="generateLicenseKey(event)" class="drawer-form">
            <div class="field">
                <label>Tier</label>
                <div class="switch-group">
                    <button type="button" class="switch-opt active" onclick="setTier(this,'BASIC')">Basic</button>
                    <button type="button" class="switch-opt" onclick="setTier(this,'BRONZE')">Bronze</button>
                    <button type="button" class="switch-opt" onclick="setTier(this,'PREMIUM')">Premium</button>
                </div>
                <span class="field-hint" id="tier-hint">150 messages / day</span>
                <select id="key-tier" style="display:none" required>
                    <option value="BASIC">Basic</option>
                    <option value="BRONZE">Bronze</option>
                    <option value="PREMIUM">Premium</option>
                </select>
            </div>
            <div class="field">
                <label for="key-duration">Duration (days)</label>
                <input type="number" id="key-duration" value="30" min="1" max="365" required>
            </div>
            <div class="field">
                <label for="key-email">User email <span class="field-optional">optional</span></label>
                <input type="email" id="key-email" placeholder="user@example.com">
            </div>
            <div class="drawer-actions">
                <button type="button" class="btn-ghost" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-solid">Generate Key</button>
            </div>
        </form>
    `;
}

// Show Modal (generic content, used for the success view)
function showModal(title, content) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('generate-key-modal');

    modal.innerHTML = `
        <div class="drawer-head">
            <h3>${title}</h3>
            <button class="icon-btn" onclick="closeModal()" aria-label="Close">✕</button>
        </div>
        <div class="drawer-body">${content}</div>
    `;

    overlay.style.display = 'flex';
}

// Close Modal
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('generate-key-modal').innerHTML = drawerFormHTML();
}

// Show Generate Key Modal
function showGenerateKeyModal() {
    document.getElementById('generate-key-modal').innerHTML = drawerFormHTML();
    document.getElementById('modal-overlay').style.display = 'flex';
}

// Logout
function logout() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_username');
    window.location.href = 'index.html';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'modal-overlay') {
        closeModal();
    }
});