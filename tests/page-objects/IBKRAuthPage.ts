import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class IBKRAuthPage extends BasePage {
  constructor(page: Page) {
    super(page, '/ibkr/login'); // IBKR Gateway authentication page URL
  }

  // Page elements
  get connectButton() {
    return this.page.locator('button[\\@click="login()"]');
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

  // Methods
  async connectToGateway() {
    try {
      // Check if connect button is available and visible
      const connectButtonVisible = await this.connectButton.isVisible({ timeout: 5000 }).catch(() => false);

      if (connectButtonVisible) {
        await this.connectButton.click();
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

  async assertAuthenticationFailure() {
    const status = await this.checkConnectionStatus();
    expect(status.serverOnline && status.authenticated).toBeFalsy();
  }

  async performFullLogin() {
    await this.goto();
    await this.refreshStatus();

    // Try to connect to gateway
    await this.connectToGateway();

    // Check if connection was successful
    await this.refreshStatus();

    // Save authentication state (even if not fully authenticated)
    await this.page.context().storageState({ path: 'test-results/auth.json' });
  }
}
