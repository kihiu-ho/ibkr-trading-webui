import { chromium, FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global test setup...');

  // Ensure test-results directory exists
  const testResultsDir = path.join(__dirname, 'test-results');
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }

  // Setup test database
  await setupTestDatabase();

  // Setup mock data
  await setupMockData();

  // Warm up the application
  await warmupApplication();

  console.log('✅ Global test setup completed');
}

async function setupTestDatabase() {
  console.log('📊 Setting up test database...');
  
  // Create test database with sample data
  const testData = {
    strategies: [
      {
        id: 1,
        name: 'Test Strategy - AAPL Momentum',
        symbol: 'AAPL',
        active: true,
        param: {
          account_size: 100000,
          risk_per_trade: 0.02,
          min_r_coefficient: 2.0,
          min_profit_margin: 3.0,
          delay_between_symbols: 30
        }
      },
      {
        id: 2,
        name: 'Test Strategy - TSLA Swing',
        symbol: 'TSLA',
        active: false,
        param: {
          account_size: 50000,
          risk_per_trade: 0.03,
          min_r_coefficient: 1.5,
          min_profit_margin: 2.5,
          delay_between_symbols: 60
        }
      }
    ],
    executions: [
      {
        id: 'test_execution_1',
        strategy_id: 1,
        status: 'completed',
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        steps: 8,
        success: true
      }
    ]
  };

  // Save test data to file for use in tests
  fs.writeFileSync(
    path.join(__dirname, 'fixtures', 'test-data.json'),
    JSON.stringify(testData, null, 2)
  );
}

async function setupMockData() {
  console.log('🎭 Setting up mock data...');
  
  // Create fixtures directory
  const fixturesDir = path.join(__dirname, 'fixtures');
  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }

  // Mock LLM responses
  const mockLLMResponses = {
    analysis: {
      'AAPL': 'Based on technical analysis, AAPL shows strong bullish momentum with RSI at 65 and MACD crossing above signal line. Recommend BUY with target at $185 and stop loss at $175.',
      'TSLA': 'TSLA exhibits mixed signals with high volatility. Current price action suggests consolidation phase. Recommend HOLD until clearer trend emerges.',
      'SPY': 'SPY demonstrates steady uptrend with support at $430. Market sentiment remains positive. Recommend BUY on any dips below $435.'
    }
  };

  fs.writeFileSync(
    path.join(fixturesDir, 'mock-llm-responses.json'),
    JSON.stringify(mockLLMResponses, null, 2)
  );

  // Mock market data
  const mockMarketData = {
    'AAPL': {
      price: 180.50,
      change: 2.35,
      changePercent: 1.32,
      volume: 45000000,
      high: 182.00,
      low: 178.25,
      open: 179.00
    },
    'TSLA': {
      price: 245.80,
      change: -3.20,
      changePercent: -1.29,
      volume: 32000000,
      high: 250.00,
      low: 244.50,
      open: 248.00
    }
  };

  fs.writeFileSync(
    path.join(fixturesDir, 'mock-market-data.json'),
    JSON.stringify(mockMarketData, null, 2)
  );
}

async function warmupApplication() {
  console.log('🔥 Warming up application...');
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Make a request to the health endpoint to ensure the app is running
    await page.goto(process.env.BASE_URL || 'http://localhost:8000');
    await page.waitForLoadState('networkidle');
    console.log('✅ Application is responsive');
  } catch (error) {
    console.error('❌ Failed to warm up application:', error);
    throw error;
  } finally {
    await browser.close();
  }
}

export default globalSetup;
