import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class WorkflowsPage extends BasePage {
  constructor(page: Page) {
    super(page, '/workflows');
  }

  // Page elements
  get pageTitle() {
    return this.page.locator('h1, [data-testid="page-title"]');
  }

  get executionsTable() {
    return this.page.locator('[data-testid="executions-table"]');
  }

  get triggerWorkflowButton() {
    return this.page.locator('[data-testid="trigger-workflow-btn"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-executions"]');
  }

  get filterDropdown() {
    return this.page.locator('[data-testid="filter-executions"]');
  }

  // Execution items
  get executionItems() {
    return this.page.locator('[data-testid="execution-item"]');
  }

  get runningExecutions() {
    return this.page.locator('[data-testid="execution-item"][data-status="running"]');
  }

  get completedExecutions() {
    return this.page.locator('[data-testid="execution-item"][data-status="completed"]');
  }

  get failedExecutions() {
    return this.page.locator('[data-testid="execution-item"][data-status="failed"]');
  }

  // Execution details
  getExecutionById(executionId: string) {
    return this.page.locator(`[data-testid="execution-item"][data-execution-id="${executionId}"]`);
  }

  getExecutionStatus(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="execution-status"]');
  }

  getExecutionProgress(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="execution-progress"]');
  }

  getExecutionStrategy(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="execution-strategy"]');
  }

  getExecutionStartTime(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="execution-start-time"]');
  }

  getExecutionDuration(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="execution-duration"]');
  }

  // Execution controls
  getViewDetailsButton(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="view-details-btn"]');
  }

  getPauseButton(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="pause-execution-btn"]');
  }

  getResumeButton(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="resume-execution-btn"]');
  }

  getStopButton(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="stop-execution-btn"]');
  }

  getViewLineageButton(executionId: string) {
    return this.getExecutionById(executionId).locator('[data-testid="view-lineage-btn"]');
  }

  // Real-time monitoring
  get realTimeUpdatesToggle() {
    return this.page.locator('[data-testid="realtime-updates-toggle"]');
  }

  get connectionStatus() {
    return this.page.locator('[data-testid="connection-status"]');
  }

  // Workflow trigger modal
  get triggerWorkflowModal() {
    return this.page.locator('[data-testid="trigger-workflow-modal"]');
  }

  get strategySelect() {
    return this.triggerWorkflowModal.locator('[data-testid="strategy-select"]');
  }

  get confirmTriggerButton() {
    return this.triggerWorkflowModal.locator('[data-testid="confirm-trigger-btn"]');
  }

  get cancelTriggerButton() {
    return this.triggerWorkflowModal.locator('[data-testid="cancel-trigger-btn"]');
  }

  // Methods
  async waitForWorkflowsLoad() {
    await this.waitForPageLoad();
    await this.executionsTable.waitFor({ state: 'visible' });
  }

  async refreshExecutions() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/workflows/executions');
  }

  async filterExecutions(filter: 'all' | 'running' | 'completed' | 'failed') {
    await this.filterDropdown.selectOption(filter);
    await this.waitForApiResponse('/api/workflows/executions');
  }

  async triggerWorkflow(strategyId: string) {
    await this.triggerWorkflowButton.click();
    await this.triggerWorkflowModal.waitFor({ state: 'visible' });
    await this.strategySelect.selectOption(strategyId);
    await this.confirmTriggerButton.click();
    await this.waitForApiResponse('/api/strategies/*/execute');
    await this.waitForToast('Workflow execution started');
  }

  async viewExecutionDetails(executionId: string) {
    await this.getViewDetailsButton(executionId).click();
    await this.page.waitForURL(`**/workflows/executions/${executionId}`);
  }

  async pauseExecution(executionId: string) {
    await this.getPauseButton(executionId).click();
    await this.waitForApiResponse(`/api/workflows/executions/${executionId}/pause`);
    await expect(this.getExecutionStatus(executionId)).toContainText('Paused');
  }

  async resumeExecution(executionId: string) {
    await this.getResumeButton(executionId).click();
    await this.waitForApiResponse(`/api/workflows/executions/${executionId}/resume`);
    await expect(this.getExecutionStatus(executionId)).toContainText('Running');
  }

  async stopExecution(executionId: string) {
    await this.getStopButton(executionId).click();
    await this.waitForApiResponse(`/api/workflows/executions/${executionId}/stop`);
    await expect(this.getExecutionStatus(executionId)).toContainText('Stopped');
  }

  async viewExecutionLineage(executionId: string) {
    await this.getViewLineageButton(executionId).click();
    await this.page.waitForURL(`**/workflows/lineage?execution_id=${executionId}`);
  }

  async enableRealTimeUpdates() {
    if (!(await this.realTimeUpdatesToggle.isChecked())) {
      await this.realTimeUpdatesToggle.check();
    }
    await expect(this.connectionStatus).toContainText('Connected');
  }

  async disableRealTimeUpdates() {
    if (await this.realTimeUpdatesToggle.isChecked()) {
      await this.realTimeUpdatesToggle.uncheck();
    }
    await expect(this.connectionStatus).toContainText('Disconnected');
  }

  async waitForExecutionStatusChange(executionId: string, expectedStatus: string, timeout = 30000) {
    await expect(this.getExecutionStatus(executionId)).toContainText(expectedStatus, { timeout });
  }

  async waitForExecutionCompletion(executionId: string, timeout = 300000) {
    await expect(this.getExecutionStatus(executionId)).toContainText(/Completed|Failed/, { timeout });
  }

  async getExecutionData(executionId: string) {
    const execution = this.getExecutionById(executionId);
    await execution.waitFor({ state: 'visible' });
    
    return {
      id: executionId,
      status: await this.getExecutionStatus(executionId).textContent(),
      progress: await this.getExecutionProgress(executionId).textContent(),
      strategy: await this.getExecutionStrategy(executionId).textContent(),
      startTime: await this.getExecutionStartTime(executionId).textContent(),
      duration: await this.getExecutionDuration(executionId).textContent()
    };
  }

  async getAllExecutions() {
    await this.waitForWorkflowsLoad();
    const items = await this.executionItems.all();
    
    const executions = [];
    for (const item of items) {
      const id = await item.getAttribute('data-execution-id');
      if (id) {
        const data = await this.getExecutionData(id);
        executions.push(data);
      }
    }
    
    return executions;
  }

  // Assertions
  async assertWorkflowsPageLoaded() {
    await this.assertElementVisible('[data-testid="executions-table"]');
    await this.assertElementVisible('[data-testid="trigger-workflow-btn"]');
  }

  async assertExecutionExists(executionId: string) {
    await this.assertElementVisible(`[data-testid="execution-item"][data-execution-id="${executionId}"]`);
  }

  async assertExecutionStatus(executionId: string, expectedStatus: string) {
    await expect(this.getExecutionStatus(executionId)).toContainText(expectedStatus);
  }

  async assertExecutionCount(expectedCount: number) {
    const actualCount = await this.executionItems.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertRunningExecutionCount(expectedCount: number) {
    const actualCount = await this.runningExecutions.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertRealTimeConnection() {
    await this.assertElementText('[data-testid="connection-status"]', 'Connected');
  }
}
