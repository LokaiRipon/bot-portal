const API_BASE = 'https://web-production-9b431.up.railway.app';
let authToken = localStorage.getItem('admin_token');
let currentLicenses = [];

// Check auth on load
if (!authToken) {
    window.location.href = 'index.html';
}

// Navigation
function showSection(sectionName) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    document.getElementById(`${sectionName}-section`).classList.add('active');
    event.target.closest('.nav-item').classList.add('active');
    
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
        
        document.getElementById('total-licenses').textContent = data.data.licenses.total;
        document.getElementById('active-licenses').textContent = data.data.licenses.active;
        document.getElementById('messages-today').textContent = data.data.chats.messages_today;
        document.getElementById('total-messages').textContent = data.data.chats.total_logs;
        document.getElementById('active-users').textContent = data.data.chats.active_sessions;
        document.getElementById('active-sessions').textContent = data.data.chats.active_sessions;
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

// Render Licenses Table
function renderLicenses(licenses) {
    const tbody = document.getElementById('licenses-table');
    tbody.innerHTML = licenses.map(key => `
        <tr>
            <td>
                <div class="key-container">
                    <span class="key-text">...${key.key.slice(-8)}</span>
                    <button class="btn-copy" onclick="copyToClipboard('${key.key}')" title="Copy full key">
                        📋
                    </button>
                </div>
            </td>
            <td><span class="badge badge-${key.tier.toLowerCase()}">${key.tier}</span></td>
            <td><span class="badge badge-${key.status}">${key.status}</span></td>
            <td>${key.messages_used}/${key.message_limit}</td>
            <td>${key.expiry_date}</td>
            <td>
                <button class="btn-small btn-secondary" onclick="copyToClipboard('${key.key}')">Copy</button>
                <button class="btn-small btn-warning" onclick="revokeKey('${key.key}')">Revoke</button>
            </td>
        </tr>
    `).join('');
}

// Copy to Clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show toast notification
        showToast('License key copied to clipboard!');
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
        
        // Show success with copy option
        showModal('License Key Generated', `
            <div class="success-content">
                <p><strong>Key:</strong> ${data.key}</p>
                <p><strong>Tier:</strong> ${tier}</p>
                <p><strong>Expires:</strong> ${new Date(data.expiry_date).toLocaleString()}</p>
                <button class="btn-primary" onclick="copyToClipboard('${data.key}'); closeModal();">
                    📋 Copy to Clipboard
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
            showToast('License key revoked successfully');
            loadLicenses();
        } else {
            alert(`Failed to revoke key: ${data.message}`);
        }
    } catch (error) {
        console.error('Failed to revoke key:', error);
        alert('Failed to revoke key');
    }
}

// Show Modal
function showModal(title, content) {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('generate-key-modal');
    
    modal.innerHTML = `
        <h3>${title}</h3>
        ${content}
        <div class="modal-actions">
            <button class="btn-secondary" onclick="closeModal()">Close</button>
        </div>
    `;
    
    overlay.style.display = 'flex';
}

// Close Modal
function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    // Reset modal content
    document.getElementById('generate-key-modal').innerHTML = `
        <h3>Generate License Key</h3>
        <form onsubmit="generateLicenseKey(event)">
            <div class="form-group">
                <label>Tier</label>
                <select id="key-tier" required>
                    <option value="BASIC">Basic (150 msgs/day)</option>
                    <option value="BRONZE">Bronze (300 msgs/day)</option>
                    <option value="PREMIUM">Premium (500 msgs/day)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Duration (days)</label>
                <input type="number" id="key-duration" value="30" min="1" required>
            </div>
            <div class="form-group">
                <label>User Email (optional)</label>
                <input type="email" id="key-email" placeholder="user@example.com">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-primary">Generate</button>
            </div>
        </form>
    `;
}

// Show Generate Key Modal
function showGenerateKeyModal() {
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('generate-key-modal');
    
    // Reset modal to initial state
    modal.innerHTML = `
        <h3>Generate License Key</h3>
        <form onsubmit="generateLicenseKey(event)">
            <div class="form-group">
                <label>Tier</label>
                <select id="key-tier" required>
                    <option value="BASIC">Basic (150 msgs/day)</option>
                    <option value="BRONZE">Bronze (300 msgs/day)</option>
                    <option value="PREMIUM">Premium (500 msgs/day)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Duration (days)</label>
                <input type="number" id="key-duration" value="30" min="1" max="365" required>
            </div>
            <div class="form-group">
                <label>User Email (optional)</label>
                <input type="email" id="key-email" placeholder="user@example.com">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn-primary">Generate</button>
            </div>
        </form>
    `;
    
    overlay.style.display = 'flex';
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