import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class IBKRAuthPage extends BasePage {
  constructor(page: Page) {
    super(page, '/ibkr/login'); // IBKR Gateway authentication page URL
  }

  // Page elements
  get connectButton() {
    return this.page.getByTestId('manual-login-button');
  }

  get autoLoginButton() {
    return this.page.getByTestId('auto-login-button');
  }

  get disconnectButton() {
    return this.page.locator('button[\\@click="logout()"]');
  }

  get refreshButton() {
    return this.page.locator('button[\\@click="checkStatus()"]');
  }

  get gatewayLoginLink() {
    return this.page.locator('a[href="https://localhost:5055"]');
  }

  get connectionStatus() {
    return this.page.locator('[data-testid="connection-status"]');
  }

  get errorMessage() {
    return this.page.locator('[data-testid="auth-error"]');
  }

  get serverStatus() {
    return this.page.locator('text=Gateway Server');
  }

  get authStatus() {
    return this.page.locator('text=Authentication');
  }

  get statusMessage() {
    return this.page.getByTestId('status-message');
  }

  // Methods
  async login(username?: string, password?: string, paperTrading?: boolean) {
    // UI uses server-side env credentials; click auto-login and wait.
    await this.autoLoginFromEnv();
    await this.waitForConnection();
  }

  async autoLoginFromEnv() {
    await this.autoLoginButton.click();
  }

  async connectToGateway() {
    try {
      // Check if connect button is available and visible
      const connectButtonVisible = await this.connectButton.isVisible({ timeout: 5000 }).catch(() => false);
      const connectButtonEnabled = connectButtonVisible
        ? await this.connectButton.isEnabled({ timeout: 1000 }).catch(() => false)
        : false;

      if (connectButtonVisible && connectButtonEnabled) {
        await this.connectButton.click({ timeout: 5000 });
        console.log('✅ Connect button clicked');

        // Wait for connection attempt to complete
        await this.page.waitForTimeout(3000);

        // Check for any error messages or success indicators
        const errorVisible = await this.errorMessage.isVisible({ timeout: 2000 }).catch(() => false);
        if (errorVisible) {
          const errorText = await this.errorMessage.textContent();
          console.log(`⚠️ Connection error displayed: ${errorText}`);
        }

        // Look for "Authentication Connected" or similar success message
        const successIndicators = [
          'text=Authentication Connected',
          'text=Connected',
          'text=Online',
          'text=Authenticated'
        ];

        for (const indicator of successIndicators) {
          const isVisible = await this.page.locator(indicator).isVisible({ timeout: 1000 }).catch(() => false);
          if (isVisible) {
            console.log(`✅ Success indicator found: ${indicator}`);
            return true;
          }
        }

      } else if (connectButtonVisible) {
        console.log('⚠️ Connect button is visible but disabled; skipping click');
      } else {
        console.log('⚠️ Connect button not found or not visible');
      }

      return false;
    } catch (error) {
      console.log(`⚠️ Connection attempt failed: ${error.message}`);
      return false;
    }
  }

  async disconnect() {
    await this.disconnectButton.click();
    await this.page.waitForTimeout(1000);
  }

  async refreshStatus() {
    await this.refreshButton.click();
    await this.page.waitForTimeout(1000);
  }

  async checkConnectionStatus() {
    try {
      await this.refreshStatus();

      // Check for various possible status indicators
      const serverOnline = await this.page.locator('text=Online').isVisible({ timeout: 5000 }).catch(() => false);
      const authenticated = await this.page.locator('text=Authenticated').isVisible({ timeout: 5000 }).catch(() => false);

      // Also check for "Connected" status which might be used instead
      const connected = await this.page.locator('text=Connected').isVisible({ timeout: 2000 }).catch(() => false);



      return {
        serverOnline: serverOnline || connected,
        authenticated: authenticated || connected
      };
    } catch (error) {
      console.log('⚠️ Status check failed, assuming disconnected state');
      return { serverOnline: false, authenticated: false };
    }
  }

  async assertAuthenticationSuccess() {
    const status = await this.checkConnectionStatus();
    expect(status.serverOnline || status.authenticated).toBeTruthy();
  }

  async assertAuthenticationFailure(expectedText?: string) {
    const status = await this.checkConnectionStatus();
    expect(status.serverOnline && status.authenticated).toBeFalsy();
    if (expectedText) {
      await expect(this.errorMessage).toContainText(expectedText);
    }
  }

  async performFullLogin() {
    await this.goto();

    const canClickAutoLogin = await this.autoLoginButton.isEnabled().catch(() => false);
    if (canClickAutoLogin) {
      await this.autoLoginFromEnv();
    }
    await this.waitForConnection();

    // Save authentication state (even if not fully authenticated)
    await this.page.context().storageState({ path: 'test-results/auth.json' });
  }

  async waitForConnection() {
    await expect(this.connectionStatus).toContainText('Connected');
  }
}
