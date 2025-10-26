import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  constructor(page: Page) {
    super(page, '/');
  }

  // Dashboard sections
  get workflowStatsSection() {
    return this.page.locator('[data-testid="workflow-stats"]');
  }

  get activeExecutionsSection() {
    return this.page.locator('[data-testid="active-executions"]');
  }

  get recentResultsSection() {
    return this.page.locator('[data-testid="recent-results"]');
  }

  get strategyManagementPanel() {
    return this.page.locator('[data-testid="strategy-management"]');
  }

  // Workflow statistics
  get totalExecutionsCount() {
    return this.page.locator('[data-testid="total-executions"]');
  }

  get successfulExecutionsCount() {
    return this.page.locator('[data-testid="successful-executions"]');
  }

  get failedExecutionsCount() {
    return this.page.locator('[data-testid="failed-executions"]');
  }

  get successRate() {
    return this.page.locator('[data-testid="success-rate"]');
  }

  get averageExecutionTime() {
    return this.page.locator('[data-testid="avg-execution-time"]');
  }

  // Active executions
  get activeExecutionsList() {
    return this.page.locator('[data-testid="active-executions-list"]');
  }

  get activeExecutionItems() {
    return this.activeExecutionsList.locator('.execution-item');
  }

  // Recent results
  get recentResultsList() {
    return this.page.locator('[data-testid="recent-results-list"]');
  }

  get recentResultItems() {
    return this.recentResultsList.locator('.result-item');
  }

  // Strategy management
  get activeStrategiesCount() {
    return this.page.locator('[data-testid="active-strategies-count"]');
  }

  get strategiesList() {
    return this.page.locator('[data-testid="strategies-list"]');
  }

  get createStrategyButton() {
    return this.page.locator('[data-testid="create-strategy-btn"]');
  }

  get manageStrategiesButton() {
    return this.page.locator('[data-testid="manage-strategies-btn"]');
  }

  // Quick actions
  get quickActionsPanel() {
    return this.page.locator('[data-testid="quick-actions"]');
  }

  get executeWorkflowButton() {
    return this.page.locator('[data-testid="execute-workflow-btn"]');
  }

  get viewLineageButton() {
    return this.page.locator('[data-testid="view-lineage-btn"]');
  }

  get refreshDashboardButton() {
    return this.page.locator('[data-testid="refresh-dashboard-btn"]');
  }

  // Methods
  async waitForDashboardLoad() {
    await this.waitForPageLoad();
    await this.workflowStatsSection.waitFor({ state: 'visible' });
    await this.activeExecutionsSection.waitFor({ state: 'visible' });
    await this.recentResultsSection.waitFor({ state: 'visible' });
  }

  async getWorkflowStats() {
    await this.workflowStatsSection.waitFor({ state: 'visible' });
    
    return {
      totalExecutions: await this.totalExecutionsCount.textContent(),
      successfulExecutions: await this.successfulExecutionsCount.textContent(),
      failedExecutions: await this.failedExecutionsCount.textContent(),
      successRate: await this.successRate.textContent(),
      averageExecutionTime: await this.averageExecutionTime.textContent()
    };
  }

  async getActiveExecutions() {
    await this.activeExecutionsSection.waitFor({ state: 'visible' });
    const items = await this.activeExecutionItems.all();
    
    const executions = [];
    for (const item of items) {
      const id = await item.locator('[data-testid="execution-id"]').textContent();
      const strategy = await item.locator('[data-testid="strategy-name"]').textContent();
      const status = await item.locator('[data-testid="execution-status"]').textContent();
      const progress = await item.locator('[data-testid="execution-progress"]').textContent();
      
      executions.push({ id, strategy, status, progress });
    }
    
    return executions;
  }

  async getRecentResults() {
    await this.recentResultsSection.waitFor({ state: 'visible' });
    const items = await this.recentResultItems.all();
    
    const results = [];
    for (const item of items) {
      const strategy = await item.locator('[data-testid="strategy-name"]').textContent();
      const status = await item.locator('[data-testid="result-status"]').textContent();
      const timestamp = await item.locator('[data-testid="result-timestamp"]').textContent();
      const duration = await item.locator('[data-testid="result-duration"]').textContent();
      
      results.push({ strategy, status, timestamp, duration });
    }
    
    return results;
  }

  async clickActiveExecution(executionId: string) {
    const execution = this.activeExecutionItems.filter({ hasText: executionId });
    await execution.click();
  }

  async clickRecentResult(index: number) {
    const result = this.recentResultItems.nth(index);
    await result.click();
  }

  async refreshDashboard() {
    await this.refreshDashboardButton.click();
    await this.waitForApiResponse('/api/dashboard');
    await this.waitForDashboardLoad();
  }

  async navigateToStrategies() {
    await this.manageStrategiesButton.click();
    await this.page.waitForURL('**/strategies');
  }

  async navigateToWorkflows() {
    await this.executeWorkflowButton.click();
    await this.page.waitForURL('**/workflows');
  }

  async navigateToLineage() {
    await this.viewLineageButton.click();
    await this.page.waitForURL('**/workflows/lineage');
  }

  async createNewStrategy() {
    await this.createStrategyButton.click();
    await this.page.waitForURL('**/strategies/new');
  }

  // Assertions
  async assertDashboardLoaded() {
    await this.assertElementVisible('[data-testid="workflow-stats"]');
    await this.assertElementVisible('[data-testid="active-executions"]');
    await this.assertElementVisible('[data-testid="recent-results"]');
    await this.assertElementVisible('[data-testid="strategy-management"]');
  }

  async assertWorkflowStatsVisible() {
    await this.assertElementVisible('[data-testid="total-executions"]');
    await this.assertElementVisible('[data-testid="successful-executions"]');
    await this.assertElementVisible('[data-testid="failed-executions"]');
    await this.assertElementVisible('[data-testid="success-rate"]');
  }

  async assertActiveExecutionsCount(expectedCount: number) {
    const actualCount = await this.activeExecutionItems.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertRecentResultsCount(expectedCount: number) {
    const actualCount = await this.recentResultItems.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertExecutionStatus(executionId: string, expectedStatus: string) {
    const execution = this.activeExecutionItems.filter({ hasText: executionId });
    const status = execution.locator('[data-testid="execution-status"]');
    await expect(status).toContainText(expectedStatus);
  }
}
