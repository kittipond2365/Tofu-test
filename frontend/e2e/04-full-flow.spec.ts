import { test, expect } from '@playwright/test';
import { testLogin } from './setup';

test('complete user journey', async ({ page }) => {
  // User A: create club + session
  await testLogin(page, { name: 'E2E User A', line_user_id: 'e2e-user-a' });
  const tokenA = await page.evaluate(() => JSON.parse(localStorage.getItem('auth-store') || '{}').state?.token);

  const clubRes = await page.request.post('/api/v1/clubs', {
    data: {
      name: `E2E Full Flow Club ${Date.now()}`,
      slug: `e2e-full-flow-${Date.now()}`,
      is_public: true,
      description: 'full flow',
    },
    headers: { Authorization: `Bearer ${tokenA}` },
  });
  expect(clubRes.ok()).toBeTruthy();
  const club = await clubRes.json();

  const sessionRes = await page.request.post(`/api/v1/clubs/${club.id}/sessions`, {
    data: { title: 'E2E Friday', start_time: '2026-02-20T18:00:00', max_participants: 20 },
    headers: { Authorization: `Bearer ${tokenA}` },
  });
  const session = await sessionRes.json();
  await page.request.post(`/api/v1/sessions/${session.id}/open`, {
    headers: { Authorization: `Bearer ${tokenA}` },
  });

  await page.goto(`/clubs/${club.id}/sessions/${session.id}`);
  await page.screenshot({ path: 'e2e/screens/04-user-a-session-created.png', fullPage: true });

  // User B: join + register
  await testLogin(page, { name: 'E2E User B', line_user_id: 'e2e-user-b' });
  const tokenB = await page.evaluate(() => JSON.parse(localStorage.getItem('auth-store') || '{}').state?.token);

  await page.request.post(`/api/v1/clubs/${club.id}/join`, {
    headers: { Authorization: `Bearer ${tokenB}` },
  });

  await page.goto(`/clubs/${club.id}/sessions/${session.id}`);
  await page.getByRole('button', { name: 'สมัครเข้าร่วม' }).click();
  await expect(page.getByText('คุณได้ลงทะเบียนแล้ว')).toBeVisible();
  await page.screenshot({ path: 'e2e/screens/04-user-b-registered.png', fullPage: true });
});
