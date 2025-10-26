import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class OrdersPage extends BasePage {
  constructor(page: Page) {
    super(page, '/orders');
  }

  // Page elements
  get ordersTable() {
    return this.page.locator('[data-testid="orders-table"]');
  }

  get orderItems() {
    return this.page.locator('[data-testid="order-item"]');
  }

  get refreshButton() {
    return this.page.locator('[data-testid="refresh-orders"]');
  }

  get filterDropdown() {
    return this.page.locator('[data-testid="filter-orders"]');
  }

  // Order details
  getOrderById(orderId: string) {
    return this.page.locator(`[data-testid="order-item"][data-order-id="${orderId}"]`);
  }

  getOrderStatus(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-status"]');
  }

  getOrderSymbol(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-symbol"]');
  }

  getOrderSide(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-side"]');
  }

  getOrderQuantity(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-quantity"]');
  }

  getOrderPrice(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-price"]');
  }

  getOrderTimestamp(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="order-timestamp"]');
  }

  // Order actions
  getCancelButton(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="cancel-order-btn"]');
  }

  getModifyButton(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="modify-order-btn"]');
  }

  getViewDetailsButton(orderId: string) {
    return this.getOrderById(orderId).locator('[data-testid="view-details-btn"]');
  }

  // Methods
  async waitForOrdersLoad() {
    await this.waitForPageLoad();
    await this.ordersTable.waitFor({ state: 'visible' });
  }

  async refreshOrders() {
    await this.refreshButton.click();
    await this.waitForApiResponse('/api/orders');
  }

  async filterOrders(filter: 'all' | 'pending' | 'filled' | 'cancelled') {
    await this.filterDropdown.selectOption(filter);
    await this.waitForApiResponse('/api/orders');
  }

  async cancelOrder(orderId: string) {
    await this.getCancelButton(orderId).click();
    await this.waitForApiResponse(`/api/orders/${orderId}/cancel`);
    await this.waitForToast('Order cancelled successfully');
  }

  async getOrderData(orderId: string) {
    const order = this.getOrderById(orderId);
    await order.waitFor({ state: 'visible' });
    
    return {
      id: orderId,
      status: await this.getOrderStatus(orderId).textContent(),
      symbol: await this.getOrderSymbol(orderId).textContent(),
      side: await this.getOrderSide(orderId).textContent(),
      quantity: await this.getOrderQuantity(orderId).textContent(),
      price: await this.getOrderPrice(orderId).textContent(),
      timestamp: await this.getOrderTimestamp(orderId).textContent()
    };
  }

  // Assertions
  async assertOrderExists(orderId: string) {
    await this.assertElementVisible(`[data-testid="order-item"][data-order-id="${orderId}"]`);
  }

  async assertOrderStatus(orderId: string, expectedStatus: string) {
    await expect(this.getOrderStatus(orderId)).toContainText(expectedStatus);
  }
}
