import { Page, Route } from '@playwright/test';

export class APIMocks {
  constructor(private page: Page) {}

  async mockStrategiesAPI() {
    // Mock GET /api/strategies
    await this.page.route('**/api/strategies', async (route: Route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 1,
              name: 'AAPL Momentum Strategy',
              workflow_id: 'momentum_trading',
              active: true,
              param: {
                account_size: 100000,
                risk_per_trade: 0.02,
                min_r_coefficient: 2.0,
                min_profit_margin: 3.0,
                delay_between_symbols: 30
              },
              created_at: '2024-01-01T10:00:00Z',
              updated_at: '2024-01-01T10:00:00Z'
            },
            {
              id: 2,
              name: 'TSLA Swing Strategy',
              workflow_id: 'swing_trading',
              active: false,
              param: {
                account_size: 50000,
                risk_per_trade: 0.03,
                min_r_coefficient: 1.5,
                min_profit_margin: 2.5,
                delay_between_symbols: 60
              },
              created_at: '2024-01-01T11:00:00Z',
              updated_at: '2024-01-01T11:00:00Z'
            }
          ])
        });
      } else if (route.request().method() === 'POST') {
        const requestData = route.request().postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: Date.now(),
            ...requestData,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          })
        });
      }
    });

    // Mock strategy executions
    await this.page.route('**/api/strategies/*/executions', async (route: Route) => {
      const strategyId = route.request().url().match(/strategies\/(\d+)\/executions/)?.[1];
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: `execution_${strategyId}_1`,
            strategy_id: parseInt(strategyId || '1'),
            status: 'completed',
            started_at: '2024-01-01T12:00:00Z',
            completed_at: '2024-01-01T12:05:00Z',
            steps: 8,
            success: true
          },
          {
            id: `execution_${strategyId}_2`,
            strategy_id: parseInt(strategyId || '1'),
            status: 'running',
            started_at: '2024-01-01T13:00:00Z',
            completed_at: null,
            steps: 5,
            success: null
          }
        ])
      });
    });

    // Mock strategy execution trigger
    await this.page.route('**/api/strategies/*/execute', async (route: Route) => {
      const strategyId = route.request().url().match(/strategies\/(\d+)\/execute/)?.[1];
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Workflow execution started',
          strategy_id: parseInt(strategyId || '1'),
          task_id: `task_${Date.now()}`
        })
      });
    });
  }

  async mockWorkflowsAPI() {
    // Mock workflow executions
    await this.page.route('**/api/workflows/executions', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'exec_001',
            strategy_id: 1,
            strategy_name: 'AAPL Momentum Strategy',
            status: 'running',
            progress: '60%',
            started_at: '2024-01-01T14:00:00Z',
            duration: '2m 30s',
            current_step: 'LLM Analysis',
            total_steps: 8
          },
          {
            id: 'exec_002',
            strategy_id: 2,
            strategy_name: 'TSLA Swing Strategy',
            status: 'completed',
            progress: '100%',
            started_at: '2024-01-01T13:00:00Z',
            completed_at: '2024-01-01T13:08:00Z',
            duration: '8m 15s',
            total_steps: 8
          },
          {
            id: 'exec_003',
            strategy_id: 1,
            strategy_name: 'AAPL Momentum Strategy',
            status: 'failed',
            progress: '40%',
            started_at: '2024-01-01T12:00:00Z',
            completed_at: '2024-01-01T12:03:00Z',
            duration: '3m 12s',
            error: 'Market data fetch timeout',
            total_steps: 8
          }
        ])
      });
    });

    // Mock execution control endpoints
    await this.page.route('**/api/workflows/executions/*/pause', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Execution paused successfully' })
      });
    });

    await this.page.route('**/api/workflows/executions/*/resume', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Execution resumed successfully' })
      });
    });

    await this.page.route('**/api/workflows/executions/*/stop', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Execution stopped successfully' })
      });
    });
  }

  async mockLineageAPI() {
    // Mock execution lineage
    await this.page.route('**/api/lineage/execution/*', async (route: Route) => {
      const executionId = route.request().url().split('/').pop();
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          execution_id: executionId,
          steps: [
            {
              id: 1,
              step_name: 'load_strategy',
              step_type: 'strategy',
              step_number: 1,
              success: true,
              duration_ms: 150,
              input_data: {
                strategy_id: 1,
                strategy_name: 'AAPL Momentum Strategy'
              },
              output_data: {
                strategy_id: 1,
                strategy_name: 'AAPL Momentum Strategy',
                symbol: 'AAPL',
                active: true
              },
              started_at: '2024-01-01T14:00:00Z',
              completed_at: '2024-01-01T14:00:00.150Z'
            },
            {
              id: 2,
              step_name: 'fetch_market_data',
              step_type: 'market_data',
              step_number: 2,
              success: true,
              duration_ms: 2340,
              input_data: {
                symbol: 'AAPL',
                conid: 265598,
                period: '1d'
              },
              output_data: {
                data_points: 100,
                latest_price: 180.50,
                date_range: '2024-01-01 to 2024-01-01'
              },
              started_at: '2024-01-01T14:00:00.150Z',
              completed_at: '2024-01-01T14:00:02.490Z'
            },
            {
              id: 3,
              step_name: 'calculate_indicators',
              step_type: 'indicators',
              step_number: 3,
              success: true,
              duration_ms: 890,
              input_data: {
                symbol: 'AAPL',
                indicators: ['RSI', 'MACD', 'SMA_20', 'SMA_50']
              },
              output_data: {
                indicators: {
                  RSI: 65.4,
                  MACD: 1.23,
                  SMA_20: 178.90,
                  SMA_50: 175.20
                },
                data_points: 100
              },
              started_at: '2024-01-01T14:00:02.490Z',
              completed_at: '2024-01-01T14:00:03.380Z'
            },
            {
              id: 4,
              step_name: 'generate_charts',
              step_type: 'charts',
              step_number: 4,
              success: true,
              duration_ms: 1560,
              input_data: {
                symbol: 'AAPL',
                chart_types: ['daily', 'weekly']
              },
              output_data: {
                daily_chart_url: '/static/charts/AAPL_daily_20240101.png',
                weekly_chart_url: '/static/charts/AAPL_weekly_20240101.png'
              },
              started_at: '2024-01-01T14:00:03.380Z',
              completed_at: '2024-01-01T14:00:04.940Z'
            },
            {
              id: 5,
              step_name: 'llm_analysis',
              step_type: 'llm_analysis',
              step_number: 5,
              success: true,
              duration_ms: 8920,
              input_data: {
                symbol: 'AAPL',
                model: 'gpt-4',
                prompt_template_id: 'technical_analysis_v2',
                temperature: 0.7,
                max_tokens: 4000
              },
              output_data: {
                analysis: 'Based on technical analysis, AAPL shows strong bullish momentum with RSI at 65.4 indicating healthy uptrend without being overbought. MACD crossover above signal line confirms bullish sentiment. Price above both 20-day and 50-day SMAs suggests continued upward movement. Recommend BUY with target at $185 and stop loss at $175.',
                model: 'gpt-4',
                tokens_used: 3456
              },
              started_at: '2024-01-01T14:00:04.940Z',
              completed_at: '2024-01-01T14:00:13.860Z'
            },
            {
              id: 6,
              step_name: 'parse_trading_signal',
              step_type: 'signal',
              step_number: 6,
              success: true,
              duration_ms: 320,
              input_data: {
                analysis: 'Based on technical analysis, AAPL shows strong bullish momentum...',
                current_price: 180.50
              },
              output_data: {
                type: 'BUY',
                current_price: 180.50,
                target_price: 185.00,
                stop_loss: 175.00,
                confidence: 0.85,
                profit_margin: 0.025
              },
              started_at: '2024-01-01T14:00:13.860Z',
              completed_at: '2024-01-01T14:00:14.180Z'
            },
            {
              id: 7,
              step_name: 'place_order',
              step_type: 'order',
              step_number: 7,
              success: true,
              duration_ms: 1890,
              input_data: {
                symbol: 'AAPL',
                side: 'BUY',
                quantity: 100,
                price: 180.50,
                order_type: 'LMT'
              },
              output_data: {
                order_id: 'ORD_001',
                ibkr_order_id: 'IB123456789',
                status: 'SUBMITTED',
                quantity: 100,
                price: 180.50
              },
              started_at: '2024-01-01T14:00:14.180Z',
              completed_at: '2024-01-01T14:00:16.070Z'
            }
          ],
          total_steps: 7,
          has_errors: false
        })
      });
    });
  }

  async mockDashboardAPI() {
    await this.page.route('**/api/dashboard', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_stats: {
            total_executions: 156,
            successful_executions: 142,
            failed_executions: 14,
            success_rate: 91.0,
            avg_execution_time: '6m 45s'
          },
          active_executions: [
            {
              id: 'exec_001',
              strategy: 'AAPL Momentum Strategy',
              status: 'Running',
              progress: '60%'
            }
          ],
          recent_results: [
            {
              strategy: 'TSLA Swing Strategy',
              status: 'Completed',
              timestamp: '2024-01-01T13:08:00Z',
              duration: '8m 15s'
            },
            {
              strategy: 'AAPL Momentum Strategy',
              status: 'Failed',
              timestamp: '2024-01-01T12:03:00Z',
              duration: '3m 12s'
            }
          ]
        })
      });
    });
  }

  async mockMarketDataAPI() {
    await this.page.route('**/api/market-data**', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
        })
      });
    });
  }

  async mockOrdersAPI() {
    await this.page.route('**/api/orders**', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'ORD_001',
            symbol: 'AAPL',
            side: 'BUY',
            quantity: 100,
            price: 180.50,
            status: 'FILLED',
            timestamp: '2024-01-01T14:00:16Z',
            execution_id: 'exec_001'
          },
          {
            id: 'ORD_002',
            symbol: 'TSLA',
            side: 'SELL',
            quantity: 50,
            price: 245.80,
            status: 'PENDING',
            timestamp: '2024-01-01T14:05:00Z',
            execution_id: 'exec_002'
          }
        ])
      });
    });
  }

  async mockPortfolioAPI() {
    await this.page.route('**/api/portfolio**', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_value: 125000.00,
          cash_balance: 25000.00,
          total_pnl: 5000.00,
          total_pnl_percent: 4.17,
          buying_power: 50000.00,
          positions: [
            {
              symbol: 'AAPL',
              quantity: 100,
              avg_price: 175.00,
              current_price: 180.50,
              pnl: 550.00,
              pnl_percent: 3.14
            },
            {
              symbol: 'TSLA',
              quantity: 50,
              avg_price: 250.00,
              current_price: 245.80,
              pnl: -210.00,
              pnl_percent: -1.68
            }
          ]
        })
      });
    });
  }

  async mockHealthAPI() {
    await this.page.route('**/api/health', async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'healthy',
          timestamp: new Date().toISOString(),
          version: '2.0.0',
          database: 'connected',
          ibkr_connection: 'connected'
        })
      });
    });
  }

  async mockIBKRAuthAPI() {
    await this.page.route('**/api/ibkr/auth/**', async (route: Route) => {
      const url = route.request().url();

      if (url.includes('/login')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Authentication successful',
            session_id: 'mock_session_123',
            paper_trading: true
          })
        });
      } else if (url.includes('/status')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            connected: true,
            authenticated: true,
            paper_trading: true,
            server_version: '10.19'
          })
        });
      }
    });
  }

  async enableAllMocks() {
    await this.mockStrategiesAPI();
    await this.mockWorkflowsAPI();
    await this.mockLineageAPI();
    await this.mockDashboardAPI();
    await this.mockMarketDataAPI();
    await this.mockOrdersAPI();
    await this.mockPortfolioAPI();
    await this.mockHealthAPI();
    await this.mockIBKRAuthAPI();
  }

  async disableAllMocks() {
    await this.page.unroute('**/api/**');
  }
}
