'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  MapPin,
  Calendar,
  Trophy,
  Plus,
  ChevronRight,
  Bell,
  Share2,
  Crown,
  Shield,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, StatsCard, EmptyState, PageSkeleton } from '@/components/shared';
import { ClubActivityChart } from '@/components/charts';
import { MemberBadge } from '@/components/features/ClubCard';
import { Button } from '@/components/ui/button';
import type { ClubMemberResponse } from '@/lib/types';

function getClubGradient(name: string): string {
  const gradients = [
    'from-emerald-600 via-teal-600 to-cyan-600',
    'from-blue-600 via-indigo-600 to-violet-600',
    'from-violet-600 via-purple-600 to-fuchsia-600',
    'from-amber-600 via-orange-600 to-red-600',
    'from-rose-600 via-pink-600 to-purple-600',
    'from-cyan-600 via-blue-600 to-indigo-600',
  ];
  const index = name.charCodeAt(0) % gradients.length;
  return gradients[index];
}

export default function ClubDetailPage({ params }: { params: { clubId: string } }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'members' | 'sessions'>('overview');

  const { data: club, isLoading, error } = useQuery({
    queryKey: ['club', params.clubId],
    queryFn: () => apiClient.getClub(params.clubId),
  });

  const { data: stats } = useQuery({
    queryKey: ['clubStats', params.clubId],
    queryFn: () => apiClient.getClubStats(params.clubId),
    enabled: !!club,
  });

  if (isLoading) {
    return (
      <ProtectedLayout>
        <Navbar />
        <main className="page-container">
          <PageSkeleton />
        </main>
      </ProtectedLayout>
    );
  }

  if (error || !club) {
    return (
      <ProtectedLayout>
        <Navbar />
        <main className="page-container">
          <EmptyState
            icon={Users}
            title="ไม่พบก๊วน"
            description="ก๊วนนี้อาจถูกลบหรือคุณไม่มีสิทธิ์เข้าถึง"
            action={{ label: 'กลับไปหน้าก๊วน', href: '/clubs' }}
          />
        </main>
      </ProtectedLayout>
    );
  }

  const gradient = getClubGradient(club.name);
  const isFull = club.member_count >= club.max_members;

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="pb-8">
        {/* Hero Section */}
        <div className={cn('relative bg-gradient-to-r text-white overflow-hidden', gradient)}>
          <div className="absolute inset-0 bg-black/20" />
          {/* Decorative circles */}
          <div className="absolute -top-20 -right-20 w-60 h-60 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-white/10 rounded-full blur-3xl" />

          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-24">
            {/* Breadcrumbs */}
            <nav className="flex items-center gap-2 text-sm text-white/80 mb-4">
              <Link href="/clubs" className="hover:text-white transition-colors">
                ก๊วน
              </Link>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white font-medium">{club.name}</span>
            </nav>

            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3 flex-wrap">
                  <span
                    className={cn(
                      'badge border-0',
                      isFull ? 'bg-rose-500/90 text-white' : 'bg-emerald-500/90 text-white'
                    )}
                  >
                    {isFull ? 'เต็ม' : 'รับสมาชิก'}
                  </span>
                  <span className="text-white/60 text-sm">@{club.slug}</span>
                </div>
                <h1 className="text-3xl md:text-4xl lg:text-5xl font-black mb-3">{club.name}</h1>
                <p className="text-white/80 max-w-2xl text-lg">{club.description || 'ไม่มีคำอธิบาย'}</p>

                <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-white/80">
                  <span className="flex items-center gap-1.5">
                    <Users className="w-4 h-4" />
                    {club.member_count} / {club.max_members} สมาชิก
                  </span>
                  {club.location && (
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4" />
                      {club.location}
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 flex-wrap">
                <button className="px-4 py-2.5 bg-white/10 hover:bg-white/20 rounded-xl text-white text-sm font-medium transition-colors backdrop-blur-sm flex items-center gap-2">
                  <Bell className="w-4 h-4" />
                  <span className="hidden sm:inline">แจ้งเตือน</span>
                </button>
                <button className="px-4 py-2.5 bg-white/10 hover:bg-white/20 rounded-xl text-white text-sm font-medium transition-colors backdrop-blur-sm flex items-center gap-2">
                  <Share2 className="w-4 h-4" />
                  <span className="hidden sm:inline">แชร์</span>
                </button>
                <Link href={`/clubs/${params.clubId}/sessions/create`}>
                  <Button className="bg-white text-neutral-900 hover:bg-neutral-100">
                    <Plus className="w-4 h-4" />
                    สร้างนัดตี
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatsCard
              title="สมาชิก"
              value={club.member_count}
              icon={Users}
              color="emerald"
              subtitle={`จาก ${club.max_members} คน`}
            />
            <StatsCard
              title="นัดตี"
              value={stats?.total_sessions || 0}
              icon={Calendar}
              color="blue"
            />
            <StatsCard
              title="แมทช์"
              value={stats?.total_matches || 0}
              icon={Trophy}
              color="amber"
            />
            <StatsCard
              title="Rating เฉลี่ย"
              value={
                stats?.top_players?.length
                  ? Math.round(
                      stats.top_players.reduce((acc, p) => acc + p.rating, 0) /
                        stats.top_players.length
                    )
                  : 1000
              }
              icon={Trophy}
              color="purple"
            />
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-neutral-100/80 p-1 rounded-xl mb-6 w-fit overflow-x-auto">
            {(['overview', 'members', 'sessions'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap',
                  activeTab === tab
                    ? 'bg-white text-neutral-900 shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900'
                )}
              >
                {tab === 'overview' && 'ภาพรวม'}
                {tab === 'members' && 'สมาชิก'}
                {tab === 'sessions' && 'นัดตี'}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Main Content */}
              <div className="lg:col-span-2 space-y-6">
                {/* Activity Chart */}
                <div className="glass-card p-6">
                  <h3 className="text-lg font-bold text-neutral-900 mb-4">นัดตีล่าสุด</h3>
                  <ClubActivityChart />
                </div>

                {/* Recent Sessions */}
                <div className="glass-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-neutral-900">นัดตีที่จะมาถึง</h3>
                    <Link
                      href={`/clubs/${params.clubId}/sessions`}
                      className="text-sm text-emerald-600 hover:text-emerald-700 flex items-center gap-1 font-medium"
                    >
                      ดูทั้งหมด
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>

                  {stats?.recent_sessions && stats.recent_sessions.length > 0 ? (
                    <div className="space-y-3">
                      {stats.recent_sessions.slice(0, 3).map((session) => (
                        <Link
                          key={session.id}
                          href={`/clubs/${params.clubId}/sessions/${session.id}`}
                          className="flex items-center justify-between p-4 bg-neutral-50 rounded-xl hover:bg-neutral-100 transition-colors"
                        >
                          <div>
                            <h4 className="font-semibold text-neutral-900">{session.title}</h4>
                            <p className="text-sm text-neutral-500">
                              {new Date(session.start_time).toLocaleDateString('th-TH', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </p>
                          </div>
                          <span
                            className={cn('badge', {
                              'badge-emerald': session.status === 'open',
                              'badge-amber': session.status === 'full',
                              'badge-blue': session.status === 'ongoing',
                              'badge-neutral': session.status === 'completed',
                            })}
                          >
                            {session.status === 'open'
                              ? 'เปิดรับ'
                              : session.status === 'full'
                              ? 'เต็ม'
                              : session.status === 'ongoing'
                              ? 'กำลังแข่ง'
                              : session.status}
                          </span>
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon={Calendar}
                      title="ยังไม่มีนัดตี"
                      description="สร้างนัดตีแรกของก๊วน"
                      action={{
                        label: 'สร้างนัดตี',
                        href: `/clubs/${params.clubId}/sessions/create`,
                      }}
                    />
                  )}
                </div>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Quick Actions */}
                <div className="glass-card p-6">
                  <h3 className="text-lg font-bold text-neutral-900 mb-4">ลิงก์ด่วน</h3>
                  <div className="space-y-2">
                    <Link
                      href={`/clubs/${params.clubId}/sessions`}
                      className="flex items-center gap-3 p-3 rounded-xl hover:bg-neutral-50 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                        <Calendar className="w-5 h-5 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-neutral-900">นัดตีทั้งหมด</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-neutral-300" />
                    </Link>
                    <Link
                      href={`/clubs/${params.clubId}/leaderboard`}
                      className="flex items-center gap-3 p-3 rounded-xl hover:bg-neutral-50 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                        <Trophy className="w-5 h-5 text-amber-600" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-neutral-900">กระดานคะแนน</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-neutral-300" />
                    </Link>
                  </div>
                </div>

                {/* Top Players */}
                {stats?.top_players && stats.top_players.length > 0 && (
                  <div className="glass-card p-6">
                    <h3 className="text-lg font-bold text-neutral-900 mb-4">ผู้เล่นยอดเยี่ยม</h3>
                    <div className="space-y-3">
                      {stats.top_players.slice(0, 5).map((player, index) => (
                        <div key={player.user_id} className="flex items-center gap-3">
                          <div
                            className={cn(
                              'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold',
                              index === 0
                                ? 'bg-amber-100 text-amber-700'
                                : index === 1
                                ? 'bg-neutral-200 text-neutral-700'
                                : index === 2
                                ? 'bg-orange-100 text-orange-700'
                                : 'bg-neutral-100 text-neutral-500'
                            )}
                          >
                            {index + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-neutral-900 text-sm truncate">
                              {player.display_name || player.full_name}
                            </p>
                          </div>
                          <span className="text-sm font-bold text-emerald-600">{player.rating}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'members' && (
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-neutral-900">
                  สมาชิกทั้งหมด ({club.members.length})
                </h3>
              </div>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {club.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 p-4 bg-neutral-50 rounded-xl"
                  >
                    {member.avatar_url ? (
                      <img
                        src={member.avatar_url}
                        alt={member.display_name || member.full_name}
                        className="w-12 h-12 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold">
                        {(member.display_name || member.full_name).charAt(0)}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-neutral-900 truncate">
                        {member.display_name || member.full_name}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <MemberBadge role={member.role} />
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-emerald-600">{member.rating_in_club}</p>
                      <p className="text-xs text-neutral-400">Rating</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'sessions' && (
            <div className="text-center py-12">
              <p className="text-neutral-500 mb-4">ดูนัดตีทั้งหมดของก๊วน</p>
              <Link href={`/clubs/${params.clubId}/sessions`}>
                <Button>
                  <Calendar className="w-5 h-5" />
                  ดูนัดตีทั้งหมด
                </Button>
              </Link>
            </div>
          )}
        </div>
      </main>
    </ProtectedLayout>
  );
}