import { test, expect } from '@playwright/test';
import { testLogin } from './setup';

test('user can create club', async ({ page }) => {
  await testLogin(page, { name: 'E2E Club Owner', line_user_id: 'e2e-owner' });

  await page.goto('/clubs/create');
  await page.getByLabel('ชื่อก๊วน').fill('E2E Test Club');
  await page.getByLabel('รหัสก๊วน (slug)').fill(`e2e-test-club-${Date.now()}`);
  await page.getByRole('button', { name: 'สร้างก๊วน' }).click();

  await expect(page).toHaveURL(/\/clubs\//);
  await page.screenshot({ path: 'e2e/screens/02-club-created.png', fullPage: true });
});
