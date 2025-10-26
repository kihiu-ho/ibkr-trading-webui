import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class LineagePage extends BasePage {
  constructor(page: Page) {
    super(page, '/workflows/lineage');
  }

  // Page elements
  get pageTitle() {
    return this.page.locator('h1, [data-testid="page-title"]');
  }

  get strategySelect() {
    return this.page.locator('[data-testid="strategy-select"]');
  }

  get executionSelect() {
    return this.page.locator('[data-testid="execution-select"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-lineage"]');
  }

  // Lineage visualization
  get lineageContainer() {
    return this.page.locator('[data-testid="lineage-container"]');
  }

  get stepCards() {
    return this.page.locator('[data-testid="step-card"]');
  }

  get stepConnectors() {
    return this.page.locator('[data-testid="step-connector"]');
  }

  // Step details
  getStepCard(stepIndex: number) {
    return this.stepCards.nth(stepIndex);
  }

  getStepByName(stepName: string) {
    return this.page.locator(`[data-testid="step-card"][data-step-name="${stepName}"]`);
  }

  getStepStatus(stepIndex: number) {
    return this.getStepCard(stepIndex).locator('[data-testid="step-status"]');
  }

  getStepName(stepIndex: number) {
    return this.getStepCard(stepIndex).locator('[data-testid="step-name"]');
  }

  getStepDuration(stepIndex: number) {
    return this.getStepCard(stepIndex).locator('[data-testid="step-duration"]');
  }

  getStepVisualization(stepIndex: number) {
    return this.getStepCard(stepIndex).locator('[data-testid="step-visualization"]');
  }

  getViewDetailsButton(stepIndex: number) {
    return this.getStepCard(stepIndex).locator('[data-testid="view-details-btn"]');
  }

  // Step detail modal
  get stepDetailModal() {
    return this.page.locator('[data-testid="step-detail-modal"]');
  }

  get modalStepName() {
    return this.stepDetailModal.locator('[data-testid="modal-step-name"]');
  }

  get modalVisualization() {
    return this.stepDetailModal.locator('[data-testid="modal-visualization"]');
  }

  get rawInputToggle() {
    return this.stepDetailModal.locator('[data-testid="raw-input-toggle"]');
  }

  get rawOutputToggle() {
    return this.stepDetailModal.locator('[data-testid="raw-output-toggle"]');
  }

  get rawInputData() {
    return this.stepDetailModal.locator('[data-testid="raw-input-data"]');
  }

  get rawOutputData() {
    return this.stepDetailModal.locator('[data-testid="raw-output-data"]');
  }

  get closeModalButton() {
    return this.stepDetailModal.locator('[data-testid="close-modal-btn"]');
  }

  // Statistics
  get lineageStats() {
    return this.page.locator('[data-testid="lineage-stats"]');
  }

  get totalStepsCount() {
    return this.lineageStats.locator('[data-testid="total-steps"]');
  }

  get successfulStepsCount() {
    return this.lineageStats.locator('[data-testid="successful-steps"]');
  }

  get failedStepsCount() {
    return this.lineageStats.locator('[data-testid="failed-steps"]');
  }

  // Empty state
  get emptyState() {
    return this.page.locator('[data-testid="empty-state"]');
  }

  // Methods
  async waitForLineageLoad() {
    await this.waitForPageLoad();
    await this.lineageContainer.waitFor({ state: 'visible' });
  }

  async selectStrategy(strategyId: string) {
    await this.strategySelect.selectOption(strategyId);
    await this.waitForApiResponse(`/api/strategies/${strategyId}/executions`);
  }

  async selectExecution(executionId: string) {
    await this.executionSelect.selectOption(executionId);
    await this.waitForApiResponse(`/api/lineage/execution/${executionId}`);
    await this.waitForLineageLoad();
  }

  async refreshLineage() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/lineage/execution/*');
  }

  async viewStepDetails(stepIndex: number) {
    await this.getViewDetailsButton(stepIndex).click();
    await this.stepDetailModal.waitFor({ state: 'visible' });
  }

  async closeStepDetails() {
    await this.closeModalButton.click();
    await this.stepDetailModal.waitFor({ state: 'hidden' });
  }

  async toggleRawInput() {
    await this.rawInputToggle.click();
    await this.rawInputData.waitFor({ state: 'visible' });
  }

  async toggleRawOutput() {
    await this.rawOutputToggle.click();
    await this.rawOutputData.waitFor({ state: 'visible' });
  }

  async getStepData(stepIndex: number) {
    const stepCard = this.getStepCard(stepIndex);
    await stepCard.waitFor({ state: 'visible' });
    
    return {
      name: await this.getStepName(stepIndex).textContent(),
      status: await this.getStepStatus(stepIndex).textContent(),
      duration: await this.getStepDuration(stepIndex).textContent()
    };
  }

  async getAllSteps() {
    await this.waitForLineageLoad();
    const stepCount = await this.stepCards.count();
    
    const steps = [];
    for (let i = 0; i < stepCount; i++) {
      const stepData = await this.getStepData(i);
      steps.push(stepData);
    }
    
    return steps;
  }

  async getLineageStats() {
    await this.lineageStats.waitFor({ state: 'visible' });
    
    return {
      totalSteps: await this.totalStepsCount.textContent(),
      successfulSteps: await this.successfulStepsCount.textContent(),
      failedSteps: await this.failedStepsCount.textContent()
    };
  }

  async waitForStepVisualization(stepIndex: number) {
    const visualization = this.getStepVisualization(stepIndex);
    await visualization.waitFor({ state: 'visible' });
    return visualization;
  }

  async getStepVisualizationType(stepIndex: number) {
    const visualization = await this.waitForStepVisualization(stepIndex);
    
    // Check for different visualization types
    if (await visualization.locator('.strategy-config').isVisible()) {
      return 'strategy';
    } else if (await visualization.locator('.market-data').isVisible()) {
      return 'market-data';
    } else if (await visualization.locator('.indicators').isVisible()) {
      return 'indicators';
    } else if (await visualization.locator('.charts').isVisible()) {
      return 'charts';
    } else if (await visualization.locator('.llm-analysis').isVisible()) {
      return 'llm-analysis';
    } else if (await visualization.locator('.trading-signal').isVisible()) {
      return 'signal';
    } else if (await visualization.locator('.order-details').isVisible()) {
      return 'order';
    } else {
      return 'generic';
    }
  }

  // Assertions
  async assertLineagePageLoaded() {
    await this.assertElementVisible('[data-testid="lineage-container"]');
    await this.assertElementVisible('[data-testid="strategy-select"]');
    await this.assertElementVisible('[data-testid="execution-select"]');
  }

  async assertStepCount(expectedCount: number) {
    const actualCount = await this.stepCards.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertStepStatus(stepIndex: number, expectedStatus: 'SUCCESS' | 'FAILED' | 'PENDING') {
    await expect(this.getStepStatus(stepIndex)).toContainText(expectedStatus);
  }

  async assertStepExists(stepName: string) {
    await this.assertElementVisible(`[data-testid="step-card"][data-step-name="${stepName}"]`);
  }

  async assertVisualizationVisible(stepIndex: number) {
    await this.assertElementVisible(`[data-testid="step-card"]:nth-child(${stepIndex + 1}) [data-testid="step-visualization"]`);
  }

  async assertEmptyState() {
    await this.assertElementVisible('[data-testid="empty-state"]');
  }

  async assertLineageStats(expectedStats: { total: number; successful: number; failed: number }) {
    await expect(this.totalStepsCount).toContainText(expectedStats.total.toString());
    await expect(this.successfulStepsCount).toContainText(expectedStats.successful.toString());
    await expect(this.failedStepsCount).toContainText(expectedStats.failed.toString());
  }

  async assertStepDetailModalOpen(stepName: string) {
    await this.assertElementVisible('[data-testid="step-detail-modal"]');
    await expect(this.modalStepName).toContainText(stepName);
  }

  async assertRawDataVisible(dataType: 'input' | 'output') {
    const selector = dataType === 'input' ? '[data-testid="raw-input-data"]' : '[data-testid="raw-output-data"]';
    await this.assertElementVisible(selector);
  }
}
