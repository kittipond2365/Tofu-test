import { Page } from '@playwright/test';

type LoginIdentity = { name?: string; line_user_id?: string };

export async function testLogin(page: Page, identity: LoginIdentity = {}) {
  const user = {
    name: identity.name ?? 'E2E Test User',
    line_user_id: identity.line_user_id,
  };

  const response = await page.request.post('/api/v1/auth/test-login', { data: user });
  if (!response.ok()) {
    throw new Error(`test-login failed: ${response.status()} ${await response.text()}`);
  }

  const { access_token, refresh_token, user: profile } = await response.json();

  await page.addInitScript(
    ({ token, refreshToken, userData }) => {
      localStorage.setItem(
        'auth-store',
        JSON.stringify({
          state: {
            token,
            refreshToken,
            user: userData,
            isAuthenticated: true,
          },
          version: 0,
        })
      );
      document.cookie = `auth-token=${token}; path=/`;
    },
    { token: access_token, refreshToken: refresh_token, userData: profile }
  );

  await page.goto('/clubs');
}
