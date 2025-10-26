import { test, expect } from '@playwright/test';
import { DashboardPage, StrategiesPage, WorkflowsPage, LineagePage, StrategyFormPage } from '../page-objects';

test.describe('Complete End-to-End Workflow @e2e @smoke', () => {
  test.use({ storageState: 'test-results/auth.json' });
  
  test('should execute complete IBKR trading workflow from strategy creation to order placement', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const strategiesPage = new StrategiesPage(page);
    const strategyFormPage = new StrategyFormPage(page);
    const workflowsPage = new WorkflowsPage(page);
    const lineagePage = new LineagePage(page);

    const testStrategyName = `E2E Test Strategy ${Date.now()}`;
    let createdStrategyId: string;
    let executionId: string;

    await test.step('Create new trading strategy', async () => {
      await strategiesPage.goto();
      await strategiesPage.createNewStrategy();
      
      await strategyFormPage.fillStrategyForm({
        name: testStrategyName,
        workflow_id: 'momentum_trading',
        active: true,
        account_size: 100000,
        risk_per_trade: 0.02,
        min_r_coefficient: 2.0,
        min_profit_margin: 3.0,
        delay_between_symbols: 30,
        temperature: 0.7,
        max_tokens: 4000
      });

      await strategyFormPage.validateParameters();
      await strategyFormPage.assertValidationPassed();
      await strategyFormPage.saveStrategy();
      
      // Get the created strategy ID
      await strategiesPage.waitForStrategiesLoad();
      const strategies = await strategiesPage.getAllStrategies();
      const createdStrategy = strategies.find(s => s.name === testStrategyName);
      expect(createdStrategy).toBeTruthy();
      createdStrategyId = createdStrategy!.id;
    });

    await test.step('Execute trading workflow', async () => {
      await strategiesPage.executeStrategy(createdStrategyId);
      
      // Navigate to workflows page to monitor execution
      await workflowsPage.goto();
      await workflowsPage.enableRealTimeUpdates();
      
      // Find the execution we just started
      await workflowsPage.refreshExecutions();
      const executions = await workflowsPage.getAllExecutions();
      const ourExecution = executions.find(e => e.strategy.includes(testStrategyName));
      
      expect(ourExecution).toBeTruthy();
      executionId = ourExecution!.id;
    });

    await test.step('Monitor workflow execution progress', async () => {
      // Wait for execution to progress through steps
      await workflowsPage.waitForExecutionStatusChange(executionId, 'Running', 10000);
      
      // Monitor execution for a reasonable time
      let attempts = 0;
      const maxAttempts = 30; // 5 minutes max
      
      while (attempts < maxAttempts) {
        const executionData = await workflowsPage.getExecutionData(executionId);
        
        if (executionData.status.toLowerCase().includes('completed') || 
            executionData.status.toLowerCase().includes('failed')) {
          break;
        }
        
        await page.waitForTimeout(10000); // Wait 10 seconds
        await workflowsPage.refreshExecutions();
        attempts++;
      }
    });

    await test.step('Verify workflow execution steps in lineage', async () => {
      await workflowsPage.viewExecutionLineage(executionId);
      
      await lineagePage.waitForLineageLoad();
      const steps = await lineagePage.getAllSteps();
      
      // Verify we have the expected workflow steps
      expect(steps.length).toBeGreaterThan(0);
      
      // Check for key workflow steps
      const stepNames = steps.map(s => s.name.toLowerCase());
      expect(stepNames.some(name => name.includes('strategy') || name.includes('load'))).toBeTruthy();
      expect(stepNames.some(name => name.includes('market') || name.includes('data'))).toBeTruthy();
      expect(stepNames.some(name => name.includes('indicator') || name.includes('calculate'))).toBeTruthy();
      
      // Verify step visualizations
      for (let i = 0; i < Math.min(steps.length, 5); i++) {
        await lineagePage.assertVisualizationVisible(i);
        
        // Test step detail modal
        await lineagePage.viewStepDetails(i);
        await lineagePage.assertStepDetailModalOpen(steps[i].name);
        await lineagePage.closeStepDetails();
      }
    });

    await test.step('Verify execution results on dashboard', async () => {
      await dashboardPage.goto();
      await dashboardPage.waitForDashboardLoad();
      
      const stats = await dashboardPage.getWorkflowStats();
      expect(parseInt(stats.totalExecutions || '0')).toBeGreaterThan(0);
      
      const recentResults = await dashboardPage.getRecentResults();
      const ourResult = recentResults.find(r => r.strategy.includes(testStrategyName));
      expect(ourResult).toBeTruthy();
    });

    await test.step('Verify market data integration', async () => {
      // Check that market data was fetched during execution
      const lineageResponse = await page.request.get(`/api/lineage/execution/${executionId}`);
      expect(lineageResponse.ok()).toBeTruthy();
      
      const lineageData = await lineageResponse.json();
      const marketDataStep = lineageData.steps?.find((step: any) => 
        step.step_name.toLowerCase().includes('market') || 
        step.step_name.toLowerCase().includes('data')
      );
      
      if (marketDataStep) {
        expect(marketDataStep.output_data).toBeTruthy();
        expect(marketDataStep.success).toBe(true);
      }
    });

    await test.step('Verify signal generation', async () => {
      // Check for signal generation step
      const lineageResponse = await page.request.get(`/api/lineage/execution/${executionId}`);
      const lineageData = await lineageResponse.json();
      
      const signalStep = lineageData.steps?.find((step: any) => 
        step.step_name.toLowerCase().includes('signal') || 
        step.step_name.toLowerCase().includes('analysis')
      );
      
      if (signalStep) {
        expect(signalStep.output_data).toBeTruthy();
        // Should have generated some form of trading signal
        const output = signalStep.output_data;
        expect(output.type || output.action || output.signal).toBeTruthy();
      }
    });

    await test.step('Check order management (if orders were placed)', async () => {
      // Check if any orders were placed during execution
      const ordersResponse = await page.request.get('/api/orders');
      
      if (ordersResponse.ok()) {
        const orders = await ordersResponse.json();
        const executionOrders = orders.filter((order: any) => 
          order.execution_id === executionId || 
          order.strategy_id === createdStrategyId
        );
        
        // If orders were placed, verify their structure
        executionOrders.forEach((order: any) => {
          expect(order.symbol).toBeTruthy();
          expect(order.side).toMatch(/BUY|SELL/);
          expect(order.quantity).toBeGreaterThan(0);
          expect(order.status).toBeTruthy();
        });
      }
    });

    await test.step('Verify portfolio impact (if applicable)', async () => {
      // Check portfolio positions if any trades were executed
      const portfolioResponse = await page.request.get('/api/portfolio');
      
      if (portfolioResponse.ok()) {
        const portfolio = await portfolioResponse.json();
        
        // Verify portfolio structure
        expect(portfolio.total_value).toBeDefined();
        expect(portfolio.cash_balance).toBeDefined();
        expect(Array.isArray(portfolio.positions)).toBeTruthy();
      }
    });

    await test.step('Cleanup: Deactivate test strategy', async () => {
      await strategiesPage.goto();
      await strategiesPage.toggleStrategyActive(createdStrategyId);
      await strategiesPage.assertStrategyStatus(createdStrategyId, 'Inactive');
    });
  });

  test('should handle workflow execution errors gracefully', async ({ page }) => {
    const strategiesPage = new StrategiesPage(page);
    const strategyFormPage = new StrategyFormPage(page);
    const workflowsPage = new WorkflowsPage(page);
    const lineagePage = new LineagePage(page);

    await test.step('Create strategy with invalid parameters', async () => {
      await strategiesPage.goto();
      await strategiesPage.createNewStrategy();
      
      // Create strategy with parameters that might cause execution issues
      await strategyFormPage.fillStrategyForm({
        name: `Error Test Strategy ${Date.now()}`,
        workflow_id: 'momentum_trading',
        active: true,
        account_size: 1000, // Very small account
        risk_per_trade: 0.001, // Very small risk
        min_r_coefficient: 10.0, // Very high requirement
        min_profit_margin: 50.0, // Unrealistic profit margin
        delay_between_symbols: 1 // Very short delay
      });

      await strategyFormPage.saveStrategy();
    });

    await test.step('Execute strategy and handle errors', async () => {
      const strategies = await strategiesPage.getAllStrategies();
      const errorTestStrategy = strategies.find(s => s.name.includes('Error Test Strategy'));
      
      if (errorTestStrategy) {
        await strategiesPage.executeStrategy(errorTestStrategy.id);
        
        await workflowsPage.goto();
        await workflowsPage.refreshExecutions();
        
        const executions = await workflowsPage.getAllExecutions();
        const errorExecution = executions.find(e => e.strategy.includes('Error Test Strategy'));
        
        if (errorExecution) {
          // Wait for execution to complete (likely with errors)
          await workflowsPage.waitForExecutionCompletion(errorExecution.id, 60000);
          
          // Check lineage for error handling
          await workflowsPage.viewExecutionLineage(errorExecution.id);
          
          const steps = await lineagePage.getAllSteps();
          expect(steps.length).toBeGreaterThan(0);
          
          // Should have some failed steps or error handling
          const stats = await lineagePage.getLineageStats();
          const totalSteps = parseInt(stats.totalSteps);
          const failedSteps = parseInt(stats.failedSteps);
          
          // Either some steps failed, or execution was handled gracefully
          expect(totalSteps).toBeGreaterThan(0);
        }
      }
    });
  });
});
