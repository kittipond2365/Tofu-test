'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Users, ChevronRight, Plus } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState } from '@/components/shared';
import { Button } from '@/components/ui/button';

export default function HomePage() {
  const { data: clubs = [], isLoading, error } = useQuery({
    queryKey: ['clubs'],
    queryFn: apiClient.getClubs,
  });

  return (
    <ProtectedLayout>
      <Navbar />
      <main className="page-container">
        <PageHeader
          title="ก๊วนของฉัน"
          subtitle="เข้าถึงก๊วนที่เข้าร่วมได้อย่างรวดเร็ว"
          action={
            <div className="flex gap-2">
              <Link href="/clubs">
                <Button variant="secondary">ดูก๊วนทั้งหมด</Button>
              </Link>
              <Link href="/clubs/create">
                <Button>
                  <Plus className="w-4 h-4" />
                  ตั้งก๊วนใหม่
                </Button>
              </Link>
            </div>
          }
        />

        {isLoading && <p className="text-neutral-500">กำลังโหลดก๊วนของคุณ...</p>}

        {error && (
          <EmptyState
            icon={Users}
            title="โหลดข้อมูลก๊วนไม่สำเร็จ"
            description="กรุณาลองใหม่อีกครั้ง"
          />
        )}

        {!isLoading && !error && clubs.length === 0 && (
          <EmptyState
            icon={Users}
            title="ยังไม่มีก๊วนที่เข้าร่วม"
            description="เริ่มต้นด้วยการสร้างก๊วนใหม่หรือเข้าร่วมก๊วนที่มีอยู่"
            action={{ label: 'ไปหน้าก๊วนแบด', href: '/clubs' }}
          />
        )}

        {!isLoading && !error && clubs.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {clubs.map((club) => (
              <Link key={club.id} href={`/clubs/${club.id}`} className="glass-card p-5 hover:border-emerald-200/60 transition-colors group">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-neutral-900 group-hover:text-emerald-600 transition-colors">
                      {club.name}
                    </h3>
                    <p className="text-sm text-neutral-500 mt-1">สมาชิก {club.member_count}/{club.max_members}</p>
                    {club.location && <p className="text-sm text-neutral-400 mt-1">{club.location}</p>}
                  </div>
                  <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-emerald-500" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}
