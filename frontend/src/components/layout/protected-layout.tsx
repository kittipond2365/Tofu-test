"use client";
import { useEffect, useState } from 'react'; 
import { useRouter } from 'next/navigation'; 
import { useAuthStore } from '@/stores/authStore';

export function ProtectedLayout({ children }: { children: React.ReactNode }) { 
  const router = useRouter(); 
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const token = useAuthStore((s) => s.token);
  const [isHydrated, setIsHydrated] = useState(false);
  
  // Wait for store hydration
  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => {
      setIsHydrated(true);
    });
    // If already hydrated
    if (useAuthStore.persist.hasHydrated()) {
      setIsHydrated(true);
    }
    return unsub;
  }, []);
  
  useEffect(() => { 
    if (isHydrated && !isAuthenticated) {
      router.replace('/login'); 
    } 
  }, [isHydrated, isAuthenticated, router]); 
  
  // Show loading state while hydrating
  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) return null; 
  
  return <>{children}</>; 
}
