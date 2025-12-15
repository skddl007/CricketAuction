/**
 * Team Analysis Page Functionality
 */

const TEAMS = ['CSK', 'RCB', 'MI', 'KKR', 'DC', 'GT', 'LSG', 'PBKS', 'RR', 'SRH'];
let currentTeam = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeTeamSelector();
    loadTeamFromURL();
    if (currentTeam) {
        // Check server health before loading data
        checkServerAndLoadData();
    }
});

/**
 * Check if server is available before loading data
 */
async function checkServerAndLoadData() {
    try {
        console.log('[Team Analysis] Checking server health...');
        const isHealthy = await API.checkHealth();
        
        if (!isHealthy) {
            showError(
                'Server is not responding. Please ensure:<br>' +
                '1. Backend server is running on http://127.0.0.1:8000<br>' +
                '2. Run: <code>python main.py</code> from Cricket_Auction directory<br>' +
                '3. Or run: <code>uvicorn main:app --host 127.0.0.1 --port 8000</code>'
            );
            return;
        }
        
        console.log('[Team Analysis] Server is healthy, loading team data...');
        loadTeamData(currentTeam);
    } catch (error) {
        console.error('[Team Analysis] Error checking server:', error);
        showError(
            'Failed to connect to backend server<br>' +
            'Error: ' + error.message + '<br><br>' +
            'Please ensure the backend server is running:<br>' +
            '1. Open terminal in Cricket_Auction directory<br>' +
            '2. Run: <code>python main.py</code><br>' +
            '3. Or: <code>uvicorn main:app --host 127.0.0.1 --port 8000</code>'
        );
    }
}

/**
 * Initialize team selector
 */
function initializeTeamSelector() {
    const selector = document.getElementById('team-selector');
    if (!selector) return;

    // Create team buttons
    TEAMS.forEach(team => {
        const btn = document.createElement('button');
        btn.className = 'team-btn';
        btn.textContent = team;
        btn.dataset.team = team;
        btn.addEventListener('click', () => selectTeam(team));
        selector.appendChild(btn);
    });
}

/**
 * Load team from URL parameter
 */
function loadTeamFromURL() {
    const params = new URLSearchParams(window.location.search);
    const team = params.get('team');
    if (team && TEAMS.includes(team.toUpperCase())) {
        selectTeam(team.toUpperCase());
    } else if (TEAMS.length > 0) {
        selectTeam(TEAMS[0]);
    }
}

/**
 * Select team and load data
 */
function selectTeam(team) {
    currentTeam = team;
    
    // Update active button
    document.querySelectorAll('.team-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.team === team);
    });

    // Update URL
    window.history.pushState({}, '', `?team=${team}`);

    // Load team data
    checkServerAndLoadData();
}

/**
 * Load all team data
 */
async function loadTeamData(team) {
    showLoading();
    try {
        console.log('[Team Analysis] Loading data for team:', team);
        
        const [state, gaps, weakPoints, matrix] = await Promise.all([
            API.getState(),
            API.getTeamGaps(team),
            API.getTeamWeakPoints(team),
            API.getTeamMatrix(team)
        ]);

        console.log('[Team Analysis] Data loaded successfully');
        displayTeamOverview(team, state);
        displayGapAnalysis(gaps);
        displayWeakPoints(weakPoints);
        displayTeamMatrix(matrix);
        loadRecommendations(team);

        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('[Team Analysis] Load error:', error);
        
        let errorMessage = error.message;
        if (error instanceof APIError && error.data) {
            errorMessage = error.data.detail || error.data.message || error.message;
        }
        
        showError(
            `Failed to load team data for ${team}:<br>` +
            `<strong>${errorMessage}</strong><br><br>` +
            'Troubleshooting:<br>' +
            '1. Verify backend server is running<br>' +
            '2. Check console for detailed error messages<br>' +
            '3. Ensure data files exist in Cricket_Auction/Data/ directory'
        );
    }
}

/**
 * Display team overview
 */
function displayTeamOverview(team, state) {
    // state.teams is an object with team names as keys, not an array
    const teamData = state.teams?.[team];
    if (!teamData) {
        console.warn(`[Team Analysis] Team data not found for: ${team}`);
        return;
    }

    const overview = document.getElementById('team-overview');
    if (overview) {
        // Calculate slots available from total_slots and squad size
        const squadSize = teamData.squad?.length || 0;
        const slotsAvailable = (teamData.total_slots || 25) - squadSize;
        
        overview.innerHTML = `
            <div class="overview-card">
                <h3>Team: ${teamData.name || team}</h3>
                <div class="overview-stats">
                    <div class="stat-item">
                        <span class="stat-label">Purse Remaining:</span>
                        <span class="stat-value">${formatCurrency(teamData.purse_available || teamData.purse_remaining || 0)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Slots Available:</span>
                        <span class="stat-value">${slotsAvailable}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Players in Squad:</span>
                        <span class="stat-value">${squadSize}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Home Ground:</span>
                        <span class="stat-value">${teamData.home_ground || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Display gap analysis
 */
function displayGapAnalysis(gaps) {
    const container = document.getElementById('gap-analysis');
    if (!container) return;

    if (!gaps || Object.keys(gaps).length === 0) {
        container.innerHTML = '<p>No gap analysis available.</p>';
        return;
    }

    let html = '<div class="gap-section">';

    // Batting order gaps
    if (gaps.batting_order_gaps) {
        html += '<h3>Batting Order Gaps</h3><div class="gap-list">';
        gaps.batting_order_gaps.forEach(gap => {
            html += `
                <div class="gap-item">
                    <span class="gap-position">${gap.position || 'N/A'}</span>
                    <span class="gap-description">${gap.description || 'No description'}</span>
                    <span class="badge badge-${getSeverityClass(gap.severity)}">${gap.severity || 'Medium'}</span>
                </div>
            `;
        });
        html += '</div>';
    }

    // Bowling phase gaps
    if (gaps.bowling_phase_gaps) {
        html += '<h3>Bowling Phase Gaps</h3><div class="gap-list">';
        gaps.bowling_phase_gaps.forEach(gap => {
            html += `
                <div class="gap-item">
                    <span class="gap-phase">${gap.phase || 'N/A'}</span>
                    <span class="gap-description">${gap.description || 'No description'}</span>
                    <span class="badge badge-${getSeverityClass(gap.severity)}">${gap.severity || 'Medium'}</span>
                </div>
            `;
        });
        html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Display weak points
 */
function displayWeakPoints(weakPointsResponse) {
    const container = document.getElementById('weak-points');
    if (!container) return;

    // API returns an object with weak_points array, batting_order_gaps, bowling_phase_gaps
    // Extract the weak_points array from the response
    let weakPoints = [];
    
    if (Array.isArray(weakPointsResponse)) {
        // Legacy format: direct array
        weakPoints = weakPointsResponse;
    } else if (weakPointsResponse && typeof weakPointsResponse === 'object') {
        // New format: object with weak_points property
        weakPoints = weakPointsResponse.weak_points || [];
    }

    if (!weakPoints || weakPoints.length === 0) {
        container.innerHTML = '<p>No weak points identified.</p>';
        return;
    }

    let html = '<div class="weak-points-list">';
    weakPoints.forEach(point => {
        // Handle both string and object formats
        if (typeof point === 'string') {
            html += `
                <div class="weak-point-item">
                    <span class="weak-point-text">${escapeHtml(point)}</span>
                </div>
            `;
        } else if (typeof point === 'object') {
            // Object format: { category, severity, details }
            const category = point.category || 'Unknown';
            const severity = point.severity || 'Medium';
            const details = point.details || 'No details';
            const severityClass = getSeverityClass(severity);
            
            html += `
                <div class="weak-point-item">
                    <div class="weak-point-header">
                        <span class="weak-point-category">${escapeHtml(category)}</span>
                        <span class="badge badge-${severityClass}">${severity}</span>
                    </div>
                    <span class="weak-point-text">${escapeHtml(details)}</span>
                </div>
            `;
        }
    });
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Display team matrix
 */
function displayTeamMatrix(matrix) {
    const container = document.getElementById('team-matrix');
    if (!container) return;

    if (!matrix) {
        container.innerHTML = '<p>Matrix data not available.</p>';
        return;
    }

    // Handle new format: matrix is a text string
    if (matrix.matrix && typeof matrix.matrix === 'string') {
        const matrixText = matrix.matrix;
        const html = `
            <div class="matrix-container">
                <pre class="matrix-text">${escapeHtml(matrixText)}</pre>
            </div>
        `;
        container.innerHTML = html;
        return;
    }

    // Legacy format: matrix is an array of objects (if still used)
    if (Array.isArray(matrix)) {
        let html = '<div class="matrix-container"><table class="matrix-table">';

        // Header row
        html += '<thead><tr><th>Role</th>';
        if (matrix[0]) {
            Object.keys(matrix[0]).forEach(key => {
                if (key !== 'role') {
                    html += `<th>${key}</th>`;
                }
            });
        }
        html += '</tr></thead><tbody>';

        // Data rows
        matrix.forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(value => {
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
        return;
    }

    container.innerHTML = '<p>Unable to parse matrix data.</p>';
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Load recommendations
 */
async function loadRecommendations(team) {
    const container = document.getElementById('recommendations');
    if (!container) return;

    try {
        const [responseA, responseB, responseC] = await Promise.all([
            API.getTeamRecommendations(team, 'A'),
            API.getTeamRecommendations(team, 'B'),
            API.getTeamRecommendations(team, 'C')
        ]);

        // Extract recommendations from responses
        const groupA = extractRecommendationsFromResponse(responseA, 'A');
        const groupB = extractRecommendationsFromResponse(responseB, 'B');
        const groupC = extractRecommendationsFromResponse(responseC, 'C');

        // Initialize tabs
        initTabs('#recommendations');

        container.innerHTML = `
            <div class="tabs-container">
                <div class="tabs-header">
                    <button class="tab-button active" data-tab="group-a">Group A (High Priority)</button>
                    <button class="tab-button" data-tab="group-b">Group B (Alternatives)</button>
                    <button class="tab-button" data-tab="group-c">Group C (Backup)</button>
                </div>
                <div class="tabs-content">
                    <div class="tab-panel active" data-panel="group-a">
                        ${renderRecommendations(groupA)}
                    </div>
                    <div class="tab-panel" data-panel="group-b">
                        ${renderRecommendations(groupB)}
                    </div>
                    <div class="tab-panel" data-panel="group-c">
                        ${renderRecommendations(groupC)}
                    </div>
                </div>
            </div>
        `;

        // Re-initialize tabs after rendering
        initTabs('#recommendations');
    } catch (error) {
        container.innerHTML = `<p>Error loading recommendations: ${error.message}</p>`;
    }
}

/**
 * Extract recommendations from API response
 */
function extractRecommendationsFromResponse(response, group) {
    if (!response) return [];
    
    // If response is already an array (legacy format), return it
    if (Array.isArray(response)) {
        return response;
    }
    
    // If response has groups object (new format), extract the group
    if (response.groups && typeof response.groups === 'object') {
        const groupData = response.groups[group];
        if (Array.isArray(groupData)) {
            return groupData;
        }
        return [];
    }
    
    // If response itself is a single group recommendation, return as array
    if (response.player_name) {
        return [response];
    }
    
    return [];
}

/**
 * Render recommendations list
 */
function renderRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        return '<p>No recommendations available.</p>';
    }

    let html = '<div class="recommendations-grid">';
    recommendations.forEach(player => {
        html += `
            <div class="recommendation-card card">
                <h4>${player.player_name || player.name || 'Unknown'}</h4>
                <div class="player-details">
                    <p><strong>Role:</strong> ${player.primary_role || player.role || 'N/A'}</p>
                    <p><strong>Speciality:</strong> ${player.speciality || 'N/A'}</p>
                    <p><strong>Demand Score:</strong> ${player.overall_demand_score?.toFixed(1) || 'N/A'}/10</p>
                    ${player.fair_price_range ? `<p><strong>Fair Price:</strong> ${player.fair_price_range}Cr</p>` : ''}
                </div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

/**
 * Get severity class for badges
 */
function getSeverityClass(severity) {
    const sev = (severity || '').toLowerCase();
    if (sev.includes('critical')) return 'error';
    if (sev.includes('high')) return 'warning';
    return 'secondary';
}
