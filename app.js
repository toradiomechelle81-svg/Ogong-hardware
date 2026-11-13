/* =========================================
   OGONG HARDWARE — SHARED UTILITIES
   app.js — used by all pages
========================================= */


/* =========================================
   TOAST NOTIFICATION SYSTEM
========================================= */

(function () {
    const container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
})();

/**
 * Show a toast notification.
 * @param {string} msg   - Message text
 * @param {'success'|'error'|'info'|''} type
 * @param {number} duration - ms
 */
function toast(msg, type = '', duration = 3200) {
    const icons = {
        success: '✅',
        error:   '❌',
        info:    'ℹ️',
        '':      '🔔'
    };

    const container = document.getElementById('toast-container');

    const el = document.createElement('div');
    el.className = `toast${type ? ' toast-' + type : ''}`;
    el.innerHTML = `
        <span class="toast-icon">${icons[type] ?? '🔔'}</span>
        <span class="toast-msg">${msg}</span>
    `;

    container.appendChild(el);

    setTimeout(() => {
        el.classList.add('removing');
        el.addEventListener('animationend', () => el.remove());
    }, duration);
}


/* =========================================
   MODAL HELPERS
========================================= */

/**
 * Open a modal overlay by ID.
 */
function openModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

/**
 * Close a modal overlay by ID.
 */
function closeModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
}

// Close modal when clicking overlay background
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
        document.body.style.overflow = '';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open')
            .forEach(m => {
                m.classList.remove('open');
                document.body.style.overflow = '';
            });
    }
});


/* =========================================
   CURRENCY FORMATTER
========================================= */

/**
 * Format number as Philippine Peso string.
 */
function peso(amount) {
    return '₱' + Number(amount).toLocaleString('en-PH', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


/* =========================================
   ACTIVE NAV LINK
========================================= */

(function () {
    const page = window.location.pathname.split('/').pop() || 'login.html';
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href === page) {
            link.classList.add('active');
        }
    });
})();


/* =========================================
   LOGOUT
========================================= */

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (_) {}
    window.location.href = 'login.html';
}


/* =========================================
   SIDEBAR MOBILE TOGGLE
========================================= */

function toggleSidebar() {
    const sidebar   = document.querySelector('.sidebar');
    const backdrop  = document.getElementById('sidebarBackdrop');
    const toggle    = document.getElementById('sidebarToggle');
    if (!sidebar) return;
    const isOpen = sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('open', isOpen);
    if (toggle)   toggle.classList.toggle('open', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

function closeSidebar() {
    const sidebar   = document.querySelector('.sidebar');
    const backdrop  = document.getElementById('sidebarBackdrop');
    const toggle    = document.getElementById('sidebarToggle');
    if (sidebar)  sidebar.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    if (toggle)   toggle.classList.remove('open');
    document.body.style.overflow = '';
}

// Close sidebar when a nav link is clicked on mobile
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.sidebar-nav a').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) closeSidebar();
        });
    });
});




/* =========================================
   CURRENT USER
========================================= */

async function getCurrentUser() {
    try {
        const res = await fetch('/api/current-user');
        return await res.json();
    } catch (_) {
        return { logged_in: false };
    }
}

/**
 * Populate user chip elements if present.
 */
async function populateUserChip() {
    const user = await getCurrentUser();
    if (!user.logged_in) return;

    const chipName = document.getElementById('userChipName');
    const chipRole = document.getElementById('userChipRole');
    const chipAvatar = document.getElementById('userChipAvatar');

    if (chipName) chipName.textContent = user.username;
    if (chipRole) chipRole.textContent = user.role;
    if (chipAvatar) chipAvatar.textContent = user.username.charAt(0).toUpperCase();
}

populateUserChip();
