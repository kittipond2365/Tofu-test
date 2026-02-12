'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Trophy, Play, ChevronRight, ExternalLink, Radio } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { PageHeader, EmptyState } from '@/components/shared';
import { Button } from '@/components/ui/button';
import type { MatchResponse } from '@/lib/types';

function LiveMatchCard({ match }: { match: MatchResponse }) {
  const teamAPlayers = [match.team_a_player_1, match.team_a_player_2].filter(Boolean);
  const teamBPlayers = [match.team_b_player_1, match.team_b_player_2].filter(Boolean);
  const [teamAScore, teamBScore] = match.score
    ? match.score.split('-').map((s) => parseInt(s.trim()) || 0)
    : [0, 0];

  return (
    <div className="glass-card p-6 hover:border-emerald-200/50 transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white font-bold text-lg">
            {match.court_number}
          </div>
          <div>
            <p className="font-bold text-neutral-900">คอร์ท {match.court_number}</p>
            <span className="badge badge-live">
              <Radio className="w-3 h-3" />
              LIVE
            </span>
          </div>
        </div>
        <Link href={`/matches/${match.id}`}>
          <Button variant="secondary" size="sm">
            ดูรายละเอียด
          </Button>
        </Link>
      </div>

      {/* Score Display */}
      <div className="flex items-center justify-center gap-6 mb-4">
        <div className="text-center">
          <div className="flex justify-center -space-x-2 mb-2">
            {teamAPlayers.map((player, idx) => (
              <div
                key={idx}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white font-bold text-sm border-2 border-white"
              >
                {player?.display_name?.[0] || '?'}
              </div>
            ))}
          </div>
          <p className="text-sm font-medium text-neutral-600 truncate max-w-[100px]">
            {teamAPlayers.map((p) => p?.display_name).join(' & ')}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <span
            className={cn(
              'text-4xl font-black',
              teamAScore > teamBScore ? 'text-emerald-500' : 'text-neutral-400'
            )}
          >
            {teamAScore}
          </span>
          <span className="text-2xl text-neutral-300">:</span>
          <span
            className={cn(
              'text-4xl font-black',
              teamBScore > teamAScore ? 'text-emerald-500' : 'text-neutral-400'
            )}
          >
            {teamBScore}
          </span>
        </div>

        <div className="text-center">
          <div className="flex justify-center -space-x-2 mb-2">
            {teamBPlayers.map((player, idx) => (
              <div
                key={idx}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm border-2 border-white"
              >
                {player?.display_name?.[0] || '?'}
              </div>
            ))}
          </div>
          <p className="text-sm font-medium text-neutral-600 truncate max-w-[100px]">
            {teamBPlayers.map((p) => p?.display_name).join(' & ')}
          </p>
        </div>
      </div>

      {/* TV Mode Link */}
      <Link
        href={`/tv?match=${match.id}`}
        target="_blank"
        className="flex items-center justify-center gap-2 p-3 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors"
      >
        <ExternalLink className="w-4 h-4" />
        <span className="font-medium">เปิด TV Mode</span>
      </Link>
    </div>
  );
}

export default function LivePage() {
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLiveMatches = async () => {
      try {
        // This should be replaced with actual API endpoint for live matches
        // const data = await apiClient.getLiveMatches();
        setMatches([]);
      } catch (error) {
        console.error('Failed to fetch live matches:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLiveMatches();
    const interval = setInterval(fetchLiveMatches, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        <PageHeader
          title="ถ่ายทอดสด"
          subtitle="ดูแมทช์ที่กำลังตีอยู่แบบสด"
          breadcrumbs={[{ label: 'ถ่ายทอดสด' }]}
        />

        {loading ? (
          <div className="grid md:grid-cols-2 gap-6">
            {[1, 2].map((i) => (
              <div key={i} className="glass-card p-6 h-64 animate-pulse" />
            ))}
          </div>
        ) : matches.length === 0 ? (
          <EmptyState
            icon={Play}
            title="ไม่มีแมทช์ที่กำลังตีอยู่"
            description="ตอนนี้ไม่มีแมทช์ที่กำลังตี"
            action={{ label: 'ดูก๊วนทั้งหมด', href: '/clubs' }}
          />
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {matches.map((match) => (
              <LiveMatchCard key={match.id} match={match} />
            ))}
          </div>
        )}

        {/* TV Mode Info */}
        <div className="mt-12 glass-card p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-neutral-900 mb-1">TV Mode</h3>
              <p className="text-neutral-500">
                แสดงสกอร์แบบเต็มจอ สำหรับฉายบนจอใหญ่ที่สนาม
              </p>
            </div>
            <Link href="/tv">
              <Button variant="secondary">
                <ExternalLink className="w-4 h-4" />
                เปิด TV Mode
              </Button>
            </Link>
          </div>
        </div>
      </main>
    </ProtectedLayout>
  );
}