import { test, expect } from '@playwright/test';
import { DashboardPage } from '../page-objects';

test.describe('Dashboard Functionality @e2e @dashboard', () => {
  test.use({ storageState: 'test-results/auth.json' });
  
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('should display workflow statistics correctly', async () => {
    await test.step('Verify dashboard loads with all sections', async () => {
      await dashboardPage.assertDashboardLoaded();
      await dashboardPage.assertWorkflowStatsVisible();
    });

    await test.step('Check workflow statistics data', async () => {
      const stats = await dashboardPage.getWorkflowStats();
      
      expect(stats.totalExecutions).toBeTruthy();
      expect(stats.successfulExecutions).toBeTruthy();
      expect(stats.failedExecutions).toBeTruthy();
      expect(stats.successRate).toMatch(/\d+(\.\d+)?%/);
      expect(stats.averageExecutionTime).toMatch(/\d+(\.\d+)?\s*(ms|s|min)/);
    });

    await test.step('Verify statistics are numeric and reasonable', async () => {
      const stats = await dashboardPage.getWorkflowStats();
      
      const totalExec = parseInt(stats.totalExecutions || '0');
      const successfulExec = parseInt(stats.successfulExecutions || '0');
      const failedExec = parseInt(stats.failedExecutions || '0');
      
      expect(totalExec).toBeGreaterThanOrEqual(0);
      expect(successfulExec).toBeGreaterThanOrEqual(0);
      expect(failedExec).toBeGreaterThanOrEqual(0);
      expect(successfulExec + failedExec).toBeLessThanOrEqual(totalExec);
    });
  });

  test('should display active executions with real-time updates', async () => {
    await test.step('Check active executions section', async () => {
      const executions = await dashboardPage.getActiveExecutions();
      
      // Should have at least the structure even if empty
      expect(Array.isArray(executions)).toBeTruthy();
    });

    await test.step('Verify execution details format', async () => {
      const executions = await dashboardPage.getActiveExecutions();
      
      if (executions.length > 0) {
        const execution = executions[0];
        expect(execution.id).toBeTruthy();
        expect(execution.strategy).toBeTruthy();
        expect(execution.status).toMatch(/running|pending|paused/i);
        expect(execution.progress).toMatch(/\d+%|\d+\/\d+/);
      }
    });

    await test.step('Test clicking on active execution', async () => {
      const executions = await dashboardPage.getActiveExecutions();
      
      if (executions.length > 0) {
        await dashboardPage.clickActiveExecution(executions[0].id);
        // Should navigate to execution details
        await expect(dashboardPage.page).toHaveURL(/.*\/workflows\/executions\/.*/);
      }
    });
  });

  test('should show recent results with proper formatting', async () => {
    await test.step('Load recent results', async () => {
      const results = await dashboardPage.getRecentResults();
      expect(Array.isArray(results)).toBeTruthy();
    });

    await test.step('Verify result data structure', async () => {
      const results = await dashboardPage.getRecentResults();
      
      if (results.length > 0) {
        const result = results[0];
        expect(result.strategy).toBeTruthy();
        expect(result.status).toMatch(/completed|failed|cancelled/i);
        expect(result.timestamp).toBeTruthy();
        expect(result.duration).toMatch(/\d+(\.\d+)?\s*(ms|s|min)/);
      }
    });

    await test.step('Test result interaction', async () => {
      const results = await dashboardPage.getRecentResults();
      
      if (results.length > 0) {
        await dashboardPage.clickRecentResult(0);
        // Should navigate to lineage or execution details
        await expect(dashboardPage.page).toHaveURL(/.*\/(workflows|lineage).*/);
      }
    });
  });

  test('should provide strategy management functionality', async () => {
    await test.step('Verify strategy management panel', async () => {
      await dashboardPage.assertElementVisible('[data-testid="strategy-management"]');
      await dashboardPage.assertElementVisible('[data-testid="active-strategies-count"]');
    });

    await test.step('Test create new strategy navigation', async () => {
      await dashboardPage.createNewStrategy();
      await expect(dashboardPage.page).toHaveURL(/.*\/strategies\/new/);
    });

    await test.step('Test manage strategies navigation', async () => {
      await dashboardPage.goto(); // Go back to dashboard
      await dashboardPage.navigateToStrategies();
      await expect(dashboardPage.page).toHaveURL(/.*\/strategies/);
    });
  });

  test('should handle dashboard refresh correctly', async () => {
    await test.step('Capture initial state', async () => {
      const initialStats = await dashboardPage.getWorkflowStats();
      const initialExecutions = await dashboardPage.getActiveExecutions();
      
      expect(initialStats).toBeTruthy();
      expect(Array.isArray(initialExecutions)).toBeTruthy();
    });

    await test.step('Refresh dashboard', async () => {
      await dashboardPage.refreshDashboard();
      
      // Should still show data after refresh
      await dashboardPage.assertDashboardLoaded();
    });

    await test.step('Verify data consistency after refresh', async () => {
      const refreshedStats = await dashboardPage.getWorkflowStats();
      expect(refreshedStats.totalExecutions).toBeTruthy();
    });
  });

  test('should navigate to different sections correctly', async () => {
    await test.step('Navigate to workflows', async () => {
      await dashboardPage.navigateToWorkflows();
      await expect(dashboardPage.page).toHaveURL(/.*\/workflows/);
    });

    await test.step('Navigate to lineage', async () => {
      await dashboardPage.goto(); // Back to dashboard
      await dashboardPage.navigateToLineage();
      await expect(dashboardPage.page).toHaveURL(/.*\/workflows\/lineage/);
    });
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    await test.step('Test mobile viewport', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await dashboardPage.goto();
      await dashboardPage.assertDashboardLoaded();
    });

    await test.step('Test tablet viewport', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await dashboardPage.goto();
      await dashboardPage.assertDashboardLoaded();
    });

    await test.step('Test desktop viewport', async () => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await dashboardPage.goto();
      await dashboardPage.assertDashboardLoaded();
    });
  });
});
