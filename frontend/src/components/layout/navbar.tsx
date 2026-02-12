'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useState } from 'react';
import {
  Trophy,
  Users,
  Calendar,
  User,
  LogOut,
  Menu,
  X,
  ChevronRight,
  BarChart3,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

const navItems = [
  { href: '/clubs', label: 'ชมรม', icon: Users, description: 'ดูชมรมทั้งหมด' },
  { href: '/profile', label: 'โปรไฟล์', icon: User, description: 'ข้อมูลส่วนตัว' },
];

export function Navbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const isActive = (href: string) => {
    if (href === '/clubs') {
      return pathname.startsWith('/clubs');
    }
    return pathname === href;
  };

  return (
    <>
      <nav className="sticky top-0 z-50 glass-card border-b border-white/50 rounded-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/clubs" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25 group-hover:shadow-emerald-500/40 group-hover:scale-105 transition-all duration-300">
                <Trophy className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gradient hidden sm:block">
                Tofu Badminton
              </span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200',
                    isActive(item.href)
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                  )}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              ))}
            </div>

            {/* User & Logout - Desktop */}
            <div className="hidden md:flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-neutral-100 rounded-full">
                <div className="w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-neutral-700 max-w-[120px] truncate">
                  {user?.display_name || user?.full_name || 'User'}
                </span>
              </div>

              <button
                onClick={handleLogout}
                className="p-2 text-neutral-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                title="ออกจากระบบ"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 text-neutral-600 hover:bg-neutral-100 rounded-xl transition-colors"
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-neutral-100 animate-fade-in">
            <div className="px-4 py-3 space-y-1">
              {/* User Info */}
              <div className="flex items-center gap-3 px-3 py-3 bg-neutral-50 rounded-xl mb-2">
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900">
                    {user?.display_name || user?.full_name || 'User'}
                  </p>
                  <p className="text-xs text-neutral-500">{user?.email || ''}</p>
                </div>
              </div>

              {/* Nav Items */}
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-3 rounded-xl transition-colors',
                    isActive(item.href)
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-neutral-600 hover:bg-neutral-50'
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  <div className="flex-1">
                    <p className="font-medium">{item.label}</p>
                    <p className="text-xs text-neutral-400">{item.description}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-neutral-300" />
                </Link>
              ))}

              {/* Logout */}
              <button
                onClick={() => {
                  setIsMobileMenuOpen(false);
                  handleLogout();
                }}
                className="w-full flex items-center gap-3 px-3 py-3 text-rose-600 hover:bg-rose-50 rounded-xl transition-colors mt-2"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-medium">ออกจากระบบ</span>
              </button>
            </div>
          </div>
        )}
      </nav>
    </>
  );
}

// Bottom Navigation for Mobile
export function BottomNav() {
  const pathname = usePathname();
  const { user } = useAuthStore();

  const isActive = (href: string) => {
    if (href === '/clubs') {
      return pathname.startsWith('/clubs');
    }
    return pathname === href;
  };

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 glass-card border-t border-white/50 rounded-none pb-safe">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-col items-center justify-center gap-1 flex-1 h-full transition-colors',
              isActive(item.href)
                ? 'text-emerald-600'
                : 'text-neutral-400 hover:text-neutral-600'
            )}
          >
            <item.icon className="w-5 h-5" />
            <span className="text-xs font-medium">{item.label}</span>
          </Link>
        ))}
      </div>
    </nav>
  );
}