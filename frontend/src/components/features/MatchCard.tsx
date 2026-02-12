'use client';

import Link from 'next/link';
import {
  Trophy,
  Users,
  Play,
  CheckCircle,
  Clock,
  MapPin,
  ChevronRight,
  Calendar,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MatchResponse, MatchStatus } from '@/lib/types';

interface MatchCardProps {
  match: MatchResponse;
  showSessionInfo?: boolean;
}

const statusConfig: Record<
  MatchStatus,
  {
    label: string;
    className: string;
    icon: typeof Play;
  }
> = {
  scheduled: {
    label: 'รอแข่ง',
    className: 'badge-neutral',
    icon: Clock,
  },
  ongoing: {
    label: 'กำลังแข่ง',
    className: 'badge-live',
    icon: Play,
  },
  completed: {
    label: 'เสร็จสิ้น',
    className: 'badge-emerald',
    icon: CheckCircle,
  },
  cancelled: {
    label: 'ยกเลิก',
    className: 'badge-rose',
    icon: Trophy,
  },
};

export function MatchCard({ match, showSessionInfo }: MatchCardProps) {
  const status = statusConfig[match.status];
  const StatusIcon = status.icon;

  const teamAPlayers = [match.team_a_player_1, match.team_a_player_2].filter(Boolean);
  const teamBPlayers = [match.team_b_player_1, match.team_b_player_2].filter(Boolean);

  const isDoubles = teamAPlayers.length === 2 && teamBPlayers.length === 2;
  const isCompleted = match.status === 'completed';
  const winner = match.winner_team;

  return (
    <Link href={`/matches/${match.id}`} className="block group">
      <div className="glass-card overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-200/50">
        <div className="p-5">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-emerald-500/20">
                {match.court_number}
              </div>
              <div>
                <p className="font-semibold text-neutral-900">คอร์ท {match.court_number}</p>
                <p className="text-sm text-neutral-500">{isDoubles ? 'ประเภทคู่' : 'ประเภทเดี่ยว'}</p>
              </div>
            </div>

            <span className={cn('badge', status.className)}>
              <StatusIcon className="w-3.5 h-3.5" />
              {status.label}
            </span>
          </div>

          {/* Teams */}
          <div className="flex items-center gap-4">
            {/* Team A */}
            <div
              className={cn(
                'flex-1 text-center p-4 rounded-xl transition-colors',
                isCompleted && winner === 'A'
                  ? 'bg-emerald-50 border-2 border-emerald-200'
                  : 'bg-neutral-50'
              )}
            >
              <div className="flex justify-center -space-x-2 mb-3">
                {teamAPlayers.map((player, idx) => (
                  <div
                    key={idx}
                    className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold text-sm border-3 border-white shadow-md"
                  >
                    {player?.display_name?.[0] || player?.full_name?.[0] || '?'}
                  </div>
                ))}
              </div>
              <p className="text-sm font-semibold text-neutral-900 truncate">
                {teamAPlayers.map((p) => p?.display_name || p?.full_name).join(' & ')}
              </p>
              {isCompleted && winner === 'A' && (
                <div className="flex items-center justify-center gap-1 mt-1.5 text-emerald-600 text-xs font-medium">
                  <Trophy className="w-3.5 h-3.5" />
                  ชนะ
                </div>
              )}
            </div>

            {/* VS */}
            <div className="text-neutral-300 font-bold text-lg">VS</div>

            {/* Team B */}
            <div
              className={cn(
                'flex-1 text-center p-4 rounded-xl transition-colors',
                isCompleted && winner === 'B'
                  ? 'bg-emerald-50 border-2 border-emerald-200'
                  : 'bg-neutral-50'
              )}
            >
              <div className="flex justify-center -space-x-2 mb-3">
                {teamBPlayers.map((player, idx) => (
                  <div
                    key={idx}
                    className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm border-3 border-white shadow-md"
                  >
                    {player?.display_name?.[0] || player?.full_name?.[0] || '?'}
                  </div>
                ))}
              </div>
              <p className="text-sm font-semibold text-neutral-900 truncate">
                {teamBPlayers.map((p) => p?.display_name || p?.full_name).join(' & ')}
              </p>
              {isCompleted && winner === 'B' && (
                <div className="flex items-center justify-center gap-1 mt-1.5 text-emerald-600 text-xs font-medium">
                  <Trophy className="w-3.5 h-3.5" />
                  ชนะ
                </div>
              )}
            </div>
          </div>

          {/* Score */}
          {match.score && (
            <div className="mt-5 text-center">
              <div className="inline-flex items-center gap-4 px-6 py-3 bg-neutral-900 text-white rounded-xl font-mono text-2xl shadow-lg">
                <span className={match.score.split('-')[0] > match.score.split('-')[1] ? 'text-emerald-400' : ''}>
                  {match.score.split('-')[0] || 0}
                </span>
                <span className="text-neutral-500">-</span>
                <span className={match.score.split('-')[1] > match.score.split('-')[0] ? 'text-emerald-400' : ''}>
                  {match.score.split('-')[1] || 0}
                </span>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between mt-5 pt-4 border-t border-neutral-100">
            <div className="text-sm text-neutral-400">
              {match.started_at
                ? new Date(match.started_at).toLocaleTimeString('th-TH', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'ยังไม่เริ่ม'}
            </div>
            <span className="flex items-center gap-1 text-sm font-medium text-emerald-600 group-hover:text-emerald-700">
              ดูรายละเอียด
              <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}