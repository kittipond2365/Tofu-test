'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Users, Search, Hash, ChevronRight, MapPin } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState } from '@/components/shared';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import { cn } from '@/lib/utils';

export default function JoinClubPage() {
  const [slug, setSlug] = useState('');
  const router = useRouter();
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();
  const [isJoining, setIsJoining] = useState<string | null>(null);

  const { data: clubs } = useQuery({
    queryKey: ['clubs'],
    queryFn: apiClient.getClubs,
  });

  const join = async (clubId: string, clubName: string) => {
    setIsJoining(clubId);
    try {
      await apiClient.joinClub(clubId);
      await queryClient.invalidateQueries({ queryKey: ['clubs'] });
      success('เข้าร่วมสำเร็จ! 🎉', `คุณเข้าร่วมก๊วน "${clubName}" แล้ว`);
      router.push(`/clubs/${clubId}`);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'ไม่สามารถเข้าร่วมได้';
      showError('เข้าร่วมไม่สำเร็จ', detail);
      setIsJoining(null);
    }
  };

  const joinBySlug = async () => {
    if (!slug.trim()) {
      showError('กรุณากรอกข้อมูล', 'กรุณาใส่รหัสก๊วน');
      return;
    }
    const club = clubs?.find((c) => c.slug === slug.trim());
    if (!club) {
      showError('ไม่พบก๊วน', `ไม่พบก๊วนที่มีรหัส "${slug}"`);
      return;
    }
    await join(club.id, club.name);
  };

  return (
    <ProtectedLayout>
      <Navbar />
      <main className="page-container">
        <PageHeader
          title="เข้าร่วมก๊วน"
          subtitle="หาก๊วนแบดแล้วเข้าร่วมได้เลย"
          breadcrumbs={[
            { label: 'ก๊วนแบด', href: '/clubs' },
            { label: 'เข้าร่วมก๊วน' },
          ]}
        />

        <div className="max-w-lg mx-auto">
          {/* Join by slug */}
          <div className="glass-card p-6 mb-6">
            <h2 className="text-lg font-bold text-neutral-900 mb-4">มีรหัสก๊วน?</h2>
            <div className="flex gap-2">
              <Input
                placeholder="ใส่รหัสก๊วน (slug)"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                leftIcon={<Hash className="w-5 h-5" />}
                className="flex-1"
              />
              <Button onClick={joinBySlug} disabled={isJoining !== null}>
                เข้าร่วม
              </Button>
            </div>
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}
