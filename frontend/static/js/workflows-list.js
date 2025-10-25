/**
 * Workflows List Component
 * Manages workflow execution list, filtering, and triggering new executions
 */

function workflowsList() {
    return {
        executions: [],
        strategies: [],
        activeStrategies: [],
        selectedStrategyId: '',
        selectedStrategy: null,
        showExecuteModal: false,
        executing: false,
        executionStatus: null,
        
        filters: {
            strategy_id: '',
            status: ''
        },
        
        pagination: {
            skip: 0,
            limit: 10
        },
        
        hasMore: false,
        
        async init() {
            console.log('Initializing workflows list');
            await this.loadStrategies();
            await this.loadExecutions();
            
            // Auto-refresh every 15 seconds
            setInterval(() => this.autoRefresh(), 15000);
        },
        
        async loadExecutions() {
            try {
                // Build query parameters
                const params = new URLSearchParams({
                    skip: this.pagination.skip,
                    limit: this.pagination.limit
                });
                
                if (this.filters.strategy_id) {
                    params.append('strategy_id', this.filters.strategy_id);
                }
                
                if (this.filters.status) {
                    params.append('status', this.filters.status);
                }
                
                const response = await fetch(`/api/workflows/executions?${params}`);
                if (response.ok) {
                    const data = await response.json();
                    this.executions = data;
                    this.hasMore = data.length === this.pagination.limit;
                    console.log('Executions loaded:', data.length);
                } else {
                    console.error('Failed to load executions');
                    this.showToast('Failed to load executions', 'error');
                }
            } catch (error) {
                console.error('Error loading executions:', error);
                this.showToast('Error loading executions', 'error');
            }
        },
        
        async loadStrategies() {
            try {
                const response = await fetch('/api/strategies');
                if (response.ok) {
                    this.strategies = await response.json();
                    // Filter active strategies for execution
                    this.activeStrategies = this.strategies.filter(s => s.active);
                    console.log('Strategies loaded:', this.strategies.length);
                } else {
                    console.error('Failed to load strategies');
                }
            } catch (error) {
                console.error('Error loading strategies:', error);
            }
        },
        
        async loadStrategyDetails() {
            if (!this.selectedStrategyId) {
                this.selectedStrategy = null;
                return;
            }
            
            try {
                const response = await fetch(`/api/strategies/${this.selectedStrategyId}`);
                if (response.ok) {
                    this.selectedStrategy = await response.json();
                    
                    // Load symbols/codes for this strategy
                    // Note: This would need a backend endpoint to get strategy codes
                    // For now, we'll show what's in the param
                    if (this.selectedStrategy.param && this.selectedStrategy.param.symbols) {
                        this.selectedStrategy.symbols = this.selectedStrategy.param.symbols;
                    }
                    
                    console.log('Strategy details loaded:', this.selectedStrategy);
                } else {
                    console.error('Failed to load strategy details');
                }
            } catch (error) {
                console.error('Error loading strategy details:', error);
            }
        },
        
        async executeWorkflow() {
            if (!this.selectedStrategyId) {
                this.showToast('Please select a strategy', 'error');
                return;
            }
            
            if (this.selectedStrategy && !this.selectedStrategy.active) {
                this.showToast('Cannot execute inactive strategy', 'error');
                return;
            }
            
            this.executing = true;
            this.executionStatus = null;
            
            try {
                const response = await fetch(`/api/strategies/${this.selectedStrategyId}/execute`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Workflow execution started:', result);
                    
                    this.executionStatus = {
                        success: true,
                        message: 'Workflow execution started successfully! Redirecting to monitor...'
                    };
                    
                    this.showToast('Workflow execution started!', 'success');
                    
                    // Refresh executions list
                    await this.loadExecutions();
                    
                    // Wait a moment, then redirect to the newest execution
                    setTimeout(async () => {
                        // Get the latest execution for this strategy
                        const execResponse = await fetch(`/api/workflows/executions?strategy_id=${this.selectedStrategyId}&limit=1`);
                        if (execResponse.ok) {
                            const executions = await execResponse.json();
                            if (executions.length > 0) {
                                window.location.href = `/workflows/executions/${executions[0].id}`;
                            } else {
                                this.closeExecuteModal();
                            }
                        }
                    }, 1500);
                    
                } else {
                    const error = await response.json();
                    this.executionStatus = {
                        success: false,
                        message: `Failed to execute: ${error.detail || 'Unknown error'}`
                    };
                    this.showToast('Failed to execute workflow', 'error');
                }
            } catch (error) {
                console.error('Error executing workflow:', error);
                this.executionStatus = {
                    success: false,
                    message: `Error: ${error.message}`
                };
                this.showToast('Error executing workflow', 'error');
            } finally {
                this.executing = false;
            }
        },
        
        async autoRefresh() {
            // Only refresh if we have executions and at least one is running
            const hasRunning = this.executions.some(e => e.status === 'running');
            if (hasRunning) {
                console.log('Auto-refreshing executions...');
                await this.loadExecutions();
            }
        },
        
        async loadMore() {
            this.pagination.skip += this.pagination.limit;
            
            try {
                const params = new URLSearchParams({
                    skip: this.pagination.skip,
                    limit: this.pagination.limit
                });
                
                if (this.filters.strategy_id) {
                    params.append('strategy_id', this.filters.strategy_id);
                }
                
                if (this.filters.status) {
                    params.append('status', this.filters.status);
                }
                
                const response = await fetch(`/api/workflows/executions?${params}`);
                if (response.ok) {
                    const data = await response.json();
                    this.executions = [...this.executions, ...data];
                    this.hasMore = data.length === this.pagination.limit;
                }
            } catch (error) {
                console.error('Error loading more executions:', error);
                this.showToast('Error loading more executions', 'error');
            }
        },
        
        resetFilters() {
            this.filters = {
                strategy_id: '',
                status: ''
            };
            this.pagination.skip = 0;
            this.loadExecutions();
        },
        
        closeExecuteModal() {
            this.showExecuteModal = false;
            this.selectedStrategyId = '';
            this.selectedStrategy = null;
            this.executionStatus = null;
            this.executing = false;
        },
        
        formatDateTime(dateString) {
            if (!dateString) return 'N/A';
            const date = new Date(dateString);
            return date.toLocaleString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            if (!container) return;
            
            const colors = {
                success: 'bg-green-500',
                error: 'bg-red-500',
                info: 'bg-blue-500'
            };
            
            const toast = document.createElement('div');
            toast.className = `${colors[type]} text-white px-6 py-3 rounded shadow-lg transform transition-all duration-300`;
            toast.textContent = message;
            
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.transform = 'translateX(0)';
            }, 10);
            
            setTimeout(() => {
                toast.style.transform = 'translateX(400px)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
    };
}

