import { test, expect } from '@playwright/test';
import { testLogin } from './setup';

test('user can login via test endpoint', async ({ page }) => {
  await page.goto('/login');
  await page.screenshot({ path: 'e2e/screens/01-login.png' });

  await testLogin(page);

  await expect(page).toHaveURL(/\/clubs/);
  await expect(page.getByText('ก๊วน', { exact: false })).toBeVisible();
});
