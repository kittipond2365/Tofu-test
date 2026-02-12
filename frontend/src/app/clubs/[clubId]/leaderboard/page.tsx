'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Trophy,
  Medal,
  Crown,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronLeft,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState, PageSkeleton } from '@/components/shared';
import { PlayerStatsRadar } from '@/components/charts';
import { Button } from '@/components/ui/Button';
import type { PlayerStatsResponse } from '@/lib/types';

type TimeFilter = 'all' | 'month' | 'week';

function PodiumPlayer({
  player,
  rank,
  gradient,
}: {
  player: PlayerStatsResponse;
  rank: number;
  gradient: string;
}) {
  const isFirst = rank === 1;

  return (
    <div className={cn('relative flex flex-col items-center', isFirst ? 'order-2 -mt-8' : 'order-1')}>
      {/* Medal */}
      <div className={cn('relative mb-3', isFirst ? 'scale-110' : '')}>
        <div
          className={cn(
            'w-20 h-20 rounded-full bg-gradient-to-br flex items-center justify-center shadow-xl',
            gradient
          )}
        >
          {player.avatar_url ? (
            <img
              src={player.avatar_url}
              alt={player.display_name || player.full_name}
              className="w-full h-full rounded-full object-cover border-4 border-white"
            />
          ) : (
            <span className="text-2xl font-black text-white">
              {(player.display_name || player.full_name).charAt(0)}
            </span>
          )}
        </div>
        {/* Rank Badge */}
        <div
          className={cn(
            'absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold shadow-lg',
            rank === 1 ? 'bg-amber-400' : rank === 2 ? 'bg-neutral-400' : 'bg-orange-400'
          )}
        >
          {rank}
        </div>
      </div>

      {/* Info */}
      <div className="text-center">
        <p className="font-bold text-neutral-900 truncate max-w-[120px]">
          {player.display_name || player.full_name}
        </p>
        <div
          className={cn(
            'text-2xl font-black mt-1',
            rank === 1 ? 'text-amber-500' : rank === 2 ? 'text-neutral-500' : 'text-orange-500'
          )}
        >
          {player.rating}
        </div>
        <p className="text-xs text-neutral-500">
          {player.wins}W / {player.losses}L
        </p>
      </div>
    </div>
  );
}

export default function LeaderboardPage({ params }: { params: { clubId: string } }) {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');

  const { data: club } = useQuery({
    queryKey: ['club', params.clubId],
    queryFn: () => apiClient.getClub(params.clubId),
  });

  const { data: leaderboard, isLoading } = useQuery({
    queryKey: ['leaderboard', params.clubId, timeFilter],
    queryFn: () => apiClient.getLeaderboard(params.clubId),
  });

  const sortedLeaderboard = leaderboard ? [...leaderboard].sort((a, b) => b.rating - a.rating) : [];

  const top3 = sortedLeaderboard.slice(0, 3);
  const rest = sortedLeaderboard.slice(3);

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

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        {/* Header */}
        <PageHeader
          title="กระดานคะแนน"
          subtitle={`อันดับผู้เล่นใน ${club?.name || 'ชมรม'}`}
          breadcrumbs={[
            { label: 'ชมรม', href: '/clubs' },
            { label: club?.name || '', href: `/clubs/${params.clubId}` },
            { label: 'กระดานคะแนน' },
          ]}
          action={
            <Link href={`/clubs/${params.clubId}`}>
              <Button variant="secondary">
                <ChevronLeft className="w-4 h-4" />
                กลับ
              </Button>
            </Link>
          }
        />

        {/* Time Filter */}
        <div className="flex gap-2 mb-6">
          {(['all', 'month', 'week'] as TimeFilter[]).map((filter) => (
            <button
              key={filter}
              onClick={() => setTimeFilter(filter)}
              className={cn(
                'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
                timeFilter === filter
                  ? 'bg-emerald-500 text-white'
                  : 'bg-white text-neutral-600 hover:bg-neutral-50 border border-neutral-200'
              )}
            >
              {filter === 'all' && 'ทั้งหมด'}
              {filter === 'month' && 'เดือนนี้'}
              {filter === 'week' && 'สัปดาห์นี้'}
            </button>
          ))}
        </div>

        {sortedLeaderboard.length === 0 ? (
          <EmptyState
            icon={Trophy}
            title="ยังไม่มีข้อมูล"
            description="ยังไม่มีผู้เล่นในกระดานคะแนน"
          />
        ) : (
          <div className="space-y-6">
            {/* Podium Section */}
            {top3.length > 0 && (
              <div className="glass-card p-8">
                <div className="flex justify-center items-end gap-8 md:gap-16 py-8">
                  {top3[1] && (
                    <PodiumPlayer
                      player={top3[1]}
                      rank={2}
                      gradient="from-neutral-300 to-neutral-400"
                    />
                  )}
                  {top3[0] && (
                    <PodiumPlayer
                      player={top3[0]}
                      rank={1}
                      gradient="from-amber-400 to-amber-500"
                    />
                  )}
                  {top3[2] && (
                    <PodiumPlayer
                      player={top3[2]}
                      rank={3}
                      gradient="from-orange-400 to-orange-500"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Charts Section */}
            {top3.length > 0 && (
              <div className="grid md:grid-cols-3 gap-6">
                {top3.map((player) => (
                  <div key={player.user_id} className="glass-card p-6">
                    <h4 className="text-center font-semibold text-neutral-900 mb-2">
                      {player.display_name || player.full_name}
                    </h4>
                    <PlayerStatsRadar
                      height={200}
                      data={[
                        { category: 'Attack', value: 70 + Math.random() * 30, fullMark: 100 },
                        { category: 'Defense', value: 60 + Math.random() * 40, fullMark: 100 },
                        { category: 'Speed', value: 65 + Math.random() * 35, fullMark: 100 },
                        { category: 'Stamina', value: 55 + Math.random() * 45, fullMark: 100 },
                        { category: 'Technique', value: 75 + Math.random() * 25, fullMark: 100 },
                        { category: 'Mental', value: 80 + Math.random() * 20, fullMark: 100 },
                      ]}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Full Leaderboard Table */}
            {rest.length > 0 && (
              <div className="glass-card overflow-hidden">
                <div className="p-6 border-b border-neutral-100">
                  <h3 className="text-lg font-bold text-neutral-900">อันดับอื่นๆ</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-neutral-50">
                      <tr>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-neutral-700">#</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-neutral-700">ผู้เล่น</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-neutral-700">Rating</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-neutral-700">W/L</th>
                        <th className="px-6 py-4 text-left text-sm font-semibold text-neutral-700">Win %</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                      {rest.map((player, index) => {
                        const total = player.wins + player.losses;
                        const rate = total > 0 ? ((player.wins / total) * 100).toFixed(1) : '0.0';
                        return (
                          <tr key={player.user_id} className="hover:bg-neutral-50 transition-colors">
                            <td className="px-6 py-4">
                              <span className="font-bold text-neutral-900">{index + 4}</span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                {player.avatar_url ? (
                                  <img
                                    src={player.avatar_url}
                                    alt={player.display_name || player.full_name}
                                    className="w-10 h-10 rounded-full object-cover"
                                  />
                                ) : (
                                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold">
                                    {(player.display_name || player.full_name).charAt(0)}
                                  </div>
                                )}
                                <div>
                                  <p className="font-semibold text-neutral-900">
                                    {player.display_name || player.full_name}
                                  </p>
                                  <p className="text-xs text-neutral-500">
                                    {player.matches_this_month} แมทช์เดือนนี้
                                  </p>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="font-bold text-emerald-600 text-lg">{player.rating}</span>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-2">
                                <span className="text-emerald-600 font-semibold">{player.wins}</span>
                                <span className="text-neutral-300">/</span>
                                <span className="text-rose-600 font-semibold">{player.losses}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                <div className="w-16 h-2 bg-neutral-200 rounded-full overflow-hidden">
                                  <div
                                    className={cn(
                                      'h-full rounded-full',
                                      parseFloat(rate) >= 60
                                        ? 'bg-emerald-500'
                                        : parseFloat(rate) >= 40
                                        ? 'bg-amber-500'
                                        : 'bg-rose-500'
                                    )}
                                    style={{ width: `${rate}%` }}
                                  />
                                </div>
                                <span className="text-sm font-semibold">{rate}%</span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}