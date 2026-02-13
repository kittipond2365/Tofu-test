'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, Mail, Lock, Trophy, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', display_name: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.full_name.trim() || !form.email.trim() || !form.password.trim()) {
      setError('กรุณากรอกข้อมูลให้ครบถ้วน');
      return;
    }
    if (form.password.length < 8) {
      setError('รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      await apiClient.register(form);
      router.push('/login');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'สมัครสมาชิกไม่สำเร็จ กรุณาลองใหม่');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-2xl shadow-emerald-500/30 mb-6">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-black text-gradient mb-2">สมัครสมาชิก</h1>
          <p className="text-neutral-500">สร้างบัญชีเพื่อเข้าร่วมก๊วนแบดมินตัน</p>
        </div>

        <div className="glass-card p-8">
          <form className="space-y-4" onSubmit={submit}>
            <Input
              label="ชื่อ-นามสกุล"
              placeholder="ชื่อจริง นามสกุล"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              leftIcon={<User className="w-5 h-5" />}
              required
            />

            <Input
              label="ชื่อที่แสดง (ไม่บังคับ)"
              placeholder="ชื่อเล่น หรือชื่อที่ใช้ในก๊วน"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              leftIcon={<User className="w-5 h-5" />}
            />

            <Input
              label="อีเมล"
              type="email"
              placeholder="your@email.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              leftIcon={<Mail className="w-5 h-5" />}
              required
            />

            <Input
              label="รหัสผ่าน"
              type="password"
              placeholder="อย่างน้อย 8 ตัวอักษร"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              leftIcon={<Lock className="w-5 h-5" />}
              required
            />

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-100 rounded-xl">
                <p className="text-sm text-rose-600 text-center">{error}</p>
              </div>
            )}

            <Button type="submit" className="w-full" isLoading={isLoading} loadingText="กำลังสมัคร...">
              สร้างบัญชี
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-neutral-500">
              มีบัญชีแล้ว?{' '}
              <Link href="/login" className="text-emerald-600 hover:text-emerald-700 font-medium">
                เข้าสู่ระบบ
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
