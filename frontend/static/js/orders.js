/**
 * Orders Page JavaScript - OpenSpec 2 Enhanced
 * Handles order display, filtering, and management with improved UX
 */

let allOrders = [];
let currentFilter = 'all';
let orderDetailModal = null;
let currentDetailOrderId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modal
    const modalElement = document.getElementById('orderDetailModal');
    orderDetailModal = new bootstrap.Modal(modalElement);
    
    // Setup refresh button in modal
    document.getElementById('refreshDetailBtn').addEventListener('click', () => {
        if (currentDetailOrderId) {
            loadOrderDetails(currentDetailOrderId);
        }
    });
    
    loadOrders();
    setupFilters();
    setupSearch();
    
    // Auto-refresh every 30 seconds
    setInterval(() => loadOrders(true), 30000);
});

/**
 * Load orders from API
 * @param {boolean} silent - If true, don't show loading spinner
 */
async function loadOrders(silent = false) {
    try {
        if (!silent) {
            showLoadingState();
        }
        
        const response = await fetch('/api/orders/');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        allOrders = data.orders || [];
        
        updateMetrics();
        renderOrders();
        updateLastRefreshTime();
        updateLiveStatus(true);
    } catch (error) {
        console.error('Error loading orders:', error);
        showError('Failed to load orders: ' + error.message);
        updateLiveStatus(false);
    }
}

/**
 * Show loading state overlay
 */
function showLoadingState() {
    const container = document.getElementById('ordersContainer');
    if (container && !container.querySelector('.loading-overlay')) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        container.style.position = 'relative';
        container.appendChild(overlay);
    }
}

/**
 * Remove loading state overlay
 */
function removeLoadingState() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Update last refresh timestamp
 */
function updateLastRefreshTime() {
    const element = document.getElementById('lastUpdate');
    if (element) {
        element.textContent = new Date().toLocaleTimeString();
    }
}

/**
 * Update live connection status
 */
function updateLiveStatus(isLive) {
    const element = document.getElementById('liveStatus');
    if (element) {
        element.className = `badge ${isLive ? 'bg-success' : 'bg-warning'} live-indicator ms-2`;
        element.innerHTML = `<i class="bi bi-circle-fill" style="font-size: 0.5rem;"></i> ${isLive ? 'Live' : 'Offline'}`;
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
    
    removeLoadingState();
    
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
                <p class="text-muted mt-2">
                    ${allOrders.length === 0 ? 'No orders yet' : 'No orders match your filters'}
                </p>
                ${allOrders.length > 0 ? '<button class="btn btn-sm btn-primary mt-3" onclick="clearFilters()">Clear Filters</button>' : ''}
            </div>
        `;
        return;
    }
    
    container.innerHTML = filtered.map(order => renderOrderCard(order)).join('');
}

/**
 * Clear all filters
 */
function clearFilters() {
    currentFilter = 'all';
    document.getElementById('searchInput').value = '';
    document.querySelectorAll('.filter-chip').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === 'all');
    });
    renderOrders();
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
 * View order details in modal
 */
async function viewOrderDetails(orderId) {
    currentDetailOrderId = orderId;
    await loadOrderDetails(orderId);
    orderDetailModal.show();
}

/**
 * Load order details into modal
 */
async function loadOrderDetails(orderId) {
    const content = document.getElementById('orderDetailContent');
    
    try {
        content.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        
        const response = await fetch(`/api/orders/${orderId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const order = data.order;
        
        const statusClass = getStatusClass(order.status);
        const sideClass = order.side === 'BUY' ? 'success' : 'danger';
        
        content.innerHTML = `
            <div class="row mb-3">
                <div class="col-6">
                    <h4>
                        <span class="badge bg-${sideClass}">${order.side}</span>
                        ${order.symbol || order.conid}
                    </h4>
                </div>
                <div class="col-6 text-end">
                    <span class="status-badge badge bg-${statusClass}">
                        ${order.status.toUpperCase()}
                    </span>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Order ID</div>
                    <div class="col-8"><strong>#${order.id}</strong></div>
                </div>
            </div>
            
            ${order.ibkr_order_id ? `
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">IBKR Order ID</div>
                    <div class="col-8"><code>${order.ibkr_order_id}</code></div>
                </div>
            </div>
            ` : ''}
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Contract ID</div>
                    <div class="col-8">${order.conid}</div>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Quantity</div>
                    <div class="col-8"><strong>${order.quantity}</strong></div>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Price</div>
                    <div class="col-8"><strong>$${(order.price || 0).toFixed(2)}</strong></div>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Order Type / TIF</div>
                    <div class="col-8">${order.order_type} / ${order.tif}</div>
                </div>
            </div>
            
            ${order.filled_quantity ? `
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Filled Quantity</div>
                    <div class="col-8">
                        <strong>${order.filled_quantity}</strong> of ${order.quantity}
                        <div class="progress mt-2" style="height: 8px;">
                            <div class="progress-bar bg-success" style="width: ${(order.filled_quantity / order.quantity * 100).toFixed(0)}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${order.average_price ? `
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Average Fill Price</div>
                    <div class="col-8"><strong>$${order.average_price.toFixed(2)}</strong></div>
                </div>
            </div>
            ` : ''}
            
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Created At</div>
                    <div class="col-8">${new Date(order.created_at).toLocaleString()}</div>
                </div>
            </div>
            
            ${order.updated_at ? `
            <div class="detail-row">
                <div class="row">
                    <div class="col-4 text-muted">Last Updated</div>
                    <div class="col-8">${new Date(order.updated_at).toLocaleString()}</div>
                </div>
            </div>
            ` : ''}
            
            ${order.error_message ? `
            <div class="alert alert-danger mt-3">
                <i class="bi bi-exclamation-triangle"></i> <strong>Error:</strong><br>
                ${order.error_message}
            </div>
            ` : ''}
        `;
        
    } catch (error) {
        console.error('Error fetching order details:', error);
        content.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> Failed to load order details: ${error.message}
            </div>
        `;
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
 * Refresh orders (user-initiated)
 */
async function refreshOrders() {
    showLoadingState();
    await loadOrders();
    showSuccess('Orders refreshed successfully');
}

/**
 * Show success toast notification
 */
function showSuccess(message) {
    showToast(message, 'success');
}

/**
 * Show error toast notification
 */
function showError(message) {
    showToast(message, 'error');
}

/**
 * Show toast notification (OpenSpec 2 compliant)
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    
    const toastId = `toast-${Date.now()}`;
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-primary';
    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
    
    const toastHtml = `
        <div class="toast align-items-center text-white ${bgClass} border-0" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 5000 : 3000
    });
    
    toast.show();
    
    // Remove from DOM after hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
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

