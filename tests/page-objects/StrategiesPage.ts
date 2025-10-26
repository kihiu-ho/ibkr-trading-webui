import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class StrategiesPage extends BasePage {
  constructor(page: Page) {
    super(page, '/strategies');
  }

  // Page elements
  get pageTitle() {
    return this.page.locator('h1, [data-testid="page-title"]');
  }

  get createStrategyButton() {
    return this.page.locator('[data-testid="create-strategy-btn"]');
  }

  get strategiesTable() {
    return this.page.locator('[data-testid="strategies-table"]');
  }

  get strategiesGrid() {
    return this.page.locator('[data-testid="strategies-grid"]');
  }

  get searchInput() {
    return this.page.locator('[data-testid="search-strategies"]');
  }

  get filterDropdown() {
    return this.page.locator('[data-testid="filter-strategies"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-strategies"]');
  }

  // Strategy items
  get strategyItems() {
    return this.page.locator('[data-testid="strategy-item"]');
  }

  get activeStrategies() {
    return this.page.locator('[data-testid="strategy-item"][data-active="true"]');
  }

  get inactiveStrategies() {
    return this.page.locator('[data-testid="strategy-item"][data-active="false"]');
  }

  // Strategy actions
  getStrategyById(strategyId: string) {
    return this.page.locator(`[data-testid="strategy-item"][data-strategy-id="${strategyId}"]`);
  }

  getStrategyByName(strategyName: string) {
    return this.page.locator(`[data-testid="strategy-item"]:has-text("${strategyName}")`);
  }

  getEditButton(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="edit-strategy-btn"]');
  }

  getDeleteButton(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="delete-strategy-btn"]');
  }

  getExecuteButton(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="execute-strategy-btn"]');
  }

  getToggleActiveButton(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="toggle-active-btn"]');
  }

  getViewExecutionsButton(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="view-executions-btn"]');
  }

  // Strategy details
  getStrategyName(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="strategy-name"]');
  }

  getStrategySymbol(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="strategy-symbol"]');
  }

  getStrategyStatus(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="strategy-status"]');
  }

  getStrategyLastExecution(strategyId: string) {
    return this.getStrategyById(strategyId).locator('[data-testid="last-execution"]');
  }

  // Modals and forms
  get deleteConfirmModal() {
    return this.page.locator('[data-testid="delete-confirm-modal"]');
  }

  get confirmDeleteButton() {
    return this.deleteConfirmModal.locator('[data-testid="confirm-delete-btn"]');
  }

  get cancelDeleteButton() {
    return this.deleteConfirmModal.locator('[data-testid="cancel-delete-btn"]');
  }

  // Methods
  async waitForStrategiesLoad() {
    await this.waitForPageLoad();
    await this.strategiesTable.waitFor({ state: 'visible' });
  }

  async searchStrategies(searchTerm: string) {
    await this.searchInput.fill(searchTerm);
    await this.waitForApiResponse('/api/strategies');
  }

  async filterStrategies(filter: 'all' | 'active' | 'inactive') {
    await this.filterDropdown.selectOption(filter);
    await this.waitForApiResponse('/api/strategies');
  }

  async refreshStrategies() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/strategies');
  }

  async createNewStrategy() {
    await this.createStrategyButton.click();
    await this.page.waitForURL('**/strategies/new');
  }

  async editStrategy(strategyId: string) {
    await this.getEditButton(strategyId).click();
    await this.page.waitForURL(`**/strategies/${strategyId}/edit`);
  }

  async deleteStrategy(strategyId: string) {
    await this.getDeleteButton(strategyId).click();
    await this.deleteConfirmModal.waitFor({ state: 'visible' });
    await this.confirmDeleteButton.click();
    await this.waitForApiResponse(`/api/strategies/${strategyId}`);
    await this.waitForToast('Strategy deleted successfully');
  }

  async executeStrategy(strategyId: string) {
    await this.getExecuteButton(strategyId).click();
    await this.waitForApiResponse(`/api/strategies/${strategyId}/execute`);
    await this.waitForToast('Workflow execution started');
  }

  async toggleStrategyActive(strategyId: string) {
    const currentStatus = await this.getStrategyStatus(strategyId).textContent();
    await this.getToggleActiveButton(strategyId).click();
    await this.waitForApiResponse(`/api/strategies/${strategyId}`);
    
    // Wait for status to change
    const newStatus = currentStatus === 'Active' ? 'Inactive' : 'Active';
    await expect(this.getStrategyStatus(strategyId)).toContainText(newStatus);
  }

  async viewStrategyExecutions(strategyId: string) {
    await this.getViewExecutionsButton(strategyId).click();
    await this.page.waitForURL(`**/workflows/lineage?strategy_id=${strategyId}`);
  }

  async getStrategyData(strategyId: string) {
    const strategy = this.getStrategyById(strategyId);
    await strategy.waitFor({ state: 'visible' });
    
    return {
      id: strategyId,
      name: await this.getStrategyName(strategyId).textContent(),
      symbol: await this.getStrategySymbol(strategyId).textContent(),
      status: await this.getStrategyStatus(strategyId).textContent(),
      lastExecution: await this.getStrategyLastExecution(strategyId).textContent()
    };
  }

  async getAllStrategies() {
    await this.waitForStrategiesLoad();
    const items = await this.strategyItems.all();
    
    const strategies = [];
    for (const item of items) {
      const id = await item.getAttribute('data-strategy-id');
      if (id) {
        const data = await this.getStrategyData(id);
        strategies.push(data);
      }
    }
    
    return strategies;
  }

  // Assertions
  async assertStrategiesPageLoaded() {
    await this.assertElementVisible('[data-testid="strategies-table"]');
    await this.assertElementVisible('[data-testid="create-strategy-btn"]');
  }

  async assertStrategyExists(strategyId: string) {
    await this.assertElementVisible(`[data-testid="strategy-item"][data-strategy-id="${strategyId}"]`);
  }

  async assertStrategyNotExists(strategyId: string) {
    await this.assertElementHidden(`[data-testid="strategy-item"][data-strategy-id="${strategyId}"]`);
  }

  async assertStrategyStatus(strategyId: string, expectedStatus: 'Active' | 'Inactive') {
    await expect(this.getStrategyStatus(strategyId)).toContainText(expectedStatus);
  }

  async assertStrategyCount(expectedCount: number) {
    const actualCount = await this.strategyItems.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertActiveStrategyCount(expectedCount: number) {
    const actualCount = await this.activeStrategies.count();
    expect(actualCount).toBe(expectedCount);
  }

  async assertSearchResults(searchTerm: string) {
    const items = await this.strategyItems.all();
    for (const item of items) {
      const text = await item.textContent();
      expect(text?.toLowerCase()).toContain(searchTerm.toLowerCase());
    }
  }
}
