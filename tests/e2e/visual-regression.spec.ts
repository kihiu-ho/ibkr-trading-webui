import { test, expect } from '../fixtures/test-fixtures';

test.describe('Visual Regression Tests @visual', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should match dashboard visual snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Dashboard overview snapshot', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Wait for all dashboard sections to load
      await page.waitForSelector('[data-testid="workflow-stats"]');
      await page.waitForSelector('[data-testid="active-executions"]');
      await page.waitForSelector('[data-testid="recent-results"]');
      
      await expect(page).toHaveScreenshot('dashboard-overview.png');
    });

    await test.step('Dashboard workflow statistics section', async () => {
      const statsSection = page.locator('[data-testid="workflow-stats"]');
      await expect(statsSection).toHaveScreenshot('dashboard-stats-section.png');
    });

    await test.step('Dashboard active executions section', async () => {
      const executionsSection = page.locator('[data-testid="active-executions"]');
      await expect(executionsSection).toHaveScreenshot('dashboard-executions-section.png');
    });

    await test.step('Dashboard recent results section', async () => {
      const resultsSection = page.locator('[data-testid="recent-results"]');
      await expect(resultsSection).toHaveScreenshot('dashboard-results-section.png');
    });
  });

  test('should match strategies page visual snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Strategies list view snapshot', async () => {
      await page.goto('/strategies');
      await page.waitForLoadState('networkidle');
      await page.waitForSelector('[data-testid="strategies-table"]');
      
      await expect(page).toHaveScreenshot('strategies-list-view.png');
    });

    await test.step('Strategy item card snapshot', async () => {
      const strategyItem = page.locator('[data-testid="strategy-item"]').first();
      await expect(strategyItem).toHaveScreenshot('strategy-item-card.png');
    });

    await test.step('Strategy creation form snapshot', async ({ page }) => {
      await page.goto('/strategies/new');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('strategy-creation-form.png');
    });
  });

  test('should match workflows page visual snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Workflows execution list snapshot', async () => {
      await page.goto('/workflows');
      await page.waitForLoadState('networkidle');
      await page.waitForSelector('[data-testid="executions-table"]');
      
      await expect(page).toHaveScreenshot('workflows-execution-list.png');
    });

    await test.step('Execution item with different statuses', async () => {
      const runningExecution = page.locator('[data-testid="execution-item"][data-status="running"]').first();
      if (await runningExecution.isVisible()) {
        await expect(runningExecution).toHaveScreenshot('execution-item-running.png');
      }

      const completedExecution = page.locator('[data-testid="execution-item"][data-status="completed"]').first();
      if (await completedExecution.isVisible()) {
        await expect(completedExecution).toHaveScreenshot('execution-item-completed.png');
      }

      const failedExecution = page.locator('[data-testid="execution-item"][data-status="failed"]').first();
      if (await failedExecution.isVisible()) {
        await expect(failedExecution).toHaveScreenshot('execution-item-failed.png');
      }
    });
  });

  test('should match lineage visualization snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Lineage page overview snapshot', async () => {
      await page.goto('/workflows/lineage');
      await page.waitForLoadState('networkidle');
      
      // Select strategy and execution to show lineage
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      await page.waitForSelector('[data-testid="lineage-container"]');
      await expect(page).toHaveScreenshot('lineage-overview.png');
    });

    await test.step('Individual step card snapshots', async () => {
      const stepCards = page.locator('[data-testid="step-card"]');
      const stepCount = await stepCards.count();
      
      for (let i = 0; i < Math.min(stepCount, 5); i++) {
        const stepCard = stepCards.nth(i);
        await expect(stepCard).toHaveScreenshot(`lineage-step-card-${i}.png`);
      }
    });

    await test.step('Step detail modal snapshot', async () => {
      const firstStepCard = page.locator('[data-testid="step-card"]').first();
      const viewDetailsBtn = firstStepCard.locator('[data-testid="view-details-btn"]');
      
      if (await viewDetailsBtn.isVisible()) {
        await viewDetailsBtn.click();
        await page.waitForSelector('[data-testid="step-detail-modal"]');
        
        const modal = page.locator('[data-testid="step-detail-modal"]');
        await expect(modal).toHaveScreenshot('step-detail-modal.png');
      }
    });
  });

  test('should match step visualization types', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await page.goto('/workflows/lineage');
    await page.selectOption('[data-testid="strategy-select"]', '1');
    await page.selectOption('[data-testid="execution-select"]', 'exec_001');
    await page.waitForSelector('[data-testid="lineage-container"]');

    await test.step('Strategy step visualization', async () => {
      const strategyStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'load_strategy' });
      if (await strategyStep.isVisible()) {
        const visualization = strategyStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('strategy-step-visualization.png');
      }
    });

    await test.step('Market data step visualization', async () => {
      const marketDataStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'fetch_market_data' });
      if (await marketDataStep.isVisible()) {
        const visualization = marketDataStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('market-data-step-visualization.png');
      }
    });

    await test.step('Indicators step visualization', async () => {
      const indicatorsStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'calculate_indicators' });
      if (await indicatorsStep.isVisible()) {
        const visualization = indicatorsStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('indicators-step-visualization.png');
      }
    });

    await test.step('LLM analysis step visualization', async () => {
      const llmStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'llm_analysis' });
      if (await llmStep.isVisible()) {
        const visualization = llmStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('llm-analysis-step-visualization.png');
      }
    });

    await test.step('Trading signal step visualization', async () => {
      const signalStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'parse_trading_signal' });
      if (await signalStep.isVisible()) {
        const visualization = signalStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('trading-signal-step-visualization.png');
      }
    });

    await test.step('Order placement step visualization', async () => {
      const orderStep = page.locator('[data-testid="step-card"]').filter({ hasText: 'place_order' });
      if (await orderStep.isVisible()) {
        const visualization = orderStep.locator('[data-testid="step-visualization"]');
        await expect(visualization).toHaveScreenshot('order-placement-step-visualization.png');
      }
    });
  });

  test('should match responsive design snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Mobile viewport snapshots', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('dashboard-mobile.png');
      
      await page.goto('/strategies');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('strategies-mobile.png');
      
      await page.goto('/workflows');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('workflows-mobile.png');
    });

    await test.step('Tablet viewport snapshots', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('dashboard-tablet.png');
      
      await page.goto('/workflows/lineage');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('lineage-tablet.png');
    });

    await test.step('Desktop viewport snapshots', async () => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('dashboard-desktop.png');
    });
  });

  test('should match dark mode visual snapshots', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('Enable dark mode', async () => {
      await page.emulateMedia({ colorScheme: 'dark' });
    });

    await test.step('Dark mode dashboard snapshot', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveScreenshot('dashboard-dark-mode.png');
    });

    await test.step('Dark mode lineage visualization', async () => {
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      await page.waitForSelector('[data-testid="lineage-container"]');
      await expect(page).toHaveScreenshot('lineage-dark-mode.png');
    });
  });
});
