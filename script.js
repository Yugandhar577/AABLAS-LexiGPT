/* --- Configuration & State --- */
const API_BASE = window.__LEXIGPT_API__ || (window.location.origin.startsWith('http') ? '' : 'http://localhost:5000');
const state = {
    authToken: localStorage.getItem('authToken'),
    refreshToken: localStorage.getItem('refreshToken'),
    user: null,
    activeSession: null,
    streamMode: localStorage.getItem('STREAM_MODE') === 'true',
    sidebarExpanded: localStorage.getItem('SIDEBAR_EXPANDED') !== 'false' // default true
};

/* --- UI Elements --- */
const elements = {
    app: document.body,
    sidebar: document.getElementById('app-sidebar'),
    chatView: document.getElementById('chat-view'),
    chatHistory: document.getElementById('chat-history'),
    promptInput: document.getElementById('prompt-input'),
    initialState: document.getElementById('initial-content'),
    fileInput: document.getElementById('file-upload-input'),
    modals: {
        overlay: document.getElementById('modal-overlay'),
        auth: document.getElementById('auth-modal-card'),
        profile: document.getElementById('profile-card'),
        agent: document.getElementById('agent-modal')
    }
};

/* --- Core Initialization --- */
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    initSidebar();
    await initAuth();
    loadChats();
    setupEventListeners();
});

/* --- Event Listeners Setup --- */
function setupEventListeners() {
    // Input Handling
    document.getElementById('send-btn').addEventListener('click', submitMessage);
    elements.promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitMessage();
    });
    
    // File Upload
    document.getElementById('upload-icon').addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileUpload);

    // Sidebar Toggles
    document.getElementById('sidebar-toggle-btn').addEventListener('click', toggleSidebar);
    document.querySelector('.new-chat-btn').addEventListener('click', startNewChat);

    // Auth & Modals
    document.getElementById('login-btn').addEventListener('click', () => showModal('auth', 'login'));
    document.querySelector('.user-profile').addEventListener('click', () => showModal('profile'));
    document.getElementById('show-register').addEventListener('click', () => toggleAuthMode('register'));
    document.getElementById('show-login').addEventListener('click', () => toggleAuthMode('login'));
    
    // Modal Closers
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', hideModals);
    });
    elements.modals.overlay.addEventListener('click', (e) => {
        if (e.target === elements.modals.overlay) hideModals();
    });

    // Auth Submissions
    document.getElementById('login-submit').addEventListener('click', handleLogin);
    document.getElementById('register-submit').addEventListener('click', handleRegister);
    document.getElementById('settings-logout-all').addEventListener('click', handleLogout);

    // Theme
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Settings Navigation
    document.getElementById('sidebar-settings-btn').addEventListener('click', () => showView('settings'));
    document.getElementById('settings-back').addEventListener('click', () => showView('chat'));
}

/* --- UI Helper Functions --- */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`; // Safe for simple text
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showView(viewName) {
    if (viewName === 'settings') {
        document.getElementById('settings-page').classList.remove('hidden');
        document.getElementById('chat-view').classList.add('hidden');
    } else {
        document.getElementById('settings-page').classList.add('hidden');
        document.getElementById('chat-view').classList.remove('hidden');
    }
}

function toggleTheme() {
    const isLight = document.body.getAttribute('data-theme') === 'light';
    const newTheme = isLight ? 'dark' : 'light';
    document.body.setAttribute('data-theme', newTheme);
    document.getElementById('moon-icon').classList.toggle('hidden', !isLight); // if becoming dark, show moon? No, show sun in dark mode usually
    document.getElementById('sun-icon').classList.toggle('hidden', isLight);
    localStorage.setItem('theme', newTheme);
}

function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.body.setAttribute('data-theme', saved);
    if(saved === 'light') {
        document.getElementById('moon-icon').classList.add('hidden');
        document.getElementById('sun-icon').classList.remove('hidden');
    }
}

/* --- Sidebar Logic --- */
function toggleSidebar() {
    state.sidebarExpanded = !state.sidebarExpanded;
    localStorage.setItem('SIDEBAR_EXPANDED', state.sidebarExpanded);
    updateSidebarUI();
}

function initSidebar() {
    // Check if mobile
    if (window.innerWidth < 768) state.sidebarExpanded = false;
    updateSidebarUI();
}

function updateSidebarUI() {
    if (state.sidebarExpanded) {
        elements.sidebar.classList.remove('collapsed');
        elements.sidebar.classList.add('expanded');
    } else {
        elements.sidebar.classList.add('collapsed');
        elements.sidebar.classList.remove('expanded');
    }
}

/* --- Chat Logic --- */
async function submitMessage() {
    const text = elements.promptInput.value.trim();
    if (!text) return;
    
    elements.promptInput.value = '';
    
    // UI Update
    if (!state.activeSession) {
        elements.app.classList.add('chat-active');
    }
    
    appendMessage(text, 'user');
    
    // Bot Placeholder
    const botMsgId = appendMessage('...', 'bot', true); // returns ID
    const botContentEl = document.getElementById(botMsgId).querySelector('.message-bubble');

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': state.authToken ? `Bearer ${state.authToken}` : ''
            },
            body: JSON.stringify({ message: text, session_id: state.activeSession })
        });

        const data = await res.json();
        
        if (!res.ok) throw new Error(data.error || 'Failed to get response');

        state.activeSession = data.session_id;
        botContentEl.textContent = data.response;
        
        // Add "Reasoning" button if data exists
        if (data.explain || data.sources) {
            addReasoningTrigger(botContentEl.parentElement, data);
        }

    } catch (err) {
        botContentEl.textContent = "Error: " + err.message;
        botContentEl.parentElement.style.color = 'var(--danger)';
    }
    
    loadChats(); // Refresh sidebar list
}

function appendMessage(text, role, isLoading = false) {
    const id = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.className = `chat-message ${role}-message`;
    div.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    // Set Avatar Content
    if (role === 'user') {
        if (state.user && state.user.avatar_url) {
            avatar.innerHTML = `<img src="${state.user.avatar_url}" style="width:100%;height:100%;border-radius:6px;">`;
        } else {
            avatar.textContent = 'You';
        }
    } else {
        avatar.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/></svg>';
    }

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    if (isLoading) bubble.classList.add('typing-indicator');

    div.appendChild(avatar);
    div.appendChild(bubble);
    
    elements.chatHistory.appendChild(div);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    return id;
}

function startNewChat() {
    state.activeSession = null;
    elements.chatHistory.innerHTML = '';
    elements.app.classList.remove('chat-active');
    // Deselect active sidebar items
    document.querySelectorAll('.chats-list-item').forEach(el => el.classList.remove('active'));
}

async function loadChats() {
    try {
        const res = await fetch(`${API_BASE}/api/chats`);
        if (!res.ok) return;
        const chats = await res.json();
        const list = document.getElementById('chats-list');
        list.innerHTML = '';
        
        chats.forEach(chat => {
            const li = document.createElement('li');
            li.className = `chats-list-item ${chat.session_id === state.activeSession ? 'active' : ''}`;
            li.innerHTML = `
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span>${chat.title || 'New Consultation'}</span>
            `;
            li.onclick = () => loadSession(chat.session_id);
            list.appendChild(li);
        });
    } catch (e) { console.warn('Load chats failed', e); }
}

async function loadSession(id) {
    state.activeSession = id;
    elements.app.classList.add('chat-active');
    loadChats(); // Update active state in sidebar
    
    const res = await fetch(`${API_BASE}/api/chats/${id}`);
    const data = await res.json();
    
    elements.chatHistory.innerHTML = '';
    data.messages.forEach(msg => appendMessage(msg.text, msg.role === 'user' ? 'user' : 'bot'));
}

/* --- Auth Logic --- */
async function initAuth() {
    if (!state.authToken) return updateAuthUI(false);
    
    try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${state.authToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            state.user = data.user;
            updateAuthUI(true);
        } else {
            handleLogout();
        }
    } catch (e) { handleLogout(); }
}

function updateAuthUI(isLoggedIn) {
    const loginBtn = document.getElementById('login-btn');
    const profileTrigger = document.querySelector('.user-profile');
    
    if (isLoggedIn && state.user) {
        loginBtn.classList.add('hidden');
        profileTrigger.classList.remove('hidden');
        document.getElementById('header-user-name').textContent = state.user.display_name || state.user.username;
        if (state.user.avatar_url) {
            document.getElementById('header-user-avatar').src = state.user.avatar_url;
        }
    } else {
        loginBtn.classList.remove('hidden');
        profileTrigger.classList.add('hidden');
    }
}

async function handleLogin() {
    const u = document.getElementById('login-username').value;
    const p = document.getElementById('login-password').value;
    
    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        
        state.authToken = data.token;
        state.refreshToken = data.refresh_token;
        state.user = data.user;
        
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('refreshToken', data.refresh_token);
        
        updateAuthUI(true);
        hideModals();
        showToast('Successfully logged in', 'success');
        
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function handleLogout() {
    state.authToken = null;
    state.user = null;
    localStorage.removeItem('authToken');
    updateAuthUI(false);
    showToast('Logged out');
    showView('chat'); // Reset to main view
}

/* --- Modal Helpers --- */
function showModal(name, subType) {
    elements.modals.overlay.classList.remove('hidden');
    // hide all cards first
    Object.values(elements.modals).forEach(el => {
        if(el && el !== elements.modals.overlay) el.classList.add('hidden');
    });
    
    // show specific card
    if (elements.modals[name]) elements.modals[name].classList.remove('hidden');

    if (name === 'auth') toggleAuthMode(subType || 'login');
}

function hideModals() {
    elements.modals.overlay.classList.add('hidden');
}

function toggleAuthMode(mode) {
    const loginForm = document.getElementById('login-form');
    const regForm = document.getElementById('register-form');
    if (mode === 'login') {
        loginForm.classList.remove('hidden');
        regForm.classList.add('hidden');
    } else {
        loginForm.classList.add('hidden');
        regForm.classList.remove('hidden');
    }
}

/* --- File Upload --- */
function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    showToast(`Uploaded: ${file.name}`, 'success');
    // Add logic here to actually send file to backend
    // For now, simulating user message
    appendMessage(`[Uploaded Document: ${file.name}]`, 'user');
    elements.app.classList.add('chat-active');
}