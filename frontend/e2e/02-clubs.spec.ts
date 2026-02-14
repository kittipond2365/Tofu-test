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

test('club owner can delete their club', async ({ page }) => {
  // Login as owner
  await testLogin(page, { name: 'Club Owner For Delete', line_user_id: 'e2e-delete-owner' });

  // Create a club first
  await page.goto('/clubs/create');
  const uniqueSlug = `e2e-delete-club-${Date.now()}`;
  await page.getByLabel('ชื่อก๊วน').fill('Club To Delete');
  await page.getByLabel('รหัสก๊วน (slug)').fill(uniqueSlug);
  await page.getByRole('button', { name: 'สร้างก๊วน' }).click();

  // Wait for club detail page
  await expect(page).toHaveURL(/\/clubs\//);

  // Verify delete button is visible for owner
  const deleteButton = page.getByRole('button', { name: 'ลบก๊วน' });
  await expect(deleteButton).toBeVisible();

  // Click delete button
  await deleteButton.click();

  // Confirm deletion in dialog
  await page.getByRole('button', { name: 'ลบก๊วน' }).filter({ hasText: 'ลบก๊วน' }).nth(1).click();

  // Should redirect to clubs list
  await expect(page).toHaveURL('/clubs');

  await page.screenshot({ path: 'e2e/screens/02-club-deleted.png', fullPage: true });
});
