/* --- Configuration & State --- */
const API_BASE = window.__LEXIGPT_API__ || (window.location.origin.startsWith('http') ? '' : 'http://localhost:5000');
const state = {
    authToken: localStorage.getItem('authToken'),
    refreshToken: localStorage.getItem('refreshToken'),
    user: null,
    activeSession: null,
    streamMode: localStorage.getItem('STREAM_MODE') === 'true',
    sidebarExpanded: localStorage.getItem('SIDEBAR_EXPANDED') !== 'false',
    agentEventSource: null
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
    // Modals
    modals: {
        overlay: document.getElementById('modal-overlay'),
        auth: document.getElementById('auth-modal-card'),
        profile: document.getElementById('profile-card'),
        agent: document.getElementById('agent-modal')
    },
    // Sidebar Buttons
    authGroup: document.getElementById('sidebar-auth-group'),
    userProfile: document.getElementById('user-profile-trigger'),
    logoutBtn: document.getElementById('sidebar-logout-btn')
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
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) sendBtn.addEventListener('click', submitMessage);
    if (elements.promptInput) elements.promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitMessage();
    });
    
    // File Upload
    const uploadIcon = document.getElementById('upload-icon');
    if (uploadIcon && elements.fileInput) uploadIcon.addEventListener('click', () => elements.fileInput.click());
    if (elements.fileInput) elements.fileInput.addEventListener('change', handleFileUpload);

    // Sidebar Toggles
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    if (sidebarToggleBtn) sidebarToggleBtn.addEventListener('click', toggleSidebar);
    const newChatBtn = document.querySelector('.new-chat-btn');
    if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);

    // Sidebar Auth Buttons
    const sidebarLoginBtn = document.getElementById('sidebar-login-btn');
    if (sidebarLoginBtn) sidebarLoginBtn.addEventListener('click', () => showModal('auth', 'login'));
    const sidebarRegisterBtn = document.getElementById('sidebar-register-btn');
    if (sidebarRegisterBtn) sidebarRegisterBtn.addEventListener('click', () => showModal('auth', 'register'));
    if (elements.logoutBtn) elements.logoutBtn.addEventListener('click', handleLogout);

    // Auth Modals logic
    // Note: some pages use different IDs. Use null-checks to avoid runtime errors.
    const loginTrigger = document.getElementById('login-btn');
    if (loginTrigger) loginTrigger.addEventListener('click', () => showModal('auth', 'login'));
    const userProfileEls = document.querySelectorAll('.user-profile');
    userProfileEls.forEach(el => el.addEventListener('click', () => showModal('profile')));
    const showRegister = document.getElementById('show-register');
    if (showRegister) showRegister.addEventListener('click', () => toggleAuthMode('register'));
    const showLogin = document.getElementById('show-login');
    if (showLogin) showLogin.addEventListener('click', () => toggleAuthMode('login'));
    
    // Agent Logs
    const agentBtn = document.getElementById('sidebar-agent-btn');
    if (agentBtn) agentBtn.addEventListener('click', openAgentModal);
    const agentStart = document.getElementById('agent-start');
    if (agentStart) agentStart.addEventListener('click', startAgent);
    const agentStop = document.getElementById('agent-stop');
    if (agentStop) agentStop.addEventListener('click', stopAgent);
    const agentClear = document.getElementById('agent-clear');
    if (agentClear) agentClear.addEventListener('click', () => { const c = document.getElementById('agent-log-container'); if(c) c.innerHTML = ''; });
    
    // Modal Closers
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', hideModals);
    });
    if (elements.modals.overlay) {
        elements.modals.overlay.addEventListener('click', (e) => {
            if (e.target === elements.modals.overlay) hideModals();
        });
    }

    // Auth Submissions
    document.getElementById('login-submit').addEventListener('click', handleLogin);
    document.getElementById('register-submit').addEventListener('click', handleRegister);
    document.getElementById('settings-logout-all').addEventListener('click', handleLogout);

    // Theme (Top Right)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

    // Stream Toggle (if present) - toggles streaming response mode
    const streamToggle = document.getElementById('stream-toggle');
    if (streamToggle) {
        streamToggle.addEventListener('click', () => {
            state.streamMode = !state.streamMode;
            localStorage.setItem('STREAM_MODE', state.streamMode ? 'true' : 'false');
            // update UI text if present
            if (state.streamMode) {
                streamToggle.textContent = 'Stream: On';
            } else {
                streamToggle.textContent = 'Stream: Off';
            }
            showToast(`Streaming ${state.streamMode ? 'enabled' : 'disabled'}`, 'info');
        });
        // initialize label
        streamToggle.textContent = state.streamMode ? 'Stream: On' : 'Stream: Off';
    }

    // Settings Navigation
    const settingsBtn = document.getElementById('sidebar-settings-btn');
    if (settingsBtn) settingsBtn.addEventListener('click', () => showView('settings'));
    const settingsBack = document.getElementById('settings-back');
    if (settingsBack) settingsBack.addEventListener('click', () => showView('chat'));

    // Sidebar Search filtering (client-side filter of loaded chat list)
    const sidebarSearch = document.getElementById('sidebar-search-input');
    if (sidebarSearch) {
        sidebarSearch.addEventListener('input', (e) => {
            const q = sidebarSearch.value.trim().toLowerCase();
            const items = document.querySelectorAll('.chats-list-item');
            items.forEach(li => {
                const txt = (li.textContent || '').toLowerCase();
                li.style.display = q === '' || txt.includes(q) ? '' : 'none';
            });
        });
    }
}

/* --- UI Helper Functions --- */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);
    
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
    document.getElementById('moon-icon').classList.toggle('hidden', !isLight);
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
    
    // UI Update: This triggers the input to move from center to bottom
    elements.app.classList.add('chat-active');
    
    appendMessage(text, 'user');
    
    const botMsgId = appendMessage('...', 'bot', true); 
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
        botContentEl.classList.remove('typing-indicator');
        
        // Render Reasoning / Sources
        if (data.explain || data.sources) {
            const cotHTML = renderReasoning(data);
            if (cotHTML) {
                const wrapper = document.createElement('div');
                wrapper.innerHTML = cotHTML;
                // Add click handlers for tabs
                const tabs = wrapper.querySelectorAll('.cot-tab');
                tabs.forEach(t => t.addEventListener('click', (e) => {
                    const mode = e.target.dataset.tab;
                    const contentDiv = wrapper.querySelector('.cot-content');
                    // Reset tabs
                    tabs.forEach(x => x.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    if (mode === 'reasoning') {
                        contentDiv.innerHTML = data.explain ? (data.explain.chain_of_thought || JSON.stringify(data.explain)) : 'No reasoning provided.';
                    } else {
                        // Sources
                        if (data.sources && data.sources.length) {
                             contentDiv.innerHTML = data.sources.map(s => 
                                 `<div class="source-item"><div class="source-title">${s.title || 'Document'}</div><div class="source-snippet">${s.snippet || '...'}</div></div>`
                             ).join('');
                        } else {
                            contentDiv.innerHTML = 'No sources cited.';
                        }
                    }
                }));
                botContentEl.parentElement.appendChild(wrapper);
            }
        }

    } catch (err) {
        botContentEl.textContent = "Error: " + err.message;
        botContentEl.parentElement.style.color = 'var(--danger)';
    }
    
    loadChats();
}

// Render helper for Chain of Thought / Sources
function renderReasoning(data) {
    // Initial content is reasoning if available, else sources
    const hasReasoning = !!data.explain;
    const initialText = hasReasoning ? (data.explain.chain_of_thought || 'Processing...') : 'Select a tab';
    
    return `
        <div class="cot-wrapper">
            <div class="cot-header">
                <div class="cot-tab active" data-tab="reasoning">Reasoning</div>
                <div class="cot-tab" data-tab="sources">Sources (${data.sources ? data.sources.length : 0})</div>
            </div>
            <div class="cot-content">
                ${initialText}
            </div>
        </div>
    `;
}

function appendMessage(text, role, isLoading = false) {
    const id = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.className = `chat-message ${role}-message`;
    div.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
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
    // Deselect sidebar items
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
    elements.app.classList.add('chat-active'); // Force input to bottom
    loadChats();
    
    const res = await fetch(`${API_BASE}/api/chats/${id}`);
    const data = await res.json();
    
    elements.chatHistory.innerHTML = '';
    data.messages.forEach(msg => appendMessage(msg.text, msg.role === 'user' ? 'user' : 'bot'));
}

/* --- Agent Logs Logic --- */
function openAgentModal() {
    showModal('agent');
    connectAgentStream();
}

function connectAgentStream() {
    if (state.agentEventSource) return; // already connected
    const container = document.getElementById('agent-log-container');
    
    state.agentEventSource = new EventSource(`${API_BASE}/api/agent/stream`);
    state.agentEventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const ts = new Date().toLocaleTimeString();
            entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#6366f1">${data.action || 'INFO'}</span>: ${JSON.stringify(data)}`;
            container.appendChild(entry);
            
            // Auto scroll
            if (!document.getElementById('agent-pause-autoscroll').checked) {
                container.scrollTop = container.scrollHeight;
            }
        } catch (err) { console.error('Log parse error', err); }
    };
}

async function startAgent() {
    await fetch(`${API_BASE}/api/agent/run`, { method: 'POST' });
}

async function stopAgent() {
    await fetch(`${API_BASE}/api/agent/stop`, { method: 'POST' });
    if (state.agentEventSource) {
        state.agentEventSource.close();
        state.agentEventSource = null;
    }
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
    if (isLoggedIn && state.user) {
        elements.authGroup.classList.add('hidden');
        elements.userProfile.classList.remove('hidden');
        elements.logoutBtn.classList.remove('hidden');
        
        document.getElementById('header-user-name').textContent = state.user.display_name || state.user.username;
        if (state.user.avatar_url) {
            document.getElementById('header-user-avatar').src = state.user.avatar_url;
        }
    } else {
        elements.authGroup.classList.remove('hidden');
        elements.userProfile.classList.add('hidden');
        elements.logoutBtn.classList.add('hidden');
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

async function handleRegister() {
    const u = document.getElementById('reg-username').value;
    const p = document.getElementById('reg-password').value;
    const d = document.getElementById('reg-display').value;
    
    try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p, display_name: d })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        
        state.authToken = data.token;
        state.user = data.user;
        localStorage.setItem('authToken', data.token);
        
        updateAuthUI(true);
        hideModals();
        showToast('Account created!', 'success');
    } catch(e) { showToast(e.message, 'error'); }
}

function handleLogout() {
    state.authToken = null;
    state.user = null;
    localStorage.removeItem('authToken');
    updateAuthUI(false);
    showToast('Logged out');
    showView('chat'); 
}

/* --- Modal Helpers --- */
function showModal(name, subType) {
    elements.modals.overlay.classList.remove('hidden');
    Object.values(elements.modals).forEach(el => {
        if(el && el !== elements.modals.overlay) el.classList.add('hidden');
    });
    
    if (elements.modals[name]) elements.modals[name].classList.remove('hidden');

    if (name === 'auth') toggleAuthMode(subType || 'login');
}

function hideModals() {
    elements.modals.overlay.classList.add('hidden');
    // Stop agent stream if closing agent modal
    if (state.agentEventSource) {
        state.agentEventSource.close();
        state.agentEventSource = null;
    }
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
    appendMessage(`[Uploaded Document: ${file.name}]`, 'user');
    elements.app.classList.add('chat-active');
}