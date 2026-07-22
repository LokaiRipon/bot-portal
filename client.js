const API_BASE = 'https://web-production-9b431.up.railway.app';
let currentUser = null;
let selectedRating = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadReviews();
    checkAuth();
});

// Load Stats
// Note: the hero counters default to static placeholder copy in the HTML
// ("500+", "50k+") so the page never gets stuck on "Loading…" for visitors —
// this just overwrites them if the stats call succeeds.
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/dev/api/stats`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('dev_token') || ''}` }
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('stat-users').textContent = `${data.data.licenses.active}+`;
            document.getElementById('stat-messages').textContent = `${Math.floor(data.data.chats.total_logs / 1000)}k+`;
        }
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

// Load Reviews
async function loadReviews() {
    try {
        const response = await fetch(`${API_BASE}/api/reviews?approved=true`);
        const data = await response.json();

        const container = document.getElementById('reviews-list');
        if (data.reviews && data.reviews.length > 0) {
            container.innerHTML = data.reviews.map(review => {
                const dots = Array.from({ length: 5 }, (_, i) =>
                    `<span class="dot${i < review.rating ? ' filled' : ''}"></span>`
                ).join('');
                return `
                <div class="review-card">
                    <div class="review-header">
                        <div class="review-author">${review.user_email.split('@')[0]}</div>
                        <div class="review-rating">${dots}</div>
                    </div>
                    <div class="review-comment">${review.comment}</div>
                    <div class="review-date">${new Date(review.created_at).toLocaleDateString()}</div>
                </div>`;
            }).join('');
        } else {
            container.innerHTML = '<p class="review-empty">No reviews yet. Be the first!</p>';
        }
    } catch (e) {
        console.error('Failed to load reviews:', e);
        document.getElementById('reviews-list').innerHTML = '<p class="review-error">Failed to load reviews.</p>';
    }
}

// Check Authentication
function checkAuth() {
    const licenseKey = localStorage.getItem('license_key');
    if (licenseKey) {
        currentUser = { license_key: licenseKey };
        document.getElementById('login-prompt').style.display = 'none';
        document.getElementById('review-form-container').style.display = 'block';
    }
}

// Set Rating
function setRating(rating) {
    selectedRating = rating;
    document.getElementById('review-rating').value = rating;
    document.querySelectorAll('.star').forEach((star, index) => {
        star.classList.toggle('active', index < rating);
    });
}

// Submit Review
async function submitReview(event) {
    event.preventDefault();

    if (!currentUser) {
        alert('Please login first');
        showLoginModal();
        return;
    }

    const rating = document.getElementById('review-rating').value;
    const comment = document.getElementById('review-comment').value;

    try {
        const response = await fetch(`${API_BASE}/api/submit_review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentUser.license_key}`
            },
            body: JSON.stringify({
                rating: parseInt(rating),
                comment: comment
            })
        });

        if (response.ok) {
            alert('Review submitted successfully! It will be published after approval.');
            document.getElementById('review-form').reset();
            setRating(0);
            loadReviews();
        } else {
            const error = await response.json();
            alert(`Failed to submit review: ${error.detail}`);
        }
    } catch (e) {
        console.error('Failed to submit review:', e);
        alert('Failed to submit review. Please try again.');
    }
}

// Download Bot
async function downloadBot(platform, version) {
    try {
        const response = await fetch(`${API_BASE}/api/app_version`);
        const data = await response.json();
        version = version || data["version"];
        const key = `${platform}_${version}`;
        const downloadUrl = data["download_url"];

        if (downloadUrl) {
            window.open(downloadUrl, '_blank');
        } else {
            alert('Download link not available. Please contact support.');
        }
    } catch (e) {
        console.error('Failed to get download link:', e);
        alert('Failed to get download link. Please contact support.');
    }
}

// Show Login Modal
function showLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

// Close Login Modal
function closeLoginModal() {
    document.getElementById('login-modal').classList.remove('active');
}

// Admin Login
async function adminLogin(event) {
    event.preventDefault();

    const username = document.getElementById('admin-username').value;
    const token = document.getElementById('admin-token').value;

    try {
        const response = await fetch(`${API_BASE}/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, admin_token: token })
        });

        if (response.ok) {
            localStorage.setItem('admin_username', username);
            localStorage.setItem('admin_token', token);
            window.location.href = 'admin.html';
        } else {
            alert('Invalid credentials');
        }
    } catch (e) {
        console.error('Login failed:', e);
        alert('Login failed. Please try again.');
    }
}

// Purchase License
function purchaseLicense(tier) {
    alert(`To purchase ${tier} license, please contact us via WhatsApp or Telegram.`);
    window.open('https://wa.me/25499196459', '_blank');
}

// Mobile nav toggle
function toggleNav() {
    document.getElementById('nav-links').classList.toggle('open');
}

// Close the mobile menu once a link is tapped
document.getElementById('nav-links')?.addEventListener('click', (e) => {
    if (e.target.classList.contains('nav-link')) {
        document.getElementById('nav-links').classList.remove('open');
    }
});

// Close modals on outside click
window.onclick = function (event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
};