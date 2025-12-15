/**
 * Direct Backend Integration for Chat
 * This module directly calls the backend endpoints without going through the API layer
 */

const BACKEND_API_URL = 'https://cricketauction-1.onrender.com';

// Check if backend is available on page load
let backendAvailable = false;

async function checkBackendAvailability() {
    try {
        const response = await fetch(`${BACKEND_API_URL}/state`, {
            method: 'GET',
            timeout: 3000
        });
        backendAvailable = response.ok;
        console.log(`[BACKEND] Backend availability: ${backendAvailable}`);
    } catch (e) {
        backendAvailable = false;
        console.log(`[BACKEND] Backend not available: ${e.message}`);
    }
}

// Direct backend chat request
async function sendDirectChatRequest(message, teamName = null) {
    if (!backendAvailable) {
        return {
            response: "Backend is not available. Please start the backend server with: uvicorn main:app --host 0.0.0.0 --port 8000",
            source: "offline",
            error: true
        };
    }

    try {
        console.log(`[BACKEND] Sending direct request to /chat`);
        console.log(`[BACKEND] Message: ${message}`);
        console.log(`[BACKEND] Team: ${teamName}`);

        const payload = {
            message: message,
            team_name: teamName,
            context: null
        };

        const response = await fetch(`${BACKEND_API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
            timeout: 60000  // 60 second timeout
        });

        console.log(`[BACKEND] Response status: ${response.status}`);

        if (!response.ok) {
            const error = await response.json();
            console.error(`[BACKEND] Error response:`, error);
            return {
                response: `Error from backend: ${error.detail || response.statusText}`,
                source: "error",
                error: true
            };
        }

        const result = await response.json();
        console.log(`[BACKEND] Response received:`, result);

        return {
            response: result.response || result.message || 'No response',
            source: result.source || 'backend',
            context_provided: result.context_provided || false,
            error: false
        };
    } catch (error) {
        console.error(`[BACKEND] Request failed:`, error);
        return {
            response: `Failed to connect to backend: ${error.message}. Is the backend running on port 8000?`,
            source: "offline",
            error: true
        };
    }
}

// Direct backend gaps request
async function sendDirectGapsRequest(teamName) {
    if (!backendAvailable) {
        return null;
    }

    try {
        console.log(`[BACKEND] Fetching gaps for team: ${teamName}`);

        const response = await fetch(`${BACKEND_API_URL}/teams/${teamName}/gaps`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 30000
        });

        if (!response.ok) {
            console.error(`[BACKEND] Error fetching gaps: ${response.status}`);
            return null;
        }

        const result = await response.json();
        console.log(`[BACKEND] Gaps data received`);
        return result;
    } catch (error) {
        console.error(`[BACKEND] Gaps request failed:`, error);
        return null;
    }
}

// Initialize backend check on page load
document.addEventListener('DOMContentLoaded', () => {
    checkBackendAvailability();
});
