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
        const [groupA, groupB, groupC] = await Promise.all([
            API.getTeamRecommendations(team, 'A'),
            API.getTeamRecommendations(team, 'B'),
            API.getTeamRecommendations(team, 'C')
        ]);

        allRecommendations = {
            A: groupA || [],
            B: groupB || [],
            C: groupC || []
        };

        displayRecommendations();
        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Failed to load recommendations: ${error.message}`);
    }
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
            <div class="recommendation-card card" onclick="openPlayerModal('${player.name || ''}')">
                <h3>${player.name || 'Unknown'}</h3>
                <div class="player-badges">
                    <span class="badge badge-primary">${player.role || 'N/A'}</span>
                    <span class="badge badge-secondary">${player.speciality || 'N/A'}</span>
                </div>
                <div class="player-stats">
                    ${player.match_score ? `<div class="stat"><strong>Match Score:</strong> ${player.match_score.toFixed(2)}</div>` : ''}
                    ${player.price_estimate ? `<div class="stat"><strong>Price Estimate:</strong> ${formatCurrency(player.price_estimate)}</div>` : ''}
                    ${player.quality ? `<div class="stat"><strong>Quality:</strong> ${player.quality}</div>` : ''}
                </div>
                ${player.reason ? `<div class="recommendation-reason">${player.reason}</div>` : ''}
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
