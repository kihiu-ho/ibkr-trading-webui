/**
 * Workflow Execution Component
 * Handles real-time workflow execution monitoring with WebSocket updates
 */

function workflowExecution(executionId) {
    return {
        executionId: executionId,
        execution: {},
        logs: [],
        filteredLogs: [],
        recentLogs: [],
        currentStep: null,
        lineageData: { nodes: [], edges: [] },
        lineageNetwork: null,
        selectedLog: null,
        wsConnected: false,
        ws: null,
        
        logFilters: {
            step_type: '',
            success: '',
            code: ''
        },
        
        async init() {
            console.log('Initializing workflow execution view for execution:', this.executionId);
            
            // Load initial data
            await this.loadExecution();
            await this.loadLogs();
            await this.loadLineage();
            
            // Connect to WebSocket for real-time updates
            this.connectWebSocket();
            
            // Auto-refresh if execution is running
            if (this.execution.status === 'running') {
                this.startAutoRefresh();
            }
            
            // Render lineage visualization
            this.$nextTick(() => {
                this.renderLineage();
            });
        },
        
        async loadExecution() {
            try {
                const response = await fetch(`/api/workflows/executions/${this.executionId}`);
                if (response.ok) {
                    this.execution = await response.json();
                    console.log('Execution loaded:', this.execution);
                } else {
                    console.error('Failed to load execution');
                    this.showToast('Failed to load execution details', 'error');
                }
            } catch (error) {
                console.error('Error loading execution:', error);
                this.showToast('Error loading execution', 'error');
            }
        },
        
        async loadLogs() {
            try {
                const response = await fetch(`/api/workflows/executions/${this.executionId}/logs`);
                if (response.ok) {
                    this.logs = await response.json();
                    this.filterLogs();
                    this.updateRecentLogs();
                    console.log('Logs loaded:', this.logs.length);
                } else {
                    console.error('Failed to load logs');
                }
            } catch (error) {
                console.error('Error loading logs:', error);
            }
        },
        
        async loadLineage() {
            try {
                const response = await fetch(`/api/workflows/executions/${this.executionId}/lineage`);
                if (response.ok) {
                    this.lineageData = await response.json();
                    console.log('Lineage loaded:', this.lineageData.nodes.length, 'nodes');
                } else {
                    console.error('Failed to load lineage');
                }
            } catch (error) {
                console.error('Error loading lineage:', error);
            }
        },
        
        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.wsConnected = true;
                
                // Subscribe to this execution's logs
                this.ws.send(JSON.stringify({
                    command: 'subscribe',
                    execution_id: this.executionId
                }));
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data.type);
                
                if (data.type === 'subscription_confirmed') {
                    console.log('Subscribed to execution:', data.execution_id);
                    this.showToast('Real-time updates enabled', 'success');
                } else if (data.workflow_execution_id === this.executionId) {
                    // New log entry for this execution
                    this.handleNewLog(data);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.wsConnected = false;
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.wsConnected = false;
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (this.execution.status === 'running') {
                        console.log('Attempting to reconnect...');
                        this.connectWebSocket();
                    }
                }, 5000);
            };
        },
        
        handleNewLog(logData) {
            console.log('New log received:', logData.step_name);
            
            // Add to logs array
            this.logs.push(logData);
            
            // Update current step
            this.currentStep = logData;
            
            // Update filtered logs
            this.filterLogs();
            
            // Update recent logs
            this.updateRecentLogs();
            
            // Update lineage visualization
            this.updateLineageNode(logData);
            
            // Refresh execution data to update statistics
            this.loadExecution();
        },
        
        updateRecentLogs() {
            // Keep last 10 logs, most recent first
            this.recentLogs = [...this.logs]
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, 10);
        },
        
        filterLogs() {
            this.filteredLogs = this.logs.filter(log => {
                if (this.logFilters.step_type && log.step_type !== this.logFilters.step_type) {
                    return false;
                }
                if (this.logFilters.success !== '' && log.success.toString() !== this.logFilters.success) {
                    return false;
                }
                if (this.logFilters.code && log.code !== this.logFilters.code) {
                    return false;
                }
                return true;
            });
        },
        
        renderLineage() {
            if (!this.lineageData.nodes || this.lineageData.nodes.length === 0) {
                console.log('No lineage data to render');
                return;
            }
            
            const container = document.getElementById('lineage-graph');
            if (!container) {
                console.error('Lineage graph container not found');
                return;
            }
            
            // Transform data for vis.js
            const nodes = new vis.DataSet(this.lineageData.nodes.map(node => ({
                id: node.id,
                label: node.label + (node.code ? `\n${node.code}` : ''),
                color: this.getNodeColor(node.status),
                font: { size: 12 },
                shape: 'box',
                margin: 10,
                data: node
            })));
            
            const edges = new vis.DataSet(this.lineageData.edges.map(edge => ({
                from: edge.from,
                to: edge.to,
                label: edge.label,
                arrows: 'to',
                font: { size: 10, align: 'top' }
            })));
            
            const data = { nodes, edges };
            
            const options = {
                layout: {
                    hierarchical: {
                        direction: 'UD',
                        sortMethod: 'directed',
                        levelSeparation: 100,
                        nodeSpacing: 150
                    }
                },
                physics: {
                    enabled: false
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 100
                },
                edges: {
                    smooth: {
                        type: 'cubicBezier',
                        forceDirection: 'vertical'
                    }
                }
            };
            
            this.lineageNetwork = new vis.Network(container, data, options);
            
            // Add click handler
            this.lineageNetwork.on('click', (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);
                    if (node && node.data) {
                        this.showNodeDetail(node.data);
                    }
                }
            });
            
            console.log('Lineage visualization rendered');
        },
        
        updateLineageNode(logData) {
            if (!this.lineageNetwork) return;
            
            // Add new node to lineage
            const nodeId = `node_${this.logs.length - 1}`;
            const newNode = {
                id: nodeId,
                label: logData.step_name + (logData.code ? `\n${logData.code}` : ''),
                color: this.getNodeColor(logData.success ? 'success' : 'failed'),
                font: { size: 12 },
                shape: 'box',
                margin: 10,
                data: logData
            };
            
            try {
                this.lineageNetwork.body.data.nodes.add(newNode);
                
                // Add edge from last node
                if (this.logs.length > 1) {
                    const prevNodeId = `node_${this.logs.length - 2}`;
                    this.lineageNetwork.body.data.edges.add({
                        from: prevNodeId,
                        to: nodeId,
                        label: logData.duration_ms ? `${logData.duration_ms}ms` : '',
                        arrows: 'to',
                        font: { size: 10, align: 'top' }
                    });
                }
            } catch (error) {
                console.error('Error updating lineage visualization:', error);
            }
        },
        
        getNodeColor(status) {
            const colors = {
                'success': { background: '#d1fae5', border: '#10b981' },
                'failed': { background: '#fee2e2', border: '#ef4444' },
                'running': { background: '#dbeafe', border: '#3b82f6' },
                'pending': { background: '#f3f4f6', border: '#9ca3af' }
            };
            return colors[status] || colors.pending;
        },
        
        showNodeDetail(nodeData) {
            // Find the log entry for this node
            const log = this.logs.find(l => 
                l.step_name === nodeData.label.split('\n')[0] && 
                l.code === nodeData.code
            );
            if (log) {
                this.showLogDetail(log);
            }
        },
        
        showLogDetail(log) {
            this.selectedLog = log;
        },
        
        async stopExecution() {
            if (!confirm('Are you sure you want to stop this workflow execution?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/workflows/executions/${this.executionId}/stop`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    this.showToast('Workflow execution stopped', 'success');
                    await this.loadExecution();
                } else {
                    const error = await response.json();
                    this.showToast(`Failed to stop execution: ${error.detail}`, 'error');
                }
            } catch (error) {
                console.error('Error stopping execution:', error);
                this.showToast('Error stopping execution', 'error');
            }
        },
        
        async refreshData() {
            await Promise.all([
                this.loadExecution(),
                this.loadLogs(),
                this.loadLineage()
            ]);
            this.showToast('Data refreshed', 'success');
        },
        
        async exportLogs() {
            try {
                const response = await fetch(
                    `/api/logs/export?format=json&workflow_execution_id=${this.executionId}`
                );
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `workflow_logs_${this.executionId}_${Date.now()}.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    this.showToast('Logs exported successfully', 'success');
                } else {
                    this.showToast('Failed to export logs', 'error');
                }
            } catch (error) {
                console.error('Error exporting logs:', error);
                this.showToast('Error exporting logs', 'error');
            }
        },
        
        startAutoRefresh() {
            const intervalId = setInterval(async () => {
                if (this.execution.status !== 'running') {
                    clearInterval(intervalId);
                    return;
                }
                await this.loadExecution();
            }, 10000); // Refresh every 10 seconds
        },
        
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleString();
        },
        
        formatTime(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleTimeString();
        },
        
        formatDuration(seconds) {
            if (!seconds) return '-';
            if (seconds < 60) return `${Math.round(seconds)}s`;
            const minutes = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            if (minutes < 60) return `${minutes}m ${secs}s`;
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return `${hours}h ${mins}m`;
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
            
            // Animate in
            setTimeout(() => {
                toast.style.transform = 'translateX(0)';
            }, 10);
            
            // Remove after 3 seconds
            setTimeout(() => {
                toast.style.transform = 'translateX(400px)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        },
        
        // Cleanup on component destroy
        destroy() {
            if (this.ws) {
                this.ws.close();
            }
            if (this.lineageNetwork) {
                this.lineageNetwork.destroy();
            }
        }
    };
}

