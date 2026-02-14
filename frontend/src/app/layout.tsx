import './globals.css';
import { Inter } from 'next/font/google';
import QueryProvider from '@/providers/query-provider';
import SocketProvider from '@/providers/socket-provider';
import { ToastProvider } from '@/components/ui/toast';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata = {
  title: 'Tofu Badminton | จัดการก๊วนแบดมินตัน',
  description: 'แอปจัดการก๊วนแบด Session จับคู่แมทช์ บันทึกสกอร์ ดูอันดับ ครบจบในที่เดียว',
  keywords: 'badminton, แบดมินตัน, ก๊วนแบด, Session, กีฬา',
  authors: [{ name: 'Tofu Badminton' }],
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
    viewportFit: 'cover',
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#10b981' },
    { media: '(prefers-color-scheme: dark)', color: '#064e3b' },
  ],
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Tofu Badminton',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="th" className={inter.variable} suppressHydrationWarning style={{ colorScheme: 'light' }}>
      <head>
        <script dangerouslySetInnerHTML={{
          __html: `
            (function() {
              // Force light mode
              document.documentElement.style.colorScheme = 'light';
              document.documentElement.classList.remove('dark');
            })();
          `
        }} />
      </head>
      <body className="font-sans antialiased bg-white text-neutral-900">
        <QueryProvider>
          <ToastProvider>
            <SocketProvider />
            {children}
          </ToastProvider>
        </QueryProvider>
      </body>
    </html>
  );
}