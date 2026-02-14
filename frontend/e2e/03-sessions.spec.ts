import { test, expect } from '@playwright/test';
import { testLogin } from './setup';

test('user can create session and open registration', async ({ page }) => {
  await testLogin(page, { name: 'E2E Session Owner', line_user_id: 'e2e-session-owner' });

  const token = await page.evaluate(() => JSON.parse(localStorage.getItem('auth-store') || '{}').state?.token);

  // Create club via API first to get deterministic clubId
  const clubResp = await page.request.post('/api/v1/clubs', {
    data: {
      name: `E2E Session Club ${Date.now()}`,
      slug: `e2e-session-club-${Date.now()}`,
      description: 'club for session e2e',
      is_public: true,
    },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const club = await clubResp.json();

  await page.goto(`/clubs/${club.id}/sessions/create`);
  await page.getByLabel('ชื่อ Session').fill('Friday Badminton');
  await page.locator('input[type="datetime-local"]').first().fill('2026-02-20T18:00');
  await page.getByRole('button', { name: 'สร้าง Session' }).click();

  await expect(page).toHaveURL(/\/sessions\//);
  await page.getByRole('button', { name: 'เปิดรับสมัคร' }).click();
  await expect(page.getByText('เปิดรับสมัคร', { exact: false })).toBeVisible();

  await page.screenshot({ path: 'e2e/screens/03-session-open.png', fullPage: true });
});
