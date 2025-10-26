import { test, expect } from '../fixtures/test-fixtures';

test.describe('API Integration Tests @api @integration', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should handle API responses correctly with mocked data', async ({ page, apiMocks }) => {
    await test.step('Enable API mocks', async () => {
      await apiMocks.enableAllMocks();
    });

    await test.step('Test strategies API integration', async () => {
      const response = await page.request.get('/api/strategies');
      expect(response.ok()).toBeTruthy();
      
      const strategies = await response.json();
      expect(Array.isArray(strategies)).toBeTruthy();
      expect(strategies.length).toBeGreaterThan(0);
      
      const strategy = strategies[0];
      expect(strategy.id).toBeTruthy();
      expect(strategy.name).toBeTruthy();
      expect(strategy.workflow_id).toBeTruthy();
    });

    await test.step('Test workflow executions API', async () => {
      const response = await page.request.get('/api/workflows/executions');
      expect(response.ok()).toBeTruthy();
      
      const executions = await response.json();
      expect(Array.isArray(executions)).toBeTruthy();
      
      if (executions.length > 0) {
        const execution = executions[0];
        expect(execution.id).toBeTruthy();
        expect(execution.status).toBeValidExecutionStatus();
      }
    });

    await test.step('Test lineage API integration', async () => {
      const response = await page.request.get('/api/lineage/execution/exec_001');
      expect(response.ok()).toBeTruthy();
      
      const lineage = await response.json();
      expect(lineage.execution_id).toBe('exec_001');
      expect(Array.isArray(lineage.steps)).toBeTruthy();
      expect(lineage.total_steps).toBeGreaterThan(0);
    });
  });

  test('should handle API errors gracefully', async ({ page, apiMocks }) => {
    await test.step('Mock API error responses', async () => {
      await page.route('**/api/strategies', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });
    });

    await test.step('Verify error handling in UI', async () => {
      await page.goto('/strategies');
      
      // Should show error message
      await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    });
  });

  test('should validate API request/response formats', async ({ page, testData }) => {
    await test.step('Test strategy creation API format', async () => {
      const testStrategy = testData.generateStrategy({
        name: 'API Test Strategy',
        active: true
      });

      const response = await page.request.post('/api/strategies', {
        data: testStrategy
      });

      if (response.ok()) {
        const created = await response.json();
        expect(created.id).toBeTruthy();
        expect(created.name).toBe(testStrategy.name);
        expect(created.active).toBe(testStrategy.active);
      }
    });

    await test.step('Test execution trigger API format', async () => {
      const response = await page.request.post('/api/strategies/1/execute');
      
      if (response.ok()) {
        const result = await response.json();
        expect(result.message).toBeTruthy();
        expect(result.strategy_id).toBeTruthy();
        expect(result.task_id).toBeTruthy();
      }
    });
  });
});

test.describe('Real-time Updates @api @websocket', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should handle WebSocket connections for real-time updates', async ({ page }) => {
    let wsConnected = false;
    let wsMessages: any[] = [];

    await test.step('Setup WebSocket listeners', async () => {
      page.on('websocket', ws => {
        wsConnected = true;
        
        ws.on('framereceived', event => {
          try {
            const data = JSON.parse(event.payload.toString());
            wsMessages.push(data);
          } catch (e) {
            // Ignore non-JSON messages
          }
        });
      });
    });

    await test.step('Navigate to workflows page and enable real-time updates', async () => {
      await page.goto('/workflows');
      
      const realTimeToggle = page.locator('[data-testid="realtime-updates-toggle"]');
      if (await realTimeToggle.isVisible()) {
        await realTimeToggle.check();
      }
    });

    await test.step('Verify WebSocket connection', async () => {
      await page.waitForTimeout(2000);
      expect(wsConnected).toBeTruthy();
    });

    await test.step('Trigger execution to generate real-time updates', async () => {
      // Get available strategies
      const strategiesResponse = await page.request.get('/api/strategies');
      if (strategiesResponse.ok()) {
        const strategies = await strategiesResponse.json();
        const activeStrategies = strategies.filter((s: any) => s.active);
        
        if (activeStrategies.length > 0) {
          await page.request.post(`/api/strategies/${activeStrategies[0].id}/execute`);
          
          // Wait for WebSocket messages
          await page.waitForTimeout(5000);
          
          // Should have received some updates
          expect(wsMessages.length).toBeGreaterThan(0);
        }
      }
    });
  });
});

test.describe('Performance Testing @api @performance', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should load pages within acceptable time limits', async ({ page }) => {
    const performanceThresholds = {
      dashboard: 3000,
      strategies: 2000,
      workflows: 2000,
      lineage: 2500
    };

    await test.step('Test dashboard load time', async () => {
      const startTime = Date.now();
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(performanceThresholds.dashboard);
    });

    await test.step('Test strategies page load time', async () => {
      const startTime = Date.now();
      await page.goto('/strategies');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(performanceThresholds.strategies);
    });

    await test.step('Test workflows page load time', async () => {
      const startTime = Date.now();
      await page.goto('/workflows');
      await page.waitForLoadState('networkidle');
      const loadTime = Date.now() - startTime;
      
      expect(loadTime).toBeLessThan(performanceThresholds.workflows);
    });
  });

  test('should handle concurrent API requests efficiently', async ({ page }) => {
    await test.step('Make concurrent API requests', async () => {
      const requests = [
        page.request.get('/api/strategies'),
        page.request.get('/api/workflows/executions'),
        page.request.get('/api/dashboard'),
        page.request.get('/api/health')
      ];

      const startTime = Date.now();
      const responses = await Promise.all(requests);
      const totalTime = Date.now() - startTime;

      // All requests should complete within 5 seconds
      expect(totalTime).toBeLessThan(5000);
      
      // All responses should be successful
      responses.forEach(response => {
        expect(response.ok()).toBeTruthy();
      });
    });
  });
});
