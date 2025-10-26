import { Page, Locator, expect } from '@playwright/test';

export abstract class BasePage {
  readonly page: Page;
  readonly url: string;

  constructor(page: Page, url: string) {
    this.page = page;
    this.url = url;
  }

  // Navigation
  async goto() {
    try {
      await this.page.goto(this.url, {
        waitUntil: 'domcontentloaded',
        timeout: 30000
      });
      await this.waitForPageLoad();
    } catch (error) {
      console.log(`⚠️ Navigation to ${this.url} failed: ${error.message}`);
      // Try to continue anyway - the page might be partially loaded
      try {
        await this.page.waitForTimeout(2000);
        await this.waitForPageLoad();
      } catch (waitError) {
        console.log(`⚠️ Page load wait also failed: ${waitError.message}`);
        // Continue anyway - tests should handle missing elements gracefully
      }
    }
  }

  async waitForPageLoad() {
    try {
      await this.page.waitForLoadState('domcontentloaded', { timeout: 15000 });
      // Try to wait for network idle, but don't fail if it times out
      await this.page.waitForLoadState('networkidle', { timeout: 10000 });
    } catch (error) {
      console.log(`⚠️ Page load state wait failed: ${error.message}`);
      // Continue anyway - the page might be functional even if not fully loaded
    }
  }

  // Common elements
  get navigation() {
    return this.page.locator('nav');
  }

  get header() {
    return this.page.locator('header');
  }

  get footer() {
    return this.page.locator('footer');
  }

  get loadingSpinner() {
    return this.page.locator('[data-testid="loading-spinner"]');
  }

  get errorMessage() {
    return this.page.locator('[data-testid="error-message"]');
  }

  get successMessage() {
    return this.page.locator('[data-testid="success-message"]');
  }

  // Common actions
  async clickNavLink(linkText: string) {
    await this.page.locator(`nav a:has-text("${linkText}")`).click();
  }

  async waitForToast(message?: string) {
    const toast = this.page.locator('.toast, .notification, [role="alert"]');
    await toast.waitFor({ state: 'visible' });
    
    if (message) {
      await expect(toast).toContainText(message);
    }
    
    return toast;
  }

  async dismissToast() {
    const dismissButton = this.page.locator('.toast button, .notification button');
    if (await dismissButton.isVisible()) {
      await dismissButton.click();
    }
  }

  // Form helpers
  async fillForm(formData: Record<string, string | number | boolean>) {
    for (const [field, value] of Object.entries(formData)) {
      const input = this.page.locator(`[name="${field}"], [data-testid="${field}"]`);
      
      if (typeof value === 'boolean') {
        if (value) {
          await input.check();
        } else {
          await input.uncheck();
        }
      } else {
        await input.fill(String(value));
      }
    }
  }

  async selectOption(selector: string, value: string) {
    await this.page.locator(selector).selectOption(value);
  }

  // Wait helpers
  async waitForApiResponse(urlPattern: string | RegExp) {
    return await this.page.waitForResponse(response => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    });
  }

  async waitForElement(selector: string, options?: { timeout?: number; state?: 'visible' | 'hidden' | 'attached' | 'detached' }) {
    return await this.page.locator(selector).waitFor(options);
  }

  // Assertions
  async assertPageTitle(title: string) {
    await expect(this.page).toHaveTitle(title);
  }

  async assertUrl(url: string | RegExp) {
    await expect(this.page).toHaveURL(url);
  }

  async assertElementVisible(selector: string) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  async assertElementHidden(selector: string) {
    await expect(this.page.locator(selector)).toBeHidden();
  }

  async assertElementText(selector: string, text: string | RegExp) {
    await expect(this.page.locator(selector)).toContainText(text);
  }

  // Screenshot helpers
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}.png`,
      fullPage: true 
    });
  }

  async takeElementScreenshot(selector: string, name: string) {
    await this.page.locator(selector).screenshot({ 
      path: `test-results/screenshots/${name}.png` 
    });
  }

  // Debug helpers
  async logPageInfo() {
    console.log(`Current URL: ${this.page.url()}`);
    console.log(`Page Title: ${await this.page.title()}`);
  }

  async logNetworkRequests() {
    this.page.on('request', request => {
      console.log(`Request: ${request.method()} ${request.url()}`);
    });
    
    this.page.on('response', response => {
      console.log(`Response: ${response.status()} ${response.url()}`);
    });
  }
}
