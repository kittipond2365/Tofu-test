'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { MapPin, Users, FileText, Plus } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader } from '@/components/shared';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';

export default function CreateSessionPage({ params }: { params: { clubId: string } }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    location: '',
    start_time: '',
    end_time: '',
    max_participants: 20,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();

  const { data: club } = useQuery({
    queryKey: ['club', params.clubId],
    queryFn: () => apiClient.getClub(params.clubId),
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!form.title.trim() || !form.start_time) {
      showError('กรุณากรอกข้อมูล', 'กรุณากรอกชื่อ Session และเวลาเริ่ม');
      return;
    }

    if (form.end_time && new Date(form.end_time) <= new Date(form.start_time)) {
      showError('เวลาไม่ถูกต้อง', 'เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        start_time: new Date(form.start_time).toISOString(),
        end_time: form.end_time ? new Date(form.end_time).toISOString() : undefined,
      };
      const s = await apiClient.createSession(params.clubId, payload);
      await queryClient.invalidateQueries({ queryKey: ['sessions', params.clubId] });
      success('สร้าง Session สำเร็จ! 🏸', `"${s.title}" พร้อมเปิดรับคนแล้ว`);
      router.push(`/clubs/${params.clubId}/sessions/${s.id}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'ไม่สามารถสร้าง Session ได้ กรุณาลองใหม่';
      showError('สร้าง Session ไม่สำเร็จ', detail);
      setIsSubmitting(false);
    }
  };

  return (
    <ProtectedLayout>
      <Navbar />
      <main className="page-container">
        <PageHeader
          title="สร้าง Session ใหม่"
          subtitle={club?.name ? `สำหรับก๊วน ${club.name}` : 'เปิด Session ให้สมาชิกมาตีแบด'}
          breadcrumbs={[
            { label: 'ก๊วนแบด', href: '/clubs' },
            { label: club?.name || '', href: `/clubs/${params.clubId}` },
            { label: 'สร้าง Session' },
          ]}
        />

        <div className="max-w-xl mx-auto">
          <div className="glass-card p-6 sm:p-8">
            <form onSubmit={submit} className="space-y-5">
              <Input
                label="ชื่อ Session"
                placeholder="เช่น ตีแบดวันเสาร์เช้า"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                leftIcon={<FileText className="w-5 h-5" />}
                required
              />

              <Textarea
                label="รายละเอียด"
                placeholder="เช่น ตีแบดสนุกๆ ทุกระดับ มาได้เลย"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={3}
              />

              <Input
                label="สนาม / สถานที่ (ไม่บังคับ)"
                placeholder="เช่น สนามแบด ABC ลาดพร้าว"
                value={form.location}
                onChange={(e) => setForm({ ...form, location: e.target.value })}
                leftIcon={<MapPin className="w-5 h-5" />}
              />

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="วัน-เวลาเริ่ม"
                  type="datetime-local"
                  value={form.start_time}
                  onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                  required
                />
                <Input
                  label="วัน-เวลาสิ้นสุด (ไม่บังคับ)"
                  type="datetime-local"
                  value={form.end_time}
                  onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                />
              </div>

              <Input
                label="จำนวนคนสูงสุด"
                type="number"
                value={form.max_participants}
                onChange={(e) => setForm({ ...form, max_participants: parseInt(e.target.value) || 4 })}
                leftIcon={<Users className="w-5 h-5" />}
                min={2}
                max={100}
              />

              <div className="flex gap-3 pt-2">
                <Button type="submit" isLoading={isSubmitting} loadingText="กำลังสร้าง..." className="flex-1">
                  <Plus className="w-4 h-4" />
                  สร้าง Session
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
