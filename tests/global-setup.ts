import { FullConfig } from '@playwright/test';
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

  console.log('✅ Global test setup completed');
}

async function setupTestDatabase() {
  console.log('📊 Setting up test database...');

  const fixturesDir = path.join(__dirname, 'fixtures');
  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }

  const testDataPath = path.join(fixturesDir, 'test-data.json');
  if (fs.existsSync(testDataPath)) {
    return;
  }
  
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
    testDataPath,
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

  const llmResponsePath = path.join(fixturesDir, 'mock-llm-responses.json');
  if (!fs.existsSync(llmResponsePath)) {
    fs.writeFileSync(llmResponsePath, JSON.stringify(mockLLMResponses, null, 2));
  }

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

  const marketDataPath = path.join(fixturesDir, 'mock-market-data.json');
  if (!fs.existsSync(marketDataPath)) {
    fs.writeFileSync(marketDataPath, JSON.stringify(mockMarketData, null, 2));
  }
}

export default globalSetup;
