'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Plus, Users, MapPin, Hash, FileText, Globe, Lock } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader } from '@/components/shared';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';

export default function CreateClubPage() {
  const [form, setForm] = useState({
    name: '',
    slug: '',
    description: '',
    location: '',
    max_members: 100,
    is_public: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();

  // Auto-generate slug from name (English only)
  const handleNameChange = (name: string) => {
    const slug = name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 50);
    setForm({ ...form, name, slug });
  };

  // Validate slug format
  const isValidSlug = (slug: string): boolean => {
    return /^[a-z0-9-]+$/.test(slug) && slug.length >= 3 && slug.length <= 50;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.name.trim()) {
      showError('กรุณากรอกข้อมูล', 'ชื่อก๊วนห้ามว่าง');
      return;
    }
    if (!form.slug.trim()) {
      showError('กรุณากรอกข้อมูล', 'รหัสก๊วนห้ามว่าง');
      return;
    }
    if (!isValidSlug(form.slug)) {
      showError(
        'รหัสก๊วนไม่ถูกต้อง',
        'ใช้ได้เฉพาะตัวอักษร a-z, ตัวเลข 0-9 และขีด (-) ความยาว 3-50 ตัวอักษร'
      );
      return;
    }

    setIsSubmitting(true);
    try {
      const c = await apiClient.createClub(form);
      if (!c || !c.id) {
        throw new Error('ได้รับข้อมูลไม่ครบจากเซิร์ฟเวอร์');
      }
      // Invalidate clubs cache so list refreshes
      await queryClient.invalidateQueries({ queryKey: ['clubs'] });
      success('สร้างก๊วนสำเร็จ! 🎉', `ก๊วน "${c.name || form.name}" พร้อมใช้งานแล้ว`);
      router.push(`/clubs/${c.id}`);
    } catch (err: any) {
      console.error('Club creation error:', err);
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        'ไม่สามารถสร้างก๊วนได้ กรุณาลองใหม่';
      showError('สร้างก๊วนไม่สำเร็จ', typeof detail === 'string' ? detail : JSON.stringify(detail));
      setIsSubmitting(false);
    }
  };

  return (
    <ProtectedLayout>
      <Navbar />
      <main className="page-container">
        <PageHeader
          title="สร้างก๊วนใหม่"
          subtitle="ตั้งก๊วนแบดของคุณ แล้วชวนเพื่อนมาตี"
          breadcrumbs={[
            { label: 'ก๊วนแบด', href: '/clubs' },
            { label: 'สร้างก๊วนใหม่' },
          ]}
        />

        <div className="max-w-xl mx-auto">
          <div className="glass-card p-6 sm:p-8">
            <form onSubmit={submit} className="space-y-5">
              <Input
                label="ชื่อก๊วน"
                placeholder="เช่น ก๊วนแบดทอฟู่"
                value={form.name}
                onChange={(e) => handleNameChange(e.target.value)}
                leftIcon={<Users className="w-5 h-5" />}
                required
                maxLength={100}
              />

              <Input
                label="รหัสก๊วน (slug)"
                placeholder="เช่น tofu-badminton"
                value={form.slug}
                onChange={(e) =>
                  setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '') })
                }
                leftIcon={<Hash className="w-5 h-5" />}
                helpText="ใช้ตัวอักษรภาษาอังกฤษพิมพ์เล็ก a-z, ตัวเลข 0-9 และขีด (-) เท่านั้น ความยาว 3-50 ตัวอักษร"
                required
                minLength={3}
                maxLength={50}
              />

              <Textarea
                label="คำอธิบาย"
                placeholder="บอกเล่าเกี่ยวกับก๊วนของคุณ เช่น วันที่ตีประจำ ระดับฝีมือ"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
              />

              <Input
                label="สถานที่ / สนามประจำ"
                placeholder="เช่น สนามแบด ABC ลาดพร้าว"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                leftIcon={<MapPin className="w-5 h-5" />}
              />

              <Input
                label="จำนวนสมาชิกสูงสุด"
                type="number"
                value={form.max_members}
                onChange={(e) => setForm({ ...form, max_members: parseInt(e.target.value) || 10 })}
                min={2}
                max={1000}
              />

              <div className="flex items-center gap-3 p-4 bg-neutral-50 rounded-xl">
                <button
                  type="button"
                  onClick={() => setForm({ ...form, is_public: !form.is_public })}
                  className={`relative w-12 h-7 rounded-full transition-colors ${
                    form.is_public ? 'bg-emerald-500' : 'bg-neutral-300'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
                      form.is_public ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
                <div className="flex items-center gap-2">
                  {form.is_public ? (
                    <Globe className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Lock className="w-4 h-4 text-neutral-500" />
                  )}
                  <div>
                    <p className="font-medium text-neutral-900">
                      {form.is_public ? 'เปิดรับสมาชิก' : 'ก๊วนปิด (เชิญเท่านั้น)'}
                    </p>
                    <p className="text-xs text-neutral-500">
                      {form.is_public
                        ? 'ใครก็เข้าร่วมได้'
                        : 'ต้องได้รับเชิญจากแอดมินเท่านั้น'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button type="submit" isLoading={isSubmitting} loadingText="กำลังสร้าง..." className="flex-1">
                  <Plus className="w-4 h-4" />
                  สร้างก๊วน
                </Button>
                <Button type="button" variant="secondary" onClick={() => router.back()}>
                  ยกเลิก
                </Button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}
