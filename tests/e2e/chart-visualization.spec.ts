import { test, expect } from '../fixtures/test-fixtures';

test.describe('Chart and Visualization Tests @visual @charts', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should render trading charts correctly', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Market data charts visualization', async () => {
      await page.goto('/market-data');
      await page.waitForLoadState('networkidle');
      
      // Search for a symbol to display charts
      await page.fill('[data-testid="symbol-input"]', 'AAPL');
      await page.click('[data-testid="search-symbol"]');
      
      await page.waitForSelector('[data-testid="price-chart"]');
      const chart = page.locator('[data-testid="price-chart"]');
      await expect(chart).toHaveScreenshot('market-data-price-chart.png');
    });

    await test.step('Generated chart images in lineage', async () => {
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      // Find chart generation step
      const chartStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'generate_charts' });
      if (await chartStep.isVisible()) {
        const chartVisualization = chartStep.locator('[data-testid="step-visualization"]');
        await expect(chartVisualization).toHaveScreenshot('generated-charts-visualization.png');
        
        // Check individual chart images
        const dailyChart = chartVisualization.locator('img').first();
        if (await dailyChart.isVisible()) {
          await expect(dailyChart).toHaveScreenshot('daily-chart-image.png');
        }
      }
    });
  });

  test('should display technical indicators correctly', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await page.goto('/workflows/lineage');
    await page.selectOption('[data-testid="strategy-select"]', '1');
    await page.selectOption('[data-testid="execution-select"]', 'exec_001');
    
    await test.step('Technical indicators table visualization', async () => {
      const indicatorsStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'calculate_indicators' });
      if (await indicatorsStep.isVisible()) {
        const indicatorsTable = indicatorsStep.locator('table');
        if (await indicatorsTable.isVisible()) {
          await expect(indicatorsTable).toHaveScreenshot('technical-indicators-table.png');
        }
      }
    });

    await test.step('Individual indicator values', async () => {
      const indicatorsStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'calculate_indicators' });
      if (await indicatorsStep.isVisible()) {
        const visualization = indicatorsStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('indicators-visualization-complete.png');
      }
    });
  });

  test('should render trading signal visualizations', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await page.goto('/workflows/lineage');
    await page.selectOption('[data-testid="strategy-select"]', '1');
    await page.selectOption('[data-testid="execution-select"]', 'exec_001');
    
    await test.step('BUY signal visualization', async () => {
      const signalStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'parse_trading_signal' });
      if (await signalStep.isVisible()) {
        const signalVisualization = signalStep.locator('[data-testid="step-visualization"]');
        await expect(signalVisualization).toHaveScreenshot('buy-signal-visualization.png');
        
        // Check signal components
        const signalBadge = signalVisualization.locator('.signal-badge, [class*="bg-green"]');
        if (await signalBadge.isVisible()) {
          await expect(signalBadge).toHaveScreenshot('buy-signal-badge.png');
        }
      }
    });

    await test.step('Price levels visualization', async () => {
      const signalStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'parse_trading_signal' });
      if (await signalStep.isVisible()) {
        const priceGrid = signalStep.locator('.grid, [class*="grid-cols"]');
        if (await priceGrid.isVisible()) {
          await expect(priceGrid).toHaveScreenshot('price-levels-grid.png');
        }
      }
    });
  });

  test('should display order visualization correctly', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await page.goto('/workflows/lineage');
    await page.selectOption('[data-testid="strategy-select"]', '1');
    await page.selectOption('[data-testid="execution-select"]', 'exec_001');
    
    await test.step('Order details visualization', async () => {
      const orderStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'place_order' });
      if (await orderStep.isVisible()) {
        const orderVisualization = orderStep.locator('[data-testid="step-visualization"]');
        await expect(orderVisualization).toHaveScreenshot('order-details-visualization.png');
      }
    });

    await test.step('Order status badges', async () => {
      const orderStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'place_order' });
      if (await orderStep.isVisible()) {
        const statusBadges = orderStep.locator('[class*="bg-green"], [class*="bg-blue"], [class*="bg-red"]');
        const badgeCount = await statusBadges.count();
        
        for (let i = 0; i < badgeCount; i++) {
          const badge = statusBadges.nth(i);
          await expect(badge).toHaveScreenshot(`order-status-badge-${i}.png`);
        }
      }
    });
  });

  test('should handle chart loading states', async ({ page, apiMocks }) => {
    await test.step('Chart loading spinner', async () => {
      // Mock slow chart loading
      await page.route('**/static/charts/**', route => {
        setTimeout(() => route.continue(), 2000);
      });
      
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      const chartStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'generate_charts' });
      if (await chartStep.isVisible()) {
        const loadingSpinner = chartStep.locator('[data-testid="loading-spinner"], .spinner');
        if (await loadingSpinner.isVisible()) {
          await expect(loadingSpinner).toHaveScreenshot('chart-loading-spinner.png');
        }
      }
    });
  });

  test('should display error states for failed visualizations', async ({ page, apiMocks }) => {
    await test.step('Mock failed chart generation', async () => {
      await page.route('**/api/lineage/execution/*', async route => {
        const mockData = {
          execution_id: 'exec_001',
          steps: [
            {
              id: 4,
              step_name: 'generate_charts',
              step_type: 'charts',
              step_number: 4,
              success: false,
              duration_ms: 1560,
              input_data: { symbol: 'AAPL', chart_types: ['daily', 'weekly'] },
              output_data: { error: 'Chart generation failed' },
              error: 'Failed to generate charts: API timeout',
              started_at: '2024-01-01T14:00:03.380Z',
              completed_at: '2024-01-01T14:00:04.940Z'
            }
          ],
          total_steps: 1,
          has_errors: true
        };
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockData)
        });
      });
      
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      const failedStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'generate_charts' });
      if (await failedStep.isVisible()) {
        await expect(failedStep).toHaveScreenshot('failed-chart-step.png');
        
        const errorVisualization = failedStep.locator('[data-testid="step-visualization"]');
        if (await errorVisualization.isVisible()) {
          await expect(errorVisualization).toHaveScreenshot('chart-error-visualization.png');
        }
      }
    });
  });
});
