import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class MarketDataPage extends BasePage {
  constructor(page: Page) {
    super(page, '/market-data');
  }

  // Page elements
  get symbolInput() {
    return this.page.locator('[data-testid="symbol-input"]');
  }

  get searchButton() {
    return this.page.locator('[data-testid="search-symbol"]');
  }

  get marketDataTable() {
    return this.page.locator('[data-testid="market-data-table"]');
  }

  get priceChart() {
    return this.page.locator('[data-testid="price-chart"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-data"]');
  }

  // Symbol data
  getSymbolData(symbol: string) {
    return this.page.locator(`[data-testid="symbol-data"][data-symbol="${symbol}"]`);
  }

  getSymbolPrice(symbol: string) {
    return this.getSymbolData(symbol).locator('[data-testid="current-price"]');
  }

  getSymbolChange(symbol: string) {
    return this.getSymbolData(symbol).locator('[data-testid="price-change"]');
  }

  getSymbolVolume(symbol: string) {
    return this.getSymbolData(symbol).locator('[data-testid="volume"]');
  }

  // Methods
  async searchSymbol(symbol: string) {
    await this.symbolInput.fill(symbol);
    await this.searchButton.click();
    await this.waitForApiResponse('/api/market-data');
  }

  async refreshMarketData() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/market-data');
  }

  async getSymbolInfo(symbol: string) {
    const symbolData = this.getSymbolData(symbol);
    await symbolData.waitFor({ state: 'visible' });
    
    return {
      symbol,
      price: await this.getSymbolPrice(symbol).textContent(),
      change: await this.getSymbolChange(symbol).textContent(),
      volume: await this.getSymbolVolume(symbol).textContent()
    };
  }

  // Assertions
  async assertSymbolDataVisible(symbol: string) {
    await this.assertElementVisible(`[data-testid="symbol-data"][data-symbol="${symbol}"]`);
  }

  async assertPriceChartVisible() {
    await this.assertElementVisible('[data-testid="price-chart"]');
  }
}
