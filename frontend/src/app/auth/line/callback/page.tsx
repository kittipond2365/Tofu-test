"use client";

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Trophy, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';

function LineCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const loginStore = useAuthStore((s) => s.login);

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const errorCode = searchParams.get('error');
      const errorDesc = searchParams.get('error_description');

      // Check for LINE errors
      if (errorCode) {
        setError(errorDesc || 'การเข้าสู่ระบบด้วย LINE ถูกยกเลิก');
        setIsLoading(false);
        return;
      }

      // Verify state
      const savedState = localStorage.getItem('line_oauth_state');
      if (!code || !state || state !== savedState) {
        setError('Invalid state parameter. Please try again.');
        setIsLoading(false);
        return;
      }

      try {
        // Call backend to exchange code for tokens
        const response = await fetch(
          `${apiClient.baseURL}/auth/line/callback?code=${code}&state=${state}`
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || 'Login failed');
        }

        const tokenData = await response.json();

        // Get user info
        const me = await apiClient.getMeWithToken(tokenData.access_token);

        // Store auth
        loginStore(tokenData.access_token, tokenData.refresh_token, me);

        // Clear state
        localStorage.removeItem('line_oauth_state');

        // Redirect to clubs
        router.push('/clubs');
      } catch (err: any) {
        setError(err.message || 'เข้าสู่ระบบไม่สำเร็จ กรุณาลองใหม่อีกครั้ง');
        setIsLoading(false);
      }
    };

    handleCallback();
  }, [searchParams, router, loginStore]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="w-full max-w-md">
        {/* Logo & Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-blue-500/25">
            <Trophy className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gradient mb-2">
            เข้าสู่ระบบด้วย LINE
          </h1>
        </div>

        {/* Status Card */}
        <div className="card-modern p-8 text-center">
          {isLoading && !error && (
            <>
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
              <p className="text-gray-600">กำลังดำเนินการเข้าสู่ระบบ...</p>
              <p className="text-sm text-gray-400 mt-2">กรุณารอสักครู่</p>
            </>
          )}

          {error && (
            <>
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                เข้าสู่ระบบไม่สำเร็จ
              </h2>
              <p className="text-gray-600 mb-6">{error}</p>
              <div className="space-y-3">
                <button
                  onClick={() => router.push('/login')}
                  className="w-full btn-primary"
                >
                  กลับไปหน้าเข้าสู่ระบบ
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="w-full btn-secondary"
                >
                  ลองใหม่อีกครั้ง
                </button>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-gray-400 mt-8">
          Badminton Club Management System © 2026
        </p>
      </div>
    </div>
  );
}

export default function LineCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-50 via-white to-slate-100">
        <div className="w-full max-w-md text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">กำลังโหลด...</p>
        </div>
      </div>
    }>
      <LineCallbackContent />
    </Suspense>
  );
}
