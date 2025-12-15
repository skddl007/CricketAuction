/**
 * Recommender Page Functionality
 */

const TEAMS = ['CSK', 'RCB', 'MI', 'KKR', 'DC', 'GT', 'LSG', 'PBKS', 'RR', 'SRH'];
let currentTeam = null;
let currentGroup = null;
let allRecommendations = [];

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeTeamSelector();
    initializeFilters();
    loadTeamFromURL();
    if (currentTeam) {
        loadRecommendations(currentTeam);
    }
});

/**
 * Initialize team selector
 */
function initializeTeamSelector() {
    const selector = document.getElementById('team-selector');
    if (!selector) return;

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
 * Load team from URL
 */
function loadTeamFromURL() {
    const params = new URLSearchParams(window.location.search);
    const team = params.get('team');
    const group = params.get('group');
    
    if (team && TEAMS.includes(team.toUpperCase())) {
        selectTeam(team.toUpperCase());
    } else if (TEAMS.length > 0) {
        selectTeam(TEAMS[0]);
    }

    if (group && ['A', 'B', 'C'].includes(group.toUpperCase())) {
        selectGroup(group.toUpperCase());
    }
}

/**
 * Select team
 */
function selectTeam(team) {
    currentTeam = team;
    
    document.querySelectorAll('.team-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.team === team);
    });

    window.history.pushState({}, '', `?team=${team}${currentGroup ? `&group=${currentGroup}` : ''}`);
    loadRecommendations(team);
}

/**
 * Select group
 */
function selectGroup(group) {
    currentGroup = group;
    
    document.querySelectorAll('.group-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.group === group);
    });

    window.history.pushState({}, '', `?team=${currentTeam}${group ? `&group=${group}` : ''}`);
    filterRecommendations();
}

/**
 * Load recommendations
 */
async function loadRecommendations(team) {
    showLoading();
    try {
        const [responseA, responseB, responseC] = await Promise.all([
            API.getTeamRecommendations(team, 'A'),
            API.getTeamRecommendations(team, 'B'),
            API.getTeamRecommendations(team, 'C')
        ]);

        // Extract recommendations from each response
        // The API returns {team, purse, slots, groups, formatted, gap_analysis}
        // We need to extract the groups data
        allRecommendations = {
            A: extractRecommendationsFromResponse(responseA, 'A'),
            B: extractRecommendationsFromResponse(responseB, 'B'),
            C: extractRecommendationsFromResponse(responseC, 'C')
        };

        displayRecommendations();
        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Failed to load recommendations: ${error.message}`);
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
 * Display recommendations
 */
function displayRecommendations() {
    const container = document.getElementById('recommendations-container');
    if (!container) return;

    if (currentGroup) {
        displayGroupRecommendations(allRecommendations[currentGroup], currentGroup);
    } else {
        // Display all groups
        let html = '';
        ['A', 'B', 'C'].forEach(group => {
            html += `
                <div class="group-section">
                    <h2 class="group-title">Group ${group} ${group === 'A' ? '(High Priority)' : group === 'B' ? '(Alternatives)' : '(Backup)'}</h2>
                    ${renderRecommendationsGrid(allRecommendations[group] || [])}
                </div>
            `;
        });
        container.innerHTML = html;
    }
}

/**
 * Display single group recommendations
 */
function displayGroupRecommendations(recommendations, group) {
    const container = document.getElementById('recommendations-container');
    if (!container) return;

    container.innerHTML = `
        <div class="group-section">
            <h2 class="group-title">Group ${group} ${group === 'A' ? '(High Priority)' : group === 'B' ? '(Alternatives)' : '(Backup)'}</h2>
            ${renderRecommendationsGrid(recommendations)}
        </div>
    `;
}

/**
 * Render recommendations grid
 */
function renderRecommendationsGrid(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        return '<p>No recommendations available.</p>';
    }

    let html = '<div class="recommendations-grid">';
    recommendations.forEach(player => {
        html += `
            <div class="recommendation-card card" onclick="openPlayerModal('${player.player_name || player.name || ''}')">
                <h3>${player.player_name || player.name || 'Unknown'}</h3>
                <div class="player-badges">
                    <span class="badge badge-primary">${player.primary_role || player.role || 'N/A'}</span>
                    <span class="badge badge-secondary">${player.speciality || 'N/A'}</span>
                </div>
                <div class="player-stats">
                    ${player.overall_demand_score ? `<div class="stat"><strong>Demand Score:</strong> ${player.overall_demand_score.toFixed(1)}/10</div>` : ''}
                    ${player.fair_price_range ? `<div class="stat"><strong>Fair Price:</strong> ${player.fair_price_range}Cr</div>` : ''}
                    ${player.quality ? `<div class="stat"><strong>Quality:</strong> Tier ${player.quality}</div>` : ''}
                </div>
                ${player.gaps_filled && player.gaps_filled.length > 0 ? `<div class="recommendation-reason">Fills: ${player.gaps_filled.slice(0, 2).join(', ')}</div>` : ''}
            </div>
        `;
    });
    html += '</div>';
    return html;
}

/**
 * Initialize filters
 */
function initializeFilters() {
    const roleFilter = document.getElementById('filter-role');
    const specialityFilter = document.getElementById('filter-speciality');
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');

    if (roleFilter) {
        roleFilter.addEventListener('change', filterRecommendations);
    }
    if (specialityFilter) {
        specialityFilter.addEventListener('change', filterRecommendations);
    }
    if (searchInput) {
        searchInput.addEventListener('input', filterRecommendations);
    }
    if (sortSelect) {
        sortSelect.addEventListener('change', filterRecommendations);
    }

    // Group buttons
    document.querySelectorAll('.group-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.dataset.group;
            selectGroup(group === 'all' ? null : group);
        });
    });
}

/**
 * Filter recommendations
 */
function filterRecommendations() {
    // This would filter the displayed recommendations
    // For now, just re-display based on current group
    displayRecommendations();
}

/**
 * Open player modal
 */
function openPlayerModal(playerName) {
    // Find player in all recommendations
    let player = null;
    for (const group of ['A', 'B', 'C']) {
        player = allRecommendations[group]?.find(p => p.name === playerName);
        if (player) break;
    }

    if (!player) return;

    const modal = document.getElementById('player-modal');
    if (!modal) return;

    modal.innerHTML = `
        <div class="modal-content">
            <span class="modal-close" onclick="closePlayerModal()">&times;</span>
            <h2>${player.name || 'Unknown'}</h2>
            <div class="modal-body">
                <div class="modal-section">
                    <h3>Basic Info</h3>
                    <p><strong>Role:</strong> ${player.role || 'N/A'}</p>
                    <p><strong>Speciality:</strong> ${player.speciality || 'N/A'}</p>
                    <p><strong>Quality:</strong> ${player.quality || 'N/A'}</p>
                </div>
                <div class="modal-section">
                    <h3>Metrics</h3>
                    <p><strong>Match Score:</strong> ${player.match_score?.toFixed(2) || 'N/A'}</p>
                    <p><strong>Price Estimate:</strong> ${player.price_estimate ? formatCurrency(player.price_estimate) : 'N/A'}</p>
                </div>
                ${player.reason ? `
                <div class="modal-section">
                    <h3>Why Recommended</h3>
                    <p>${player.reason}</p>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}

/**
 * Close player modal
 */
function closePlayerModal() {
    const modal = document.getElementById('player-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Make functions global for onclick handlers
window.openPlayerModal = openPlayerModal;
window.closePlayerModal = closePlayerModal;
