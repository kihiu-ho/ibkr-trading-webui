import { test, expect } from '@playwright/test';
import { WorkflowsPage } from '../page-objects';

test.describe('Workflow Execution Monitoring @e2e @workflows', () => {
  test.use({ storageState: 'test-results/auth.json' });
  
  let workflowsPage: WorkflowsPage;

  test.beforeEach(async ({ page }) => {
    workflowsPage = new WorkflowsPage(page);
    await workflowsPage.goto();
  });

  test('should display workflow executions with real-time updates', async () => {
    await test.step('Verify workflows page loads', async () => {
      await workflowsPage.assertWorkflowsPageLoaded();
    });

    await test.step('Check executions data', async () => {
      const executions = await workflowsPage.getAllExecutions();
      expect(Array.isArray(executions)).toBeTruthy();
      
      if (executions.length > 0) {
        const execution = executions[0];
        expect(execution.id).toBeTruthy();
        expect(execution.status).toMatch(/running|completed|failed|paused/i);
        expect(execution.strategy).toBeTruthy();
      }
    });

    await test.step('Enable real-time updates', async () => {
      await workflowsPage.enableRealTimeUpdates();
      await workflowsPage.assertRealTimeConnection();
    });
  });

  test('should trigger new workflow execution', async () => {
    // Get available strategies first
    const strategiesResponse = await workflowsPage.page.request.get('/api/strategies');
    expect(strategiesResponse.ok()).toBeTruthy();
    
    const strategies = await strategiesResponse.json();
    const activeStrategies = strategies.filter((s: any) => s.active);
    
    if (activeStrategies.length === 0) {
      test.skip('No active strategies available for execution');
    }

    const strategy = activeStrategies[0];
    
    await test.step('Trigger workflow execution', async () => {
      await workflowsPage.triggerWorkflow(strategy.id.toString());
    });

    await test.step('Verify execution appears in list', async () => {
      await workflowsPage.refreshExecutions();
      const executions = await workflowsPage.getAllExecutions();
      
      // Should have at least one execution
      expect(executions.length).toBeGreaterThan(0);
      
      // Find the most recent execution
      const recentExecution = executions[0];
      expect(recentExecution.strategy).toContain(strategy.name);
    });
  });

  test('should control workflow execution (pause/resume/stop)', async () => {
    // First trigger an execution
    const strategiesResponse = await workflowsPage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    const activeStrategies = strategies.filter((s: any) => s.active);
    
    if (activeStrategies.length === 0) {
      test.skip('No active strategies available');
    }

    await workflowsPage.triggerWorkflow(activeStrategies[0].id.toString());
    await workflowsPage.refreshExecutions();
    
    const executions = await workflowsPage.getAllExecutions();
    const runningExecution = executions.find(e => e.status.toLowerCase().includes('running'));
    
    if (!runningExecution) {
      test.skip('No running executions available for control testing');
    }

    await test.step('Pause execution', async () => {
      await workflowsPage.pauseExecution(runningExecution.id);
    });

    await test.step('Resume execution', async () => {
      await workflowsPage.resumeExecution(runningExecution.id);
    });

    await test.step('Stop execution', async () => {
      await workflowsPage.stopExecution(runningExecution.id);
    });
  });

  test('should filter executions by status', async () => {
    await test.step('Filter by running executions', async () => {
      await workflowsPage.filterExecutions('running');
      
      const executions = await workflowsPage.getAllExecutions();
      executions.forEach(execution => {
        expect(execution.status.toLowerCase()).toContain('running');
      });
    });

    await test.step('Filter by completed executions', async () => {
      await workflowsPage.filterExecutions('completed');
      
      const executions = await workflowsPage.getAllExecutions();
      executions.forEach(execution => {
        expect(execution.status.toLowerCase()).toContain('completed');
      });
    });

    await test.step('Filter by failed executions', async () => {
      await workflowsPage.filterExecutions('failed');
      
      const executions = await workflowsPage.getAllExecutions();
      executions.forEach(execution => {
        expect(execution.status.toLowerCase()).toContain('failed');
      });
    });
  });

  test('should navigate to execution details', async ({ page }) => {
    const executions = await workflowsPage.getAllExecutions();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    const execution = executions[0];
    
    await test.step('Navigate to execution details', async () => {
      await workflowsPage.viewExecutionDetails(execution.id);
      await expect(page).toHaveURL(new RegExp(`.*\/workflows\/executions\/${execution.id}`));
    });
  });

  test('should navigate to execution lineage', async ({ page }) => {
    const executions = await workflowsPage.getAllExecutions();
    
    if (executions.length === 0) {
      test.skip('No executions available');
    }

    const execution = executions[0];
    
    await test.step('Navigate to execution lineage', async () => {
      await workflowsPage.viewExecutionLineage(execution.id);
      await expect(page).toHaveURL(new RegExp(`.*\/workflows\/lineage\\?execution_id=${execution.id}`));
    });
  });

  test('should handle WebSocket connection for real-time updates', async ({ page }) => {
    let wsMessages: any[] = [];
    
    // Listen for WebSocket messages
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        try {
          const data = JSON.parse(event.payload.toString());
          wsMessages.push(data);
        } catch (e) {
          // Ignore non-JSON messages
        }
      });
    });

    await test.step('Enable real-time updates', async () => {
      await workflowsPage.enableRealTimeUpdates();
    });

    await test.step('Trigger execution to generate updates', async () => {
      const strategiesResponse = await page.request.get('/api/strategies');
      const strategies = await strategiesResponse.json();
      const activeStrategies = strategies.filter((s: any) => s.active);
      
      if (activeStrategies.length > 0) {
        await workflowsPage.triggerWorkflow(activeStrategies[0].id.toString());
        
        // Wait for WebSocket messages
        await page.waitForTimeout(5000);
        
        // Should have received some real-time updates
        expect(wsMessages.length).toBeGreaterThan(0);
      }
    });
  });

  test('should refresh executions data', async () => {
    await test.step('Capture initial state', async () => {
      const initialExecutions = await workflowsPage.getAllExecutions();
      expect(Array.isArray(initialExecutions)).toBeTruthy();
    });

    await test.step('Refresh executions', async () => {
      await workflowsPage.refreshExecutions();
      
      // Should still show executions after refresh
      const refreshedExecutions = await workflowsPage.getAllExecutions();
      expect(Array.isArray(refreshedExecutions)).toBeTruthy();
    });
  });

  test('should wait for execution completion', async () => {
    // Create a quick test execution
    const strategiesResponse = await workflowsPage.page.request.get('/api/strategies');
    const strategies = await strategiesResponse.json();
    const activeStrategies = strategies.filter((s: any) => s.active);
    
    if (activeStrategies.length === 0) {
      test.skip('No active strategies available');
    }

    await workflowsPage.triggerWorkflow(activeStrategies[0].id.toString());
    await workflowsPage.refreshExecutions();
    
    const executions = await workflowsPage.getAllExecutions();
    const newExecution = executions[0];
    
    await test.step('Wait for execution to complete', async () => {
      // Wait for completion (with reasonable timeout)
      await workflowsPage.waitForExecutionCompletion(newExecution.id, 60000);
    });
  });
});
