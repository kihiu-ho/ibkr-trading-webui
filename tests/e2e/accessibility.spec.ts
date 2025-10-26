import { test, expect } from '../fixtures/test-fixtures';

test.describe('Accessibility Tests @visual @a11y', () => {
  test.use({ storageState: 'test-results/auth.json' });

  test('should meet accessibility standards', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();

    await test.step('Dashboard accessibility', async () => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      // Check for proper heading hierarchy
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      expect(headings.length).toBeGreaterThan(0);
      
      // Check for alt text on images
      const images = await page.locator('img').all();
      for (const img of images) {
        const alt = await img.getAttribute('alt');
        expect(alt).toBeTruthy();
      }
      
      // Check for proper form labels
      const inputs = await page.locator('input').all();
      for (const input of inputs) {
        const id = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledBy = await input.getAttribute('aria-labelledby');
        
        if (id) {
          const label = page.locator(`label[for="${id}"]`);
          const hasLabel = await label.count() > 0;
          expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
        }
      }
    });

    await test.step('Keyboard navigation', async () => {
      await page.goto('/');
      
      // Test tab navigation
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(['BUTTON', 'A', 'INPUT', 'SELECT']).toContain(focusedElement);
      
      // Test skip links
      await page.keyboard.press('Tab');
      const skipLink = page.locator('a:has-text("Skip to main content")');
      if (await skipLink.isVisible()) {
        await expect(skipLink).toBeFocused();
      }
    });

    await test.step('Color contrast and visual indicators', async () => {
      // Take screenshot for manual color contrast review
      await expect(page).toHaveScreenshot('accessibility-color-contrast.png');
      
      // Check for focus indicators
      const button = page.locator('button').first();
      await button.focus();
      await expect(page).toHaveScreenshot('focus-indicator.png');
    });
  });

  test('should support screen reader navigation', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('ARIA landmarks and roles', async () => {
      await page.goto('/');
      
      // Check for main landmark
      const main = page.locator('main, [role="main"]');
      expect(await main.count()).toBeGreaterThan(0);
      
      // Check for navigation landmark
      const nav = page.locator('nav, [role="navigation"]');
      expect(await nav.count()).toBeGreaterThan(0);
      
      // Check for proper button roles
      const buttons = await page.locator('button, [role="button"]').all();
      expect(buttons.length).toBeGreaterThan(0);
    });

    await test.step('ARIA labels and descriptions', async () => {
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      // Check step cards have proper ARIA labels
      const stepCards = await page.locator('[data-testid="step-card"]').all();
      for (const card of stepCards) {
        const ariaLabel = await card.getAttribute('aria-label');
        const ariaLabelledBy = await card.getAttribute('aria-labelledby');
        expect(ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    });
  });

  test('should handle high contrast mode', async ({ page, apiMocks }) => {
    await apiMocks.enableAllMocks();
    
    await test.step('High contrast mode compatibility', async () => {
      // Simulate high contrast mode
      await page.emulateMedia({ 
        colorScheme: 'dark',
        forcedColors: 'active'
      });
      
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      
      await expect(page).toHaveScreenshot('high-contrast-dashboard.png');
      
      await page.goto('/workflows/lineage');
      await page.selectOption('[data-testid="strategy-select"]', '1');
      await page.selectOption('[data-testid="execution-select"]', 'exec_001');
      
      await expect(page).toHaveScreenshot('high-contrast-lineage.png');
    });
  });
});
