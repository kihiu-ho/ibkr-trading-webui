import { test, expect } from '@playwright/test';
import { StrategiesPage, StrategyFormPage } from '../page-objects';

test.describe('Strategy Management @e2e @strategies', () => {
  test.use({ storageState: 'test-results/auth.json' });
  
  let strategiesPage: StrategiesPage;

  test.beforeEach(async ({ page }) => {
    strategiesPage = new StrategiesPage(page);
    await strategiesPage.goto();
  });

  test('should display strategies list correctly', async () => {
    await test.step('Verify strategies page loads', async () => {
      await strategiesPage.assertStrategiesPageLoaded();
    });

    await test.step('Check strategies data', async () => {
      const strategies = await strategiesPage.getAllStrategies();
      expect(Array.isArray(strategies)).toBeTruthy();
      
      if (strategies.length > 0) {
        const strategy = strategies[0];
        expect(strategy.id).toBeTruthy();
        expect(strategy.name).toBeTruthy();
        expect(strategy.status).toMatch(/Active|Inactive/);
      }
    });
  });

  test('should create new strategy successfully', async ({ page }) => {
    const strategyFormPage = new StrategyFormPage(page);
    
    await test.step('Navigate to create strategy form', async () => {
      await strategiesPage.createNewStrategy();
      await strategyFormPage.assertFormLoaded();
    });

    await test.step('Fill and submit strategy form', async () => {
      const testStrategy = {
        name: `Test Strategy ${Date.now()}`,
        workflow_id: 'momentum_trading',
        active: true,
        account_size: 100000,
        risk_per_trade: 0.02,
        min_r_coefficient: 2.0,
        min_profit_margin: 3.0,
        delay_between_symbols: 30,
        temperature: 0.7,
        max_tokens: 4000
      };

      await strategyFormPage.fillStrategyForm(testStrategy);
      await strategyFormPage.saveStrategy();
    });

    await test.step('Verify strategy was created', async () => {
      await expect(page).toHaveURL(/.*\/strategies$/);
      await strategiesPage.waitForStrategiesLoad();
    });
  });

  test('should validate strategy parameters', async ({ page }) => {
    const strategyFormPage = new StrategyFormPage(page);
    
    await strategiesPage.createNewStrategy();
    
    await test.step('Fill form with invalid parameters', async () => {
      await strategyFormPage.fillStrategyForm({
        name: 'Invalid Strategy',
        account_size: -1000, // Invalid negative value
        risk_per_trade: 1.5, // Invalid > 1
        min_r_coefficient: -1, // Invalid negative
        temperature: 3.0 // Invalid > 2
      });
    });

    await test.step('Validate parameters', async () => {
      await strategyFormPage.validateParameters();
      const results = await strategyFormPage.getValidationResults();
      
      expect(results.errors.length).toBeGreaterThan(0);
      expect(results.errors.some(error => error.includes('account_size'))).toBeTruthy();
      expect(results.errors.some(error => error.includes('risk_per_trade'))).toBeTruthy();
    });
  });

  test('should edit existing strategy', async ({ page }) => {
    const strategies = await strategiesPage.getAllStrategies();
    
    if (strategies.length === 0) {
      test.skip('No strategies available for editing');
    }

    const strategyToEdit = strategies[0];
    const strategyFormPage = new StrategyFormPage(page, strategyToEdit.id);
    
    await test.step('Navigate to edit form', async () => {
      await strategiesPage.editStrategy(strategyToEdit.id);
      await strategyFormPage.assertFormLoaded();
    });

    await test.step('Modify strategy parameters', async () => {
      await strategyFormPage.fillStrategyForm({
        name: `${strategyToEdit.name} - Updated`,
        account_size: 150000
      });
      
      await strategyFormPage.saveStrategy();
    });

    await test.step('Verify changes were saved', async () => {
      await expect(page).toHaveURL(/.*\/strategies$/);
      const updatedStrategy = await strategiesPage.getStrategyData(strategyToEdit.id);
      expect(updatedStrategy.name).toContain('Updated');
    });
  });

  test('should toggle strategy active status', async () => {
    const strategies = await strategiesPage.getAllStrategies();
    
    if (strategies.length === 0) {
      test.skip('No strategies available for status toggle');
    }

    const strategy = strategies[0];
    const initialStatus = strategy.status;
    
    await test.step('Toggle strategy status', async () => {
      await strategiesPage.toggleStrategyActive(strategy.id);
      
      const expectedStatus = initialStatus === 'Active' ? 'Inactive' : 'Active';
      await strategiesPage.assertStrategyStatus(strategy.id, expectedStatus);
    });
  });

  test('should execute strategy workflow', async () => {
    const strategies = await strategiesPage.getAllStrategies();
    const activeStrategies = strategies.filter(s => s.status === 'Active');
    
    if (activeStrategies.length === 0) {
      test.skip('No active strategies available for execution');
    }

    const strategy = activeStrategies[0];
    
    await test.step('Execute strategy', async () => {
      await strategiesPage.executeStrategy(strategy.id);
    });

    await test.step('Verify execution started', async () => {
      // Should show success toast
      await strategiesPage.waitForToast('Workflow execution started');
    });
  });

  test('should filter and search strategies', async () => {
    await test.step('Filter by active strategies', async () => {
      await strategiesPage.filterStrategies('active');
      
      const strategies = await strategiesPage.getAllStrategies();
      strategies.forEach(strategy => {
        expect(strategy.status).toBe('Active');
      });
    });

    await test.step('Filter by inactive strategies', async () => {
      await strategiesPage.filterStrategies('inactive');
      
      const strategies = await strategiesPage.getAllStrategies();
      strategies.forEach(strategy => {
        expect(strategy.status).toBe('Inactive');
      });
    });

    await test.step('Search strategies by name', async () => {
      await strategiesPage.filterStrategies('all');
      const allStrategies = await strategiesPage.getAllStrategies();
      
      if (allStrategies.length > 0) {
        const searchTerm = allStrategies[0].name.split(' ')[0];
        await strategiesPage.searchStrategies(searchTerm);
        await strategiesPage.assertSearchResults(searchTerm);
      }
    });
  });

  test('should delete strategy with confirmation', async () => {
    // First create a strategy to delete
    const testStrategyName = `Delete Test ${Date.now()}`;
    
    await test.step('Create strategy for deletion', async () => {
      const response = await strategiesPage.page.request.post('/api/strategies', {
        data: {
          name: testStrategyName,
          workflow_id: 'momentum_trading',
          active: false,
          param: { account_size: 10000 }
        }
      });
      
      expect(response.ok()).toBeTruthy();
    });

    await test.step('Refresh and find created strategy', async () => {
      await strategiesPage.refreshStrategies();
      const strategies = await strategiesPage.getAllStrategies();
      const strategyToDelete = strategies.find(s => s.name === testStrategyName);
      
      expect(strategyToDelete).toBeTruthy();
      
      if (strategyToDelete) {
        await strategiesPage.deleteStrategy(strategyToDelete.id);
        await strategiesPage.assertStrategyNotExists(strategyToDelete.id);
      }
    });
  });

  test('should view strategy executions', async ({ page }) => {
    const strategies = await strategiesPage.getAllStrategies();
    
    if (strategies.length === 0) {
      test.skip('No strategies available');
    }

    const strategy = strategies[0];
    
    await test.step('Navigate to strategy executions', async () => {
      await strategiesPage.viewStrategyExecutions(strategy.id);
      await expect(page).toHaveURL(new RegExp(`.*\/workflows\/lineage\\?strategy_id=${strategy.id}`));
    });
  });
});
