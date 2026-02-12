'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Trophy,
  Play,
  CheckCircle,
  ChevronLeft,
  RotateCw,
  Users,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState, PageSkeleton } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/toast';
import type { MatchResponse, MatchStatus } from '@/lib/types';

const statusConfig: Record<
  MatchStatus,
  {
    label: string;
    className: string;
  }
> = {
  scheduled: {
    label: 'รอแข่ง',
    className: 'badge-neutral',
  },
  ongoing: {
    label: 'กำลังแข่ง',
    className: 'badge-live',
  },
  completed: {
    label: 'เสร็จสิ้น',
    className: 'badge-emerald',
  },
  cancelled: {
    label: 'ยกเลิก',
    className: 'badge-rose',
  },
};

interface PlayerCardProps {
  player: { display_name?: string; full_name: string; avatar_url?: string; rating?: number };
  isWinner?: boolean;
  team: 'A' | 'B';
}

function PlayerCard({ player, isWinner, team }: PlayerCardProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 p-4 rounded-xl transition-colors',
        isWinner ? 'bg-emerald-50 border-2 border-emerald-200' : 'bg-neutral-50'
      )}
    >
      {player.avatar_url ? (
        <img
          src={player.avatar_url}
          alt={player.display_name || player.full_name}
          className="w-14 h-14 rounded-full object-cover border-2 border-white shadow-sm"
        />
      ) : (
        <div
          className={cn(
            'w-14 h-14 rounded-full flex items-center justify-center text-white text-xl font-bold shadow-sm',
            team === 'A'
              ? 'bg-gradient-to-br from-emerald-500 to-teal-600'
              : 'bg-gradient-to-br from-violet-500 to-purple-600'
          )}
        >
          {(player.display_name || player.full_name).charAt(0)}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-neutral-900 truncate">
          {player.display_name || player.full_name}
        </p>
        {player.rating && <p className="text-sm text-neutral-500">Rating: {player.rating}</p>}
      </div>
      {isWinner && (
        <div className="flex items-center gap-1 text-emerald-600">
          <Trophy className="w-5 h-5" />
        </div>
      )}
    </div>
  );
}

function ScoreDisplay({ score }: { score?: string }) {
  if (!score)
    return (
      <div className="text-center py-8">
        <p className="text-neutral-400 text-lg">ยังไม่มีคะแนน</p>
      </div>
    );

  const [teamA, teamB] = score.split('-').map((s) => parseInt(s.trim()) || 0);

  return (
    <div className="flex items-center justify-center gap-6 py-6">
      <div
        className={cn(
          'text-7xl md:text-8xl font-black transition-colors',
          teamA > teamB ? 'text-emerald-500' : 'text-neutral-400'
        )}
      >
        {teamA}
      </div>
      <div className="text-4xl text-neutral-300 font-bold">:</div>
      <div
        className={cn(
          'text-7xl md:text-8xl font-black transition-colors',
          teamB > teamA ? 'text-emerald-500' : 'text-neutral-400'
        )}
      >
        {teamB}
      </div>
    </div>
  );
}

export default function MatchPage({ params }: { params: { matchId: string } }) {
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();
  const [showScoreForm, setShowScoreForm] = useState(false);
  const [scoreInput, setScoreInput] = useState('');
  const [winnerTeam, setWinnerTeam] = useState<'A' | 'B'>('A');

  const { data: match, isLoading } = useQuery({
    queryKey: ['match', params.matchId],
    queryFn: () => apiClient.getMatch(params.matchId),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['match', params.matchId] });

  const startMutation = useMutation({
    mutationFn: () => apiClient.startMatch(params.matchId),
    onSuccess: () => {
      refresh();
      success('เริ่มแข่งขันแล้ว', 'แมทช์ได้เริ่มขึ้นแล้ว');
    },
    onError: () => showError('เกิดข้อผิดพลาด', 'ไม่สามารถเริ่มแข่งขันได้'),
  });

  const completeMutation = useMutation({
    mutationFn: (winner: 'A' | 'B') => apiClient.completeMatch(params.matchId, winner),
    onSuccess: () => {
      refresh();
      success('จบแมทช์แล้ว', 'ผลแมทช์ถูกบันทึกแล้ว');
    },
    onError: () => showError('เกิดข้อผิดพลาด', 'ไม่สามารถจบแมทช์ได้'),
  });

  const scoreMutation = useMutation({
    mutationFn: (data: { score: string; winner_team: 'A' | 'B' }) =>
      apiClient.updateScore(params.matchId, data),
    onSuccess: () => {
      refresh();
      setShowScoreForm(false);
      success('บันทึกคะแนนแล้ว', 'คะแนนถูกอัปเดตแล้ว');
    },
    onError: () => showError('เกิดข้อผิดพลาด', 'ไม่สามารถบันทึกคะแนนได้'),
  });

  const handleScoreSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    scoreMutation.mutate({ score: scoreInput, winner_team: winnerTeam });
  };

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

  if (!match) {
    return (
      <ProtectedLayout>
        <Navbar />
        <main className="page-container">
          <EmptyState
            icon={Trophy}
            title="ไม่พบแมทช์"
            description="แมทช์นี้อาจถูกลบหรือคุณไม่มีสิทธิ์เข้าถึง"
          />
        </main>
      </ProtectedLayout>
    );
  }

  const status = statusConfig[match.status];
  const teamAPlayers = [match.team_a_player_1, match.team_a_player_2].filter(Boolean);
  const teamBPlayers = [match.team_b_player_1, match.team_b_player_2].filter(Boolean);
  const isCompleted = match.status === 'completed';
  const winner = match.winner_team;

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        {/* Header */}
        <PageHeader
          title={`แมทช์คอร์ท ${match.court_number}`}
          subtitle="รายละเอียดแมทช์"
          breadcrumbs={[{ label: 'ก๊วน', href: '/clubs' }]}
          action={
            <button onClick={() => window.history.back()} className="btn-secondary flex items-center gap-2">
              <ChevronLeft className="w-4 h-4" />
              กลับ
            </button>
          }
        />

        {/* Status Banner */}
        <div className={cn('mb-6 p-4 rounded-xl bg-opacity-50 border', status.className)}>
          <div className="flex items-center gap-3">
            <span className={cn('badge', status.className)}>{status.label}</span>
            {isCompleted && winner && (
              <div className="flex items-center gap-2 text-emerald-700">
                <Trophy className="w-5 h-5" />
                <span className="font-semibold">ทีม {winner === 'A' ? 'A' : 'B'} ชนะ!</span>
              </div>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Score Board */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold text-neutral-900 mb-4 text-center">
                คะแนนแมทช์
              </h2>

              <ScoreDisplay score={match.score} />

              {/* Timeline */}
              <div className="mt-6 pt-6 border-t border-neutral-100">
                <h3 className="text-sm font-semibold text-neutral-500 mb-4">ไทม์ไลน์</h3>
                <div className="space-y-3">
                  {match.created_at && (
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-neutral-100 flex items-center justify-center">
                        <Users className="w-4 h-4 text-neutral-500" />
                      </div>
                      <div>
                        <p className="text-sm text-neutral-900">สร้างแมทช์</p>
                        <p className="text-xs text-neutral-500">
                          {new Date(match.created_at).toLocaleString('th-TH')}
                        </p>
                      </div>
                    </div>
                  )}
                  {match.started_at && (
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
                        <Play className="w-4 h-4 text-emerald-600" />
                      </div>
                      <div>
                        <p className="text-sm text-neutral-900">เริ่มแข่งขัน</p>
                        <p className="text-xs text-neutral-500">
                          {new Date(match.started_at).toLocaleString('th-TH')}
                        </p>
                      </div>
                    </div>
                  )}
                  {match.completed_at && (
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                        <CheckCircle className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-neutral-900">จบแมทช์</p>
                        <p className="text-xs text-neutral-500">
                          {new Date(match.completed_at).toLocaleString('th-TH')}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Teams */}
            <div className="glass-card p-6">
              <h2 className="text-xl font-bold text-neutral-900 mb-4">ผู้เล่น</h2>

              <div className="grid md:grid-cols-2 gap-4">
                {/* Team A */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-sm">
                      A
                    </div>
                    <h3 className="font-semibold text-neutral-900">ทีม A</h3>
                    {winner === 'A' && (
                      <span className="badge badge-emerald">ชนะ</span>
                    )}
                  </div>
                  <div className="space-y-2">
                    {teamAPlayers.map((player, idx) => (
                      <PlayerCard key={idx} player={player!} team="A" isWinner={winner === 'A'} />
                    ))}
                  </div>
                </div>

                {/* Team B */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
                      B
                    </div>
                    <h3 className="font-semibold text-neutral-900">ทีม B</h3>
                    {winner === 'B' && (
                      <span className="badge badge-emerald">ชนะ</span>
                    )}
                  </div>
                  <div className="space-y-2">
                    {teamBPlayers.map((player, idx) => (
                      <PlayerCard key={idx} player={player!} team="B" isWinner={winner === 'B'} />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar - Actions */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="glass-card p-6">
              <h3 className="font-bold text-neutral-900 mb-4">จัดการแมทช์</h3>

              <div className="space-y-2">
                {match.status === 'scheduled' && (
                  <Button
                    onClick={() => startMutation.mutate()}
                    isLoading={startMutation.isPending}
                    className="w-full bg-emerald-500 hover:bg-emerald-600"
                  >
                    <Play className="w-4 h-4" />
                    เริ่มแข่งขัน
                  </Button>
                )}

                {match.status === 'ongoing' && (
                  <Button onClick={() => setShowScoreForm(true)} className="w-full">
                    <Trophy className="w-4 h-4" />
                    บันทึกคะแนน
                  </Button>
                )}

                {match.status === 'completed' && (
                  <div className="p-4 bg-emerald-50 rounded-xl text-center">
                    <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                    <p className="text-emerald-700 font-semibold">แมทช์เสร็จสิ้นแล้ว</p>
                  </div>
                )}

                <Button
                  variant="secondary"
                  onClick={() => window.location.reload()}
                  className="w-full"
                >
                  <RotateCw className="w-4 h-4" />
                  รีเฟรช
                </Button>

                <Link href={`/tv?match=${match.id}`} target="_blank">
                  <Button variant="outline" className="w-full mt-2">
                    เปิด TV Mode
                  </Button>
                </Link>
              </div>
            </div>

            {/* Score Form */}
            {showScoreForm && (
              <div className="glass-card p-6">
                <h3 className="font-bold text-neutral-900 mb-4">บันทึกคะแนน</h3>
                <form onSubmit={handleScoreSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      คะแนน (เช่น 21-15)
                    </label>
                    <input
                      type="text"
                      value={scoreInput}
                      onChange={(e) => setScoreInput(e.target.value)}
                      placeholder="21-15"
                      className="input-modern"
                      pattern="\d+-\d+"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-neutral-700 mb-2">
                      ทีมที่ชนะ
                    </label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setWinnerTeam('A')}
                        className={cn(
                          'flex-1 py-2.5 px-4 rounded-xl font-semibold transition-colors',
                          winnerTeam === 'A'
                            ? 'bg-emerald-500 text-white'
                            : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                        )}
                      >
                        ทีม A
                      </button>
                      <button
                        type="button"
                        onClick={() => setWinnerTeam('B')}
                        className={cn(
                          'flex-1 py-2.5 px-4 rounded-xl font-semibold transition-colors',
                          winnerTeam === 'B'
                            ? 'bg-violet-500 text-white'
                            : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
                        )}
                      >
                        ทีม B
                      </button>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button
                      type="submit"
                      isLoading={scoreMutation.isPending}
                      className="flex-1"
                    >
                      บันทึก
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setShowScoreForm(false)}
                      className="flex-1"
                    >
                      ยกเลิก
                    </Button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}