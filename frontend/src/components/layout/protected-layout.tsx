"use client";
import { useEffect } from 'react'; import { useRouter } from 'next/navigation'; import { useAuthStore } from '@/stores/authStore';
export function ProtectedLayout({ children }: { children: React.ReactNode }) { const router = useRouter(); const isAuthenticated = useAuthStore((s) => s.isAuthenticated); useEffect(() => { if (!isAuthenticated) router.replace('/login'); }, [isAuthenticated, router]); if (!isAuthenticated) return null; return <>{children}</>; }
