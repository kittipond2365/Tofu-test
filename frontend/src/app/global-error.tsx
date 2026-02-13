'use client';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'sans-serif' }}>
          <div style={{ textAlign: 'center', maxWidth: 400, padding: 20 }}>
            <h2 style={{ fontSize: 24, marginBottom: 8 }}>เกิดข้อผิดพลาด</h2>
            <p style={{ color: '#666', marginBottom: 20 }}>{error.message || 'กรุณาลองใหม่อีกครั้ง'}</p>
            <button
              onClick={reset}
              style={{ padding: '12px 24px', background: '#10b981', color: 'white', border: 'none', borderRadius: 12, fontWeight: 600, cursor: 'pointer' }}
            >
              ลองใหม่
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
