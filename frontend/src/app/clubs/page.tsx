'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Plus, Users, Search, Grid3X3, List, Filter } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { ClubCard } from '@/components/features/ClubCard';
import { PageHeader, EmptyState } from '@/components/shared';
import { ClubCardSkeleton } from '@/components/shared';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import type { ClubResponse } from '@/lib/types';

type SortOption = 'newest' | 'members' | 'alphabetical';

export default function ClubsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const { data: clubs = [], isLoading, error } = useQuery({
    queryKey: ['clubs'],
    queryFn: async () => {
      const response = await apiClient.getClubs() as unknown;
      if (Array.isArray(response)) return response;
      if (response && typeof response === 'object' && 'clubs' in response && Array.isArray((response as { clubs: ClubResponse[] }).clubs)) {
        return (response as { clubs: ClubResponse[] }).clubs;
      }
      return [];
    },
  });

  // Filter and sort clubs
  const filteredClubs = useMemo(() => {
    if (!clubs) return [];

    let result = [...clubs];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (club) =>
          club.name.toLowerCase().includes(term) ||
          club.slug.toLowerCase().includes(term) ||
          (club.description?.toLowerCase().includes(term) ?? false) ||
          (club.location?.toLowerCase().includes(term) ?? false)
      );
    }

    // Sort
    switch (sortBy) {
      case 'newest':
        result.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        break;
      case 'members':
        result.sort((a, b) => b.member_count - a.member_count);
        break;
      case 'alphabetical':
        result.sort((a, b) => a.name.localeCompare(b.name, 'th'));
        break;
    }

    return result;
  }, [clubs, searchTerm, sortBy]);

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        {/* Header */}
        <PageHeader
          title="ก๊วนแบดมินตัน"
          subtitle="จัดการก๊วนแบดและ Session กับเพื่อนๆ"
          breadcrumbs={[{ label: 'ก๊วนแบด' }]}
          action={
            <div className="flex gap-2">
              <Link href="/clubs/join">
                <Button variant="secondary" className="hidden sm:flex">
                  <Users className="w-4 h-4" />
                  เข้าร่วมก๊วน
                </Button>
              </Link>
              <Link href="/clubs/create">
                <Button>
                  <Plus className="w-4 h-4" />
                  <span className="hidden sm:inline">ตั้งก๊วนใหม่</span>
                  <span className="sm:hidden">ตั้งก๊วน</span>
                </Button>
              </Link>
            </div>
          }
        />

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="flex-1">
            <Input
              placeholder="ค้นหาก๊วน..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              leftIcon={<Search className="w-5 h-5" />}
            />
          </div>

          {/* Sort & View Toggle */}
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input-modern"
            >
              <option value="newest">ใหม่ล่าสุด</option>
              <option value="members">สมาชิกมากสุด</option>
              <option value="alphabetical">ตามชื่อ A-Z</option>
            </select>

            {/* View Toggle */}
            <div className="flex bg-white rounded-xl border border-neutral-200 p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2.5 rounded-lg transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'text-neutral-400 hover:text-neutral-600'
                }`}
              >
                <Grid3X3 className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2.5 rounded-lg transition-colors ${
                  viewMode === 'list'
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'text-neutral-400 hover:text-neutral-600'
                }`}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        {!isLoading && clubs && (
          <div className="flex items-center gap-4 text-sm text-neutral-500 mb-6">
            <span>
              ทั้งหมด <strong className="text-neutral-900">{filteredClubs.length}</strong> ก๊วน
            </span>
            {searchTerm && (
              <span className="text-emerald-600">
                (ค้นพบจากการค้นหา &ldquo;{searchTerm}&rdquo;)
              </span>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div
            className={
              viewMode === 'grid'
                ? 'grid gap-5 sm:grid-cols-2 lg:grid-cols-3'
                : 'space-y-3'
            }
          >
            {Array.from({ length: 6 }).map((_, i) => (
              <ClubCardSkeleton key={i} />
            ))}
          </div>
        )}

        {/* Error State */}
        {error && (
          <EmptyState
            icon={Search}
            title="โหลดข้อมูลไม่สำเร็จ"
            description="กรุณาลองใหม่อีกครั้ง"
          />
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredClubs.length === 0 && (
          <EmptyState
            icon={Search}
            title={searchTerm ? 'ไม่พบก๊วนที่ค้นหา' : 'ยังไม่มีก๊วน'}
            description={
              searchTerm
                ? 'ลองค้นหาด้วยคำอื่น หรือล้างตัวกรอง'
                : 'ตั้งก๊วนแบดของคุณ หรือเข้าร่วมก๊วนที่มีอยู่'
            }
            action={
              searchTerm
                ? undefined
                : { label: 'ตั้งก๊วนใหม่', href: '/clubs/create' }
            }
            actionButton={
              searchTerm ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSearchTerm('');
                    setSortBy('newest');
                  }}
                >
                  ล้างตัวกรอง
                </Button>
              ) : undefined
            }
          />
        )}


        {!isLoading && !error && filteredClubs.length > 0 && (
          <div className="mb-6 flex flex-wrap gap-2">
            {filteredClubs.map((club) => (
              <Link
                key={`quick-${club.id}`}
                href={`/clubs/${club.id}`}
                className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm text-emerald-700 hover:bg-emerald-100"
              >
                {club.name}
              </Link>
            ))}
          </div>
        )}

        {/* Clubs Grid/List */}
        {!isLoading && !error && filteredClubs.length > 0 && (
          <div
            className={
              viewMode === 'grid'
                ? 'grid gap-5 sm:grid-cols-2 lg:grid-cols-3 stagger-children'
                : 'space-y-3 stagger-children'
            }
          >
            {filteredClubs.map((club) => (
              <ClubCard key={club.id} club={club} view={viewMode} />
            ))}
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}