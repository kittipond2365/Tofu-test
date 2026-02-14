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

test('admin/organizer can delete session', async ({ page }) => {
  await testLogin(page, { name: 'Session Admin For Delete', line_user_id: 'e2e-session-delete-admin' });

  const token = await page.evaluate(() => JSON.parse(localStorage.getItem('auth-store') || '{}').state?.token);

  // Create club via API first
  const clubResp = await page.request.post('/api/v1/clubs', {
    data: {
      name: `Delete Session Club ${Date.now()}`,
      slug: `e2e-delete-session-club-${Date.now()}`,
      description: 'club for delete session e2e',
      is_public: true,
    },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const club = await clubResp.json();

  // Create session via API
  const sessionResp = await page.request.post(`/api/v1/clubs/${club.id}/sessions`, {
    data: {
      title: 'Session To Delete',
      start_time: '2026-02-20T18:00:00',
      max_participants: 4,
    },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const session = await sessionResp.json();

  // Navigate to session detail page
  await page.goto(`/clubs/${club.id}/sessions/${session.id}`);

  // Verify delete button is visible for admin
  const deleteButton = page.getByRole('button', { name: 'ลบ Session' });
  await expect(deleteButton).toBeVisible();

  // Click delete button
  await deleteButton.click();

  // Confirm deletion in dialog
  await page.getByRole('button', { name: 'ลบ Session' }).filter({ hasText: 'ลบ Session' }).nth(1).click();

  // Should redirect to sessions list
  await expect(page).toHaveURL(`/clubs/${club.id}/sessions`);

  await page.screenshot({ path: 'e2e/screens/03-session-deleted.png', fullPage: true });
});
