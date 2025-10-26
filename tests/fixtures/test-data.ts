import { faker } from '@faker-js/faker';

export interface TestStrategy {
  id?: number;
  name: string;
  workflow_id: string;
  active: boolean;
  param: {
    account_size: number;
    risk_per_trade: number;
    min_r_coefficient: number;
    min_profit_margin: number;
    delay_between_symbols: number;
    temperature?: number;
    max_tokens?: number;
  };
}

export interface TestExecution {
  id: string;
  strategy_id: number;
  status: 'running' | 'completed' | 'failed' | 'paused';
  started_at: string;
  completed_at?: string;
  steps: number;
  success?: boolean;
}

export interface TestLineageStep {
  id: number;
  step_name: string;
  step_type: string;
  step_number: number;
  success: boolean;
  duration_ms: number;
  input_data: any;
  output_data: any;
  started_at: string;
  completed_at: string;
}

export class TestDataGenerator {
  static generateStrategy(overrides: Partial<TestStrategy> = {}): TestStrategy {
    const symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'SPY', 'QQQ'];
    const workflows = ['momentum_trading', 'swing_trading', 'mean_reversion', 'breakout_strategy'];
    
    return {
      name: overrides.name || `${faker.helpers.arrayElement(symbols)} ${faker.helpers.arrayElement(['Momentum', 'Swing', 'Scalping'])} Strategy`,
      workflow_id: overrides.workflow_id || faker.helpers.arrayElement(workflows),
      active: overrides.active !== undefined ? overrides.active : faker.datatype.boolean(),
      param: {
        account_size: faker.number.int({ min: 10000, max: 1000000 }),
        risk_per_trade: faker.number.float({ min: 0.01, max: 0.05, precision: 0.001 }),
        min_r_coefficient: faker.number.float({ min: 1.0, max: 3.0, precision: 0.1 }),
        min_profit_margin: faker.number.float({ min: 1.0, max: 10.0, precision: 0.1 }),
        delay_between_symbols: faker.number.int({ min: 10, max: 300 }),
        temperature: faker.number.float({ min: 0.1, max: 1.0, precision: 0.1 }),
        max_tokens: faker.number.int({ min: 1000, max: 8000 }),
        ...overrides.param
      },
      ...overrides
    };
  }

  static generateExecution(overrides: Partial<TestExecution> = {}): TestExecution {
    const statuses: TestExecution['status'][] = ['running', 'completed', 'failed', 'paused'];
    const status = overrides.status || faker.helpers.arrayElement(statuses);
    const startedAt = faker.date.recent({ days: 7 });
    
    return {
      id: overrides.id || `exec_${faker.string.alphanumeric(8)}`,
      strategy_id: overrides.strategy_id || faker.number.int({ min: 1, max: 10 }),
      status,
      started_at: startedAt.toISOString(),
      completed_at: status === 'completed' || status === 'failed' 
        ? faker.date.between({ from: startedAt, to: new Date() }).toISOString()
        : undefined,
      steps: faker.number.int({ min: 5, max: 12 }),
      success: status === 'completed' ? true : status === 'failed' ? false : undefined,
      ...overrides
    };
  }

  static generateLineageSteps(executionId: string, stepCount: number = 8): TestLineageStep[] {
    const stepTypes = [
      { name: 'load_strategy', type: 'strategy' },
      { name: 'fetch_market_data', type: 'market_data' },
      { name: 'calculate_indicators', type: 'indicators' },
      { name: 'generate_charts', type: 'charts' },
      { name: 'llm_analysis', type: 'llm_analysis' },
      { name: 'parse_trading_signal', type: 'signal' },
      { name: 'place_order', type: 'order' },
      { name: 'update_portfolio', type: 'portfolio' }
    ];

    const steps: TestLineageStep[] = [];
    let currentTime = faker.date.recent({ days: 1 });

    for (let i = 0; i < stepCount; i++) {
      const stepType = stepTypes[i] || { name: `custom_step_${i}`, type: 'generic' };
      const duration = faker.number.int({ min: 100, max: 10000 });
      const startTime = new Date(currentTime);
      const endTime = new Date(currentTime.getTime() + duration);

      steps.push({
        id: i + 1,
        step_name: stepType.name,
        step_type: stepType.type,
        step_number: i + 1,
        success: faker.datatype.boolean(0.9), // 90% success rate
        duration_ms: duration,
        input_data: this.generateStepInputData(stepType.type),
        output_data: this.generateStepOutputData(stepType.type),
        started_at: startTime.toISOString(),
        completed_at: endTime.toISOString()
      });

      currentTime = endTime;
    }

    return steps;
  }

  private static generateStepInputData(stepType: string): any {
    switch (stepType) {
      case 'strategy':
        return {
          strategy_id: faker.number.int({ min: 1, max: 10 }),
          strategy_name: faker.company.name() + ' Strategy'
        };
      
      case 'market_data':
        return {
          symbol: faker.helpers.arrayElement(['AAPL', 'TSLA', 'MSFT', 'GOOGL']),
          conid: faker.number.int({ min: 100000, max: 999999 }),
          period: faker.helpers.arrayElement(['1d', '5d', '1m', '3m'])
        };
      
      case 'indicators':
        return {
          symbol: faker.helpers.arrayElement(['AAPL', 'TSLA', 'MSFT', 'GOOGL']),
          indicators: ['RSI', 'MACD', 'SMA_20', 'SMA_50']
        };
      
      case 'llm_analysis':
        return {
          symbol: faker.helpers.arrayElement(['AAPL', 'TSLA', 'MSFT', 'GOOGL']),
          model: faker.helpers.arrayElement(['gpt-4', 'gpt-3.5-turbo', 'claude-3']),
          prompt_template_id: 'technical_analysis_v2',
          temperature: faker.number.float({ min: 0.1, max: 1.0, precision: 0.1 }),
          max_tokens: faker.number.int({ min: 1000, max: 8000 })
        };
      
      case 'order':
        return {
          symbol: faker.helpers.arrayElement(['AAPL', 'TSLA', 'MSFT', 'GOOGL']),
          side: faker.helpers.arrayElement(['BUY', 'SELL']),
          quantity: faker.number.int({ min: 10, max: 1000 }),
          price: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
          order_type: faker.helpers.arrayElement(['MKT', 'LMT', 'STP'])
        };
      
      default:
        return {
          timestamp: faker.date.recent().toISOString(),
          data: faker.lorem.words(5)
        };
    }
  }

  private static generateStepOutputData(stepType: string): any {
    switch (stepType) {
      case 'strategy':
        return {
          strategy_id: faker.number.int({ min: 1, max: 10 }),
          strategy_name: faker.company.name() + ' Strategy',
          symbol: faker.helpers.arrayElement(['AAPL', 'TSLA', 'MSFT', 'GOOGL']),
          active: true
        };
      
      case 'market_data':
        return {
          data_points: faker.number.int({ min: 50, max: 500 }),
          latest_price: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
          date_range: `${faker.date.past().toISOString().split('T')[0]} to ${faker.date.recent().toISOString().split('T')[0]}`
        };
      
      case 'indicators':
        return {
          indicators: {
            RSI: faker.number.float({ min: 0, max: 100, precision: 0.1 }),
            MACD: faker.number.float({ min: -5, max: 5, precision: 0.01 }),
            SMA_20: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
            SMA_50: faker.number.float({ min: 50, max: 500, precision: 0.01 })
          },
          data_points: faker.number.int({ min: 50, max: 500 })
        };
      
      case 'charts':
        return {
          daily_chart_url: `/static/charts/${faker.helpers.arrayElement(['AAPL', 'TSLA'])}_daily_${faker.date.recent().toISOString().split('T')[0]}.png`,
          weekly_chart_url: `/static/charts/${faker.helpers.arrayElement(['AAPL', 'TSLA'])}_weekly_${faker.date.recent().toISOString().split('T')[0]}.png`
        };
      
      case 'llm_analysis':
        return {
          analysis: faker.lorem.paragraphs(3),
          model: faker.helpers.arrayElement(['gpt-4', 'gpt-3.5-turbo', 'claude-3']),
          tokens_used: faker.number.int({ min: 500, max: 4000 })
        };
      
      case 'signal':
        return {
          type: faker.helpers.arrayElement(['BUY', 'SELL', 'HOLD']),
          current_price: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
          target_price: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
          stop_loss: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
          confidence: faker.number.float({ min: 0.5, max: 1.0, precision: 0.01 })
        };
      
      case 'order':
        return {
          order_id: `ORD_${faker.string.alphanumeric(8)}`,
          ibkr_order_id: `IB${faker.number.int({ min: 100000000, max: 999999999 })}`,
          status: faker.helpers.arrayElement(['SUBMITTED', 'FILLED', 'CANCELLED']),
          quantity: faker.number.int({ min: 10, max: 1000 }),
          price: faker.number.float({ min: 50, max: 500, precision: 0.01 })
        };
      
      default:
        return {
          result: faker.lorem.sentence(),
          timestamp: faker.date.recent().toISOString()
        };
    }
  }

  static generateTestSymbols(): string[] {
    return ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'SPY', 'QQQ', 'NVDA', 'META', 'NFLX'];
  }

  static generateMarketData(symbol: string) {
    const basePrice = faker.number.float({ min: 50, max: 500, precision: 0.01 });
    const change = faker.number.float({ min: -10, max: 10, precision: 0.01 });
    
    return {
      symbol,
      price: basePrice,
      change,
      changePercent: (change / basePrice) * 100,
      volume: faker.number.int({ min: 1000000, max: 100000000 }),
      high: basePrice + faker.number.float({ min: 0, max: 5, precision: 0.01 }),
      low: basePrice - faker.number.float({ min: 0, max: 5, precision: 0.01 }),
      open: basePrice + faker.number.float({ min: -2, max: 2, precision: 0.01 })
    };
  }
}
