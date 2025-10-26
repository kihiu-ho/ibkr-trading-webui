import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class StrategyFormPage extends BasePage {
  constructor(page: Page, strategyId?: string) {
    const url = strategyId ? `/strategies/${strategyId}/edit` : '/strategies/new';
    super(page, url);
  }

  // Form elements
  get strategyNameInput() {
    return this.page.locator('input[name="name"]');
  }

  get workflowSelect() {
    return this.page.locator('select[name="workflow_id"]');
  }

  get activeToggle() {
    return this.page.locator('input[name="active"]');
  }

  get symbolsSelect() {
    return this.page.locator('[data-testid="symbols-select"]');
  }

  get indicatorsSelect() {
    return this.page.locator('[data-testid="indicators-select"]');
  }

  // Parameter inputs
  get accountSizeInput() {
    return this.page.locator('input[name="account_size"]');
  }

  get riskPerTradeInput() {
    return this.page.locator('input[name="risk_per_trade"]');
  }

  get minRCoefficientInput() {
    return this.page.locator('input[name="min_r_coefficient"]');
  }

  get minProfitMarginInput() {
    return this.page.locator('input[name="min_profit_margin"]');
  }

  get delayBetweenSymbolsInput() {
    return this.page.locator('input[name="delay_between_symbols"]');
  }

  get temperatureInput() {
    return this.page.locator('input[name="temperature"]');
  }

  get maxTokensInput() {
    return this.page.locator('input[name="max_tokens"]');
  }

  // Form actions
  get saveButton() {
    return this.page.locator('button[type="submit"]');
  }

  get cancelButton() {
    return this.page.locator('button:has-text("Cancel")');
  }

  get validateButton() {
    return this.page.locator('[data-testid="validate-params-btn"]');
  }

  get resetButton() {
    return this.page.locator('[data-testid="reset-form-btn"]');
  }

  // Validation
  get validationResults() {
    return this.page.locator('[data-testid="validation-results"]');
  }

  get validationErrors() {
    return this.page.locator('[data-testid="validation-errors"]');
  }

  get validationWarnings() {
    return this.page.locator('[data-testid="validation-warnings"]');
  }

  // Methods
  async fillStrategyForm(strategyData: {
    name: string;
    workflow_id?: string;
    active?: boolean;
    symbols?: string[];
    indicators?: string[];
    account_size?: number;
    risk_per_trade?: number;
    min_r_coefficient?: number;
    min_profit_margin?: number;
    delay_between_symbols?: number;
    temperature?: number;
    max_tokens?: number;
  }) {
    await this.strategyNameInput.fill(strategyData.name);

    if (strategyData.workflow_id) {
      await this.workflowSelect.selectOption(strategyData.workflow_id);
    }

    if (strategyData.active !== undefined) {
      if (strategyData.active) {
        await this.activeToggle.check();
      } else {
        await this.activeToggle.uncheck();
      }
    }

    if (strategyData.symbols) {
      for (const symbol of strategyData.symbols) {
        await this.symbolsSelect.selectOption(symbol);
      }
    }

    if (strategyData.indicators) {
      for (const indicator of strategyData.indicators) {
        await this.indicatorsSelect.selectOption(indicator);
      }
    }

    // Fill parameter inputs
    if (strategyData.account_size) {
      await this.accountSizeInput.fill(strategyData.account_size.toString());
    }

    if (strategyData.risk_per_trade) {
      await this.riskPerTradeInput.fill(strategyData.risk_per_trade.toString());
    }

    if (strategyData.min_r_coefficient) {
      await this.minRCoefficientInput.fill(strategyData.min_r_coefficient.toString());
    }

    if (strategyData.min_profit_margin) {
      await this.minProfitMarginInput.fill(strategyData.min_profit_margin.toString());
    }

    if (strategyData.delay_between_symbols) {
      await this.delayBetweenSymbolsInput.fill(strategyData.delay_between_symbols.toString());
    }

    if (strategyData.temperature) {
      await this.temperatureInput.fill(strategyData.temperature.toString());
    }

    if (strategyData.max_tokens) {
      await this.maxTokensInput.fill(strategyData.max_tokens.toString());
    }
  }

  async validateParameters() {
    await this.validateButton.click();
    await this.validationResults.waitFor({ state: 'visible' });
  }

  async saveStrategy() {
    await this.saveButton.click();
    await this.waitForApiResponse('/api/strategies');
    await this.waitForToast('Strategy saved successfully');
  }

  async cancelForm() {
    await this.cancelButton.click();
    await this.page.waitForURL('**/strategies');
  }

  async resetForm() {
    await this.resetButton.click();
  }

  async getValidationResults() {
    await this.validationResults.waitFor({ state: 'visible' });
    
    const errors = await this.validationErrors.allTextContents();
    const warnings = await this.validationWarnings.allTextContents();
    
    return { errors, warnings };
  }

  // Assertions
  async assertFormLoaded() {
    await this.assertElementVisible('input[name="name"]');
    await this.assertElementVisible('button[type="submit"]');
  }

  async assertValidationPassed() {
    await this.assertElementVisible('[data-testid="validation-results"]');
    await this.assertElementHidden('[data-testid="validation-errors"]');
  }

  async assertValidationFailed(expectedErrors: string[]) {
    await this.assertElementVisible('[data-testid="validation-errors"]');
    
    for (const error of expectedErrors) {
      await this.assertElementText('[data-testid="validation-errors"]', error);
    }
  }
}
