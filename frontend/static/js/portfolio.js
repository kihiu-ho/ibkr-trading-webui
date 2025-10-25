/**
 * Portfolio Page JavaScript
 * Handles portfolio display, P&L tracking, and position management
 */

let allPositions = [];
let showClosed = false;
let pnlChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPortfolio();
    initializeChart();
    
    // Auto-refresh every 60 seconds
    setInterval(() => loadPortfolio(), 60000);
});

/**
 * Load complete portfolio data
 */
async function loadPortfolio() {
    try {
        // Load portfolio metrics
        await loadPortfolioMetrics();
        
        // Load positions
        await loadPositions();
        
    } catch (error) {
        console.error('Error loading portfolio:', error);
        showError('Failed to load portfolio');
    }
}

/**
 * Load portfolio metrics
 */
async function loadPortfolioMetrics() {
    try {
        const response = await fetch('/api/positions/portfolio/value');
        const data = await response.json();
        
        // Update metrics
        document.getElementById('portfolioValue').textContent = formatCurrency(data.portfolio_value || 0);
        document.getElementById('totalPnL').textContent = formatCurrency(data.total_pnl || 0);
        document.getElementById('returnPercent').textContent = formatPercent(data.return_percent || 0);
        document.getElementById('positionCount').textContent = data.position_count || 0;
        
        // Color code P&L
        const pnlElement = document.getElementById('totalPnL');
        pnlElement.className = data.total_pnl >= 0 ? 'mb-0 profit' : 'mb-0 loss';
        
        const returnElement = document.getElementById('returnPercent');
        returnElement.className = data.return_percent >= 0 ? 'mb-0 profit' : 'mb-0 loss';
        
        // Update chart
        updatePnLChart(data);
        
    } catch (error) {
        console.error('Error loading portfolio metrics:', error);
    }
}

/**
 * Load positions
 */
async function loadPositions() {
    try {
        const url = `/api/positions/?include_closed=${showClosed}`;
        const response = await fetch(url);
        const data = await response.json();
        
        allPositions = data.positions || [];
        renderPositions();
        
    } catch (error) {
        console.error('Error loading positions:', error);
        showError('Failed to load positions');
    }
}

/**
 * Render positions list
 */
function renderPositions() {
    const container = document.getElementById('positionsContainer');
    
    if (allPositions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="text-muted mt-2">No positions found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = allPositions.map(position => renderPositionCard(position)).join('');
}

/**
 * Render a single position card
 */
function renderPositionCard(position) {
    const pnl = position.unrealized_pnl || 0;
    const pnlClass = pnl >= 0 ? 'profit' : 'loss';
    const pnlIcon = pnl >= 0 ? 'arrow-up' : 'arrow-down';
    
    const currentPrice = position.last_price || position.average_price;
    const pnlPercent = ((currentPrice - position.average_price) / position.average_price * 100);
    
    return `
        <div class="position-card card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <!-- Symbol Info -->
                    <div class="col-md-2">
                        <h5 class="mb-1">
                            <i class="bi bi-building"></i> Contract ${position.conid}
                        </h5>
                        <small class="text-muted">Strategy #${position.strategy_id || 'N/A'}</small>
                    </div>
                    
                    <!-- Position Details -->
                    <div class="col-md-3">
                        <div class="mb-1">
                            <strong>Quantity:</strong> ${position.quantity}
                        </div>
                        <div class="mb-1">
                            <strong>Avg Price:</strong> ${formatCurrency(position.average_price)}
                        </div>
                        <div>
                            <strong>Current:</strong> ${formatCurrency(currentPrice)}
                        </div>
                    </div>
                    
                    <!-- P&L -->
                    <div class="col-md-3">
                        <h4 class="${pnlClass} mb-1">
                            <i class="bi bi-${pnlIcon}"></i>
                            ${formatCurrency(pnl)}
                        </h4>
                        <div class="${pnlClass}">
                            ${formatPercent(pnlPercent)}
                        </div>
                        ${position.realized_pnl ? `
                            <small class="text-muted">
                                Realized: ${formatCurrency(position.realized_pnl)}
                            </small>
                        ` : ''}
                    </div>
                    
                    <!-- Value -->
                    <div class="col-md-2">
                        <div class="mb-1">
                            <strong>Value:</strong>
                        </div>
                        <h5 class="mb-0">
                            ${formatCurrency(currentPrice * position.quantity)}
                        </h5>
                    </div>
                    
                    <!-- Actions -->
                    <div class="col-md-2 text-end">
                        <button class="btn btn-sm btn-outline-primary" onclick="viewPositionDetails(${position.conid})" title="View Details">
                            <i class="bi bi-eye"></i> Details
                        </button>
                        ${position.is_closed ? `
                            <span class="badge bg-secondary mt-2">Closed</span>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Initialize P&L chart
 */
function initializeChart() {
    const ctx = document.getElementById('pnlChart').getContext('2d');
    
    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Unrealized P&L',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.4
            }, {
                label: 'Realized P&L',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update P&L chart with current data
 */
function updatePnLChart(portfolioData) {
    if (!pnlChart) return;
    
    // For now, just show current values
    // In production, you'd fetch historical data
    const now = new Date().toLocaleTimeString();
    
    pnlChart.data.labels.push(now);
    pnlChart.data.datasets[0].data.push(portfolioData.unrealized_pnl || 0);
    pnlChart.data.datasets[1].data.push(portfolioData.realized_pnl || 0);
    
    // Keep only last 20 data points
    if (pnlChart.data.labels.length > 20) {
        pnlChart.data.labels.shift();
        pnlChart.data.datasets[0].data.shift();
        pnlChart.data.datasets[1].data.shift();
    }
    
    pnlChart.update();
}

/**
 * Toggle closed positions visibility
 */
function toggleClosedPositions() {
    showClosed = document.getElementById('showClosedPositions').checked;
    loadPositions();
}

/**
 * Sync positions with IBKR
 */
async function syncWithIBKR() {
    try {
        const btn = event.target.closest('button');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Syncing...';
        
        const response = await fetch('/api/positions/sync', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(`Synced ${result.synced} positions (${result.created} created, ${result.updated} updated)`);
            await loadPortfolio();
        } else {
            throw new Error(result.error || 'Sync failed');
        }
        
    } catch (error) {
        console.error('Error syncing with IBKR:', error);
        showError('Failed to sync with IBKR: ' + error.message);
    } finally {
        const btn = event.target.closest('button');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sync with IBKR';
    }
}

/**
 * Refresh portfolio data
 */
async function refreshPortfolio() {
    const btn = event.target.closest('button');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Refreshing...';
    
    await loadPortfolio();
    
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
}

/**
 * View position details
 */
async function viewPositionDetails(conid) {
    try {
        const response = await fetch(`/api/positions/${conid}`);
        const data = await response.json();
        
        const position = data.position;
        const metrics = data.risk_metrics;
        
        alert(
            `Position Details\n\n` +
            `Contract ID: ${position.conid}\n` +
            `Quantity: ${position.quantity}\n` +
            `Avg Price: ${formatCurrency(position.average_price)}\n` +
            `Current Price: ${formatCurrency(position.last_price || position.average_price)}\n` +
            `Unrealized P&L: ${formatCurrency(position.unrealized_pnl || 0)}\n` +
            `Realized P&L: ${formatCurrency(position.realized_pnl || 0)}\n` +
            `Position Value: ${formatCurrency(metrics.position_value)}\n` +
            `Portfolio %: ${formatPercent(metrics.position_percent)}\n` +
            `Return %: ${formatPercent(metrics.pnl_percent)}`
        );
        
        // TODO: Replace with proper modal
    } catch (error) {
        console.error('Error fetching position details:', error);
        showError('Failed to load position details');
    }
}

/**
 * Format currency
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value || 0);
}

/**
 * Format percentage
 */
function formatPercent(value) {
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

/**
 * Show success message
 */
function showSuccess(message) {
    // TODO: Implement toast notification
    console.log('Success:', message);
}

/**
 * Show error message
 */
function showError(message) {
    // TODO: Implement toast notification
    console.error('Error:', message);
}

