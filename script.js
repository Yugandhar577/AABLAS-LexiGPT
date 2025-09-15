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

// Sidebar toggle for desktop
sidebarToggle.addEventListener('click', function() {
    sidebar.classList.toggle('expanded');
});

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
        sendMessage(uploadMessage);
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
function sendMessage(message, isUser = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
    msgDiv.textContent = message;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Function to send message to backend and handle response
async function handleUserMessage(userMessage) {
    sendMessage(userMessage, true);
    try {
        const res = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage })
        });
        const data = await res.json();
        sendMessage(data.response, false);
    } catch (err) {
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