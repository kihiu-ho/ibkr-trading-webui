import { test as base, expect } from '@playwright/test';
import { APIMocks } from './api-mocks';
import { TestDataGenerator } from './test-data';
import { 
  DashboardPage, 
  StrategiesPage, 
  WorkflowsPage, 
  LineagePage, 
  IBKRAuthPage,
  StrategyFormPage,
  OrdersPage,
  PortfolioPage,
  MarketDataPage
} from '../page-objects';

// Extend the base test with custom fixtures
export const test = base.extend<{
  apiMocks: APIMocks;
  testData: typeof TestDataGenerator;
  dashboardPage: DashboardPage;
  strategiesPage: StrategiesPage;
  workflowsPage: WorkflowsPage;
  lineagePage: LineagePage;
  ibkrAuthPage: IBKRAuthPage;
  strategyFormPage: StrategyFormPage;
  ordersPage: OrdersPage;
  portfolioPage: PortfolioPage;
  marketDataPage: MarketDataPage;
}>({
  // API Mocks fixture
  apiMocks: async ({ page }, use) => {
    const mocks = new APIMocks(page);
    await use(mocks);
  },

  // Test Data Generator fixture
  testData: async ({}, use) => {
    await use(TestDataGenerator);
  },

  // Page Object fixtures
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  strategiesPage: async ({ page }, use) => {
    await use(new StrategiesPage(page));
  },

  workflowsPage: async ({ page }, use) => {
    await use(new WorkflowsPage(page));
  },

  lineagePage: async ({ page }, use) => {
    await use(new LineagePage(page));
  },

  ibkrAuthPage: async ({ page }, use) => {
    await use(new IBKRAuthPage(page));
  },

  strategyFormPage: async ({ page }, use) => {
    await use(new StrategyFormPage(page));
  },

  ordersPage: async ({ page }, use) => {
    await use(new OrdersPage(page));
  },

  portfolioPage: async ({ page }, use) => {
    await use(new PortfolioPage(page));
  },

  marketDataPage: async ({ page }, use) => {
    await use(new MarketDataPage(page));
  }
});

// Custom expect extensions for trading-specific assertions
expect.extend({
  toBeValidPrice(received: string | number) {
    const price = typeof received === 'string' ? parseFloat(received) : received;
    const pass = !isNaN(price) && price > 0;
    
    return {
      message: () => `expected ${received} to be a valid price`,
      pass,
    };
  },

  toBeValidPercentage(received: string | number) {
    const percentage = typeof received === 'string' ? parseFloat(received.replace('%', '')) : received;
    const pass = !isNaN(percentage) && percentage >= -100 && percentage <= 100;
    
    return {
      message: () => `expected ${received} to be a valid percentage`,
      pass,
    };
  },

  toBeValidExecutionStatus(received: string) {
    const validStatuses = ['running', 'completed', 'failed', 'paused', 'pending', 'cancelled'];
    const pass = validStatuses.includes(received.toLowerCase());
    
    return {
      message: () => `expected ${received} to be a valid execution status`,
      pass,
    };
  },

  toBeValidOrderSide(received: string) {
    const validSides = ['BUY', 'SELL', 'buy', 'sell'];
    const pass = validSides.includes(received);
    
    return {
      message: () => `expected ${received} to be a valid order side (BUY/SELL)`,
      pass,
    };
  },

  toBeValidSymbol(received: string) {
    const symbolPattern = /^[A-Z]{1,5}$/;
    const pass = symbolPattern.test(received);
    
    return {
      message: () => `expected ${received} to be a valid stock symbol`,
      pass,
    };
  }
});

// Declare custom matchers for TypeScript
declare global {
  namespace PlaywrightTest {
    interface Matchers<R> {
      toBeValidPrice(): R;
      toBeValidPercentage(): R;
      toBeValidExecutionStatus(): R;
      toBeValidOrderSide(): R;
      toBeValidSymbol(): R;
    }
  }
}

// Test utilities
export class TestUtils {
  static async waitForStableElement(page: any, selector: string, timeout = 5000) {
    let previousText = '';
    let stableCount = 0;
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        const element = page.locator(selector);
        await element.waitFor({ state: 'visible', timeout: 1000 });
        const currentText = await element.textContent();
        
        if (currentText === previousText) {
          stableCount++;
          if (stableCount >= 3) { // Stable for 3 checks
            return;
          }
        } else {
          stableCount = 0;
          previousText = currentText || '';
        }
        
        await page.waitForTimeout(500);
      } catch (error) {
        // Element might not be ready yet
        await page.waitForTimeout(500);
      }
    }
    
    throw new Error(`Element ${selector} did not stabilize within ${timeout}ms`);
  }

  static async retryAction(action: () => Promise<void>, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        await action();
        return;
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error;
        }
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  static generateUniqueId(): string {
    return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  static async takeFullPageScreenshot(page: any, name: string) {
    await page.screenshot({
      path: `test-results/screenshots/${name}_${Date.now()}.png`,
      fullPage: true
    });
  }

  static async logPagePerformance(page: any) {
    const metrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime
      };
    });
    
    console.log('Page Performance Metrics:', metrics);
    return metrics;
  }

  static async waitForNetworkIdle(page: any, timeout = 5000) {
    let requestCount = 0;
    let responseCount = 0;
    
    const requestHandler = () => requestCount++;
    const responseHandler = () => responseCount++;
    
    page.on('request', requestHandler);
    page.on('response', responseHandler);
    
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (requestCount === responseCount && requestCount > 0) {
        break;
      }
      await page.waitForTimeout(100);
    }
    
    page.off('request', requestHandler);
    page.off('response', responseHandler);
  }
}

export { expect };
