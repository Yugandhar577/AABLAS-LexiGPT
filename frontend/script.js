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

// Add CSS class for animation if not in stylesheet
function ensureAnimationClass() {
    if (!document.querySelector("#slideInUpStyle")) {
        const style = document.createElement("style");
        style.id = "slideInUpStyle";
        style.innerHTML = `
            .animate-slide-in-up {
                animation: slideInUp 0.5s ease-out;
            }
        `;
        document.head.appendChild(style);
    }
}
ensureAnimationClass();

// Function to handle sending a user/bot message
function sendMessage(message, isUser = true) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message ${isUser ? 'user-message' : 'bot-message'}`;
    msgDiv.textContent = message;

    msgDiv.classList.add('animate-slide-in-up');
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Core handler for sending user input and getting bot response
async function handleUserInput(userMessage) {
    sendMessage(userMessage, true);

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) throw new Error("Network error");

        const data = await response.json();
        sendMessage(data.reply, false);
    } catch (err) {
        console.error(err);
        // Fallback simulated response
        setTimeout(() => {
            sendMessage("🤖 This is a sample response (backend not connected).", false);
        }, 600);
    }
}

// Initial input box
initialPromptInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter' && initialPromptInput.value.trim() !== '') {
        const userMessage = initialPromptInput.value.trim();
        body.classList.add('chat-started');
        initialPromptInput.value = '';
        handleUserInput(userMessage);
    }
});

// Main chat input box
promptInput.addEventListener('keyup', function(event) {
    if (event.key === 'Enter' && promptInput.value.trim() !== '') {
        const userMessage = promptInput.value.trim();
        promptInput.value = '';
        handleUserInput(userMessage);
    }
});

// Sidebar toggle
sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('expanded'));
mobileMenuToggle.addEventListener('click', () => sidebar.classList.add('expanded'));
sidebarBackdrop.addEventListener('click', () => sidebar.classList.remove('expanded'));

// File upload
uploadIcon.addEventListener('click', () => fileUploadInput.click());
initialUploadIcon.addEventListener('click', () => fileUploadInput.click());

fileUploadInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        if (!body.classList.contains('chat-started')) {
            body.classList.add('chat-started');
            initialPromptInput.value = '';
        }
        const uploadMessage = `📄 User uploaded: ${file.name}`;
        sendMessage(uploadMessage, true);

        // TODO: send file to backend
        // const formData = new FormData();
        // formData.append("file", file);
        // fetch("/upload", { method: "POST", body: formData });

        fileUploadInput.value = '';
    }
});

// Theme toggle
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

const savedTheme = localStorage.getItem('theme') || 'dark';
setTheme(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    setTheme(currentTheme);
});
