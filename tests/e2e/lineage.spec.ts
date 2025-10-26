import { test, expect } from '@playwright/test';
import { LineagePage } from '../page-objects';

test.describe('Workflow Lineage Tracking @e2e @lineage', () => {
  test.use({ storageState: 'test-results/auth.json' });
  
  let lineagePage: LineagePage;

  test.beforeEach(async ({ page }) => {
    lineagePage = new LineagePage(page);
    await lineagePage.goto();
  });

  test('should display lineage visualization correctly', async () => {
    await test.step('Verify lineage page loads', async () => {
      await lineagePage.assertLineagePageLoaded();
    });

    await test.step('Select strategy and execution', async () => {
      // Get available strategies
      const strategiesResponse = await lineagePage.page.request.get('/api/strategies');
      const strategies = await strategiesResponse.json();
      
      if (strategies.length === 0) {
        test.skip('No strategies available for lineage testing');
      }

      const strategy = strategies[0];
      await lineagePage.selectStrategy(strategy.id.toString());
      
      // Get executions for the strategy
      const executionsResponse = await lineagePage.page.request.get(`/api/strategies/${strategy.id}/executions`);
      const executions = await executionsResponse.json();
      
      if (executions.length === 0) {
        test.skip('No executions available for lineage testing');
      }

      await lineagePage.selectExecution(executions[0].id);
    });

    await test.step('Verify lineage steps are displayed', async () => {
      const steps = await lineagePage.getAllSteps();
      expect(steps.length).toBeGreaterThan(0);
      
      // Verify step structure
      steps.forEach(step => {
        expect(step.name).toBeTruthy();
        expect(step.status).toMatch(/SUCCESS|FAILED|PENDING/);
      });
    });
  });

  test('should show rich step visualizations', async () => {
    // Setup: Select strategy and execution with steps
    const strategiesResponse = await lineagePage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    await lineagePage.selectStrategy(strategies[0].id.toString());
    
    const executionsResponse = await lineagePage.page.request.get(`/api/strategies/${strategies[0].id}/executions`);
    const executions = await executionsResponse.json();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    await lineagePage.selectExecution(executions[0].id);
    
    await test.step('Check step visualizations', async () => {
      const stepCount = await lineagePage.stepCards.count();
      
      if (stepCount === 0) {
        test.skip('No steps available for visualization testing');
      }

      for (let i = 0; i < Math.min(stepCount, 3); i++) {
        await lineagePage.assertVisualizationVisible(i);
        
        const visualizationType = await lineagePage.getStepVisualizationType(i);
        expect(['strategy', 'market-data', 'indicators', 'charts', 'llm-analysis', 'signal', 'order', 'generic'])
          .toContain(visualizationType);
      }
    });
  });

  test('should display step details in modal', async () => {
    // Setup execution with steps
    const strategiesResponse = await lineagePage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    await lineagePage.selectStrategy(strategies[0].id.toString());
    
    const executionsResponse = await lineagePage.page.request.get(`/api/strategies/${strategies[0].id}/executions`);
    const executions = await executionsResponse.json();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    await lineagePage.selectExecution(executions[0].id);
    
    const stepCount = await lineagePage.stepCards.count();
    
    if (stepCount === 0) {
      test.skip('No steps available');
    }

    await test.step('Open step details modal', async () => {
      const stepData = await lineagePage.getStepData(0);
      await lineagePage.viewStepDetails(0);
      
      await lineagePage.assertStepDetailModalOpen(stepData.name);
    });

    await test.step('Toggle raw input data', async () => {
      await lineagePage.toggleRawInput();
      await lineagePage.assertRawDataVisible('input');
    });

    await test.step('Toggle raw output data', async () => {
      await lineagePage.toggleRawOutput();
      await lineagePage.assertRawDataVisible('output');
    });

    await test.step('Close modal', async () => {
      await lineagePage.closeStepDetails();
      await lineagePage.assertElementHidden('[data-testid="step-detail-modal"]');
    });
  });

  test('should show lineage statistics', async () => {
    // Setup execution with steps
    const strategiesResponse = await lineagePage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    await lineagePage.selectStrategy(strategies[0].id.toString());
    
    const executionsResponse = await lineagePage.page.request.get(`/api/strategies/${strategies[0].id}/executions`);
    const executions = await executionsResponse.json();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    await lineagePage.selectExecution(executions[0].id);
    
    await test.step('Verify lineage statistics', async () => {
      const stats = await lineagePage.getLineageStats();
      
      expect(parseInt(stats.totalSteps)).toBeGreaterThanOrEqual(0);
      expect(parseInt(stats.successfulSteps)).toBeGreaterThanOrEqual(0);
      expect(parseInt(stats.failedSteps)).toBeGreaterThanOrEqual(0);
      
      const total = parseInt(stats.totalSteps);
      const successful = parseInt(stats.successfulSteps);
      const failed = parseInt(stats.failedSteps);
      
      expect(successful + failed).toBeLessThanOrEqual(total);
    });
  });

  test('should handle empty lineage state', async () => {
    await test.step('Verify empty state when no selection', async () => {
      await lineagePage.assertEmptyState();
    });

    await test.step('Select strategy with no executions', async () => {
      // Create a strategy with no executions for testing
      const response = await lineagePage.page.request.post('/api/strategies', {
        data: {
          name: `Empty Test Strategy ${Date.now()}`,
          workflow_id: 'momentum_trading',
          active: false,
          param: { account_size: 10000 }
        }
      });
      
      if (response.ok()) {
        const newStrategy = await response.json();
        await lineagePage.selectStrategy(newStrategy.id.toString());
        
        // Should show empty state for executions
        await lineagePage.assertEmptyState();
      }
    });
  });

  test('should refresh lineage data', async () => {
    const strategiesResponse = await lineagePage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    await lineagePage.selectStrategy(strategies[0].id.toString());
    
    const executionsResponse = await lineagePage.page.request.get(`/api/strategies/${strategies[0].id}/executions`);
    const executions = await executionsResponse.json();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    await lineagePage.selectExecution(executions[0].id);
    
    await test.step('Refresh lineage data', async () => {
      const initialSteps = await lineagePage.getAllSteps();
      
      await lineagePage.refreshLineage();
      
      const refreshedSteps = await lineagePage.getAllSteps();
      expect(refreshedSteps.length).toBe(initialSteps.length);
    });
  });

  test('should handle URL parameters for direct navigation', async ({ page }) => {
    const strategiesResponse = await page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    const executionsResponse = await page.request.get(`/api/strategies/${strategies[0].id}/executions`);
    const executions = await executionsResponse.json();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    await test.step('Navigate with URL parameters', async () => {
      const url = `/workflows/lineage?strategy_id=${strategies[0].id}&execution_id=${executions[0].id}`;
      await page.goto(url);
      
      await lineagePage.waitForLineageLoad();
      
      // Should automatically load the specified strategy and execution
      const steps = await lineagePage.getAllSteps();
      expect(steps.length).toBeGreaterThan(0);
    });
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    // Setup with data
    const strategiesResponse = await page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    
    if (strategies.length > 0) {
      await lineagePage.selectStrategy(strategies[0].id.toString());
      
      const executionsResponse = await page.request.get(`/api/strategies/${strategies[0].id}/executions`);
      const executions = await executionsResponse.json();
      
      if (executions.length > 0) {
        await lineagePage.selectExecution(executions[0].id);
      }
    }

    await test.step('Test mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await lineagePage.assertLineagePageLoaded();
    });

    await test.step('Test tablet viewport', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await lineagePage.assertLineagePageLoaded();
    });

    await test.step('Test desktop viewport', async () => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await lineagePage.assertLineagePageLoaded();
    });
  });
});
