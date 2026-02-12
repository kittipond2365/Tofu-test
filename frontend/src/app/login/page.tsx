'use client';

import { useState } from 'react';
import { Trophy, Users, Calendar, BarChart3, MessageCircle, Loader2, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';

const features = [
  {
    icon: Trophy,
    title: 'จัดการแข่งขัน',
    description: 'สร้างและจัดการแมทช์แบดมินตันได้ง่าย',
    color: 'from-emerald-500 to-teal-500',
  },
  {
    icon: Users,
    title: 'ชมรม',
    description: 'เข้าร่วมและจัดการชมรมของคุณ',
    color: 'from-blue-500 to-indigo-500',
  },
  {
    icon: Calendar,
    title: 'นัดหมาย',
    description: 'จองเวลาและจัดตารางการแข่งขัน',
    color: 'from-violet-500 to-purple-500',
  },
  {
    icon: BarChart3,
    title: 'สถิติ',
    description: 'ติดตามผลงานและอันดับของคุณ',
    color: 'from-amber-500 to-orange-500',
  },
];

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLineLogin = async () => {
    try {
      setIsLoading(true);
      setError('');

      const response = await fetch(`${apiClient.baseURL}/auth/line/login`);
      const data = await response.json();

      if (data.login_url) {
        localStorage.setItem('line_oauth_state', data.state);
        window.location.href = data.login_url;
      } else {
        setError('ไม่สามารถเชื่อมต่อกับ LINE ได้');
      }
    } catch (err) {
      setError('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-[100vw] h-[100vw] bg-emerald-100/50 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/2 -left-1/2 w-[100vw] h-[100vw] bg-teal-100/50 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo & Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-2xl shadow-emerald-500/30 mb-6 animate-float">
            <Trophy className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl font-black text-gradient mb-3">
            Tofu Badminton
          </h1>
          <p className="text-neutral-500 text-lg">
            จัดการชมรมแบดมินตันอย่างมืออาชีพ
          </p>
        </div>

        {/* Login Card */}
        <div className="glass-card p-8">
          <h2 className="text-xl font-bold text-center text-neutral-900 mb-6">
            เข้าสู่ระบบ
          </h2>

          {error && (
            <div className="mb-6 p-4 bg-rose-50 border border-rose-100 rounded-xl">
              <p className="text-sm text-rose-600 text-center">{error}</p>
            </div>
          )}

          {/* LINE Login Button */}
          <button
            onClick={handleLineLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-6 py-4 min-h-[56px] bg-[#06C755] hover:bg-[#05b34d] text-white font-semibold rounded-xl shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:-translate-y-0.5 active:translate-y-0 active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                กำลังเชื่อมต่อ...
              </>
            ) : (
              <>
                <svg className="w-7 h-7" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.63-.63.346 0 .628.285.628.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.17 1.021c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
                </svg>
                เข้าสู่ระบบด้วย LINE
              </>
            )}
          </button>

          <div className="mt-6 flex items-center gap-4">
            <div className="flex-1 h-px bg-neutral-200" />
            <span className="text-sm text-neutral-400">หรือ</span>
            <div className="flex-1 h-px bg-neutral-200" />
          </div>

          {/* Demo Login - for testing */}
          <button
            onClick={() => window.location.href = '/register'}
            className="w-full mt-4 btn-secondary"
          >
            สมัครสมาชิกใหม่
          </button>

          <p className="mt-6 text-center text-sm text-neutral-500">
            เข้าสู่ระบบเพื่อจัดการชมรมและเข้าร่วมกิจกรรม
          </p>
        </div>

        {/* Features Grid */}
        <div className="mt-8 grid grid-cols-2 gap-3">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="glass-card p-4 text-center hover:-translate-y-1 transition-transform duration-300"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center mx-auto mb-2 bg-gradient-to-br',
                  feature.color
                )}
              >
                <feature.icon className="w-5 h-5 text-white" />
              </div>
              <p className="text-sm font-semibold text-neutral-900">{feature.title}</p>
              <p className="text-xs text-neutral-500 mt-0.5 hidden sm:block">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-neutral-400 mt-8">
          Tofu Badminton Club Management System © 2026
        </p>
      </div>
    </div>
  );
}