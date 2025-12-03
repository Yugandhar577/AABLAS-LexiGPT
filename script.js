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
        agent: document.getElementById('agent-modal'),
        docgen: document.getElementById('docgen-modal'),
        pdfViewer: document.getElementById('pdf-viewer-modal')
    },
    // Sidebar Buttons
    authGroup: document.getElementById('sidebar-auth-group'),
    userProfile: document.getElementById('user-profile-trigger'),
    logoutBtn: document.getElementById('sidebar-logout-btn')
};

/* --- Core Initialization --- */
document.addEventListener('DOMContentLoaded', async () => {
    try {
        initTheme();
        initSidebar();
        await initAuth();
        await loadChats();
        setupEventListeners();
        
        // Save scroll position on scroll
        if (elements.chatHistory) {
            elements.chatHistory.addEventListener('scroll', () => {
                sessionStorage.setItem('chatScrollPos', elements.chatHistory.scrollTop);
            });
        }
    } catch (err) {
        console.error('Initialization error:', err);
        showToast('Failed to initialize app: ' + err.message, 'error');
    }
});

/* --- Event Listeners Setup --- */
function setupEventListeners() {
    // Input Handling
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) sendBtn.addEventListener('click', submitMessage);
    if (elements.promptInput) {
        elements.promptInput.addEventListener('keydown', (e) => {
            // Cmd+Enter or Ctrl+Enter to send
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                submitMessage();
            } else if (e.key === 'Enter' && !e.shiftKey) {
                submitMessage();
            }
        });
    }
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Cmd+K / Ctrl+K to focus search
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('sidebar-search-input');
            if (searchInput) searchInput.focus();
        }
        // Escape to close modals
        if (e.key === 'Escape') {
            hideModals();
        }
    });
    
    // File Upload
    document.getElementById('upload-icon').addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    const chatView = document.getElementById('chat-view');
    if (chatView) {
        chatView.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            chatView.classList.add('drag-over');
        });
        chatView.addEventListener('dragleave', () => {
            chatView.classList.remove('drag-over');
        });
        chatView.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            chatView.classList.remove('drag-over');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                handleMultipleFileUpload(e.dataTransfer.files);
            }
        });
    }

    // Sidebar Toggles
    document.getElementById('sidebar-toggle-btn').addEventListener('click', toggleSidebar);
    document.querySelector('.new-chat-btn').addEventListener('click', startNewChat);

    // Sidebar Auth Buttons
    document.getElementById('sidebar-login-btn').addEventListener('click', () => showModal('auth', 'login'));
    document.getElementById('sidebar-register-btn').addEventListener('click', () => showModal('auth', 'register'));
    elements.logoutBtn.addEventListener('click', handleLogout);

    // Auth Modals logic
    document.getElementById('show-register').addEventListener('click', () => toggleAuthMode('register'));
    document.getElementById('show-login').addEventListener('click', () => toggleAuthMode('login'));
    
    // Profile modal
    const userProfileBtn = document.getElementById('user-profile-trigger');
    if (userProfileBtn) userProfileBtn.addEventListener('click', () => showModal('profile'));
    
    const profileSaveBtn = document.getElementById('profile-save');
    if (profileSaveBtn) profileSaveBtn.addEventListener('click', handleProfileSave);
    const profileUploadBtn = document.getElementById('profile-upload-avatar');
    if (profileUploadBtn) profileUploadBtn.addEventListener('click', () => {
        const input = document.getElementById('profile-avatar-file');
        if (input) input.click();
    });
    const profileAvatarFile = document.getElementById('profile-avatar-file');
    if (profileAvatarFile) profileAvatarFile.addEventListener('change', handleAvatarUpload);
    
    // Agent Logs
    document.getElementById('sidebar-agent-btn').addEventListener('click', openAgentModal);
    document.getElementById('agent-start').addEventListener('click', startAgent);
    document.getElementById('agent-stop').addEventListener('click', stopAgent);
    document.getElementById('agent-clear').addEventListener('click', () => { document.getElementById('agent-log-container').innerHTML = ''; });
    // Show Reasoning toggle and refresh
    const reasoningToggle = document.getElementById('agent-show-reasoning');
    if (reasoningToggle) {
        reasoningToggle.addEventListener('change', (e) => {
            const panel = document.getElementById('agent-reasoning-container');
            if (e.target.checked) {
                panel.classList.remove('hidden');
                loadAgentReasoning();
            } else {
                panel.classList.add('hidden');
            }
        });
    }
    const reasoningRefresh = document.getElementById('agent-refresh-reasoning');
    if (reasoningRefresh) reasoningRefresh.addEventListener('click', loadAgentReasoning);
    
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

    // Theme (Top Right)
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

    // Settings Navigation
    document.getElementById('sidebar-settings-btn').addEventListener('click', () => showView('settings'));
    document.getElementById('settings-back').addEventListener('click', () => showView('chat'));
    
    // Settings Stream Toggle
    document.getElementById('settings-stream-default').checked = state.streamMode;
    document.getElementById('settings-stream-default').addEventListener('change', (e) => {
        state.streamMode = e.target.checked;
        localStorage.setItem('STREAM_MODE', state.streamMode);
        showToast(`Streaming is now ${state.streamMode ? 'ON' : 'OFF'}`);
    });

    // Delegated handler for next-step chips (insert into prompt when clicked)
    document.addEventListener('click', (e) => {
        const target = e.target;
        if (target && target.classList && target.classList.contains('chip')) {
            const text = target.textContent || '';
            const input = document.getElementById('prompt-input');
            if (input) {
                input.value = text;
                input.focus();
            }
        }
    });
    
    // Document Generation
    const docgenBtn = document.getElementById('sidebar-docgen-btn');
    if (docgenBtn) docgenBtn.addEventListener('click', () => showModal('docgen'));
    const docgenGenerateBtn = document.getElementById('docgen-generate');
    if (docgenGenerateBtn) docgenGenerateBtn.addEventListener('click', handleDocgenGenerate);
    
    // PDF viewer controls
    if (document.getElementById('pdf-prev-btn')) {
        document.getElementById('pdf-prev-btn').addEventListener('click', () => {
            if (pdfDoc && pdfPage > 1) {
                pdfPage--;
                renderPDFPage(pdfPage);
                updatePDFControls();
            }
        });
    }
    if (document.getElementById('pdf-next-btn')) {
        document.getElementById('pdf-next-btn').addEventListener('click', () => {
            if (pdfDoc && pdfPage < pdfDoc.numPages) {
                pdfPage++;
                renderPDFPage(pdfPage);
                updatePDFControls();
            }
        });
    }
    
    // Chat export
    if (document.getElementById('export-json-btn')) {
        document.getElementById('export-json-btn').addEventListener('click', exportChatAsJSON);
    }
    if (document.getElementById('export-pdf-btn')) {
        document.getElementById('export-pdf-btn').addEventListener('click', exportChatAsPDF);
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
        document.getElementById('sidebar-toggle-btn').innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>';
    } else {
        elements.sidebar.classList.add('collapsed');
        elements.sidebar.classList.remove('expanded');
        document.getElementById('sidebar-toggle-btn').innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>';
    }
}

/* --- Chat Logic --- */
async function submitMessage() {
    try {
        const text = elements.promptInput.value.trim();
        if (!text) return;
        
        elements.promptInput.value = '';
        
        // UI Update: This triggers the input to move from center to bottom
        elements.app.classList.add('chat-active');
        
        appendMessage(text, 'user');
        
        const botMsgId = appendMessage('', 'bot', true); 
        const botDiv = document.getElementById(botMsgId);
        const botContentEl = botDiv.querySelector('.message-bubble');

        // Save scroll position before fetching
        sessionStorage.setItem('chatScrollPos', elements.chatHistory.scrollHeight);

        try {
            const res = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': state.authToken ? `Bearer ${state.authToken}` : ''
                },
                body: JSON.stringify({ message: text, session_id: state.activeSession })
            });

            // Handle rate limiting
            if (res.status === 429) {
                throw new Error('Rate limited. Please wait a moment before sending another message.');
            }

            const data = await res.json();
            
            if (!res.ok) throw new Error(data.error || 'Failed to get response');

            state.activeSession = data.session_id;
            
            // If this is a document generation request, show Agent Logs and connect to agent stream
            if (data.is_document_generation) {
                botContentEl.textContent = data.response;
                botContentEl.classList.remove('typing-indicator');
                
                // Auto-open Agent Logs modal to show real-time progress
                showAgentLogsModal();
                
                // Connect to agent stream to see events as they happen
                connectAgentStream();
                
                return;
            }
            
            // Render markdown response
            if (typeof marked !== 'undefined' && data.response) {
                try {
                    botContentEl.innerHTML = marked.parse(data.response);
                } catch (e) {
                    botContentEl.textContent = data.response;
                }
            } else {
                botContentEl.textContent = data.response;
            }
            botContentEl.classList.remove('typing-indicator');
            
            // Update timestamp to current time
            const timestamp = botDiv.querySelector('.message-timestamp');
            if (timestamp) {
                const now = new Date();
                timestamp.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                timestamp.title = now.toLocaleString();
            }
            
            // Render Reasoning / Sources / Explainability
            if (data.explain || data.sources) {
                const cotHTML = renderReasoning(data);
                if (cotHTML) {
                    const wrapper = document.createElement('div');
                    wrapper.innerHTML = cotHTML;
                    
                    // Set initial content (Reasoning if available, else Sources)
                    let initialMode = data.explain ? 'reasoning' : 'sources';
                    
                    const tabs = wrapper.querySelectorAll('.cot-tab');
                    const contentDiv = wrapper.querySelector('.cot-content');
                    
                    const updateContent = (mode) => {
                        tabs.forEach(t => t.classList.remove('active'));
                        wrapper.querySelector(`[data-tab="${mode}"]`).classList.add('active');
                        
                        if (mode === 'reasoning') {
                            contentDiv.innerHTML = data.explain ? (data.explain.chain_of_thought || JSON.stringify(data.explain, null, 2)) : 'No reasoning provided.';
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
                    };
                    
                    // Add click handlers for tabs
                    tabs.forEach(t => t.addEventListener('click', (e) => {
                        updateContent(e.target.dataset.tab);
                    }));

                    // Initial render
                    updateContent(initialMode);
                    
                    botContentEl.parentElement.appendChild(wrapper);
                }
            }
            
        } catch (fetchErr) {
            botContentEl.textContent = "Error: " + fetchErr.message;
            botDiv.style.color = 'var(--danger)';
            showToast('Failed to get response: ' + fetchErr.message, 'error');
        }
        
        loadChats();
    } catch (outerErr) {
        showToast('Unexpected error: ' + outerErr.message, 'error');
        console.error('submitMessage error:', outerErr);
    }
}

// Render helper for Chain of Thought / Sources
function renderReasoning(data) {
    return `
        <div class="cot-wrapper">
            <div class="cot-header">
                <div class="cot-tab ${data.explain ? 'active' : ''}" data-tab="reasoning">Reasoning</div>
                <div class="cot-tab ${!data.explain ? 'active' : ''}" data-tab="sources">Sources (${data.sources ? data.sources.length : 0})</div>
            </div>
            <div class="cot-content">
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
    
    if (isLoading) {
        bubble.innerHTML = '<span class="typing-indicator">⠋ Thinking...</span>';
    } else {
        // Render markdown if marked.js is available, else plain text
        if (typeof marked !== 'undefined' && text) {
            try {
                bubble.innerHTML = marked.parse(text);
            } catch (e) {
                bubble.textContent = text;
            }
        } else {
            bubble.textContent = text;
        }
    }

    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    const now = new Date();
    timestamp.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    timestamp.title = now.toLocaleString();

    const messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-content-wrapper';
    messageWrapper.appendChild(bubble);
    messageWrapper.appendChild(timestamp);
    // Collapsible area for reasoning / plan attached to bot messages
    const extra = document.createElement('div');
    extra.className = 'message-extra';
    // Toggle control
    const extraToggle = document.createElement('button');
    extraToggle.className = 'extra-toggle btn-text';
    extraToggle.textContent = 'Show reasoning ▾';
    extraToggle.style.marginTop = '6px';
    extraToggle.style.display = role === 'bot' ? 'inline-block' : 'none';
    const extraContent = document.createElement('div');
    extraContent.className = 'extra-content hidden';
    extra.appendChild(extraToggle);
    extra.appendChild(extraContent);
    messageWrapper.appendChild(extra);

    // Toggle behavior
    extraToggle.addEventListener('click', (e) => {
        const open = !extraContent.classList.contains('hidden');
        if (open) {
            extraContent.classList.add('hidden');
            extraToggle.textContent = 'Show reasoning ▾';
        } else {
            extraContent.classList.remove('hidden');
            extraToggle.textContent = 'Hide reasoning ▴';
        }
    });
    
    // Add copy button for non-loading messages with content
    if (!isLoading && text && text.trim().length > 0 && role === 'bot') {
        // Add retry button
        const retryBtn = document.createElement('button');
        retryBtn.className = 'message-retry-btn';
        retryBtn.title = 'Regenerate message';
        retryBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2-8.83"/></svg>';
        retryBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                // Get the previous user message
                const previousUserMsg = div.previousElementSibling;
                if (previousUserMsg && previousUserMsg.classList.contains('user-message')) {
                    const userText = previousUserMsg.querySelector('.message-bubble').textContent;
                    // Re-submit the message
                    elements.promptInput.value = userText;
                    await submitMessage();
                }
            } catch (err) {
                showToast('Retry failed: ' + err.message, 'error');
            }
        });
        messageWrapper.appendChild(retryBtn);
    }
    
    if (!isLoading && text && text.trim().length > 0 && role !== 'bot') {
        // Add copy button for user messages
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-copy-btn';
        copyBtn.title = 'Copy message';
        copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>';
        copyBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                await navigator.clipboard.writeText(text);
                showToast('Copied to clipboard', 'success');
                copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                setTimeout(() => {
                    copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>';
                }, 1500);
            } catch (err) {
                showToast('Copy failed: ' + err.message, 'error');
            }
        });
        messageWrapper.appendChild(copyBtn);
    } else if (!isLoading && text && text.trim().length > 0 && role === 'bot') {
        // Add copy button for bot messages
        const copyBtn = document.createElement('button');
        copyBtn.className = 'message-copy-btn';
        copyBtn.title = 'Copy message';
        copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>';
        copyBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            try {
                await navigator.clipboard.writeText(text);
                showToast('Copied to clipboard', 'success');
                copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                setTimeout(() => {
                    copyBtn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>';
                }, 1500);
            } catch (err) {
                showToast('Copy failed: ' + err.message, 'error');
            }
        });
        messageWrapper.appendChild(copyBtn);
    }

    div.appendChild(avatar);
    div.appendChild(messageWrapper);
    
    elements.chatHistory.appendChild(div);
    
    // Auto-scroll to bottom or restore position
    const scrollPos = sessionStorage.getItem('chatScrollPos');
    if (scrollPos && !isLoading) {
        elements.chatHistory.scrollTop = parseInt(scrollPos);
    } else {
        elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    }
    
    return id;
}

// Attach reasoning/evaluation text to the last bot message's extra content
function attachReasoningToLastBot(itemHtml) {
    const botMsgs = document.querySelectorAll('.chat-message.bot-message');
    if (!botMsgs || botMsgs.length === 0) return false;
    const last = botMsgs[botMsgs.length - 1];
    const extraContent = last.querySelector('.extra-content');
    if (!extraContent) return false;
    // Append a block
    const block = document.createElement('div');
    block.style.padding = '8px 0';
    block.innerHTML = itemHtml;
    extraContent.appendChild(block);
    return true;
}

function renderPlanInChat(planObj) {
    // Create a plan card that looks like a bot message attachment
    const card = document.createElement('div');
    card.className = 'plan-card';
    const header = document.createElement('div');
    header.className = 'plan-header';
    header.innerHTML = `<strong>Planned Actions</strong> <span class="plan-summary" style="color:var(--text-muted);font-size:0.9rem;margin-left:8px">${planObj.rationale || ''}</span>`;
    card.appendChild(header);
    const list = document.createElement('ol');
    list.className = 'plan-steps';
    (planObj.steps || []).forEach(s => {
        const li = document.createElement('li');
        li.innerHTML = `<div style="font-weight:600">${escapeHtml(s.title || s.title)}</div><div style="color:var(--text-secondary);font-size:0.9rem">${escapeHtml(s.expectations || '')}</div>`;
        list.appendChild(li);
    });
    card.appendChild(list);
    // Next steps chips
    if (planObj.next_steps && planObj.next_steps.length) {
        const chips = document.createElement('div');
        chips.className = 'plan-chips';
        chips.style.marginTop = '8px';
        planObj.next_steps.forEach(ns => {
            const btn = document.createElement('button');
            btn.className = 'chip';
            btn.textContent = ns;
            btn.addEventListener('click', (e) => {
                elements.promptInput.value = ns;
                elements.promptInput.focus();
            });
            chips.appendChild(btn);
        });
        card.appendChild(chips);
    }

    // Insert as a bot-like system message at the bottom of chat
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-message bot-message plan-message';
    const avatar = document.createElement('div'); avatar.className = 'message-avatar'; avatar.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"/></svg>';
    const content = document.createElement('div'); content.className = 'message-content-wrapper';
    const bubble = document.createElement('div'); bubble.className = 'message-bubble'; bubble.appendChild(card);
    content.appendChild(bubble);
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    elements.chatHistory.appendChild(wrapper);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
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
            
            // Chat item with delete button
            const chatWrapper = document.createElement('div');
            chatWrapper.className = 'chat-item-wrapper';
            chatWrapper.style.display = 'flex';
            chatWrapper.style.alignItems = 'center';
            chatWrapper.style.width = '100%';
            chatWrapper.style.gap = '8px';
            
            const chatLink = document.createElement('div');
            chatLink.style.flex = '1';
            chatLink.style.cursor = 'pointer';
            chatLink.innerHTML = `
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span>${chat.title || 'New Consultation'}</span>
            `;
            chatLink.onclick = () => loadSession(chat.session_id);
            
            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.title = 'Delete chat';
            deleteBtn.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>';
            deleteBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm(`Delete "${chat.title}"?`)) {
                    try {
                        const delRes = await fetch(`${API_BASE}/api/chats/${chat.session_id}`, { method: 'DELETE' });
                        if (delRes.ok) {
                            showToast('Chat deleted', 'success');
                            if (state.activeSession === chat.session_id) {
                                startNewChat();
                            }
                            loadChats();
                        } else {
                            showToast('Failed to delete chat', 'error');
                        }
                    } catch (err) {
                        showToast('Delete failed: ' + err.message, 'error');
                    }
                }
            });
            
            chatWrapper.appendChild(chatLink);
            chatWrapper.appendChild(deleteBtn);
            li.appendChild(chatWrapper);
            li.onclick = null; // Remove old onclick
            
            list.appendChild(li);
        });
    } catch (e) { 
        console.warn('Load chats failed', e);
        showToast('Failed to load chats', 'error');
    }
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
    loadAgentHistory(); // Load past runs first
    connectAgentStream(); // Then listen for real-time updates
}

async function loadAgentHistory() {
    try {
        const res = await fetch(`${API_BASE}/api/agent/logs`);
        if (!res.ok) return;
        const logs = await res.json();
        const container = document.getElementById('agent-log-container');
        container.innerHTML = '';
        
        if (!logs || logs.length === 0) {
            container.innerHTML = '<div class="log-entry system">No agent runs yet.</div>';
            return;
        }
        
        logs.forEach(log => {
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const ts = new Date(log.timestamp || Date.now()).toLocaleTimeString();
            entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#6366f1">${log.action || 'action'}</span>: ${log.details || JSON.stringify(log)}`;
            container.appendChild(entry);
        });
    } catch (e) {
        console.error('Load agent history failed', e);
    }
}

function connectAgentStream() {
    if (state.agentEventSource) return; // already connected
    const container = document.getElementById('agent-log-container');
    
    state.agentEventSource = new EventSource(`${API_BASE}/api/agent/stream_events`);
    state.agentEventSource.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            const ts = new Date().toLocaleTimeString();

            // Handle structured event types
            if (data.type === 'file_download') {
                const url = data.url.startsWith('/') ? API_BASE + data.url : data.url;
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#059669">File</span>: <a href="${url}" download="${data.filename}">${data.filename}</a>`;
            } else if (data.type === 'next_steps') {
                // Render chips for next steps
                const steps = data.next_steps || [];
                const chips = steps.map(s => `<button class="chip">${s}</button>`).join(' ');
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <strong>Next Steps:</strong> ${chips}`;
            } else if (data.type === 'step_started') {
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#2563eb">Step started</span>: ${data.title} (${data.tool})`;
                // Also render an action card for this step
                renderActionCard({type:'step_started', step_id:data.step_id, title:data.title, tool:data.tool, input:data.input});
            } else if (data.type === 'step_result') {
                const ok = data.ok ? '<span style="color:green">OK</span>' : '<span style="color:red">FAIL</span>';
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#6b7280">Result</span>: ${data.title} ${ok} - ${data.logs || ''}`;
                renderActionCard({type:'step_result', step_id:data.step_id, title:data.title, ok:data.ok, logs:data.logs, output_preview:data.output_preview});
            } else if (data.type === 'planner_output') {
                // Planner output may include raw JSON; attempt to parse and render a plan card in chat
                let parsed = null;
                try {
                    if (typeof data.raw === 'string') {
                        parsed = JSON.parse(data.raw);
                    } else {
                        parsed = data.raw;
                    }
                } catch (e) {
                    // try to extract a JSON block
                    try {
                        const txt = data.raw || '';
                        const start = txt.indexOf('{');
                        const end = txt.lastIndexOf('}');
                        if (start !== -1 && end !== -1 && end > start) {
                            parsed = JSON.parse(txt.slice(start, end + 1));
                        }
                    } catch (e2) {
                        parsed = null;
                    }
                }

                if (parsed) {
                    try { renderPlanInChat(parsed); } catch (e) { /* ignore render errors */ }
                    entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <strong>Planner output</strong>: rendered plan in chat`;
                    renderActionCard({type:'planner', plan: parsed});
                } else {
                    const txt = typeof data.raw === 'string' ? data.raw : JSON.stringify(data.raw || data);
                    entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <pre style="white-space:pre-wrap; margin:0;">${escapeHtml(txt)}</pre>`;
                }
                // also add to reasoning panel if visible
                if (document.getElementById('agent-show-reasoning') && document.getElementById('agent-show-reasoning').checked) addReasoningEntryToPanel(data);

            } else if (data.type === 'reason' || data.type === 'run_complete' || data.type === 'evaluation') {
                // Render reasoning/evaluation as a collapsible card in the Agent logs
                renderReasoningCard(data);
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:var(--accent-primary);font-weight:600">${data.type.toUpperCase()}</span>`;
                renderActionCard({type: data.type, data: data});
            } else if (data.type === 'need_input') {
                // Render a friendly input form for required fields
                renderNeedInputForm(data);
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <strong>Awaiting input for step</strong>: ${data.title}`;
            } else if (data.type === 'agent_stopped') {
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> <span style="color:#ef4444">Agent stopped</span>`;
            } else {
                entry.innerHTML = `<span style="color:#6b7280">[${ts}]</span> ${JSON.stringify(data)}`;
            }

            container.appendChild(entry);

            // Auto scroll
            if (!document.getElementById('agent-pause-autoscroll').checked) {
                container.scrollTop = container.scrollHeight;
            }
        } catch (err) { /* console.error('Log parse error', err); */ }
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

function renderReasoningCard(data) {
    const container = document.getElementById('agent-log-container');
    if (!container) return;
    const card = document.createElement('div');
    card.className = 'reasoning-card';
    
    // Collapsible header
    const header = document.createElement('div');
    header.className = 'reasoning-header';
    header.style.cursor = 'pointer';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.justifyContent = 'space-between';
    
    const title = document.createElement('span');
    title.style.fontWeight = '700';
    title.style.color = 'var(--accent-primary)';
    title.textContent = data.type === 'evaluation' ? '✅ Evaluation' : data.type === 'reason' ? '💭 Reasoning' : '✓ Run Complete';
    header.appendChild(title);
    
    const toggle = document.createElement('span');
    toggle.textContent = '▾';
    toggle.style.color = 'var(--text-secondary)';
    toggle.style.fontSize = '1.2rem';
    header.appendChild(toggle);
    
    const content = document.createElement('div');
    content.className = 'reasoning-content';
    content.style.display = 'none';
    
    // Populate content
    if (data.type === 'evaluation') {
        const summary = escapeHtml(data.summary || data.result || '');
        const success = data.success ? '✅ SUCCESS' : '❌ FAILED';
        content.innerHTML = `<div style="margin-bottom:8px"><strong>${success}</strong></div><div>${summary}</div>`;
        if (data.sources && data.sources.length > 0) {
            const src = document.createElement('div');
            src.style.marginTop = '8px';
            src.style.borderTop = '1px solid var(--border-color)';
            src.style.paddingTop = '8px';
            src.innerHTML = '<strong>Sources:</strong>';
            data.sources.forEach(s => {
                const item = document.createElement('div');
                item.style.marginTop = '4px';
                item.style.fontSize = '0.9rem';
                item.innerHTML = `<span style="color:var(--accent-primary)">${escapeHtml(s.title || s.id || 'Source')}</span>: ${escapeHtml(s.snippet || '')}`;
                src.appendChild(item);
            });
            content.appendChild(src);
        }
    } else if (data.type === 'reason') {
        const txt = typeof data.reason === 'string' ? data.reason : JSON.stringify(data, null, 2);
        const pre = document.createElement('pre');
        pre.style.margin = '0';
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.fontSize = '0.9rem';
        pre.textContent = txt;
        content.appendChild(pre);
    } else if (data.type === 'run_complete') {
        const summary = escapeHtml(data.summary || JSON.stringify(data, null, 2));
        content.innerHTML = `<div>${summary}</div>`;
    }
    
    // Toggle behavior
    header.addEventListener('click', () => {
        const isOpen = content.style.display !== 'none';
        content.style.display = isOpen ? 'none' : 'block';
        toggle.textContent = isOpen ? '▾' : '▴';
    });
    
    card.appendChild(header);
    card.appendChild(content);
    container.appendChild(card);
    container.scrollTop = container.scrollHeight;
}

/* --- Auth Logic --- */
async function handleProfileSave() {
    try {
        const displayName = document.getElementById('profile-display').value;
        const bio = document.getElementById('profile-bio').value;
        
        if (!displayName || displayName.trim().length === 0) {
            showToast('Display name required', 'error');
            return;
        }
        
        const res = await fetch(`${API_BASE}/api/auth/update-profile`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.authToken}`
            },
            body: JSON.stringify({ display_name: displayName, bio: bio })
        });
        
        if (!res.ok) throw new Error('Failed to update profile');
        const data = await res.json();
        state.user = data.user;
        updateAuthUI(true);
        showToast('Profile updated', 'success');
        hideModals();
    } catch (e) {
        showToast('Profile update error: ' + e.message, 'error');
        console.error('Profile save error:', e);
    }
}

async function handleAvatarUpload(e) {
    try {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('avatar', file);
        
        const res = await fetch(`${API_BASE}/api/auth/upload-avatar`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.authToken}` },
            body: formData
        });
        
        if (!res.ok) throw new Error('Avatar upload failed');
        const data = await res.json();
        state.user = data.user;
        
        // Update preview
        const preview = document.getElementById('profile-avatar-preview');
        if (preview && data.user.avatar_url) {
            preview.src = data.user.avatar_url;
        }
        
        updateAuthUI(true);
        showToast('Avatar updated', 'success');
    } catch (e) {
        showToast('Avatar upload error: ' + e.message, 'error');
        console.error('Avatar upload error:', e);
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

function openMessageSearch() {
    const query = prompt('Search messages in current chat:');
    if (!query) return;
    
    const messages = document.querySelectorAll('.message-bubble');
    let found = 0;
    messages.forEach((msg, idx) => {
        const text = msg.textContent.toLowerCase();
        if (text.includes(query.toLowerCase())) {
            msg.style.backgroundColor = 'rgba(99, 102, 241, 0.2)';
            found++;
        } else {
            msg.style.backgroundColor = '';
        }
    });
    
    showToast(`Found ${found} message(s)`, found > 0 ? 'success' : 'info');
}

async function handleDocgenGenerate() {
    try {
        const docType = document.getElementById('docgen-type').value;
        const format = document.getElementById('docgen-format').value;
        const params = document.getElementById('docgen-params').value;
        
        if (!params) {
            showToast('Please enter document parameters', 'error');
            return;
        }
        
        showToast('Generating document...', 'info');
        
        const res = await fetch(`${API_BASE}/api/docgen`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': state.authToken ? `Bearer ${state.authToken}` : ''
            },
            body: JSON.stringify({ doc_type: docType, format: format, params: params })
        });
        
        if (!res.ok) throw new Error('Document generation failed');
        const data = await res.json();
        
        // Show download link
        const resultDiv = document.getElementById('docgen-result');
        const filename = data.filename || `document.${format}`;
        resultDiv.innerHTML = `
            <div style="padding:12px;background:var(--bg-card);border-radius:6px;border:1px solid var(--border-color);">
                <p>Document generated successfully!</p>
                <a href="${API_BASE}/api/docgen/download/${filename}" download class="btn-primary" style="display:inline-block;text-decoration:none;">
                    Download ${filename}
                </a>
            </div>
        `;
        showToast('Document ready for download', 'success');
    } catch (e) {
        showToast('Docgen error: ' + e.message, 'error');
        console.error('Docgen error:', e);
    }
}

// PDF Viewer state
let pdfDoc = null;
let pdfPage = 1;

async function viewPDF(pdfUrl) {
    try {
        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        if (typeof pdfjsLib !== 'undefined' && pdfjsLib.GlobalWorkerOptions) {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
        }
        
        const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
        pdfDoc = pdf;
        pdfPage = 1;
        showModal('pdf-viewer');
        renderPDFPage(pdfPage);
        updatePDFControls();
    } catch (e) {
        showToast('Failed to load PDF: ' + e.message, 'error');
    }
}

async function renderPDFPage(pageNum) {
    if (!pdfDoc) return;
    try {
        const page = await pdfDoc.getPage(pageNum);
        const canvas = document.getElementById('pdf-canvas');
        const ctx = canvas.getContext('2d');
        const viewport = page.getViewport({ scale: 1.5 });
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvasContext: ctx, viewport: viewport }).promise;
    } catch (e) {
        console.error('PDF render error:', e);
    }
}

function updatePDFControls() {
    if (!pdfDoc) return;
    document.getElementById('pdf-page-info').textContent = `Page ${pdfPage} of ${pdfDoc.numPages}`;
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
    try {
        const u = document.getElementById('login-username').value;
        const p = document.getElementById('login-password').value;
        
        if (!u || !p) {
            showToast('Please enter username and password', 'error');
            return;
        }
        
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Login failed');
        
        state.authToken = data.token;
        state.refreshToken = data.refresh_token;
        state.user = data.user;
        
        localStorage.setItem('authToken', data.token);
        localStorage.setItem('refreshToken', data.refresh_token);
        
        updateAuthUI(true);
        hideModals();
        showToast('Successfully logged in', 'success');
        
    } catch (e) {
        showToast('Login error: ' + e.message, 'error');
        console.error('Login error:', e);
    }
}

async function handleRegister() {
    try {
        const u = document.getElementById('reg-username').value;
        const p = document.getElementById('reg-password').value;
        const d = document.getElementById('reg-display').value;
        
        if (!u || !p || !d) {
            showToast('Please fill in all fields', 'error');
            return;
        }
        
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p, display_name: d })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Registration failed');
        
        state.authToken = data.token;
        state.user = data.user;
        localStorage.setItem('authToken', data.token);
        
        updateAuthUI(true);
        hideModals();
        showToast('Account created! Logging in...', 'success');
    } catch(e) {
        showToast('Registration error: ' + e.message, 'error');
        console.error('Register error:', e);
    }
}

function handleLogout() {
    state.authToken = null;
    state.user = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('refreshToken');
    updateAuthUI(false);
    showToast('Logged out');
    showView('chat'); 
}

/* --- Modal Helpers --- */
function showModal(name, subType) {
    elements.modals.overlay.classList.remove('hidden');
    // Hide all modals
    Object.entries(elements.modals).forEach(([key, el]) => {
        if (key !== 'overlay' && el) el.classList.add('hidden');
    });
    
    // Show the requested modal
    if (elements.modals[name]) elements.modals[name].classList.remove('hidden');

    if (name === 'auth') toggleAuthMode(subType || 'login');
}

function showAgentLogsModal() {
    showModal('agent');
}

function hideModals() {
    elements.modals.overlay.classList.add('hidden');
    Object.entries(elements.modals).forEach(([key, el]) => {
        if (key !== 'overlay' && el) el.classList.add('hidden');
    });
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
    if (e.target.files && e.target.files.length > 0) {
        handleMultipleFileUpload(e.target.files);
    }
}

function handleMultipleFileUpload(files) {
    try {
        if (!files || files.length === 0) return;
        const form = new FormData();
        for (const f of files) {
            form.append('files', f, f.name);
        }
        // include session id if available
        if (state.activeSession) form.append('session_id', state.activeSession);

        showToast('Uploading files to server...', 'info');

        fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            headers: state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : undefined,
            body: form
        }).then(async res => {
            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || 'Upload failed');
            }
            const data = await res.json();
            if (data && data.results) {
                const fileList = data.results.map(r => `${r.file}: ${r.inserted_chunks || r.error}`).join('\n');
                appendMessage(`[Uploaded Documents]\n${fileList}`, 'user');
                showToast('Files uploaded and indexed', 'success');
                elements.app.classList.add('chat-active');
            } else {
                showToast('Upload completed', 'success');
            }
        }).catch(err => {
            showToast('File upload error: ' + err.message, 'error');
            console.error('File upload error:', err);
        }).finally(() => {
            // Reset file input
            elements.fileInput.value = '';
        });
    } catch (err) {
        showToast('File upload error: ' + err.message, 'error');
        console.error('File upload error:', err);
    }
}

function exportChatAsJSON() {
    try {
        const messages = [];
        document.querySelectorAll('.message').forEach(msgEl => {
            const content = msgEl.querySelector('.message-content');
            const timestamp = msgEl.querySelector('.message-timestamp');
            const role = msgEl.classList.contains('user-message') ? 'user' : 'bot';
            messages.push({
                role: role,
                timestamp: timestamp ? timestamp.textContent : new Date().toISOString(),
                text: content ? content.textContent : ''
            });
        });
        
        const dataStr = JSON.stringify({ chat: state.activeSession, messages: messages }, null, 2);
        downloadFile(dataStr, `chat_export_${Date.now()}.json`, 'application/json');
        showToast('Chat exported as JSON', 'success');
    } catch (e) {
        showToast('Export error: ' + e.message, 'error');
    }
}

function exportChatAsPDF() {
    try {
        const messages = [];
        document.querySelectorAll('.message').forEach(msgEl => {
            const content = msgEl.querySelector('.message-content');
            const timestamp = msgEl.querySelector('.message-timestamp');
            const role = msgEl.classList.contains('user-message') ? 'user' : 'bot';
            messages.push({ role, timestamp: timestamp ? timestamp.textContent : '', content: content ? content.textContent : '' });
        });
        
        // Simple HTML table format for PDF
        let html = '<h1>Chat Export</h1><table border="1" cellpadding="5">';
        messages.forEach(msg => {
            html += `<tr><td><b>${msg.role}</b></td><td>${msg.timestamp}</td><td>${msg.content}</td></tr>`;
        });
        html += '</table>';
        
        const printWindow = window.open('', '', 'height=600,width=800');
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.print();
        showToast('Print dialog opened', 'info');
    } catch (e) {
        showToast('PDF export error: ' + e.message, 'error');
    }
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function addReasoningEntryToPanel(data) {
    const list = document.getElementById('agent-reasoning-list');
    if (!list) return;
    const item = document.createElement('div');
    item.className = 'reasoning-item';
    item.style.borderBottom = '1px dashed var(--border-color)';
    item.style.padding = '8px 0';
    const ts = new Date().toLocaleString();

    // Render evaluation nicely if present
    if (data.type === 'evaluation') {
        const summary = data.summary || data.result || '';
        const success = data.success ? '✅' : '❌';
        const sources = (data.sources || []).map(s => `<div class="source"><strong>${s.title || s.id || 'Source'}</strong>: ${s.snippet || ''} <small style="color:var(--muted)">${s.id || ''}</small></div>`).join('');
        item.innerHTML = `<div style="font-size:0.95rem;color:var(--muted)">[${ts}] <strong>Evaluation</strong> ${success}</div><div style="margin-top:6px">${summary}</div><div style="margin-top:8px">${sources}</div>`;
    } else if (data.type === 'planner_output') {
        const text = data.plan || data.raw || JSON.stringify(data, null, 2);
        item.innerHTML = `<div style="font-size:0.95rem;color:var(--muted)">[${ts}] <strong>Planner Output</strong></div><pre style="white-space:pre-wrap;margin:6px 0">${escapeHtml(text)}</pre>`;
    } else if (data.type === 'reason') {
        const reasonText = data.reason || data.explain || JSON.stringify(data, null, 2);
        item.innerHTML = `<div style="font-size:0.95rem;color:var(--muted)">[${ts}] <strong>Reasoning</strong></div><pre style="white-space:pre-wrap;margin:6px 0">${escapeHtml(typeof reasonText === 'string' ? reasonText : JSON.stringify(reasonText, null, 2))}</pre>`;
    } else if (data.type === 'run_complete') {
        item.innerHTML = `<div style="font-size:0.95rem;color:var(--muted)">[${ts}] <strong>Run Complete</strong></div><div style="margin-top:6px">${escapeHtml(JSON.stringify(data, null, 2))}</div>`;
    } else {
        item.innerHTML = `<div style="font-size:0.95rem;color:var(--muted)">[${ts}] <strong>${escapeHtml(data.type || 'event')}</strong></div><pre style="white-space:pre-wrap;margin:6px 0">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    }

    list.prepend(item);
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (m) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]; });
}

async function loadAgentReasoning() {
    try {
        const res = await fetch(`${API_BASE}/api/agent/logs`);
        if (!res.ok) return;
        const logs = await res.json();
        const list = document.getElementById('agent-reasoning-list');
        list.innerHTML = '';
        // Filter logs for structured reasoning/evaluation entries
        const combined = logs.filter(l => {
            const t = l.type || l.get && l.get('type');
            return ['reason','planner_output','evaluation','run_complete'].includes(t) || l.explain || l.plan || l.evaluation || l.reason;
        }).slice(-200);
        if (!combined || combined.length === 0) {
            list.innerHTML = '<div class="log-entry system">No reasoning entries found.</div>';
            return;
        }
        combined.forEach(entry => addReasoningEntryToPanel(entry));
    } catch (e) {
        console.error('Load agent reasoning failed', e);
    }
}

function renderActionCard(card) {
    const container = document.getElementById('agent-log-container');
    if (!container) return;
    const node = document.createElement('div');
    node.className = 'action-card';
    let inner = '';
    if (card.type === 'step_started') {
        inner = `<div class="action-title">Step started: ${escapeHtml(card.title)}</div><div class="action-meta">Tool: ${escapeHtml(card.tool)}</div>`;
    } else if (card.type === 'step_result') {
        inner = `<div class="action-title">Step result: ${escapeHtml(card.title)}</div><div class="action-meta">Status: ${card.ok ? 'OK' : 'FAIL'}</div><pre class="action-logs">${escapeHtml(card.logs || '')}</pre>`;
    } else if (card.type === 'planner') {
        inner = `<div class="action-title">Planner produced a plan</div><div class="action-meta">${escapeHtml((card.plan.rationale||'').toString())}</div>`;
    } else if (card.type === 'evaluation') {
        inner = `<div class="action-title">Evaluation</div><div class="action-meta">${escapeHtml(card.data.summary||'')}</div>`;
    } else {
        inner = `<div class="action-title">${escapeHtml(card.type)}</div><pre class="action-logs">${escapeHtml(JSON.stringify(card.data||card, null, 2))}</pre>`;
    }
    node.innerHTML = inner;
    container.appendChild(node);
    container.scrollTop = container.scrollHeight;
}

function renderNeedInputForm(data) {
    const container = document.getElementById('agent-log-container');
    if (!container) return;
    const panel = document.createElement('div');
    panel.className = 'need-input-panel';
    const title = document.createElement('div'); title.className = 'action-title'; title.textContent = `Input required: ${data.title}`;
    panel.appendChild(title);
    const form = document.createElement('form');
    form.className = 'need-input-form';
    (data.fields || []).forEach(f => {
        const wrapper = document.createElement('div'); wrapper.className = 'input-group';
        const label = document.createElement('label'); label.textContent = f;
        const inp = document.createElement('input'); inp.name = f; inp.placeholder = f; inp.className = 'text-input';
        wrapper.appendChild(label); wrapper.appendChild(inp); form.appendChild(wrapper);
    });
    const submit = document.createElement('button'); submit.type = 'submit'; submit.className = 'btn-primary'; submit.textContent = 'Submit and generate document';
    form.appendChild(submit);
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const payload = { fields: {} };
        for (const [k,v] of formData.entries()) payload.fields[k] = v;
        try {
            const res = await fetch(`${API_BASE}/api/docgen`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ doc_type: 'contract', format: 'pdf', params: payload })
            });
            if (!res.ok) throw new Error('Doc generation failed');
            const d = await res.json();
            const filename = d.filename || d.file || 'document.pdf';
            const link = document.createElement('a'); link.href = `${API_BASE}/api/docgen/download/${filename}`; link.textContent = `Download ${filename}`; link.className='btn-primary'; link.style.display='inline-block'; link.style.marginTop='8px';
            panel.appendChild(link);
            showToast('Document generated', 'success');
        } catch (err) {
            showToast('Generation failed: '+err.message, 'error');
        }
    });
    panel.appendChild(form);
    container.appendChild(panel);
    container.scrollTop = container.scrollHeight;
}