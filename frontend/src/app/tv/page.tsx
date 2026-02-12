'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Trophy, Clock, Users, Maximize, Minimize, RotateCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import type { MatchResponse } from '@/lib/types';

// TV Mode colors - optimized for large screens and visibility from distance
const tvColors = {
  court: 'from-emerald-600 to-emerald-800',
  text: 'text-white',
  score: 'text-white',
  teamA: 'from-blue-500 to-blue-600',
  teamB: 'from-violet-500 to-violet-600',
  winner: 'from-amber-400 to-amber-500',
};

interface TVMatchDisplayProps {
  match: MatchResponse;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}

function TVMatchDisplay({ match, isFullscreen, onToggleFullscreen }: TVMatchDisplayProps) {
  const teamAPlayers = [match.team_a_player_1, match.team_a_player_2].filter(Boolean);
  const teamBPlayers = [match.team_b_player_2, match.team_b_player_2].filter(Boolean);
  const isCompleted = match.status === 'completed';
  const winner = match.winner_team;

  const [teamAScore, teamBScore] = match.score
    ? match.score.split('-').map((s) => parseInt(s.trim()) || 0)
    : [0, 0];

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
            <Trophy className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-black text-white tracking-tight">TOFUBADMINTON</h1>
            <p className="text-emerald-400 text-lg font-medium">LIVE MATCH</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Court Badge */}
          <div className="px-6 py-3 bg-white/10 backdrop-blur rounded-2xl border border-white/20">
            <span className="text-white/60 text-lg mr-3">คอร์ท</span>
            <span className="text-4xl font-black text-white">{match.court_number}</span>
          </div>

          {/* Status */}
          <div
            className={cn(
              'px-6 py-3 rounded-2xl font-bold text-xl flex items-center gap-3',
              match.status === 'ongoing'
                ? 'bg-rose-500 text-white animate-pulse'
                : match.status === 'completed'
                ? 'bg-emerald-500 text-white'
                : 'bg-white/10 text-white/80 border border-white/20'
            )}
          >
            {match.status === 'ongoing' && <span className="w-4 h-4 bg-white rounded-full animate-ping" />}
            {match.status === 'ongoing' && 'LIVE'}
            {match.status === 'completed' && 'FINISHED'}
            {match.status === 'scheduled' && 'UPCOMING'}
          </div>

          {/* Controls */}
          <button
            onClick={onToggleFullscreen}
            className="p-4 bg-white/10 hover:bg-white/20 rounded-2xl text-white transition-colors border border-white/20"
          >
            {isFullscreen ? <Minimize className="w-6 h-6" /> : <Maximize className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Main Score Display */}
      <div className="flex-1 flex items-center justify-center px-8">
        <div className="w-full max-w-7xl">
          {/* Teams & Score */}
          <div className="flex items-center justify-center gap-8 lg:gap-16">
            {/* Team A */}
            <div
              className={cn(
                'flex-1 flex flex-col items-center',
                winner === 'A' && 'scale-105'
              )}
            >
              <div
                className={cn(
                  'w-48 h-48 lg:w-64 lg:h-64 rounded-3xl bg-gradient-to-br flex items-center justify-center mb-6 shadow-2xl',
                  winner === 'A' ? tvColors.winner : tvColors.teamA
                )}
              >
                <span className="text-7xl lg:text-8xl font-black text-white">A</span>
              </div>

              {/* Players */}
              <div className="flex flex-col items-center gap-3">
                {teamAPlayers.map((player, idx) => (
                  <div key={idx} className="text-center">
                    <p className="text-3xl lg:text-4xl font-bold text-white">
                      {player?.display_name || player?.full_name}
                    </p>
                    {player?.rating && (
                      <p className="text-xl text-white/60 mt-1">Rating: {player.rating}</p>
                    )}
                  </div>
                ))}
              </div>

              {winner === 'A' && (
                <div className="mt-6 px-8 py-3 bg-amber-400 rounded-2xl">
                  <span className="text-2xl font-black text-amber-950 flex items-center gap-2">
                    <Trophy className="w-8 h-8" />
                    WINNER
                  </span>
                </div>
              )}
            </div>

            {/* Score */}
            <div className="flex flex-col items-center">
              <div className="flex items-center gap-6 lg:gap-10">
                {/* Team A Score */}
                <div
                  className={cn(
                    'text-[10rem] lg:text-[14rem] xl:text-[16rem] font-black leading-none tabular-nums',
                    winner === 'A' ? 'text-amber-400' : 'text-white',
                    teamAScore > teamBScore && !winner && 'text-emerald-400'
                  )}
                >
                  {teamAScore}
                </div>

                {/* VS */}
                <div className="text-5xl lg:text-6xl font-black text-white/30">:</div>

                {/* Team B Score */}
                <div
                  className={cn(
                    'text-[10rem] lg:text-[14rem] xl:text-[16rem] font-black leading-none tabular-nums',
                    winner === 'B' ? 'text-amber-400' : 'text-white',
                    teamBScore > teamAScore && !winner && 'text-emerald-400'
                  )}
                >
                  {teamBScore}
                </div>
              </div>
            </div>

            {/* Team B */}
            <div
              className={cn(
                'flex-1 flex flex-col items-center',
                winner === 'B' && 'scale-105'
              )}
            >
              <div
                className={cn(
                  'w-48 h-48 lg:w-64 lg:h-64 rounded-3xl bg-gradient-to-br flex items-center justify-center mb-6 shadow-2xl',
                  winner === 'B' ? tvColors.winner : tvColors.teamB
                )}
              >
                <span className="text-7xl lg:text-8xl font-black text-white">B</span>
              </div>

              {/* Players */}
              <div className="flex flex-col items-center gap-3">
                {teamBPlayers.map((player, idx) => (
                  <div key={idx} className="text-center">
                    <p className="text-3xl lg:text-4xl font-bold text-white">
                      {player?.display_name || player?.full_name}
                    </p>
                    {player?.rating && (
                      <p className="text-xl text-white/60 mt-1">Rating: {player.rating}</p>
                    )}
                  </div>
                ))}
              </div>

              {winner === 'B' && (
                <div className="mt-6 px-8 py-3 bg-amber-400 rounded-2xl">
                  <span className="text-2xl font-black text-amber-950 flex items-center gap-2">
                    <Trophy className="w-8 h-8" />
                    WINNER
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="px-8 py-6 border-t border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-8 text-white/60">
          {match.started_at && (
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              <span className="text-lg">เริ่ม {new Date(match.started_at).toLocaleTimeString('th-TH')}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            <span className="text-lg">{teamAPlayers.length + teamBPlayers.length} ผู้เล่น</span>
          </div>
        </div>

        <div className="text-white/40 text-lg">
          Tofu Badminton Club Management System
        </div>
      </div>
    </div>
  );
}

// TV Mode Selector - for selecting which match to display
function TVSelector({ onSelect }: { onSelect: (matchId: string) => void }) {
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch ongoing and scheduled matches
    const fetchMatches = async () => {
      try {
        // This would be replaced with actual API call
        // const data = await apiClient.getActiveMatches();
        setMatches([]);
      } catch (error) {
        console.error('Failed to fetch matches:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-8">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-black text-white mb-4">TV Mode</h1>
          <p className="text-xl text-white/60">เลือกแมทช์ที่ต้องการแสดงบนจอ</p>
        </div>

        {loading ? (
          <div className="text-center text-white/60">กำลังโหลด...</div>
        ) : matches.length === 0 ? (
          <div className="text-center">
            <p className="text-white/60 mb-6">ไม่พบแมทช์ที่กำลังแข่งขัน</p>
            <p className="text-white/40 text-sm">
              คุณสามารถเข้าดูแมทช์โดยตรงได้โดยเพิ่ม ?match=match_id ที่ท้าย URL
            </p>
          </div>
        ) : (
          <div className="grid gap-4">
            {matches.map((match) => (
              <button
                key={match.id}
                onClick={() => onSelect(match.id)}
                className="p-6 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-left transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-white">คอร์ท {match.court_number}</p>
                    <p className="text-white/60 mt-1">{match.status}</p>
                  </div>
                  <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center">
                    <Trophy className="w-6 h-6 text-white" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Main TV Page Component
export default function TVPage() {
  return (
    <Suspense fallback={
      <div className="h-screen w-screen bg-slate-900 flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <TVPageInner />
    </Suspense>
  );
}

function TVPageInner() {
  const searchParams = useSearchParams();
  const matchId = searchParams.get('match');
  
  const [match, setMatch] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-refresh interval
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    if (!matchId) {
      setLoading(false);
      return;
    }

    const fetchMatch = async () => {
      try {
        const data = await apiClient.getMatch(matchId);
        setMatch(data);
        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        setError('ไม่สามารถโหลดข้อมูลแมทช์ได้');
      } finally {
        setLoading(false);
      }
    };

    fetchMatch();

    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchMatch, 5000);
    return () => clearInterval(interval);
  }, [matchId]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  if (!matchId) {
    return <TVSelector onSelect={(id) => window.location.href = `/tv?match=${id}`} />;
  }

  if (loading) {
    return (
      <div className="h-screen w-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/60 text-xl">กำลังโหลด...</p>
        </div>
      </div>
    );
  }

  if (error || !match) {
    return (
      <div className="h-screen w-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-2xl mb-4">{error || 'ไม่พบแมทช์'}</p>
          <button
            onClick={() => window.location.href = '/tv'}
            className="px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl font-semibold transition-colors"
          >
            กลับไปเลือกแมทช์
          </button>
        </div>
      </div>
    );
  }

  return <TVMatchDisplay match={match} isFullscreen={isFullscreen} onToggleFullscreen={toggleFullscreen} />;
}