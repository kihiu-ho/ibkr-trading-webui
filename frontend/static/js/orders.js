/**
 * Orders Page JavaScript
 * Handles order display, filtering, and management
 */

let allOrders = [];
let currentFilter = 'all';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadOrders();
    setupFilters();
    setupSearch();
    
    // Auto-refresh every 30 seconds
    setInterval(() => loadOrders(), 30000);
});

/**
 * Load orders from API
 */
async function loadOrders() {
    try {
        const response = await fetch('/api/orders/');
        const data = await response.json();
        
        allOrders = data.orders || [];
        
        updateMetrics();
        renderOrders();
    } catch (error) {
        console.error('Error loading orders:', error);
        showError('Failed to load orders');
    }
}

/**
 * Update metrics cards
 */
function updateMetrics() {
    const total = allOrders.length;
    const active = allOrders.filter(o => ['pending', 'submitted'].includes(o.status)).length;
    const filled = allOrders.filter(o => o.status === 'filled').length;
    
    const today = new Date().toDateString();
    const todayCount = allOrders.filter(o => {
        const orderDate = new Date(o.created_at).toDateString();
        return orderDate === today;
    }).length;
    
    document.getElementById('totalOrders').textContent = total;
    document.getElementById('activeOrders').textContent = active;
    document.getElementById('filledOrders').textContent = filled;
    document.getElementById('todayOrders').textContent = todayCount;
}

/**
 * Render orders based on current filter and search
 */
function renderOrders() {
    const container = document.getElementById('ordersContainer');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    // Filter orders
    let filtered = allOrders;
    
    if (currentFilter !== 'all') {
        filtered = filtered.filter(o => o.status === currentFilter);
    }
    
    if (searchTerm) {
        filtered = filtered.filter(o => 
            (o.symbol && o.symbol.toLowerCase().includes(searchTerm)) ||
            (o.strategy_id && o.strategy_id.toString().includes(searchTerm))
        );
    }
    
    // Sort by created_at descending
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    // Render
    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="text-muted mt-2">No orders found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = filtered.map(order => renderOrderCard(order)).join('');
}

/**
 * Render a single order card
 */
function renderOrderCard(order) {
    const statusClass = getStatusClass(order.status);
    const sideClass = order.side === 'BUY' ? 'success' : 'danger';
    const fillProgress = order.filled_quantity && order.quantity ? 
        (order.filled_quantity / order.quantity * 100).toFixed(0) : 0;
    
    return `
        <div class="card order-card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <!-- Order Info -->
                    <div class="col-md-3">
                        <h5 class="mb-1">
                            <span class="badge bg-${sideClass}">${order.side}</span>
                            ${order.symbol || order.conid}
                        </h5>
                        <small class="text-muted">
                            <i class="bi bi-hash"></i> Order #${order.id} 
                            ${order.ibkr_order_id ? `(${order.ibkr_order_id})` : ''}
                        </small>
                    </div>
                    
                    <!-- Quantity & Price -->
                    <div class="col-md-3">
                        <div class="order-details">
                            <div><strong>Quantity:</strong> ${order.quantity}</div>
                            <div><strong>Price:</strong> $${(order.price || 0).toFixed(2)}</div>
                            <div><strong>Type:</strong> ${order.order_type} / ${order.tif}</div>
                        </div>
                    </div>
                    
                    <!-- Fill Status -->
                    <div class="col-md-2">
                        ${order.filled_quantity ? `
                            <div class="mb-2">
                                <small class="text-muted">Fill Progress</small>
                                <div class="progress" style="height: 8px;">
                                    <div class="progress-bar bg-success" style="width: ${fillProgress}%"></div>
                                </div>
                                <small class="text-muted">${order.filled_quantity}/${order.quantity} (${fillProgress}%)</small>
                            </div>
                        ` : `
                            <small class="text-muted">Not filled yet</small>
                        `}
                    </div>
                    
                    <!-- Status & Time -->
                    <div class="col-md-2">
                        <span class="status-badge badge bg-${statusClass}">
                            ${order.status.toUpperCase()}
                        </span>
                        <div class="mt-2 order-details">
                            <small>${formatDate(order.created_at)}</small>
                        </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="col-md-2 text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewOrderDetails(${order.id})" title="View Details">
                                <i class="bi bi-eye"></i>
                            </button>
                            ${['pending', 'submitted'].includes(order.status) ? `
                                <button class="btn btn-outline-warning" onclick="updateOrderStatus(${order.id})" title="Refresh Status">
                                    <i class="bi bi-arrow-repeat"></i>
                                </button>
                                <button class="btn btn-outline-danger" onclick="cancelOrder(${order.id})" title="Cancel">
                                    <i class="bi bi-x-circle"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                ${order.error_message ? `
                    <div class="alert alert-danger mt-3 mb-0" role="alert">
                        <i class="bi bi-exclamation-triangle"></i> ${order.error_message}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Get status badge class
 */
function getStatusClass(status) {
    const statusMap = {
        'pending': 'secondary',
        'validated': 'info',
        'submitted': 'primary',
        'partially_filled': 'warning',
        'filled': 'success',
        'cancelled': 'dark',
        'rejected': 'danger',
        'error': 'danger'
    };
    return statusMap[status] || 'secondary';
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

/**
 * Setup filter buttons
 */
function setupFilters() {
    document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update filter
            currentFilter = btn.dataset.filter;
            renderOrders();
        });
    });
}

/**
 * Setup search
 */
function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', debounce(() => {
        renderOrders();
    }, 300));
}

/**
 * View order details (modal)
 */
async function viewOrderDetails(orderId) {
    try {
        const response = await fetch(`/api/orders/${orderId}`);
        const data = await response.json();
        const order = data.order;
        
        alert(`Order #${order.id}\\n\\n` +
              `Symbol: ${order.symbol || order.conid}\\n` +
              `Side: ${order.side}\\n` +
              `Quantity: ${order.quantity}\\n` +
              `Price: $${order.price}\\n` +
              `Status: ${order.status}\\n` +
              `Created: ${new Date(order.created_at).toLocaleString()}`);
              
        // TODO: Replace with proper modal
    } catch (error) {
        console.error('Error fetching order details:', error);
        showError('Failed to load order details');
    }
}

/**
 * Update order status from IBKR
 */
async function updateOrderStatus(orderId) {
    try {
        const response = await fetch(`/api/orders/${orderId}/status`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showSuccess('Order status updated');
            await loadOrders();
        } else {
            throw new Error('Failed to update status');
        }
    } catch (error) {
        console.error('Error updating order status:', error);
        showError('Failed to update order status');
    }
}

/**
 * Cancel an order
 */
async function cancelOrder(orderId) {
    if (!confirm('Are you sure you want to cancel this order?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/orders/${orderId}/cancel`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showSuccess('Order cancelled successfully');
            await loadOrders();
        } else {
            throw new Error('Failed to cancel order');
        }
    } catch (error) {
        console.error('Error cancelling order:', error);
        showError('Failed to cancel order');
    }
}

/**
 * Refresh orders
 */
async function refreshOrders() {
    document.getElementById('ordersContainer').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Refreshing...</span>
            </div>
            <p class="mt-2 text-muted">Refreshing orders...</p>
        </div>
    `;
    await loadOrders();
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

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

