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
    const input = document.getElementById('chat-input');
    
    if (input) {
        // Handle Enter key (without Shift)
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
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
    // If a modal-based selector exists in the page, prefer that and skip creating
    // a duplicate dropdown. This avoids showing two selection UIs.
    if (document.getElementById('team-selector-modal')) {
        console.log('[CHAT] Team selector modal present; skipping dropdown creation');
        // If the display element exists, ensure it reflects any previously selected team
        const displayEl = document.getElementById('selected-team-display');
        if (displayEl) {
            displayEl.textContent = selectedTeam || 'Not set';
        }
        return;
    }

    const selector = document.getElementById('team-context-selector');
    if (!selector) {
        // Create team selector if it doesn't exist
        console.log('[CHAT] Creating team selector');
        createTeamSelector();
        return;
    }

    const teams = ['CSK', 'RCB', 'MI', 'KKR', 'DC', 'GT', 'LSG', 'PBKS', 'RR', 'SRH'];
    
    // Clear existing options
    selector.innerHTML = '';
    
    // Add "None" option
    const noneOption = document.createElement('option');
    noneOption.value = '';
    noneOption.textContent = 'Select Team';
    selector.appendChild(noneOption);

    teams.forEach(team => {
        const option = document.createElement('option');
        option.value = team;
        option.textContent = team;
        selector.appendChild(option);
    });

    selector.addEventListener('change', (e) => {
        selectedTeam = e.target.value || null;
        const displayEl = document.getElementById('selected-team-display');
        if (displayEl) {
            displayEl.textContent = selectedTeam || 'Not set';
        }
        console.log(`[CHAT] Team selected: ${selectedTeam}`);
    });
}

/**
 * Create team selector element if missing
 */
function createTeamSelector() {
    let selector = document.getElementById('team-context-selector');
    if (!selector) {
        selector = document.createElement('select');
        selector.id = 'team-context-selector';
        selector.className = 'select-team-btn';
        
        const topBar = document.querySelector('.chat-top-bar');
        if (topBar) {
            topBar.appendChild(selector);
        }
        
        initializeTeamSelector();
    }
}

/**
 * Load team from URL
 */
function loadTeamFromURL() {
    const params = new URLSearchParams(window.location.search);
    let team = params.get('team');

    // If no team provided in URL, check persisted selection
    if (!team) {
        try {
            team = localStorage.getItem('selectedTeam') || null;
        } catch (e) {
            console.warn('Could not read persisted selectedTeam:', e);
            team = null;
        }
    }

    if (team) {
        selectedTeam = team;
        const selector = document.getElementById('team-context-selector');
        if (selector) selector.value = team;
        const displayEl = document.getElementById('selected-team-display');
        if (displayEl) displayEl.textContent = team;
        console.log(`[CHAT] Loaded selected team: ${team}`);
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
async function sendMessage(messageParam) {
    // Get message from parameter or input field
    let message = messageParam;
    if (!message) {
        const input = document.getElementById('chat-input');
        message = input ? input.value.trim() : '';
    }
    
    if (!message) return;

    console.log(`[CHAT] sendMessage called with: "${message}"`);
    
    // Get team from selector or persisted selection
    const teamSelector = document.getElementById('team-context-selector');
    const teamToSend = teamSelector ? (teamSelector.value || selectedTeam) : (selectedTeam || window.selectedTeam || null);
    console.log(`[CHAT] Selected team: ${teamToSend || 'None'}`);
    
    // If no team selected at all, require selection first. Prefer modal if available.
    if (!teamToSend) {
        console.log('[CHAT] No team selected; prompting user to choose a team before sending');
        const modal = document.getElementById('team-selector-modal');
        if (modal && typeof modal.classList !== 'undefined') {
            modal.classList.add('active');
            // Avoid repeating identical system message multiple times
            const last = chatContainerLastText();
            if (last !== 'Please select a team before asking questions.') {
                addMessageToChat('system', 'Please select a team before asking questions.');
            }
        } else if (teamSelector) {
            // Focus the dropdown
            teamSelector.focus();
            const last = chatContainerLastText();
            if (last !== 'Please select a team from the dropdown before asking questions.') {
                addMessageToChat('system', 'Please select a team from the dropdown before asking questions.');
            }
        } else {
            const last = chatContainerLastText();
            if (last !== 'Please select a team before asking questions.') {
                addMessageToChat('system', 'Please select a team before asking questions.');
            }
        }
        return;
    }

    // Warn for gap-like queries (keeps previous behavior for extra clarity)
    if (message.toLowerCase().includes('gap') || message.toLowerCase().includes('weak') || message.toLowerCase().includes('prefer')) {
        console.log(`[CHAT] Gap/weak/preference keyword detected`);
    }

    // Add user message to chat
    console.log(`[CHAT] Adding user message to chat`);
    addMessageToChat('user', message);

    // Show typing indicator
    console.log(`[CHAT] Showing typing indicator`);
    const typingId = showTypingIndicator();

    // Clear input field if message came from input
    const input = document.getElementById('chat-input');
    if (input && !messageParam) {
        input.value = '';
    }

    try {
        console.log(`[CHAT] Sending request with direct backend integration`);
        
        // Use direct backend integration instead of API wrapper
        const response = await sendDirectChatRequest(message, teamToSend);
        
        console.log(`[CHAT] Response received:`, response);
        
        // Remove typing indicator
        removeTypingIndicator(typingId);

        console.log(`[CHAT] Response source: ${response.source}`);

        // Add AI response to chat
        const responseText = response.response || 'No response received';
        console.log(`[CHAT] Adding assistant message (${responseText.length} chars)`);
        addMessageToChat('assistant', responseText);

        // Save to history
        chatHistory.push(
            { role: 'user', content: message },
            { role: 'assistant', content: responseText }
        );
        saveChatHistory();
        console.log(`[CHAT] Message saved to history`);
    } catch (error) {
        console.error(`[CHAT] Error caught:`, error);
        removeTypingIndicator(typingId);
        console.error(`[CHAT] Adding error message`);
        addMessageToChat('error', `Error: ${error.message}`);
        showError(`Failed to send message: ${error.message}`);
    }
}

/**
 * Add message to chat
 */
function addMessageToChat(role, content) {
    const chatContainer = document.getElementById('chat-messages-area');
    if (!chatContainer) {
        console.error(`[CHAT] Chat container not found`);
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message chat-message-${role}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    // For system messages, use simple format
    if (role === 'system') {
        messageDiv.innerHTML = content;
        chatContainer.appendChild(messageDiv);
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">
                ${role === 'user' ? '<strong>You:</strong>' : role === 'assistant' ? '<strong>AI:</strong>' : ''}
                ${content}
            </div>
            <div class="message-timestamp">${timestamp}</div>
        `;
        chatContainer.appendChild(messageDiv);
    }

    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Add slide-in animation
    setTimeout(() => {
        messageDiv.classList.add('slide-in-right');
    }, 10);
}

/**
 * Helper: return last chat container text (simplified) to avoid duplicate system messages
 */
function chatContainerLastText() {
    const chatContainer = document.getElementById('chat-messages-area');
    if (!chatContainer) return null;
    const last = chatContainer.lastElementChild;
    if (!last) return null;
    return last.textContent ? last.textContent.trim() : null;
}

/**
 * Display chat history
 */
function displayChatHistory() {
    const chatContainer = document.getElementById('chat-messages-area');
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
    const chatContainer = document.getElementById('chat-messages-area');
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
