import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class PortfolioPage extends BasePage {
  constructor(page: Page) {
    super(page, '/portfolio');
  }

  // Page elements
  get portfolioSummary() {
    return this.page.locator('[data-testid="portfolio-summary"]');
  }

  get positionsTable() {
    return this.page.locator('[data-testid="positions-table"]');
  }

  get positionItems() {
    return this.page.locator('[data-testid="position-item"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-portfolio"]');
  }

  // Portfolio summary
  get totalValue() {
    return this.page.locator('[data-testid="total-value"]');
  }

  get totalPnL() {
    return this.page.locator('[data-testid="total-pnl"]');
  }

  get totalPnLPercent() {
    return this.page.locator('[data-testid="total-pnl-percent"]');
  }

  get cashBalance() {
    return this.page.locator('[data-testid="cash-balance"]');
  }

  get buyingPower() {
    return this.page.locator('[data-testid="buying-power"]');
  }

  // Position details
  getPositionBySymbol(symbol: string) {
    return this.page.locator(`[data-testid="position-item"][data-symbol="${symbol}"]`);
  }

  getPositionQuantity(symbol: string) {
    return this.getPositionBySymbol(symbol).locator('[data-testid="position-quantity"]');
  }

  getPositionAvgPrice(symbol: string) {
    return this.getPositionBySymbol(symbol).locator('[data-testid="position-avg-price"]');
  }

  getPositionCurrentPrice(symbol: string) {
    return this.getPositionBySymbol(symbol).locator('[data-testid="position-current-price"]');
  }

  getPositionPnL(symbol: string) {
    return this.getPositionBySymbol(symbol).locator('[data-testid="position-pnl"]');
  }

  getPositionPnLPercent(symbol: string) {
    return this.getPositionBySymbol(symbol).locator('[data-testid="position-pnl-percent"]');
  }

  // Methods
  async waitForPortfolioLoad() {
    await this.waitForPageLoad();
    await this.portfolioSummary.waitFor({ state: 'visible' });
    await this.positionsTable.waitFor({ state: 'visible' });
  }

  async refreshPortfolio() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/portfolio');
  }

  async getPortfolioSummary() {
    await this.portfolioSummary.waitFor({ state: 'visible' });
    
    return {
      totalValue: await this.totalValue.textContent(),
      totalPnL: await this.totalPnL.textContent(),
      totalPnLPercent: await this.totalPnLPercent.textContent(),
      cashBalance: await this.cashBalance.textContent(),
      buyingPower: await this.buyingPower.textContent()
    };
  }

  async getPositionData(symbol: string) {
    const position = this.getPositionBySymbol(symbol);
    await position.waitFor({ state: 'visible' });
    
    return {
      symbol,
      quantity: await this.getPositionQuantity(symbol).textContent(),
      avgPrice: await this.getPositionAvgPrice(symbol).textContent(),
      currentPrice: await this.getPositionCurrentPrice(symbol).textContent(),
      pnl: await this.getPositionPnL(symbol).textContent(),
      pnlPercent: await this.getPositionPnLPercent(symbol).textContent()
    };
  }

  async getAllPositions() {
    await this.waitForPortfolioLoad();
    const items = await this.positionItems.all();
    
    const positions = [];
    for (const item of items) {
      const symbol = await item.getAttribute('data-symbol');
      if (symbol) {
        const data = await this.getPositionData(symbol);
        positions.push(data);
      }
    }
    
    return positions;
  }

  // Assertions
  async assertPortfolioLoaded() {
    await this.assertElementVisible('[data-testid="portfolio-summary"]');
    await this.assertElementVisible('[data-testid="positions-table"]');
  }

  async assertPositionExists(symbol: string) {
    await this.assertElementVisible(`[data-testid="position-item"][data-symbol="${symbol}"]`);
  }

  async assertPositionPnL(symbol: string, expectedPnL: string) {
    await expect(this.getPositionPnL(symbol)).toContainText(expectedPnL);
  }
}
