/**
 * Chat Page Functionality
 */

let chatHistory = [];
let selectedTeam = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeChatInterface();
    initializeTeamSelector();
    initializeSuggestedQuestions();
    loadTeamFromURL();
});

/**
 * Initialize chat interface
 */
function initializeChatInterface() {
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = input.value.trim();
            if (!message) return;

            sendMessage(message);
            input.value = '';
        });
    }

    // Load chat history from localStorage
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
        try {
            chatHistory = JSON.parse(savedHistory);
            displayChatHistory();
        } catch (e) {
            console.error('Failed to load chat history:', e);
        }
    }
}

/**
 * Initialize team selector
 */
function initializeTeamSelector() {
    const selector = document.getElementById('team-context-selector');
    if (!selector) return;

    const teams = ['CSK', 'RCB', 'MI', 'KKR', 'DC', 'GT', 'LSG', 'PBKS', 'RR', 'SRH'];
    
    // Add "None" option
    const noneOption = document.createElement('option');
    noneOption.value = '';
    noneOption.textContent = 'No Team Context';
    selector.appendChild(noneOption);

    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        selector.appendChild(option);
    });

    selector.addEventListener('change', (e) => {
        selectedTeam = e.target.value || null;
    });
}

/**
 * Load team from URL
 */
function loadTeamFromURL() {
    const params = new URLSearchParams(window.location.search);
    const team = params.get('team');
    if (team) {
        const selector = document.getElementById('team-context-selector');
        if (selector) {
            selector.value = team;
            selectedTeam = team;
        }
    }
}

/**
 * Initialize suggested questions
 */
function initializeSuggestedQuestions() {
    const container = document.getElementById('suggested-questions');
    if (!container) return;

    const questions = [
        "Analyze CSK gaps",
        "Recommend players for RCB",
        "What are the weak points of MI?",
        "Show me Group A recommendations for KKR",
        "What players should GT target?",
        "Analyze team matrix for DC"
    ];

    questions.forEach(question => {
        const btn = document.createElement('button');
        btn.className = 'suggested-question-btn btn btn-outline';
        btn.textContent = question;
        btn.addEventListener('click', () => {
            document.getElementById('chat-input').value = question;
            sendMessage(question);
        });
        container.appendChild(btn);
    });
}

/**
 * Send message
 */
async function sendMessage(message) {
    if (!message.trim()) return;

    // Add user message to chat
    addMessageToChat('user', message);

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        const response = await API.sendChatMessage(message, selectedTeam, null);
        
        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add AI response to chat
        addMessageToChat('assistant', response.response || response.message || 'No response received');

        // Save to history
        chatHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: response.response || response.message || 'No response received' }
        );
        saveChatHistory();
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToChat('error', `Error: ${error.message}`);
        showError(`Failed to send message: ${error.message}`);
    }
}

/**
 * Add message to chat
 */
function addMessageToChat(role, content) {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message chat-message-${role}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${role === 'user' ? '<strong>You:</strong>' : role === 'assistant' ? '<strong>AI:</strong>' : ''}
            ${content}
        </div>
        <div class="message-timestamp">${timestamp}</div>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Add slide-in animation
    setTimeout(() => {
        messageDiv.classList.add('slide-in-right');
    }, 10);
}

/**
 * Display chat history
 */
function displayChatHistory() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return;

    chatContainer.innerHTML = '';
    chatHistory.forEach(msg => {
        addMessageToChat(msg.role, msg.content);
    });
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const chatContainer = document.getElementById('chat-messages');
    if (!chatContainer) return null;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message chat-message-typing';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <strong>AI:</strong> <span class="typing-dots">...</span>
        </div>
    `;

    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return 'typing-indicator';
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator(id) {
    if (!id) return;
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Save chat history
 */
function saveChatHistory() {
    try {
        // Keep only last 50 messages
        const recentHistory = chatHistory.slice(-50);
        localStorage.setItem('chatHistory', JSON.stringify(recentHistory));
    } catch (e) {
        console.error('Failed to save chat history:', e);
    }
}

/**
 * Clear chat history
 */
function clearChatHistory() {
    chatHistory = [];
    localStorage.removeItem('chatHistory');
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }
}

// Make function global for button
window.clearChatHistory = clearChatHistory;
