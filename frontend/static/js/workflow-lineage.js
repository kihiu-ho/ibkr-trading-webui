/**
 * Workflow Lineage Visualization
 * Rich visualization for workflow execution steps based on openspec requirements
 */

function workflowLineage() {
    return {
        // Data
        strategies: [],
        executions: [],
        lineageSteps: [],
        selectedStrategyId: '',
        selectedExecutionId: '',
        selectedStep: null,
        showRawInput: false,
        showRawOutput: false,
        loading: false,

        // Initialize
        async init() {
            await this.loadStrategies();
            
            // Check URL parameters for direct navigation
            const urlParams = new URLSearchParams(window.location.search);
            const strategyId = urlParams.get('strategy_id');
            const executionId = urlParams.get('execution_id');
            
            if (strategyId) {
                this.selectedStrategyId = strategyId;
                await this.loadExecutions();
                
                if (executionId) {
                    this.selectedExecutionId = executionId;
                    await this.loadLineage();
                }
            }
        },

        // Load strategies
        async loadStrategies() {
            try {
                const response = await fetch('/api/strategies');
                this.strategies = await response.json();
            } catch (error) {
                console.error('Failed to load strategies:', error);
                this.showToast('Failed to load strategies', 'error');
            }
        },

        // Load executions for selected strategy
        async loadExecutions() {
            if (!this.selectedStrategyId) {
                this.executions = [];
                return;
            }

            try {
                this.loading = true;
                const response = await fetch(`/api/strategies/${this.selectedStrategyId}/executions`);
                this.executions = await response.json();
                this.selectedExecutionId = '';
                this.lineageSteps = [];
            } catch (error) {
                console.error('Failed to load executions:', error);
                this.showToast('Failed to load executions', 'error');
            } finally {
                this.loading = false;
            }
        },

        // Load lineage for selected execution
        async loadLineage() {
            if (!this.selectedExecutionId) {
                this.lineageSteps = [];
                return;
            }

            try {
                this.loading = true;
                const response = await fetch(`/api/lineage/execution/${this.selectedExecutionId}`);
                this.lineageSteps = await response.json();
                
                // Update URL for bookmarking
                const url = new URL(window.location);
                url.searchParams.set('strategy_id', this.selectedStrategyId);
                url.searchParams.set('execution_id', this.selectedExecutionId);
                window.history.replaceState({}, '', url);
                
            } catch (error) {
                console.error('Failed to load lineage:', error);
                this.showToast('Failed to load lineage data', 'error');
            } finally {
                this.loading = false;
            }
        },

        // Refresh data
        async refreshData() {
            if (this.selectedExecutionId) {
                await this.loadLineage();
            } else if (this.selectedStrategyId) {
                await this.loadExecutions();
            } else {
                await this.loadStrategies();
            }
        },

        // Show step detail modal
        showStepDetail(step) {
            this.selectedStep = step;
            this.showRawInput = false;
            this.showRawOutput = false;
        },

        // Build rich visualization for step
        buildStepVisualization(step, isModal = false) {
            if (!step) return '';

            const stepType = step.step_name.toLowerCase();
            
            // Route to appropriate visualizer based on step type
            if (stepType.includes('strategy') || stepType.includes('load_strategy')) {
                return this.visualizeStrategy(step, isModal);
            } else if (stepType.includes('fetch') && stepType.includes('data')) {
                return this.visualizeMarketData(step, isModal);
            } else if (stepType.includes('indicator') || stepType.includes('calculate')) {
                return this.visualizeIndicators(step, isModal);
            } else if (stepType.includes('chart') || stepType.includes('generate')) {
                return this.visualizeCharts(step, isModal);
            } else if (stepType.includes('llm') || stepType.includes('analysis')) {
                return this.visualizeLLMAnalysis(step, isModal);
            } else if (stepType.includes('signal') || stepType.includes('parse')) {
                return this.visualizeSignal(step, isModal);
            } else if (stepType.includes('order') || stepType.includes('place')) {
                return this.visualizeOrder(step, isModal);
            } else {
                return this.visualizeGeneric(step, isModal);
            }
        },

        // Strategy configuration visualization
        visualizeStrategy(step, isModal) {
            const input = step.input_data || {};
            const output = step.output_data || {};
            
            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-blue-50">
                    <div class="flex items-center gap-x-2 mb-3">
                        <i class="fa fa-cog text-blue-600"></i>
                        <h4 class="font-medium text-blue-900">Strategy Configuration</h4>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div><span class="font-medium">Strategy ID:</span> ${input.strategy_id || output.strategy_id || 'N/A'}</div>
                        <div><span class="font-medium">Strategy Name:</span> ${input.strategy_name || output.strategy_name || 'N/A'}</div>
                        <div><span class="font-medium">Symbol:</span> 
                            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                                ${input.symbol || output.symbol || 'N/A'}
                            </span>
                        </div>
                        <div><span class="font-medium">Active:</span> 
                            <span class="px-2 py-1 ${(input.active || output.active) ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'} rounded text-xs font-medium">
                                ${(input.active || output.active) ? '✓ Active' : '✗ Inactive'}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        },

        // Market data visualization
        visualizeMarketData(step, isModal) {
            const input = step.input_data || {};
            const output = step.output_data || {};
            
            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-green-50">
                    <div class="flex items-center gap-x-2 mb-3">
                        <i class="fa fa-chart-line text-green-600"></i>
                        <h4 class="font-medium text-green-900">Market Data Fetched</h4>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <h5 class="text-sm font-medium text-gray-700">INPUT</h5>
                            <div class="text-sm space-y-1">
                                <div><span class="font-medium">Symbol:</span> 
                                    <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">${input.symbol || 'N/A'}</span>
                                </div>
                                <div><span class="font-medium">Contract ID:</span> ${input.conid || 'N/A'}</div>
                                <div><span class="font-medium">Period:</span> ${input.period || 'N/A'}</div>
                            </div>
                        </div>
                        <div class="space-y-2">
                            <h5 class="text-sm font-medium text-gray-700">OUTPUT</h5>
                            <div class="text-sm space-y-1">
                                <div><span class="font-medium">Rows Fetched:</span> 
                                    <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">${output.data_points || 'N/A'}</span>
                                </div>
                                <div><span class="font-medium">Latest Price:</span> $${output.latest_price || 'N/A'}</div>
                                <div><span class="font-medium">Date Range:</span> ${output.date_range || 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        },

        // Technical indicators visualization
        visualizeIndicators(step, isModal) {
            const output = step.output_data || {};
            const indicators = output.indicators || {};
            
            let indicatorRows = '';
            Object.entries(indicators).forEach(([name, value]) => {
                indicatorRows += `
                    <tr>
                        <td class="px-3 py-2 text-sm font-medium">${name}</td>
                        <td class="px-3 py-2 text-sm">${typeof value === 'number' ? value.toFixed(4) : value}</td>
                        <td class="px-3 py-2 text-sm text-gray-500">${output.data_points || 'N/A'} values</td>
                    </tr>
                `;
            });
            
            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-purple-50">
                    <div class="flex items-center gap-x-2 mb-3">
                        <i class="fa fa-chart-bar text-purple-600"></i>
                        <h4 class="font-medium text-purple-900">Technical Indicators</h4>
                    </div>
                    <div class="text-sm mb-2">Indicators Calculated: ${Object.keys(indicators).length}</div>
                    ${Object.keys(indicators).length > 0 ? `
                        <div class="overflow-x-auto">
                            <table class="min-w-full border border-gray-200 rounded">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Indicator</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Latest Value</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500">Data Points</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-200">
                                    ${indicatorRows}
                                </tbody>
                            </table>
                        </div>
                    ` : '<div class="text-gray-500 text-center py-4">No indicators calculated</div>'}
                </div>
            `;
        },

        // Chart generation visualization
        visualizeCharts(step, isModal) {
            const output = step.output_data || {};
            const chartUrl = output.chart_url || output.daily_chart_url;
            const weeklyChartUrl = output.weekly_chart_url;
            
            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-indigo-50">
                    <div class="flex items-center gap-x-2 mb-3">
                        <i class="fa fa-image text-indigo-600"></i>
                        <h4 class="font-medium text-indigo-900">Generated Charts</h4>
                    </div>
                    <div class="grid grid-cols-1 ${weeklyChartUrl ? 'md:grid-cols-2' : ''} gap-4">
                        ${chartUrl ? `
                            <div class="text-center">
                                <div class="text-sm font-medium mb-2">Daily Chart</div>
                                <img src="${chartUrl}" alt="Daily Chart" class="w-full h-32 object-cover rounded border cursor-pointer hover:opacity-80" 
                                     onclick="window.open('${chartUrl}', '_blank')">
                                <div class="text-xs text-gray-500 mt-1">Click to view full size</div>
                            </div>
                        ` : ''}
                        ${weeklyChartUrl ? `
                            <div class="text-center">
                                <div class="text-sm font-medium mb-2">Weekly Chart</div>
                                <img src="${weeklyChartUrl}" alt="Weekly Chart" class="w-full h-32 object-cover rounded border cursor-pointer hover:opacity-80" 
                                     onclick="window.open('${weeklyChartUrl}', '_blank')">
                                <div class="text-xs text-gray-500 mt-1">Click to view full size</div>
                            </div>
                        ` : ''}
                    </div>
                    ${!chartUrl && !weeklyChartUrl ? '<div class="text-gray-500 text-center py-4">No charts generated</div>' : ''}
                </div>
            `;
        },

        // LLM Analysis visualization
        visualizeLLMAnalysis(step, isModal) {
            const input = step.input_data || {};
            const output = step.output_data || {};
            const analysis = output.analysis || output.consolidated_analysis || '';
            const model = input.model || output.model || 'N/A';

            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-purple-50">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-x-2">
                            <i class="fa fa-brain text-purple-600"></i>
                            <h4 class="font-medium text-purple-900">LLM Analysis</h4>
                        </div>
                        <span class="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-medium">${model}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm mb-3">
                        <div><span class="font-medium">Analysis Length:</span> ${analysis.length.toLocaleString()} characters</div>
                        <div><span class="font-medium">Template ID:</span> ${input.prompt_template_id || 'N/A'}</div>
                    </div>
                    <div class="bg-white border rounded p-3 max-h-48 overflow-y-auto">
                        <div class="text-sm whitespace-pre-wrap">${analysis.substring(0, isModal ? analysis.length : 500)}${!isModal && analysis.length > 500 ? '...' : ''}</div>
                    </div>
                    ${!isModal && analysis.length > 500 ? '<div class="text-xs text-gray-500 mt-1">Click "View Full Details" to see complete analysis</div>' : ''}
                </div>
            `;
        },

        // Trading signal visualization
        visualizeSignal(step, isModal) {
            const output = step.output_data || {};
            const signal = output.type || output.action || 'HOLD';
            const entryPrice = output.current_price || output.entry_price;
            const stopLoss = output.stop_loss;
            const targetPrice = output.target_price;
            const confidence = output.confidence || output.profit_margin;

            // Calculate risk/reward if prices available
            let riskReward = '';
            if (entryPrice && stopLoss && targetPrice) {
                const risk = Math.abs(entryPrice - stopLoss);
                const reward = Math.abs(targetPrice - entryPrice);
                const ratio = reward / risk;
                riskReward = `1:${ratio.toFixed(2)}`;
            }

            const signalColor = signal.toUpperCase() === 'BUY' ? 'green' : signal.toUpperCase() === 'SELL' ? 'red' : 'gray';

            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-yellow-50">
                    <div class="flex items-center gap-x-2 mb-4">
                        <i class="fa fa-signal text-yellow-600"></i>
                        <h4 class="font-medium text-yellow-900">Trading Signal</h4>
                    </div>

                    <div class="text-center mb-4">
                        <div class="inline-flex items-center gap-x-2 px-4 py-2 rounded-lg text-lg font-bold ${signalColor === 'green' ? 'bg-green-100 text-green-800' : signalColor === 'red' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}">
                            <i class="fa ${signal.toUpperCase() === 'BUY' ? 'fa-arrow-up' : signal.toUpperCase() === 'SELL' ? 'fa-arrow-down' : 'fa-minus'}"></i>
                            ${signal.toUpperCase()}
                        </div>
                        ${confidence ? `<div class="text-sm text-gray-600 mt-1">Confidence: ${(confidence * 100).toFixed(1)}%</div>` : ''}
                    </div>

                    <div class="grid grid-cols-3 gap-4 mb-4">
                        ${entryPrice ? `
                            <div class="text-center p-3 bg-blue-50 rounded">
                                <div class="text-xs font-medium text-blue-600 uppercase">Entry Price</div>
                                <div class="text-lg font-bold text-blue-900">$${entryPrice.toFixed(2)}</div>
                            </div>
                        ` : ''}
                        ${stopLoss ? `
                            <div class="text-center p-3 bg-red-50 rounded">
                                <div class="text-xs font-medium text-red-600 uppercase">Stop Loss</div>
                                <div class="text-lg font-bold text-red-900">$${stopLoss.toFixed(2)}</div>
                            </div>
                        ` : ''}
                        ${targetPrice ? `
                            <div class="text-center p-3 bg-green-50 rounded">
                                <div class="text-xs font-medium text-green-600 uppercase">Target Price</div>
                                <div class="text-lg font-bold text-green-900">$${targetPrice.toFixed(2)}</div>
                            </div>
                        ` : ''}
                    </div>

                    ${riskReward ? `
                        <div class="text-center p-3 bg-gray-50 rounded">
                            <div class="text-xs font-medium text-gray-600 uppercase">Risk:Reward Ratio</div>
                            <div class="text-lg font-bold text-gray-900">${riskReward}</div>
                        </div>
                    ` : ''}
                </div>
            `;
        },

        // Order visualization
        visualizeOrder(step, isModal) {
            const input = step.input_data || {};
            const output = step.output_data || {};
            const orderType = input.side || output.side || 'N/A';
            const quantity = input.quantity || output.quantity;
            const price = input.price || output.price;
            const status = output.status || 'SUBMITTED';
            const orderId = output.order_id || output.ibkr_order_id;
            const total = quantity && price ? quantity * price : null;

            const statusColor = status === 'FILLED' ? 'green' : status === 'CANCELLED' ? 'red' : status === 'REJECTED' ? 'red' : 'blue';

            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-green-50">
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-x-2">
                            <i class="fa fa-shopping-cart text-green-600"></i>
                            <h4 class="font-medium text-green-900">Order Details</h4>
                        </div>
                        <div class="flex items-center gap-x-2">
                            <span class="px-2 py-1 bg-${orderType === 'BUY' ? 'green' : 'red'}-100 text-${orderType === 'BUY' ? 'green' : 'red'}-800 rounded text-xs font-medium">${orderType}</span>
                            <span class="px-2 py-1 bg-${statusColor}-100 text-${statusColor}-800 rounded text-xs font-medium">${status}</span>
                        </div>
                    </div>

                    ${orderId ? `
                        <div class="text-sm text-gray-600 mb-3">
                            Order ID: ${orderId} ${output.ibkr_order_id ? `• IBKR ID: ${output.ibkr_order_id}` : ''}
                        </div>
                    ` : ''}

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        ${quantity ? `
                            <div class="text-center p-3 bg-white rounded border">
                                <div class="text-xs font-medium text-gray-600 uppercase">Quantity</div>
                                <div class="text-lg font-bold text-gray-900">${quantity}</div>
                            </div>
                        ` : ''}
                        ${price ? `
                            <div class="text-center p-3 bg-white rounded border">
                                <div class="text-xs font-medium text-gray-600 uppercase">Price</div>
                                <div class="text-lg font-bold text-gray-900">$${price.toFixed(2)}</div>
                            </div>
                        ` : ''}
                        <div class="text-center p-3 bg-white rounded border">
                            <div class="text-xs font-medium text-gray-600 uppercase">Order Type</div>
                            <div class="text-lg font-bold text-gray-900">${input.order_type || 'MKT'}</div>
                        </div>
                        ${total ? `
                            <div class="text-center p-3 bg-white rounded border">
                                <div class="text-xs font-medium text-gray-600 uppercase">Total</div>
                                <div class="text-lg font-bold text-gray-900">$${total.toFixed(2)}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        },

        // Generic visualization for unknown step types
        visualizeGeneric(step, isModal) {
            const hasInput = step.input_data && Object.keys(step.input_data).length > 0;
            const hasOutput = step.output_data && Object.keys(step.output_data).length > 0;

            return `
                <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <div class="flex items-center gap-x-2 mb-3">
                        <i class="fa fa-cogs text-gray-600"></i>
                        <h4 class="font-medium text-gray-900">Step Data</h4>
                    </div>
                    <div class="grid grid-cols-1 ${hasInput && hasOutput ? 'md:grid-cols-2' : ''} gap-4">
                        ${hasInput ? `
                            <div>
                                <h5 class="text-sm font-medium text-gray-700 mb-2">Input Data</h5>
                                <pre class="text-xs bg-white p-3 rounded border overflow-x-auto">${JSON.stringify(step.input_data, null, 2)}</pre>
                            </div>
                        ` : ''}
                        ${hasOutput ? `
                            <div>
                                <h5 class="text-sm font-medium text-gray-700 mb-2">Output Data</h5>
                                <pre class="text-xs bg-white p-3 rounded border overflow-x-auto">${JSON.stringify(step.output_data, null, 2)}</pre>
                            </div>
                        ` : ''}
                    </div>
                    ${!hasInput && !hasOutput ? '<div class="text-gray-500 text-center py-4">No data available</div>' : ''}
                </div>
            `;
        },

        // Utility functions
        formatDate(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        },

        showToast(message, type = 'info') {
            // Simple toast implementation
            const toast = document.createElement('div');
            toast.className = `px-4 py-2 rounded-md text-white ${type === 'error' ? 'bg-red-500' : 'bg-blue-500'}`;
            toast.textContent = message;

            const container = document.getElementById('toast-container') || document.body;
            container.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 3000);
        }
    };
}
