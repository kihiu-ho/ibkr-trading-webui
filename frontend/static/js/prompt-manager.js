/**
 * Prompt Manager - Monaco Editor Integration
 * Manages LLM prompt templates with Jinja2 support
 */

class PromptManager {
    constructor() {
        this.editor = null;
        this.currentPrompts = [];
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPrompts = 0;
        this.filters = {
            template_type: '',
            language: '',
            strategy_id: '',
            is_active: 'true'
        };
        
        this.init();
    }

    async init() {
        // Initialize Monaco Editor
        await this.initMonacoEditor();
        
        // Load strategies for dropdowns
        await this.loadStrategies();
        
        // Load prompts
        await this.loadPrompts();
    }

    /**
     * Initialize Monaco Editor with Jinja2 support
     */
    async initMonacoEditor() {
        return new Promise((resolve) => {
            require.config({ 
                paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }
            });
            
            require(['vs/editor/editor.main'], () => {
                // Register Jinja2 language
                monaco.languages.register({ id: 'jinja2' });
                
                monaco.languages.setMonarchTokensProvider('jinja2', {
                    tokenizer: {
                        root: [
                            [/\{\{/, 'variable.start', '@variable'],
                            [/\{%/, 'keyword.start', '@keyword'],
                            [/\{#/, 'comment.start', '@comment'],
                        ],
                        variable: [
                            [/\}\}/, 'variable.end', '@pop'],
                            [/[a-zA-Z_][a-zA-Z0-9_]*/, 'variable'],
                            [/\|/, 'operator'],
                        ],
                        keyword: [
                            [/%\}/, 'keyword.end', '@pop'],
                            [/\b(if|elif|else|endif|for|endfor|block|endblock|extends|include)\b/, 'keyword'],
                        ],
                        comment: [
                            [/#\}/, 'comment.end', '@pop'],
                            [/.*/, 'comment'],
                        ]
                    }
                });
                
                // Create editor
                this.editor = monaco.editor.create(document.getElementById('monacoEditor'), {
                    value: '',
                    language: 'jinja2',
                    theme: 'vs',
                    automaticLayout: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    fontSize: 14,
                });
                
                resolve();
            });
        });
    }

    /**
     * Load strategies for dropdown
     */
    async loadStrategies() {
        try {
            const response = await fetch('/api/strategies/');
            const strategies = await response.json();
            
            const selects = [
                document.getElementById('filterStrategy'),
                document.getElementById('promptStrategy')
            ];
            
            selects.forEach(select => {
                // Clear existing options (except first ones)
                while (select.options.length > (select.id === 'filterStrategy' ? 2 : 1)) {
                    select.remove(select.options.length - 1);
                }
                
                // Add strategy options
                strategies.forEach(strategy => {
                    const option = document.createElement('option');
                    option.value = strategy.id;
                    option.textContent = strategy.name;
                    select.appendChild(option);
                });
            });
        } catch (error) {
            console.error('Error loading strategies:', error);
        }
    }

    /**
     * Load prompts with filters
     */
    async loadPrompts() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
                ...Object.fromEntries(
                    Object.entries(this.filters).filter(([_, v]) => v !== '')
                )
            });
            
            const response = await fetch(`/api/v1/prompts/?${params}`);
            const data = await response.json();
            
            this.currentPrompts = data.templates;
            this.totalPrompts = data.total;
            
            this.renderPromptsTable();
            this.renderPagination();
        } catch (error) {
            console.error('Error loading prompts:', error);
            this.showError('Failed to load prompts');
        }
    }

    /**
     * Render prompts table
     */
    renderPromptsTable() {
        const tbody = document.getElementById('promptsTableBody');
        
        if (this.currentPrompts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4 text-muted">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        No prompts found. Create your first prompt!
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = this.currentPrompts.map(prompt => `
            <tr>
                <td>
                    <strong>${this.escapeHtml(prompt.name)}</strong>
                    ${prompt.is_default ? '<span class="badge bg-success ms-2">Default</span>' : ''}
                    <br>
                    <small class="text-muted">${this.escapeHtml(prompt.description || '')}</small>
                </td>
                <td><span class="badge bg-secondary">${prompt.template_type}</span></td>
                <td><span class="badge bg-info">${prompt.language.toUpperCase()}</span></td>
                <td>
                    ${prompt.strategy_id 
                        ? `<span class="badge badge-scope-strategy">Strategy ${prompt.strategy_id}</span>` 
                        : '<span class="badge badge-scope-global">Global</span>'
                    }
                </td>
                <td><span class="badge bg-light text-dark">v${prompt.template_version}</span></td>
                <td>
                    ${prompt.is_active 
                        ? '<span class="badge bg-success">Active</span>' 
                        : '<span class="badge bg-secondary">Inactive</span>'
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="promptManager.showPerformance(${prompt.id})">
                        <i class="bi bi-graph-up"></i> View
                    </button>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary" onclick="promptManager.editPrompt(${prompt.id})" title="Edit">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-secondary" onclick="promptManager.duplicatePrompt(${prompt.id})" title="Duplicate">
                            <i class="bi bi-files"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="promptManager.deletePrompt(${prompt.id})" title="Delete">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Render pagination
     */
    renderPagination() {
        const totalPages = Math.ceil(this.totalPrompts / this.pageSize);
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Previous button
        html += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="promptManager.goToPage(${this.currentPage - 1}); return false;">Previous</a>
            </li>
        `;
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= this.currentPage - 2 && i <= this.currentPage + 2)) {
                html += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="promptManager.goToPage(${i}); return false;">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }
        
        // Next button
        html += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="promptManager.goToPage(${this.currentPage + 1}); return false;">Next</a>
            </li>
        `;
        
        pagination.innerHTML = html;
    }

    /**
     * Go to specific page
     */
    goToPage(page) {
        this.currentPage = page;
        this.loadPrompts();
    }

    /**
     * Apply filters
     */
    applyFilters() {
        this.filters.template_type = document.getElementById('filterType').value;
        this.filters.language = document.getElementById('filterLanguage').value;
        this.filters.strategy_id = document.getElementById('filterStrategy').value;
        this.filters.is_active = document.getElementById('filterActive').value;
        
        this.currentPage = 1;
        this.loadPrompts();
    }

    /**
     * Reset filters
     */
    resetFilters() {
        document.getElementById('filterType').value = '';
        document.getElementById('filterLanguage').value = '';
        document.getElementById('filterStrategy').value = '';
        document.getElementById('filterActive').value = 'true';
        
        this.applyFilters();
    }

    /**
     * Show create modal
     */
    showCreateModal() {
        document.getElementById('promptModalTitle').textContent = 'Create Prompt Template';
        document.getElementById('promptForm').reset();
        document.getElementById('promptId').value = '';
        this.editor.setValue('');
        
        const modal = new bootstrap.Modal(document.getElementById('promptModal'));
        modal.show();
    }

    /**
     * Edit prompt
     */
    async editPrompt(id) {
        try {
            const response = await fetch(`/api/v1/prompts/${id}`);
            const prompt = await response.json();
            
            document.getElementById('promptModalTitle').textContent = 'Edit Prompt Template';
            document.getElementById('promptId').value = prompt.id;
            document.getElementById('promptName').value = prompt.name;
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptType').value = prompt.template_type;
            document.getElementById('promptLanguage').value = prompt.language;
            document.getElementById('promptStrategy').value = prompt.strategy_id || '';
            document.getElementById('promptActive').checked = prompt.is_active;
            document.getElementById('promptDefault').checked = prompt.is_default;
            document.getElementById('promptTags').value = prompt.tags ? prompt.tags.join(', ') : '';
            document.getElementById('promptNotes').value = prompt.notes || '';
            
            this.editor.setValue(prompt.prompt_text);
            
            const modal = new bootstrap.Modal(document.getElementById('promptModal'));
            modal.show();
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.showError('Failed to load prompt');
        }
    }

    /**
     * Duplicate prompt
     */
    async duplicatePrompt(id) {
        try {
            const response = await fetch(`/api/v1/prompts/${id}`);
            const prompt = await response.json();
            
            document.getElementById('promptModalTitle').textContent = 'Duplicate Prompt Template';
            document.getElementById('promptId').value = '';
            document.getElementById('promptName').value = prompt.name + ' (Copy)';
            document.getElementById('promptDescription').value = prompt.description || '';
            document.getElementById('promptType').value = prompt.template_type;
            document.getElementById('promptLanguage').value = prompt.language;
            document.getElementById('promptStrategy').value = prompt.strategy_id || '';
            document.getElementById('promptActive').checked = false;
            document.getElementById('promptDefault').checked = false;
            document.getElementById('promptTags').value = prompt.tags ? prompt.tags.join(', ') : '';
            document.getElementById('promptNotes').value = 'Duplicated from: ' + prompt.name;
            
            this.editor.setValue(prompt.prompt_text);
            
            const modal = new bootstrap.Modal(document.getElementById('promptModal'));
            modal.show();
        } catch (error) {
            console.error('Error duplicating prompt:', error);
            this.showError('Failed to duplicate prompt');
        }
    }

    /**
     * Save prompt
     */
    async savePrompt() {
        try {
            const id = document.getElementById('promptId').value;
            const tags = document.getElementById('promptTags').value
                .split(',')
                .map(t => t.trim())
                .filter(t => t);
            
            const data = {
                name: document.getElementById('promptName').value,
                description: document.getElementById('promptDescription').value || null,
                prompt_text: this.editor.getValue(),
                template_type: document.getElementById('promptType').value,
                language: document.getElementById('promptLanguage').value,
                strategy_id: document.getElementById('promptStrategy').value || null,
                is_active: document.getElementById('promptActive').checked,
                is_default: document.getElementById('promptDefault').checked,
                tags: tags.length > 0 ? tags : null,
                notes: document.getElementById('promptNotes').value || null,
            };
            
            // Validate
            if (!data.name || !data.prompt_text) {
                this.showError('Name and prompt text are required');
                return;
            }
            
            // Validate template syntax
            const validationResult = await this.validateTemplate(false);
            if (!validationResult.is_valid) {
                this.showError('Template has syntax errors. Please fix before saving.');
                return;
            }
            
            const url = id ? `/api/v1/prompts/${id}` : '/api/v1/prompts/';
            const method = id ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save prompt');
            }
            
            this.showSuccess(id ? 'Prompt updated successfully' : 'Prompt created successfully');
            
            bootstrap.Modal.getInstance(document.getElementById('promptModal')).hide();
            this.loadPrompts();
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.showError(error.message);
        }
    }

    /**
     * Delete prompt
     */
    async deletePrompt(id) {
        if (!confirm('Are you sure you want to delete this prompt? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/v1/prompts/${id}`, { method: 'DELETE' });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete prompt');
            }
            
            this.showSuccess('Prompt deleted successfully');
            this.loadPrompts();
        } catch (error) {
            console.error('Error deleting prompt:', error);
            this.showError(error.message);
        }
    }

    /**
     * Validate template syntax
     */
    async validateTemplate(showFeedback = true) {
        try {
            const templateText = this.editor.getValue();
            
            const response = await fetch('/api/v1/prompts/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ template_text: templateText })
            });
            
            const result = await response.json();
            
            if (showFeedback) {
                const feedback = document.getElementById('validationFeedback');
                if (result.is_valid) {
                    feedback.innerHTML = '<div class="alert alert-success"><i class="bi bi-check-circle me-2"></i>Template syntax is valid!</div>';
                } else {
                    feedback.innerHTML = `<div class="alert alert-danger"><i class="bi bi-x-circle me-2"></i>${this.escapeHtml(result.error_message)}</div>`;
                }
                
                setTimeout(() => { feedback.innerHTML = ''; }, 5000);
            }
            
            return result;
        } catch (error) {
            console.error('Error validating template:', error);
            if (showFeedback) {
                this.showError('Failed to validate template');
            }
            return { is_valid: false, error_message: error.message };
        }
    }

    /**
     * Show preview modal
     */
    showPreview() {
        const modal = new bootstrap.Modal(document.getElementById('previewModal'));
        modal.show();
    }

    /**
     * Render preview
     */
    async renderPreview() {
        try {
            const templateText = this.editor.getValue();
            const contextText = document.getElementById('previewContext').value;
            const context = JSON.parse(contextText);
            
            const response = await fetch('/api/v1/prompts/render', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_text: templateText,
                    context: context
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Render failed');
            }
            
            const result = await response.json();
            document.getElementById('previewOutput').textContent = result.rendered_text;
        } catch (error) {
            console.error('Error rendering preview:', error);
            document.getElementById('previewOutput').textContent = 'Error: ' + error.message;
        }
    }

    /**
     * Insert variable into editor
     */
    insertVariable(variable) {
        const position = this.editor.getPosition();
        const text = `{{ ${variable} }}`;
        
        this.editor.executeEdits('', [{
            range: new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column),
            text: text
        }]);
        
        this.editor.focus();
    }

    /**
     * Show performance modal
     */
    async showPerformance(promptId) {
        const modal = new bootstrap.Modal(document.getElementById('performanceModal'));
        const content = document.getElementById('performanceContent');
        
        // Get prompt info
        try {
            const promptResponse = await fetch(`/api/v1/prompts/${promptId}`);
            const prompt = await promptResponse.json();
            
            document.getElementById('performanceModalTitle').textContent = `Performance: ${prompt.name}`;
            
            modal.show();
            
            // Load performance data
            const perfResponse = await fetch(`/api/v1/prompts/${promptId}/performance`);
            const perfData = await perfResponse.json();
            
            if (perfData.length === 0) {
                content.innerHTML = `
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle me-2"></i>
                        No performance data available yet. Performance is calculated daily for completed signals.
                    </div>
                `;
                return;
            }
            
            // Calculate summary stats
            const totalSignals = perfData.reduce((sum, d) => sum + d.signals_generated, 0);
            const totalWins = perfData.reduce((sum, d) => sum + d.win_count, 0);
            const totalLosses = perfData.reduce((sum, d) => sum + d.loss_count, 0);
            const avgR = perfData.reduce((sum, d) => sum + (d.avg_r_multiple || 0), 0) / perfData.length;
            const totalPL = perfData.reduce((sum, d) => sum + (d.total_profit_loss || 0), 0);
            const winRate = totalWins / (totalWins + totalLosses);
            
            content.innerHTML = `
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h6 class="text-muted mb-2">Total Signals</h6>
                                <h3 class="mb-0">${totalSignals}</h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h6 class="text-muted mb-2">Win Rate</h6>
                                <h3 class="mb-0 ${winRate >= 0.5 ? 'text-success' : 'text-danger'}">
                                    ${(winRate * 100).toFixed(1)}%
                                </h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h6 class="text-muted mb-2">Avg R-Multiple</h6>
                                <h3 class="mb-0 ${avgR >= 1 ? 'text-success' : 'text-warning'}">
                                    ${avgR.toFixed(2)}R
                                </h3>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card text-center">
                            <div class="card-body">
                                <h6 class="text-muted mb-2">Total P/L</h6>
                                <h3 class="mb-0 ${totalPL >= 0 ? 'text-success' : 'text-danger'}">
                                    $${totalPL.toFixed(2)}
                                </h3>
                            </div>
                        </div>
                    </div>
                </div>
                
                <h6 class="mb-3">Daily Performance</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Signals</th>
                                <th>Wins</th>
                                <th>Losses</th>
                                <th>Win Rate</th>
                                <th>Avg R</th>
                                <th>P/L</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${perfData.map(d => {
                                const wr = d.win_count / (d.win_count + d.loss_count);
                                return `
                                    <tr>
                                        <td>${d.date}</td>
                                        <td>${d.signals_generated}</td>
                                        <td class="text-success">${d.win_count}</td>
                                        <td class="text-danger">${d.loss_count}</td>
                                        <td>${(wr * 100).toFixed(0)}%</td>
                                        <td>${d.avg_r_multiple ? d.avg_r_multiple.toFixed(2) + 'R' : 'N/A'}</td>
                                        <td class="${d.total_profit_loss >= 0 ? 'text-success' : 'text-danger'}">
                                            $${d.total_profit_loss ? d.total_profit_loss.toFixed(2) : '0.00'}
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (error) {
            console.error('Error loading performance:', error);
            content.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Failed to load performance data: ${error.message}
                </div>
            `;
        }
    }

    /**
     * Utility: Show success toast
     */
    showSuccess(message) {
        // You can implement a toast notification here
        alert(message);
    }

    /**
     * Utility: Show error toast
     */
    showError(message) {
        alert('Error: ' + message);
    }

    /**
     * Utility: Escape HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
let promptManager;
document.addEventListener('DOMContentLoaded', () => {
    promptManager = new PromptManager();
});

