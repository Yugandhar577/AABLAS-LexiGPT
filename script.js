const initialPromptInput = document.getElementById('initial-prompt-input');
const promptInput = document.getElementById('prompt-input');
const chatHistory = document.getElementById('chat-history');
const body = document.body;
const sidebar = document.querySelector('.sidebar');
const sidebarBackdrop = document.querySelector('.sidebar-backdrop');
const sidebarToggle = document.querySelector('.sidebar-toggle');
const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
const fileUploadInput = document.getElementById('file-upload-input');
const uploadIcon = document.getElementById('upload-icon');
const initialUploadIcon = document.getElementById('initial-upload-icon');
const themeToggle = document.getElementById('theme-toggle');
const moonIcon = document.getElementById('moon-icon');
const sunIcon = document.getElementById('sun-icon');
const chatsList = document.getElementById('chats-list');

const isHttpOrigin = window.location.origin.startsWith('http');
const API_BASE = window.__LEXIGPT_API__ || (isHttpOrigin ? '' : 'http://localhost:5000');
const apiUrl = (path) => `${API_BASE}${path}`;
let activeSession = null;
let STREAM_MODE = false;
const sidebarSearch = document.getElementById('sidebar-search-input');
let authToken = localStorage.getItem('authToken') || null;
let currentUser = null;
let refreshToken = localStorage.getItem('refreshToken') || null;

// Auth controls
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const settingsBtn = document.getElementById('settings-btn');
const profileBtn = document.getElementById('profile-btn');

if (loginBtn) loginBtn.addEventListener('click', showLoginModal);
if (registerBtn) registerBtn.addEventListener('click', showRegisterModal);
// Open settings page in main view instead of modal
if (settingsBtn) settingsBtn.addEventListener('click', showSettingsPage);
if (profileBtn) profileBtn.addEventListener('click', () => document.getElementById('profile-modal').classList.remove('hidden'));

// Sidebar auth buttons (mirror actions so they work from sidebar)
const sidebarLoginBtn = document.getElementById('sidebar-login-btn');
const sidebarRegisterBtn = document.getElementById('sidebar-register-btn');
const sidebarProfileBtn = document.getElementById('sidebar-profile-btn');
const sidebarSettingsBtn = document.getElementById('sidebar-settings-btn');
const sidebarLogoutBtn = document.getElementById('sidebar-logout-btn');

if (sidebarLoginBtn) sidebarLoginBtn.addEventListener('click', showLoginModal);
if (sidebarRegisterBtn) sidebarRegisterBtn.addEventListener('click', showRegisterModal);
if (sidebarSettingsBtn) sidebarSettingsBtn.addEventListener('click', showSettingsPage);
if (sidebarProfileBtn) sidebarProfileBtn.addEventListener('click', () => { if (profileBtn) profileBtn.click(); else document.getElementById('profile-modal').classList.remove('hidden'); });
if (sidebarLogoutBtn) sidebarLogoutBtn.addEventListener('click', () => { const hdr = document.getElementById('logout-btn'); if (hdr) hdr.click(); });

async function initAuth() {
    if (!authToken) return updateAuthUI();
    try {
        const res = await fetch(apiUrl('/api/auth/me'), { headers: { 'Authorization': 'Bearer ' + authToken } });
        if (!res.ok) { authToken = null; localStorage.removeItem('authToken'); return updateAuthUI(); }
        const d = await res.json();
        if (d && d.user) {
            currentUser = d.user;
            updateAuthUI();
        }
    } catch (e) {
        console.warn('Auth init failed', e);
        authToken = null; localStorage.removeItem('authToken');
        updateAuthUI();
    }
}

function updateAuthUI() {
    if (currentUser) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (settingsBtn) settingsBtn.style.display = 'inline-flex';
        // show header user
        const nameEl = document.getElementById('header-user-name');
        const avatarEl = document.getElementById('header-user-avatar');
        const logoutBtn = document.getElementById('logout-btn');
        if (nameEl) { nameEl.textContent = currentUser.display_name || currentUser.username; nameEl.style.display = '' }
        if (avatarEl && currentUser.avatar_url) { avatarEl.src = (API_BASE || '') + currentUser.avatar_url; avatarEl.style.display = '' }
        if (logoutBtn) logoutBtn.style.display = 'inline-flex';
        // sidebar mirrors
        const sLogin = document.getElementById('sidebar-login-btn');
        const sReg = document.getElementById('sidebar-register-btn');
        const sProfile = document.getElementById('sidebar-profile-btn');
        const sSettings = document.getElementById('sidebar-settings-btn');
        const sLogout = document.getElementById('sidebar-logout-btn');
        if (sLogin) sLogin.style.display = 'none';
        if (sReg) sReg.style.display = 'none';
        if (sProfile) sProfile.style.display = '';
        if (sSettings) sSettings.style.display = '';
        if (sLogout) sLogout.style.display = '';
    } else {
        if (loginBtn) loginBtn.style.display = 'inline-flex';
        if (registerBtn) registerBtn.style.display = 'inline-flex';
        if (settingsBtn) settingsBtn.style.display = 'none';
        const nameEl = document.getElementById('header-user-name');
        const avatarEl = document.getElementById('header-user-avatar');
        const logoutBtn = document.getElementById('logout-btn');
        if (nameEl) nameEl.style.display = 'none';
        if (avatarEl) { avatarEl.src = ''; avatarEl.style.display = 'none'; }
        if (logoutBtn) logoutBtn.style.display = 'none';
        const sLogin = document.getElementById('sidebar-login-btn');
        const sReg = document.getElementById('sidebar-register-btn');
        const sProfile = document.getElementById('sidebar-profile-btn');
        const sSettings = document.getElementById('sidebar-settings-btn');
        const sLogout = document.getElementById('sidebar-logout-btn');
        if (sLogin) sLogin.style.display = '';
        if (sReg) sReg.style.display = '';
        if (sProfile) sProfile.style.display = 'none';
        if (sSettings) sSettings.style.display = 'none';
        if (sLogout) sLogout.style.display = 'none';
    }
}

function showLoginModal() {
    showAuthModal('login');
}

function showRegisterModal() {
    showAuthModal('register');
}

function showAuthModal(mode = 'login') {
    const overlay = document.getElementById('modal-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    if (mode === 'login') { loginForm.classList.remove('hidden'); registerForm.classList.add('hidden'); }
    else { registerForm.classList.remove('hidden'); loginForm.classList.add('hidden'); }
}

function hideAuthModal() {
    const overlay = document.getElementById('modal-overlay');
    if (!overlay) return;
    overlay.classList.add('hidden');
}

// Modal wiring
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('modal-overlay');
    const closeBtn = document.getElementById('modal-close');
    const showLogin = document.getElementById('show-login');
    const showRegister = document.getElementById('show-register');
    const loginSubmit = document.getElementById('login-submit');
    const registerSubmit = document.getElementById('register-submit');
    const logoutBtn = document.getElementById('logout-btn');

    if (closeBtn) closeBtn.addEventListener('click', hideAuthModal);
    if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) hideAuthModal(); });
    if (showLogin) showLogin.addEventListener('click', () => showAuthModal('login'));
    if (showRegister) showRegister.addEventListener('click', () => showAuthModal('register'));

    if (loginSubmit) loginSubmit.addEventListener('click', async () => {
        const u = document.getElementById('login-username').value.trim();
        const p = document.getElementById('login-password').value.trim();
        if (!u || !p) return alert('Enter username and password');
        try {
            const res = await fetch(apiUrl('/api/auth/login'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) });
            const d = await res.json();
            if (!res.ok) return alert(d.error || 'Login failed');
            if (d.token) {
                authToken = d.token;
                localStorage.setItem('authToken', authToken);
                if (d.refresh_token) { refreshToken = d.refresh_token; localStorage.setItem('refreshToken', refreshToken); }
                currentUser = d.user;
                updateAuthUI();
                hideAuthModal();
            }
        } catch (e) { console.error(e); alert('Login failed'); }
    });

    if (registerSubmit) registerSubmit.addEventListener('click', async () => {
        const u = document.getElementById('reg-username').value.trim();
        const p = document.getElementById('reg-password').value.trim();
        const dn = document.getElementById('reg-display').value.trim();
        if (!u || !p) return alert('Choose username and password');
        try {
            const res = await fetch(apiUrl('/api/auth/register'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p, display_name: dn }) });
            const d = await res.json();
            if (!res.ok) return alert(d.error || 'Registration failed');
            if (d.token) {
                authToken = d.token;
                localStorage.setItem('authToken', authToken);
                if (d.refresh_token) { refreshToken = d.refresh_token; localStorage.setItem('refreshToken', refreshToken); }
                currentUser = d.user;
                updateAuthUI();
                hideAuthModal();
            }
        } catch (e) { console.error(e); alert('Registration failed'); }
    });

    if (logoutBtn) logoutBtn.addEventListener('click', async () => {
        try {
            const body = refreshToken ? { refresh_token: refreshToken } : {};
            const res = await fetch(apiUrl('/api/auth/logout'), { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
            if (res.ok) {
                authToken = null; localStorage.removeItem('authToken'); currentUser = null; updateAuthUI();
                refreshToken = null; localStorage.removeItem('refreshToken');
                alert('Logged out');
            } else {
                alert('Logout failed');
            }
        } catch (e) { console.error(e); alert('Logout failed'); }
    });
});

// Profile modal wiring
document.addEventListener('DOMContentLoaded', () => {
    const profileBtn = document.getElementById('profile-btn');
    const profileModal = document.getElementById('profile-modal');
    const profileClose = document.getElementById('profile-close');
    const profileSave = document.getElementById('profile-save');
    const profileUpload = document.getElementById('profile-upload');
    const profileDisplay = document.getElementById('profile-display');
    const profileAvatarPreview = document.getElementById('profile-avatar-preview');

    if (profileBtn) profileBtn.addEventListener('click', async () => {
        // ensure we have auth and currentUser
        if (!currentUser) {
            alert('Please login first');
            return;
        }
        // fill fields
        profileDisplay.value = currentUser.display_name || currentUser.username;
        if (currentUser.avatar_url) { profileAvatarPreview.src = (API_BASE || '') + currentUser.avatar_url; profileAvatarPreview.style.display = ''; } else { profileAvatarPreview.style.display = 'none'; }
        profileModal.classList.remove('hidden');
    });
    if (profileClose) profileClose.addEventListener('click', () => profileModal.classList.add('hidden'));
    if (profileModal) profileModal.addEventListener('click', (e) => { if (e.target === profileModal) profileModal.classList.add('hidden'); });

    if (profileUpload) profileUpload.addEventListener('click', () => {
        const input = document.createElement('input'); input.type = 'file'; input.accept = 'image/*';
        input.onchange = async (ev) => {
            const file = ev.target.files[0]; if (!file) return;
            const fd = new FormData(); fd.append('avatar', file);
            try {
                // ensure token
                const ok = await ensureAuth(); if (!ok) return alert('Not authenticated');
                const res = await fetch(apiUrl('/api/auth/upload-avatar'), { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken }, body: fd });
                if (!res.ok) return alert('Upload failed');
                const d = await res.json();
                if (d.avatar_url) {
                    currentUser.avatar_url = d.avatar_url;
                    profileAvatarPreview.src = (API_BASE || '') + d.avatar_url; profileAvatarPreview.style.display = '';
                    // update header
                    const headerAvatar = document.getElementById('header-user-avatar'); if (headerAvatar) { headerAvatar.src = (API_BASE || '') + d.avatar_url; headerAvatar.style.display = ''; }
                    alert('Avatar updated');
                }
            } catch (e) { console.error(e); alert('Upload failed'); }
        };
        input.click();
    });

    if (profileSave) profileSave.addEventListener('click', async () => {
        const newName = profileDisplay.value.trim();
        if (!newName) return alert('Enter a display name');
        try {
            const ok = await ensureAuth(); if (!ok) return alert('Not authenticated');
            const res = await fetchWithAuth(apiUrl('/api/auth/update-profile'), { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: newName }) });
            if (!res.ok) { const d = await res.json().catch(()=>({})); return alert(d.error || 'Save failed'); }
            const d = await res.json();
            if (d.user) { currentUser = d.user; updateAuthUI(); profileModal.classList.add('hidden'); alert('Profile updated'); }
        } catch (e) { console.error(e); alert('Update failed'); }
    });
});

// Settings page actions
document.addEventListener('DOMContentLoaded', () => {
    const settingsBack = document.getElementById('settings-back');
    const settingsSave = document.getElementById('settings-save-profile');
    const settingsUpload = document.getElementById('settings-upload-avatar');
    const settingsStream = document.getElementById('settings-stream-default');
    const logoutAllBtn = document.getElementById('settings-logout-all');

    if (settingsBack) settingsBack.addEventListener('click', () => hideSettingsPage());
    if (settingsStream) settingsStream.addEventListener('change', () => {
        localStorage.setItem('STREAM_MODE_DEFAULT', settingsStream.checked ? 'true' : 'false');
    });

    if (settingsSave) settingsSave.addEventListener('click', async () => {
        const newName = document.getElementById('settings-display').value.trim();
        if (!newName) return alert('Enter a display name');
        const ok = await ensureAuth(); if (!ok) return alert('Not authenticated');
        try {
            const res = await fetchWithAuth(apiUrl('/api/auth/update-profile'), { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: newName }) });
            if (!res.ok) { const d = await res.json().catch(()=>({})); return alert(d.error || 'Save failed'); }
            const d = await res.json(); currentUser = d.user; updateAuthUI(); alert('Saved');
        } catch (e) { console.error(e); alert('Save failed'); }
    });

    if (settingsUpload) settingsUpload.addEventListener('click', () => {
        const input = document.createElement('input'); input.type = 'file'; input.accept = 'image/*';
        input.onchange = async (ev) => {
            const file = ev.target.files[0]; if (!file) return;
            const fd = new FormData(); fd.append('avatar', file);
            const ok = await ensureAuth(); if (!ok) return alert('Not authenticated');
            try {
                const res = await fetch(apiUrl('/api/auth/upload-avatar'), { method: 'POST', headers: { 'Authorization': 'Bearer ' + authToken }, body: fd });
                if (!res.ok) return alert('Upload failed');
                const d = await res.json(); if (d.avatar_url) { currentUser.avatar_url = d.avatar_url; updateAuthUI(); alert('Avatar updated'); }
            } catch (e) { console.error(e); alert('Upload failed'); }
        };
        input.click();
    });

    if (logoutAllBtn) logoutAllBtn.addEventListener('click', async () => {
        if (!confirm('Logout from all sessions?')) return;
        const ok = await ensureAuth(); if (!ok) return alert('Not authenticated');
        try {
            const res = await fetchWithAuth(apiUrl('/api/auth/logout-all'), { method: 'POST' });
            if (res.ok) { authToken = null; refreshToken = null; localStorage.removeItem('authToken'); localStorage.removeItem('refreshToken'); currentUser = null; updateAuthUI(); alert('Logged out from all sessions'); hideSettingsPage(); }
            else { alert('Logout all failed'); }
        } catch (e) { console.error(e); alert('Logout all failed'); }
    });
});

// Helper: ensure we have a valid authToken, try refresh if needed
async function ensureAuth() {
    if (authToken) return true;
    if (!refreshToken) return false;
    try {
        const res = await fetch(apiUrl('/api/auth/refresh'), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refreshToken }) });
        if (!res.ok) { refreshToken = null; localStorage.removeItem('refreshToken'); return false; }
        const d = await res.json();
        if (d && d.token) { authToken = d.token; localStorage.setItem('authToken', authToken); return true; }
    } catch (e) { console.warn('refresh failed', e); }
    return false;
}

// fetch wrapper that automatically attempts refresh on 401 once
async function fetchWithAuth(url, opts = {}) {
    opts.headers = opts.headers || {};
    if (authToken) opts.headers['Authorization'] = 'Bearer ' + authToken;
    let res = await fetch(url, opts);
    if (res.status === 401 && refreshToken) {
        const ok = await ensureAuth();
        if (ok) {
            opts.headers['Authorization'] = 'Bearer ' + authToken;
            res = await fetch(url, opts);
        }
    }
    return res;
}

function showSettingsModal() {
    // Simple settings dialog using prompt for avatar upload via file input
    // open settings page in main content
    showSettingsPage();
}

function showSettingsPage() {
    // populate fields
    const settings = document.getElementById('settings-page');
    if (!settings) return;
    // hide chat view elements to show settings instead
    settings.classList.remove('hidden');
    document.querySelector('.prompt-area').style.display = 'none';
    const chatHist = document.getElementById('chat-history'); if (chatHist) chatHist.style.display = 'none';
    // fill current values
    const disp = document.getElementById('settings-display');
    if (disp && currentUser) disp.value = currentUser.display_name || currentUser.username;
    const streamChk = document.getElementById('settings-stream-default');
    if (streamChk) streamChk.checked = !!(localStorage.getItem('STREAM_MODE_DEFAULT') === 'true');
}

function hideSettingsPage() {
    const settings = document.getElementById('settings-page');
    if (!settings) return;
    settings.classList.add('hidden');
    document.querySelector('.prompt-area').style.display = '';
    const chatHist = document.getElementById('chat-history'); if (chatHist) chatHist.style.display = '';
}

// Sidebar toggle for desktop
sidebarToggle.addEventListener('click', function() {
    sidebar.classList.toggle('expanded');
});

const newChatButton = document.querySelector('.sidebar-item-new-chat');
if (newChatButton) {
    newChatButton.addEventListener('click', startNewChat);
}

// Stream toggle button
const streamToggle = document.getElementById('stream-toggle');
if (streamToggle) {
    streamToggle.addEventListener('click', () => {
        STREAM_MODE = !STREAM_MODE;
        document.getElementById('stream-off').classList.toggle('hidden', STREAM_MODE);
        document.getElementById('stream-on').classList.toggle('hidden', !STREAM_MODE);
        streamToggle.title = STREAM_MODE ? 'Streaming enabled' : 'Streaming disabled';
    });
}

// Sidebar toggle for mobile
mobileMenuToggle.addEventListener('click', function() {
    sidebar.classList.add('expanded');
});

// Hide sidebar when clicking outside on mobile
sidebarBackdrop.addEventListener('click', function() {
    sidebar.classList.remove('expanded');
});

// Event listener for the main chat upload icon
uploadIcon.addEventListener('click', () => {
    fileUploadInput.click();
});

// Event listener for the initial screen upload icon
initialUploadIcon.addEventListener('click', () => {
    fileUploadInput.click();
});

// Event listener for file selection
fileUploadInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        if (!body.classList.contains('chat-started')) {
            body.classList.add('chat-started');
            initialPromptInput.value = '';
        }

        const uploadMessage = `User has uploaded a document: ${file.name}`;
        handleUserMessage(uploadMessage);
        fileUploadInput.value = '';
    }
});

// Theme Toggle Logic
function setTheme(theme) {
    if (theme === 'light') {
        body.setAttribute('data-theme', 'light');
        moonIcon.classList.add('hidden');
        sunIcon.classList.remove('hidden');
    } else {
        body.removeAttribute('data-theme');
        moonIcon.classList.remove('hidden');
        sunIcon.classList.add('hidden');
    }
    localStorage.setItem('theme', theme);
}

// Set initial theme on page load
const savedTheme = localStorage.getItem('theme') || 'dark';
setTheme(savedTheme);

// Toggle theme on button click
themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    setTheme(currentTheme);
});

// Function to add a message to chat history
function sendMessage(message, isUser = true, opts = {}) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.title = isUser ? 'You' : 'Assistant';
    // If caller provided an avatar URL, use it; otherwise use initial
    if (opts.avatarUrl) {
        avatar.style.backgroundImage = `url('${opts.avatarUrl}')`;
        avatar.style.backgroundSize = 'cover';
        avatar.style.backgroundPosition = 'center';
        avatar.textContent = '';
    } else if (isUser && currentUser && currentUser.avatar_url) {
        // use logged-in user's avatar
        const full = (API_BASE || '') + currentUser.avatar_url;
        avatar.style.backgroundImage = `url('${full}')`;
        avatar.style.backgroundSize = 'cover';
        avatar.style.backgroundPosition = 'center';
        avatar.textContent = '';
    } else {
        avatar.textContent = isUser ? 'U' : 'A';
    }
    msgDiv.appendChild(avatar);

    const contentWrapper = document.createElement('div');
    contentWrapper.className = 'message-bubble';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    contentWrapper.appendChild(contentDiv);

    msgDiv.appendChild(contentWrapper);

    // For assistant messages, add a small bottom-right trigger to show chain-of-thought / sources
    if (!isUser) {
        // Ensure bubble has relative positioning so dropdown can be absolute
        contentWrapper.classList.add('message-bubble');

        const cotTrigger = document.createElement('button');
        cotTrigger.className = 'cot-trigger';
        cotTrigger.title = 'Show reasoning and sources';
        cotTrigger.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14a2 2 0 110-4 2 2 0 010 4zm1-7h-2v5h2V9z" fill="currentColor"/></svg>';

        cotTrigger.addEventListener('click', async () => {
            // If dropdown exists, toggle visibility
            let dropdown = contentWrapper.querySelector('.reasoning-dropdown');
            if (dropdown) {
                const isOpen = dropdown.classList.toggle('open');
                return;
            }

            // Create placeholder dropdown while loading
            dropdown = document.createElement('div');
            dropdown.className = 'reasoning-dropdown';
            dropdown.innerHTML = '<div class="rd-header"><div class="rd-tab active">Reasoning</div><div class="rd-tab">Sources</div></div><div class="rd-body">Loading...</div>';
            contentWrapper.appendChild(dropdown);
            requestAnimationFrame(() => dropdown.classList.add('open'));

            try {
                const res = await fetch(apiUrl('/api/chat'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: opts.userMessage || '', session_id: activeSession, explain: true })
                });
                const d = await res.json();
                let parsed = d.explain || d;

                // Build full dropdown content
                dropdown.innerHTML = '';
                const header = document.createElement('div'); header.className = 'rd-header';
                const tabReason = document.createElement('div'); tabReason.className = 'rd-tab active'; tabReason.textContent = 'Reasoning';
                const tabSources = document.createElement('div'); tabSources.className = 'rd-tab'; tabSources.textContent = 'Sources';
                header.appendChild(tabReason); header.appendChild(tabSources);

                const bodyDiv = document.createElement('div'); bodyDiv.className = 'rd-body';
                const reasoningBlock = document.createElement('div'); reasoningBlock.className = 'rd-reasoning';
                const sourcesBlock = document.createElement('div'); sourcesBlock.className = 'rd-sources'; sourcesBlock.style.display = 'none';

                if (parsed) {
                    reasoningBlock.textContent = parsed.chain_of_thought || parsed.raw || 'No reasoning available.';
                    if (parsed.sources && Array.isArray(parsed.sources) && parsed.sources.length) {
                        parsed.sources.forEach(s => {
                            const sitem = document.createElement('div');
                            sitem.className = 'rd-source-item';
                            if (typeof s === 'object') {
                                sitem.innerHTML = `<strong>${s.id ? '['+s.id+'] ' : ''}${s.title || ''}</strong><div style="font-size:0.9rem;color:var(--link-color);margin-top:6px">${(s.snippet||'').slice(0,300)}</div>`;
                            } else {
                                sitem.textContent = s;
                            }
                            sourcesBlock.appendChild(sitem);
                        });
                    } else {
                        sourcesBlock.textContent = 'No sources available.';
                    }
                } else {
                    reasoningBlock.textContent = 'No explanation available.';
                    sourcesBlock.textContent = 'No sources available.';
                }

                bodyDiv.appendChild(reasoningBlock);
                bodyDiv.appendChild(sourcesBlock);
                dropdown.appendChild(header);
                dropdown.appendChild(bodyDiv);

                // tab switching
                tabReason.addEventListener('click', () => { tabReason.classList.add('active'); tabSources.classList.remove('active'); reasoningBlock.style.display='block'; sourcesBlock.style.display='none'; });
                tabSources.addEventListener('click', () => { tabSources.classList.add('active'); tabReason.classList.remove('active'); reasoningBlock.style.display='none'; sourcesBlock.style.display='block'; });

            } catch (e) {
                console.error('Explain error', e);
                dropdown.querySelector('.rd-body').textContent = 'Failed to load explanation.';
            }
        });

        contentWrapper.appendChild(cotTrigger);
    }

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return msgDiv; // return the element for progressive updates
}

async function startNewChat() {
    activeSession = null;
    chatHistory.innerHTML = '';
    body.classList.add('chat-started');
    await renderChatList();
}

// Fallback fetch-based streaming implementation used when EventSource is unavailable
async function handleFetchStreamFallback(userMessage, assistantEl, contentEl) {
    try {
        const res = await fetch(apiUrl('/api/chat/stream'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage, session_id: activeSession })
        });

        if (!res.ok) {
            const errorBody = await res.text();
            throw new Error(errorBody || 'Stream request failed');
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let buffer = '';
        while (!done) {
            const { value, done: d } = await reader.read();
            done = d;
            if (value) {
                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split('\n\n');
                buffer = parts.pop();
                for (const part of parts) {
                    const line = part.replace(/^data:\s*/i, '');
                    contentEl.textContent += line;
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }
            }
        }

        // After stream completes, request explanation similarly
        try {
            const explainRes = await fetch(apiUrl('/api/chat'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage, session_id: activeSession, explain: true })
            });
            if (explainRes.ok) {
                const explainData = await explainRes.json();
                const parsed = explainData.explain || explainData;
                const detailsDiv = document.createElement('div');
                detailsDiv.className = 'message-details';
                if (parsed) {
                    if (parsed.chain_of_thought) {
                        const h = document.createElement('div');
                        h.className = 'cot-block';
                        h.textContent = parsed.chain_of_thought;
                        detailsDiv.appendChild(h);
                    }
                    if (parsed.sources && Array.isArray(parsed.sources)) {
                        const s = document.createElement('div');
                        s.className = 'cot-sources';
                        const ul = document.createElement('ul');
                        parsed.sources.forEach(src => {
                            const li = document.createElement('li');
                            li.textContent = `${src.id || ''} — ${src.title || ''} — ${src.snippet || ''}`;
                            ul.appendChild(li);
                        });
                        s.appendChild(ul);
                        detailsDiv.appendChild(s);
                    }
                }
                assistantEl.appendChild(detailsDiv);
            }
        } catch (e) {
            console.warn('Explain failed after fetch stream', e);
        }
    } catch (e) {
        console.error('Fetch stream fallback failed', e);
        contentEl.textContent = 'Error: streaming failed.';
    }
}

// Function to send message to backend and handle response
async function handleUserMessage(userMessage) {
    body.classList.add('chat-started');
    sendMessage(userMessage, true);
    try {
        if (STREAM_MODE) {
            // Use EventSource-based SSE flow: POST to /chat/stream/start to get a stream_id,
            // then open EventSource at /chat/stream/{stream_id} to receive tokens.
            const assistantEl = sendMessage('', false, { userMessage });
            assistantEl.classList.add('typing');
            const contentEl = assistantEl.querySelector('.message-content');
            const avatarEl = assistantEl.querySelector('.message-avatar');
            // add typing indicator near avatar
            const typingIndicator = document.createElement('span');
            typingIndicator.className = 'typing-indicator';
            typingIndicator.innerHTML = '<span></span><span></span><span></span>';
            avatarEl.appendChild(typingIndicator);

            // show a small spinner while stream starts
            const spinner = document.createElement('span');
            spinner.className = 'spinner';
            avatarEl.appendChild(spinner);

            // Start the stream and obtain id
            const startRes = await fetch(apiUrl('/api/chat/stream/start'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage, session_id: activeSession })
            });
            if (!startRes.ok) {
                // fallback to legacy fetch streaming endpoint
                console.warn('Stream start failed; falling back to fetch streaming');
                return await handleFetchStreamFallback(userMessage, assistantEl, contentEl);
            }

            const startData = await startRes.json();
            if (startData.session_id) activeSession = startData.session_id;
            const streamId = startData.stream_id;
            const sseUrl = apiUrl(`/api/chat/stream/${streamId}`);

            if (window.EventSource) {
                const es = new EventSource(sseUrl);
                es.onmessage = (evt) => {
                    // default message events carry token chunks
                    // remove spinner on first token
                    if (spinner && spinner.parentNode) spinner.remove();
                    contentEl.textContent += evt.data;
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                };
                es.addEventListener('done', (evt) => {
                    try {
                        const payload = JSON.parse(evt.data);
                        // payload.response contains the full assembled response
                        contentEl.textContent = payload.response;
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    } catch (e) {
                        console.warn('Invalid done payload', e);
                    }
                    // cleanup typing indicator
                    assistantEl.classList.remove('typing');
                    const ti = avatarEl.querySelector('.typing-indicator'); if (ti) ti.remove();
                    if (spinner && spinner.parentNode) spinner.remove();
                    es.close();
                    // Optionally fetch explanation (structured sources)
                    fetch(apiUrl('/api/chat'), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: userMessage, session_id: activeSession, explain: true })
                    }).then(r => r.ok ? r.json() : null).then(d => {
                        if (!d) return;
                        const parsed = d.explain || d;
                        const detailsDiv = document.createElement('div');
                        detailsDiv.className = 'message-details';
                        if (parsed) {
                            if (parsed.chain_of_thought) {
                                const h = document.createElement('div');
                                h.className = 'cot-block';
                                h.textContent = parsed.chain_of_thought;
                                detailsDiv.appendChild(h);
                            }
                            if (parsed.sources && Array.isArray(parsed.sources)) {
                                const s = document.createElement('div');
                                s.className = 'cot-sources';
                                const ul = document.createElement('ul');
                                parsed.sources.forEach(src => {
                                    const li = document.createElement('li');
                                    li.textContent = `${src.id || ''} — ${src.title || ''} — ${src.snippet || ''}`;
                                    ul.appendChild(li);
                                });
                                s.appendChild(ul);
                                detailsDiv.appendChild(s);
                            }
                        }
                        assistantEl.appendChild(detailsDiv);
                    }).catch(e => console.warn('Explain fetch failed', e));
                });
                es.onerror = (e) => {
                    console.error('SSE error', e);
                    assistantEl.classList.remove('typing');
                    const ti = avatarEl.querySelector('.typing-indicator'); if (ti) ti.remove();
                    if (spinner && spinner.parentNode) spinner.remove();
                    es.close();
                };
            } else {
                // Browser doesn't support EventSource; fallback to fetch stream
                await handleFetchStreamFallback(userMessage, assistantEl, contentEl);
            }

            await renderChatList();
        } else {
            const res = await fetch(apiUrl("/api/chat"), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMessage, session_id: activeSession })
            });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || 'Chat request failed');
            }
            if (data.session_id) {
                activeSession = data.session_id;
            }
            sendMessage(data.response, false, { userMessage });
            await renderChatList();
        }
    } catch (err) {
        console.error(err);
        sendMessage('Error: Could not connect to backend.', false);
    }
}

// Initial prompt input (first message)
initialPromptInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter' && initialPromptInput.value.trim() !== '') {
        const userMessage = initialPromptInput.value.trim();
        body.classList.add('chat-started');
        initialPromptInput.value = '';
        handleUserMessage(userMessage);
    }
});

// Main chat input (subsequent messages)
promptInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter' && promptInput.value.trim() !== '') {
        const userMessage = promptInput.value.trim();
        promptInput.value = '';
        handleUserMessage(userMessage);
    }
});

// Fetch one chat’s history
async function openChat(sessionId) {
    activeSession = sessionId;
    let res = await fetch(apiUrl(`/api/chats/${sessionId}`));
    if (!res.ok) return;
    let chat = await res.json();

    chatHistory.innerHTML = "";
    body.classList.add('chat-started');
    chat.messages.forEach(msg => {
        sendMessage(msg.text, msg.role === "user");
    });

    await renderChatList();
}

// Fetch all chats for sidebar
async function renderChatList() {
    try {
        let res = await fetch(apiUrl("/api/chats"));
        if (!res.ok) return;
        let sessions = await res.json();
        chatsList.innerHTML = "";
        sessions.forEach(sess => {
            let li = document.createElement("li");
            li.className = "chats-list-item";
            if (sess.session_id === activeSession) li.classList.add("active");
            li.onclick = () => openChat(sess.session_id);

            // small icon + title layout
            const icon = document.createElement('div');
            icon.className = 'chat-icon';
            icon.textContent = sess.title ? sess.title.charAt(0).toUpperCase() : 'C';
            const title = document.createElement('div');
            title.className = 'chat-title';
            title.textContent = sess.title;

            li.appendChild(icon);
            li.appendChild(title);
            chatsList.appendChild(li);
        });

        // apply search filter if present
        if (sidebarSearch && sidebarSearch.value.trim()) {
            const q = sidebarSearch.value.trim().toLowerCase();
            Array.from(chatsList.children).forEach(li => {
                const t = (li.querySelector('.chat-title')?.textContent || '').toLowerCase();
                li.style.display = t.includes(q) ? '' : 'none';
            });
        }
    } catch (err) {
        console.error("Unable to load chats", err);
    }
}

if (sidebarSearch) {
    sidebarSearch.addEventListener('input', () => renderChatList());
}

renderChatList();
// Initialize authentication state (loads current user if token present)
initAuth();

// Sidebar action handlers
const saveBtn = document.getElementById('save-chat');
const exportBtn = document.getElementById('export-chat');
const importBtn = document.getElementById('import-chat');
const clearBtn = document.getElementById('clear-history');

if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        const title = prompt('Enter chat title:') || 'Saved chat';
        const res = await fetch(apiUrl('/api/chats'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, message: '' })
        });
        if (res.ok) {
            const d = await res.json();
            alert('Saved as session ' + d.session_id);
            await renderChatList();
        } else {
            alert('Save failed');
        }
    });
}

if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
        if (!activeSession) return alert('Open a chat to export.');
        const res = await fetch(apiUrl(`/api/chats/${activeSession}`));
        if (!res.ok) return alert('Unable to fetch session');
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.title || 'chat'}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    });
}

if (importBtn) {
    importBtn.addEventListener('click', () => {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.json';
        fileInput.onchange = async (e) => {
            const f = e.target.files[0];
            if (!f) return;
            const text = await f.text();
            try {
                const obj = JSON.parse(text);
                // Render locally as a new chat (no server persistence)
                activeSession = null;
                chatHistory.innerHTML = '';
                body.classList.add('chat-started');
                (obj.messages || []).forEach(m => sendMessage(m.text || m.content || '', m.role === 'user'));
                await renderChatList();
            } catch (err) {
                alert('Invalid JSON');
            }
        };
        fileInput.click();
    });
}

if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (confirm('Clear chat view? This does not delete server sessions.')) {
            activeSession = null;
            chatHistory.innerHTML = '';
            renderChatList();
        }
    });
}
