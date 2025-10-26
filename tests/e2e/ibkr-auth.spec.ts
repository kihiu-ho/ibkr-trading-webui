import { test, expect } from '@playwright/test';
import { IBKRAuthPage } from '../page-objects';

test.describe('IBKR Authentication @smoke @auth', () => {
  let authPage: IBKRAuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new IBKRAuthPage(page);
  });

  test('should successfully authenticate with paper trading credentials', async () => {
    await test.step('Navigate to authentication page', async () => {
      await authPage.goto();
      await expect(authPage.usernameInput).toBeVisible();
      await expect(authPage.passwordInput).toBeVisible();
    });

    await test.step('Enter credentials and enable paper trading', async () => {
      await authPage.login(
        process.env.IBKR_USERNAME || 'loginhiuhiu250',
        process.env.IBKR_PASSWORD || 'qazwsX321',
        true // Enable paper trading
      );
    });

    await test.step('Verify successful connection', async () => {
      await authPage.waitForConnection();
      await authPage.assertAuthenticationSuccess();
    });
  });

  test('should handle invalid credentials gracefully', async () => {
    await authPage.goto();
    
    await authPage.login('invalid_user', 'invalid_pass');
    
    await expect(authPage.errorMessage).toBeVisible();
    await authPage.assertAuthenticationFailure('Invalid credentials');
  });

  test('should maintain paper trading mode selection', async () => {
    await authPage.goto();
    
    // Ensure paper trading is enabled
    if (!(await authPage.paperTradingToggle.isChecked())) {
      await authPage.paperTradingToggle.check();
    }
    
    await expect(authPage.paperTradingToggle).toBeChecked();
    
    // Login should maintain paper trading mode
    await authPage.login();
    await authPage.waitForConnection();
    
    // Verify we're still in paper trading mode
    await expect(authPage.connectionStatus).toContainText('Paper Trading');
  });

  test('should handle connection timeout', async () => {
    await authPage.goto();
    
    // Mock a slow connection response
    await authPage.page.route('**/api/ibkr/auth/**', route => {
      setTimeout(() => route.continue(), 65000); // Longer than timeout
    });
    
    await authPage.login();
    
    // Should show timeout error
    await expect(authPage.errorMessage).toContainText('Connection timeout');
  });

  test('should persist authentication state', async ({ context }) => {
    await authPage.goto();
    await authPage.performFullLogin();
    
    // Create new page in same context
    const newPage = await context.newPage();
    const newAuthPage = new IBKRAuthPage(newPage);
    
    await newAuthPage.goto();
    
    // Should already be authenticated
    await expect(newAuthPage.connectionStatus).toContainText('Connected');
  });
});

test.describe('IBKR Connection Management @api', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should maintain stable connection during trading hours', async ({ page }) => {
    const authPage = new IBKRAuthPage(page);
    await authPage.goto();
    
    // Verify initial connection
    await expect(authPage.connectionStatus).toContainText('Connected');
    
    // Wait and check connection stability
    await page.waitForTimeout(5000);
    await expect(authPage.connectionStatus).toContainText('Connected');
  });

  test('should handle connection reconnection', async ({ page }) => {
    const authPage = new IBKRAuthPage(page);
    await authPage.goto();
    
    // Simulate connection loss
    await page.route('**/api/ibkr/**', route => route.abort());
    
    await page.waitForTimeout(2000);
    
    // Remove route to allow reconnection
    await page.unroute('**/api/ibkr/**');
    
    // Should automatically reconnect
    await expect(authPage.connectionStatus).toContainText('Connected', { timeout: 30000 });
  });

  test('should provide connection status updates', async ({ page }) => {
    const authPage = new IBKRAuthPage(page);
    await authPage.goto();
    
    const connectionMessages = [];
    
    // Listen for connection status changes
    page.on('console', msg => {
      if (msg.text().includes('IBKR Connection')) {
        connectionMessages.push(msg.text());
      }
    });
    
    await page.waitForTimeout(3000);
    
    // Should have received connection status updates
    expect(connectionMessages.length).toBeGreaterThan(0);
  });
});
