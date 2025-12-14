/**
 * API Communication Layer
 * Centralized fetch wrapper with error handling and loading states
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

/**
 * Main API fetch wrapper
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw new APIError(
                data.detail || `HTTP error! status: ${response.status}`,
                response.status,
                data
            );
        }

        return data;
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError(
            `Network error: ${error.message}`,
            0,
            null
        );
    }
}

/**
 * API Methods
 */
const API = {
    // Get current auction state
    getState: () => apiFetch('/state'),

    // Team-specific endpoints
    getTeamMatrix: (team) => apiFetch(`/teams/${team}/matrix`),
    getTeamRecommendations: (team, group = null) => {
        const url = group 
            ? `/teams/${team}/recommendations?group=${group}`
            : `/teams/${team}/recommendations`;
        return apiFetch(url);
    },
    getTeamGaps: (team) => apiFetch(`/teams/${team}/gaps`),
    getTeamWeakPoints: (team) => apiFetch(`/teams/${team}/weak-points`),

    // Live auction endpoints
    getLiveRecommendations: () => apiFetch('/live/recommendations'),
    sellPlayer: (playerName, team, price) => 
        apiFetch('/auction/sell', {
            method: 'POST',
            body: { player_name: playerName, team, price }
        }),

    // Chat endpoint
    sendChatMessage: (message, teamName = null, context = null) =>
        apiFetch('/chat', {
            method: 'POST',
            body: { message, team_name: teamName, context }
        })
};

/**
 * Error notification system
 */
function showError(message, duration = 5000) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f44336;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;
    document.body.appendChild(errorDiv);

    setTimeout(() => {
        errorDiv.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => errorDiv.remove(), 300);
    }, duration);
}

/**
 * Success notification system
 */
function showSuccess(message, duration = 3000) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-notification';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => successDiv.remove(), 300);
    }, duration);
}

/**
 * Loading state management
 */
function createLoadingIndicator() {
    const loader = document.createElement('div');
    loader.className = 'loading-indicator';
    loader.innerHTML = `
        <div class="spinner"></div>
        <p>Loading...</p>
    `;
    loader.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10001;
        text-align: center;
    `;
    return loader;
}

let currentLoader = null;

function showLoading() {
    if (currentLoader) return;
    currentLoader = createLoadingIndicator();
    document.body.appendChild(currentLoader);
}

function hideLoading() {
    if (currentLoader) {
        currentLoader.remove();
        currentLoader = null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, APIError, showError, showSuccess, showLoading, hideLoading };
}
