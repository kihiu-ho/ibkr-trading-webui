import { test, expect } from '@playwright/test';

test.describe('IBKR Workflow Testing @workflow @ibkr', () => {
  // Skip authentication for direct workflow testing
  test.use({ storageState: undefined });

  test('should validate IBKR workflow components', async ({ page }) => {
    await test.step('Test Dashboard Access', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Verify dashboard loads
      await expect(page.locator('h1')).toContainText('Dashboard');
      await expect(page.locator('body')).toBeVisible();
    });

    await test.step('Test Strategies Page Access', async () => {
      await page.goto('/strategies');
      await page.waitForLoadState('networkidle');
      
      // Verify strategies page loads
      await expect(page.locator('body')).toBeVisible();
      
      // Check if strategies API is accessible
      const response = await page.request.get('/api/strategies');
      expect(response.status()).toBeLessThan(500); // Allow 401/403 but not 500 errors
    });

    await test.step('Test Workflows Page Access', async () => {
      await page.goto('/workflows');
      await page.waitForLoadState('networkidle');
      
      // Verify workflows page loads
      await expect(page.locator('body')).toBeVisible();
    });

    await test.step('Test IBKR Authentication Page', async () => {
      await page.goto('/ibkr/login');
      await page.waitForLoadState('networkidle');
      
      // Verify IBKR auth page loads
      await expect(page.locator('h1')).toContainText('IBKR Gateway Authentication');
      await expect(page.locator('text=Connection Status')).toBeVisible();
      await expect(page.locator('text=Gateway Server')).toBeVisible();
    });

    await test.step('Test API Health Endpoints', async () => {
      // Test health endpoint
      const healthResponse = await page.request.get('/health');
      expect(healthResponse.ok()).toBeTruthy();
      
      const healthData = await healthResponse.json();
      expect(healthData.status).toBe('healthy');
      expect(healthData.database).toBe('connected');
    });

    await test.step('Test Strategy API Endpoints', async () => {
      // Test strategies endpoint (may require auth but should not 500)
      const strategiesResponse = await page.request.get('/api/strategies');
      expect(strategiesResponse.status()).toBeLessThan(500);
    });
  });

  test('should test IBKR workflow navigation', async ({ page }) => {
    await test.step('Navigate through workflow components', async () => {
      // Start at dashboard
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Navigate to strategies
      await page.click('a[href="/strategies"]');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL('/strategies');
      
      // Navigate to workflows
      await page.click('a[href="/workflows"]');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL('/workflows');
      
      // Navigate to lineage
      await page.click('a[href="/workflows/lineage"]');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL('/workflows/lineage');
      
      // Navigate to IBKR auth
      await page.click('a[href="/ibkr/login"]');
      await page.waitForLoadState('networkidle');
      await expect(page).toHaveURL('/ibkr/login');
    });
  });

  test('should validate IBKR Gateway connection interface', async ({ page }) => {
    await test.step('Test IBKR Gateway UI Components', async () => {
      await page.goto('/ibkr/login');
      await page.waitForLoadState('networkidle');
      
      // Verify connection status section
      await expect(page.locator('text=Connection Status')).toBeVisible();
      await expect(page.locator('text=Gateway Server')).toBeVisible();
      await expect(page.locator('text=Authentication')).toBeVisible();
      
      // Verify action buttons section
      await expect(page.locator('text=Actions')).toBeVisible();
      
      // Check for refresh button
      const refreshButton = page.locator('button[\\@click="checkStatus()"]');
      await expect(refreshButton).toBeVisible();
      
      // Test refresh functionality
      await refreshButton.click();
      await page.waitForTimeout(1000); // Wait for refresh to complete
    });
  });

  test('should test workflow API integration', async ({ page }) => {
    await test.step('Test Core API Endpoints', async () => {
      // Test health endpoint
      const health = await page.request.get('/health');
      expect(health.ok()).toBeTruthy();
      
      // Test strategies endpoint structure
      const strategies = await page.request.get('/api/strategies');
      expect([200, 401, 403]).toContain(strategies.status()); // Allow auth errors but not server errors
      
      // Test dashboard API if available
      const dashboard = await page.request.get('/api/dashboard/stats');
      expect(dashboard.status()).toBeLessThan(500); // Allow auth errors but not server errors
    });
  });
});
