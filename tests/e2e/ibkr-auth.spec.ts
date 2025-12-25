import { test, expect } from '@playwright/test';
import { IBKRAuthPage } from '../page-objects';

const gatewayUrl = 'https://127.0.0.1:5055';

test.describe('IBKR Authentication @smoke @auth', () => {
  let authPage: IBKRAuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new IBKRAuthPage(page);
  });

  test('should successfully authenticate with paper trading credentials', async () => {
    let statusCall = 0;
    await authPage.page.route('**/api/ibkr/auth/status', route => {
      statusCall += 1;
      if (statusCall === 1) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            authenticated: false,
            server_online: true,
            connected: false,
            accounts: [],
            account_id: null,
            gateway_url: gatewayUrl,
            message: 'Not authenticated'
          })
        });
      }
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          server_online: true,
          connected: true,
          accounts: ['DU123456'],
          account_id: 'DU123456',
          gateway_url: gatewayUrl,
          message: 'Connected',
          trading_mode: 'PAPER'
        })
      });
    });

    await authPage.page.route('**/api/ibkr/auth/auto-login/env', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          authenticated: true,
          connected: true,
          server_online: true,
          message: 'Login successful',
          trading_mode: 'PAPER'
        })
      });
    });

    await test.step('Navigate to authentication page', async () => {
      await authPage.goto();
    });

    await test.step('Trigger auto-login from server env credentials', async () => {
      await authPage.autoLoginFromEnv();
    });

    await test.step('Verify successful connection', async () => {
      await authPage.waitForConnection();
      await expect(authPage.connectionStatus).toContainText('Connected');
      await expect(authPage.statusMessage).toContainText('Connected');
      await expect(authPage.page.getByTestId('trading-mode')).toContainText('PAPER');
    });
  });

  test('should treat login-required as a status message (not an error)', async () => {
    await authPage.page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: false,
          server_online: true,
          connected: false,
          accounts: [],
          account_id: null,
          gateway_url: gatewayUrl,
          message: 'Authentication required. Please login to IBKR Gateway.',
          trading_mode: 'paper',
        }),
      });
    });

    await authPage.goto();

    await expect(authPage.statusMessage).toBeVisible();
    await expect(authPage.statusMessage).toContainText('Authentication required');
    await expect(authPage.errorMessage).toBeHidden();
    await expect(authPage.page.getByTestId('trading-mode')).toContainText('PAPER');
  });

  test('should handle invalid credentials gracefully', async () => {
    await authPage.page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: false,
          server_online: true,
          connected: false,
          accounts: [],
          account_id: null,
          gateway_url: gatewayUrl,
          message: 'Not authenticated'
        })
      });
    });

    await authPage.page.route('**/api/ibkr/auth/auto-login/env', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' })
      });
    });

    await authPage.goto();
    
    await authPage.autoLoginFromEnv();
    
    await expect(authPage.errorMessage).toBeVisible();
    await expect(authPage.errorMessage).toContainText('Invalid credentials');
    await expect(authPage.connectionStatus).toContainText('Not Connected');
  });

  test('should maintain paper trading mode selection', async () => {
    let statusAuthenticated = false;

    await authPage.page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: statusAuthenticated,
          server_online: true,
          connected: statusAuthenticated,
          accounts: statusAuthenticated ? ['DU123456'] : [],
          account_id: statusAuthenticated ? 'DU123456' : null,
          gateway_url: gatewayUrl,
          message: statusAuthenticated ? 'Connected' : 'Not authenticated',
          trading_mode: 'PAPER'
        })
      });
    });

    await authPage.page.route('**/api/ibkr/auth/auto-login/env', route => {
      statusAuthenticated = true;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          authenticated: true,
          connected: true,
          server_online: true,
          message: 'Login successful',
          trading_mode: 'PAPER'
        })
      });
    });

    await authPage.goto();
    await authPage.autoLoginFromEnv();
    await authPage.waitForConnection();
    await expect(authPage.page.getByTestId('trading-mode')).toContainText('PAPER');
  });

  test('should handle connection timeout', async () => {
    await authPage.page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: false,
          server_online: false,
          connected: false,
          error: 'Gateway timeout',
          gateway_url: gatewayUrl
        })
      });
    });

    await authPage.page.route('**/api/ibkr/auth/auto-login/env', route => {
      setTimeout(() => {
        route.fulfill({
          status: 504,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Connection timeout' })
        });
      }, 200);
    });

    await authPage.goto();
    await authPage.autoLoginFromEnv();

    await expect(authPage.errorMessage).toContainText('timeout');
  });

  test('should persist authentication state', async ({ context }) => {
    await authPage.page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          server_online: true,
          connected: true,
          accounts: ['DU123456'],
          account_id: 'DU123456',
          gateway_url: gatewayUrl,
          message: 'Connected'
        })
      });
    });
    await authPage.page.route('**/api/ibkr/auth/auto-login/env', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          authenticated: true,
          connected: true,
          server_online: true,
          message: 'Login successful'
        })
      });
    });

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

    await page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          server_online: true,
          connected: true,
          accounts: ['DU123456'],
          account_id: 'DU123456',
          gateway_url: gatewayUrl,
          message: 'Connected'
        })
      });
    });

    await authPage.goto();
    
    // Verify initial connection
    await expect(authPage.connectionStatus).toContainText('Connected');
    
    // Wait and check connection stability
    await page.waitForTimeout(5000);
    await expect(authPage.connectionStatus).toContainText('Connected');
  });

  test('should handle connection reconnection', async ({ page }) => {
    const authPage = new IBKRAuthPage(page);
    let connected = false;

    await page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: connected,
          server_online: true,
          connected,
          accounts: connected ? ['DU123456'] : [],
          account_id: connected ? 'DU123456' : null,
          gateway_url: gatewayUrl,
          message: connected ? 'Connected' : 'Disconnected'
        })
      });
    });

    await authPage.goto();
    await expect(authPage.connectionStatus).toContainText('Not Connected');

    connected = true;
    await authPage.refreshStatus();

    await expect(authPage.connectionStatus).toContainText('Connected');
  });

  test('should provide connection status updates', async ({ page }) => {
    const authPage = new IBKRAuthPage(page);
    let message = 'Starting';

    await page.route('**/api/ibkr/auth/status', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          server_online: true,
          connected: true,
          accounts: ['DU123456'],
          account_id: 'DU123456',
          gateway_url: gatewayUrl,
          message
        })
      });
    });

    await authPage.goto();
    
    message = 'Updated';
    await authPage.refreshStatus();

    await expect(authPage.statusMessage).toContainText('Updated');
  });
});
