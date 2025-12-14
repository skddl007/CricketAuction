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
        loadTeamData(currentTeam);
    }
});

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
    loadTeamData(team);
}

/**
 * Load all team data
 */
async function loadTeamData(team) {
    showLoading();
    try {
        const [state, gaps, weakPoints, matrix] = await Promise.all([
            API.getState(),
            API.getTeamGaps(team),
            API.getTeamWeakPoints(team),
            API.getTeamMatrix(team)
        ]);

        displayTeamOverview(team, state);
        displayGapAnalysis(gaps);
        displayWeakPoints(weakPoints);
        displayTeamMatrix(matrix);
        loadRecommendations(team);

        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Failed to load team data: ${error.message}`);
    }
}

/**
 * Display team overview
 */
function displayTeamOverview(team, state) {
    const teamData = state.teams?.find(t => t.name === team);
    if (!teamData) return;

    const overview = document.getElementById('team-overview');
    if (overview) {
        overview.innerHTML = `
            <div class="overview-card">
                <h3>Team: ${team}</h3>
                <div class="overview-stats">
                    <div class="stat-item">
                        <span class="stat-label">Purse Remaining:</span>
                        <span class="stat-value">${formatCurrency(teamData.purse_remaining || 0)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Slots Available:</span>
                        <span class="stat-value">${teamData.slots_available || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Players Bought:</span>
                        <span class="stat-value">${teamData.players_bought || 0}</span>
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
function displayWeakPoints(weakPoints) {
    const container = document.getElementById('weak-points');
    if (!container) return;

    if (!weakPoints || weakPoints.length === 0) {
        container.innerHTML = '<p>No weak points identified.</p>';
        return;
    }

    let html = '<div class="weak-points-list">';
    weakPoints.forEach(point => {
        html += `
            <div class="weak-point-item">
                <span class="weak-point-text">${point}</span>
            </div>
        `;
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

    if (!matrix || !matrix.matrix) {
        container.innerHTML = '<p>Matrix data not available.</p>';
        return;
    }

    const matrixData = matrix.matrix;
    let html = '<div class="matrix-container"><table class="matrix-table">';

    // Header row
    html += '<thead><tr><th>Role</th>';
    if (matrixData[0]) {
        Object.keys(matrixData[0]).forEach(key => {
            if (key !== 'role') {
                html += `<th>${key}</th>`;
            }
        });
    }
    html += '</tr></thead><tbody>';

    // Data rows
    matrixData.forEach(row => {
        html += '<tr>';
        html += `<td class="matrix-role">${row.role || ''}</td>`;
        Object.keys(row).forEach(key => {
            if (key !== 'role') {
                const value = row[key];
                const cellClass = value ? 'matrix-cell filled' : 'matrix-cell empty';
                html += `<td class="${cellClass}" title="${value || 'Empty'}">${value || '-'}</td>`;
            }
        });
        html += '</tr>';
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

/**
 * Load recommendations
 */
async function loadRecommendations(team) {
    const container = document.getElementById('recommendations');
    if (!container) return;

    try {
        const [groupA, groupB, groupC] = await Promise.all([
            API.getTeamRecommendations(team, 'A'),
            API.getTeamRecommendations(team, 'B'),
            API.getTeamRecommendations(team, 'C')
        ]);

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
                <h4>${player.name || 'Unknown'}</h4>
                <div class="player-details">
                    <p><strong>Role:</strong> ${player.role || 'N/A'}</p>
                    <p><strong>Speciality:</strong> ${player.speciality || 'N/A'}</p>
                    <p><strong>Match Score:</strong> ${player.match_score?.toFixed(2) || 'N/A'}</p>
                    ${player.price_estimate ? `<p><strong>Price Estimate:</strong> ${formatCurrency(player.price_estimate)}</p>` : ''}
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
