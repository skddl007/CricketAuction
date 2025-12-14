/**
 * Live Auction Page Functionality
 */

let refreshInterval = null;
const REFRESH_INTERVAL = 5000; // 5 seconds

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeSellForm();
    loadAuctionStatus();
    loadLiveRecommendations();
    loadRecentSales();
    
    // Start auto-refresh
    startAutoRefresh();
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        stopAutoRefresh();
    });
});

/**
 * Initialize sell player form
 */
function initializeSellForm() {
    const form = document.getElementById('sell-player-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const playerName = formData.get('player_name');
        const team = formData.get('team');
        const price = parseFloat(formData.get('price'));

        if (!playerName || !team || !price) {
            showError('Please fill in all fields');
            return;
        }

        try {
            showLoading();
            await API.sellPlayer(playerName, team, price);
            showSuccess(`Player ${playerName} sold to ${team} for ${formatCurrency(price)}`);
            form.reset();
            
            // Refresh data
            loadAuctionStatus();
            loadLiveRecommendations();
            loadRecentSales();
            
            hideLoading();
        } catch (error) {
            hideLoading();
            showError(`Failed to record sale: ${error.message}`);
        }
    });
}

/**
 * Load auction status
 */
async function loadAuctionStatus() {
    try {
        const state = await API.getState();
        displayAuctionStatus(state);
    } catch (error) {
        showError(`Failed to load auction status: ${error.message}`);
    }
}

/**
 * Display auction status
 */
function displayAuctionStatus(state) {
    const container = document.getElementById('auction-status');
    if (!container) return;

    container.innerHTML = `
        <div class="status-grid">
            <div class="status-card card">
                <div class="status-label">Available Players</div>
                <div class="status-value">${state.available_players_count || 0}</div>
            </div>
            <div class="status-card card">
                <div class="status-label">Sold Players</div>
                <div class="status-value">${state.sold_players_count || 0}</div>
            </div>
            <div class="status-card card">
                <div class="status-label">Supply Count</div>
                <div class="status-value">${state.supply_count || 0}</div>
            </div>
            <div class="status-card card">
                <div class="status-label">Total Teams</div>
                <div class="status-value">${state.teams?.length || 0}</div>
            </div>
        </div>
    `;

    // Add pulse animation
    container.querySelectorAll('.status-card').forEach(card => {
        card.classList.add('pulse');
        setTimeout(() => card.classList.remove('pulse'), 1000);
    });
}

/**
 * Load live recommendations
 */
async function loadLiveRecommendations() {
    try {
        const recommendations = await API.getLiveRecommendations();
        displayLiveRecommendations(recommendations);
    } catch (error) {
        const container = document.getElementById('live-recommendations');
        if (container) {
            container.innerHTML = `<p>Error loading recommendations: ${error.message}</p>`;
        }
    }
}

/**
 * Display live recommendations
 */
function displayLiveRecommendations(recommendations) {
    const container = document.getElementById('live-recommendations');
    if (!container) return;

    if (!recommendations || Object.keys(recommendations).length === 0) {
        container.innerHTML = '<p>No recommendations available.</p>';
        return;
    }

    let html = '<div class="accordion-group">';
    
    Object.keys(recommendations).forEach(team => {
        const teamRecs = recommendations[team];
        html += `
            <div class="accordion">
                <div class="accordion-header">
                    <h3>${team}</h3>
                    <span class="accordion-icon">▼</span>
                </div>
                <div class="accordion-content">
                    <div class="recommendations-list">
                        ${renderTeamRecommendations(teamRecs)}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;

    // Re-initialize accordions
    initAccordions();
}

/**
 * Render team recommendations
 */
function renderTeamRecommendations(recs) {
    if (!recs || recs.length === 0) {
        return '<p>No recommendations for this team.</p>';
    }

    let html = '';
    recs.forEach(player => {
        html += `
            <div class="recommendation-item card">
                <h4>${player.name || 'Unknown'}</h4>
                <div class="player-info">
                    <span class="badge badge-primary">${player.role || 'N/A'}</span>
                    <span class="badge badge-secondary">${player.speciality || 'N/A'}</span>
                    ${player.match_score ? `<span class="match-score">Score: ${player.match_score.toFixed(2)}</span>` : ''}
                </div>
            </div>
        `;
    });
    return html;
}

/**
 * Load recent sales
 */
async function loadRecentSales() {
    try {
        const state = await API.getState();
        displayRecentSales(state);
    } catch (error) {
        console.error('Failed to load recent sales:', error);
    }
}

/**
 * Display recent sales
 */
function displayRecentSales(state) {
    const container = document.getElementById('recent-sales');
    if (!container) return;

    const soldPlayers = state.sold_players || [];
    
    if (soldPlayers.length === 0) {
        container.innerHTML = '<p>No sales recorded yet.</p>';
        return;
    }

    // Show last 10 sales
    const recentSales = soldPlayers.slice(-10).reverse();
    
    let html = '<div class="sales-list">';
    recentSales.forEach(sale => {
        html += `
            <div class="sale-item card slide-in-right">
                <div class="sale-player">${sale.player_name || 'Unknown'}</div>
                <div class="sale-details">
                    <span class="sale-team badge badge-primary">${sale.team || 'N/A'}</span>
                    <span class="sale-price">${formatCurrency(sale.price || 0)}</span>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (refreshInterval) return;
    
    refreshInterval = setInterval(() => {
        loadAuctionStatus();
        loadLiveRecommendations();
        loadRecentSales();
    }, REFRESH_INTERVAL);

    // Show refresh indicator
    const indicator = document.getElementById('refresh-indicator');
    if (indicator) {
        indicator.textContent = 'Auto-refreshing every 5 seconds...';
    }
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}
