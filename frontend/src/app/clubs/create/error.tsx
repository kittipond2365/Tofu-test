'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw, ArrowLeft } from 'lucide-react';

export default function CreateClubError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Club creation error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        <h2 className="text-xl font-bold text-neutral-900 mb-2">สร้างก๊วนไม่สำเร็จ</h2>
        <p className="text-neutral-500 mb-6">
          {error.message || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'}
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl font-semibold hover:bg-emerald-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            ลองใหม่
          </button>
          <Link
            href="/clubs"
            className="inline-flex items-center gap-2 px-6 py-3 bg-neutral-100 text-neutral-700 rounded-xl font-semibold hover:bg-neutral-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            กลับ
          </Link>
        </div>
      </div>
    </div>
  );
}
