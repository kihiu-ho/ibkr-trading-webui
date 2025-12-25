import { test, expect } from '@playwright/test';

test.describe('Airflow Monitor UI @smoke @airflow', () => {
  test('does not log Alpine $index errors when rendering run tasks', async ({ page }) => {
    const indexErrors: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('$index is not defined') || (text.includes('Alpine Expression Error') && text.includes('$index'))) {
        indexErrors.push(text);
      }
    });

    page.on('pageerror', error => {
      const text = error.message || String(error);
      if (text.includes('$index is not defined')) {
        indexErrors.push(text);
      }
    });

    const dagId = 'ibkr_trading_signal_workflow';
    const runId = 'manual__2025-12-22T13:45:00.819679+00:00';

    await page.route('**/api/airflow/health', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy' }),
      }),
    );

    await page.route('**/api/airflow/dags?**', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          dags: [
            {
              dag_id: dagId,
              description: 'Test DAG',
              is_paused: false,
              has_import_errors: false,
              last_run_start_date: '2025-12-22T13:00:00+00:00',
              next_dagrun: null,
            },
          ],
        }),
      }),
    );

    await page.route(/.*\/api\/airflow\/dags\/[^/]+\/dagRuns\?.*/, async route => {
      const url = route.request().url();
      const requestedDagId = decodeURIComponent(url.split('/api/airflow/dags/')[1].split('/dagRuns')[0]);

      const dagRuns =
        requestedDagId === dagId
          ? [
              {
                dag_run_id: runId,
                state: 'running',
                start_date: '2025-12-22T13:45:00.819679+00:00',
                end_date: null,
                execution_date: '2025-12-22T13:45:00.819679+00:00',
              },
            ]
          : [];

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ dag_runs: dagRuns }),
      });
    });

    await page.route(/.*\/api\/airflow\/dags\/[^/]+\/dagRuns\/[^/]+\/taskInstances.*/, route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_instances: [
            {
              task_id: 'extract_symbols',
              state: 'success',
              operator: 'PythonOperator',
              try_number: 1,
              start_date: '2025-12-22T13:45:00+00:00',
              end_date: '2025-12-22T13:45:03+00:00',
            },
            {
              task_id: 'generate_signal',
              state: 'running',
              operator: 'PythonOperator',
              try_number: 2,
              start_date: '2025-12-22T13:45:04+00:00',
              end_date: null,
            },
            {
              task_id: 'place_order',
              state: 'queued',
              operator: 'PythonOperator',
              try_number: 1,
              start_date: null,
              end_date: null,
            },
          ],
        }),
      }),
    );

    await page.route('**/api/artifacts/**', route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ artifacts: [] }),
      }),
    );

    await page.goto('/airflow');

    const viewDetails = page.locator('button[title="View Details"]').first();
    await expect(viewDetails).toBeVisible();
    await viewDetails.click();

    await expect(page.getByRole('heading', { name: 'Workflow Run Details' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Task Execution Flow' })).toBeVisible();

    await expect(page.getByRole('heading', { name: 'extract_symbols' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'generate_signal' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'place_order' })).toBeVisible();

    await page.waitForTimeout(250);
    expect(indexErrors).toEqual([]);
  });
});
