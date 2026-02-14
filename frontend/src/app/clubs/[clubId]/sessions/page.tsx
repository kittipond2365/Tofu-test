'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  Plus,
  Calendar as CalendarIcon,
  List,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Users,
  Clock,
} from 'lucide-react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, addMonths, subMonths, isToday } from 'date-fns';
import { th } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { ProtectedLayout } from '@/components/layout/protected-layout';
import { Navbar } from '@/components/layout/navbar';
import { SessionCard } from '@/components/features/SessionCard';
import { PageHeader, EmptyState, SessionCardSkeleton } from '@/components/shared';
import { Button } from '@/components/ui/button';
import type { SessionResponse, SessionStatus } from '@/lib/types';

type ViewMode = 'list' | 'calendar';
type StatusFilter = 'all' | SessionStatus;

const statusOptions: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'ทั้งหมด' },
  { value: 'open', label: 'เปิดรับ' },
  { value: 'full', label: 'เต็ม' },
  { value: 'ongoing', label: 'กำลังแข่ง' },
  { value: 'completed', label: 'เสร็จสิ้น' },
  { value: 'cancelled', label: 'ยกเลิก' },
];

export default function SessionsPage({ params }: { params: { clubId: string } }) {
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const { data: sessions, isLoading } = useQuery({
    queryKey: ['sessions', params.clubId],
    queryFn: () => apiClient.getSessions(params.clubId),
  });

  const { data: club } = useQuery({
    queryKey: ['club', params.clubId],
    queryFn: () => apiClient.getClub(params.clubId),
  });

  // Filter sessions
  const filteredSessions = useMemo(() => {
    if (!sessions) return [];
    if (statusFilter === 'all') return sessions;
    return sessions.filter((s) => s.status === statusFilter);
  }, [sessions, statusFilter]);

  // Calendar data
  const calendarDays = useMemo(() => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  const getSessionsForDay = (day: Date) => {
    return filteredSessions.filter((s) => isSameDay(new Date(s.start_time), day));
  };

  return (
    <ProtectedLayout>
      <Navbar />

      <main className="page-container">
        {/* Header */}
        <PageHeader
          title="Session"
          subtitle={`Session ทั้งหมดของ ${club?.name || 'ก๊วน'}`}
          breadcrumbs={[
            { label: 'ก๊วน', href: '/clubs' },
            { label: club?.name || '', href: `/clubs/${params.clubId}` },
            { label: 'Session' },
          ]}
          action={
            <Link href={`/clubs/${params.clubId}/sessions/create`}>
              <Button>
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">สร้าง Session</span>
              </Button>
            </Link>
          }
        />

        {/* Filters & View Toggle */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Status Filter */}
          <div className="flex-1 overflow-x-auto">
            <div className="flex gap-2 pb-2">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setStatusFilter(option.value)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-colors',
                    statusFilter === option.value
                      ? 'bg-emerald-500 text-white'
                      : 'bg-white text-neutral-600 hover:bg-neutral-50 border border-neutral-200'
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex gap-2">
            <div className="flex bg-white rounded-xl border border-neutral-200 p-1">
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors',
                  viewMode === 'list'
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'text-neutral-600 hover:text-neutral-900'
                )}
              >
                <List className="w-4 h-4" />
                รายการ
              </button>
              <button
                onClick={() => setViewMode('calendar')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors',
                  viewMode === 'calendar'
                    ? 'bg-emerald-100 text-emerald-600'
                    : 'text-neutral-600 hover:text-neutral-900'
                )}
              >
                <CalendarIcon className="w-4 h-4" />
                ปฏิทิน
              </button>
            </div>
          </div>
        </div>

        {/* Stats */}
        {!isLoading && sessions && (
          <div className="flex items-center gap-4 text-sm text-neutral-500 mb-6">
            <span>
              ทั้งหมด <strong className="text-neutral-900">{filteredSessions.length}</strong> Session
            </span>
            {statusFilter !== 'all' && (
              <span className="text-emerald-600">
                (กรอง: {statusOptions.find((o) => o.value === statusFilter)?.label})
              </span>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="space-y-4">
            <SessionCardSkeleton />
            <SessionCardSkeleton />
            <SessionCardSkeleton />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredSessions.length === 0 && (
          <EmptyState
            icon={CalendarIcon}
            title={statusFilter !== 'all' ? 'ไม่พบ Session' : 'ยังไม่มี Session'}
            description={
              statusFilter !== 'all'
                ? 'ลองเลือกสถานะอื่น หรือสร้าง Session ใหม่'
                : 'สร้าง Session แรกของก๊วน'
            }
            action={{
              label: 'สร้าง Session',
              href: `/clubs/${params.clubId}/sessions/create`,
            }}
          />
        )}

        {/* List View */}
        {!isLoading && viewMode === 'list' && filteredSessions.length > 0 && (
          <div className="space-y-4 stagger-children">
            {filteredSessions.map((session) => (
              <SessionCard key={session.id} session={session} clubId={params.clubId} />
            ))}
          </div>
        )}

        {/* Calendar View */}
        {!isLoading && viewMode === 'calendar' && filteredSessions.length > 0 && (
          <div className="glass-card p-6">
            {/* Calendar Header */}
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-neutral-900">
                {format(currentMonth, 'MMMM yyyy', { locale: th })}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
                  className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setCurrentMonth(new Date())}
                  className="px-4 py-2 text-sm font-medium text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  วันนี้
                </button>
                <button
                  onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
                  className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-1">
              {/* Day Headers */}
              {['อา', 'จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส'].map((day) => (
                <div key={day} className="text-center text-sm font-semibold text-neutral-500 py-2">
                  {day}
                </div>
              ))}

              {/* Calendar Days */}
              {calendarDays.map((day) => {
                const daySessions = getSessionsForDay(day);
                const hasSessions = daySessions.length > 0;
                const isCurrentDay = isToday(day);

                return (
                  <div
                    key={day.toISOString()}
                    className={cn(
                      'min-h-[100px] p-2 border border-neutral-100 rounded-lg transition-colors',
                      isCurrentDay
                        ? 'bg-emerald-50 border-emerald-200'
                        : 'hover:bg-neutral-50'
                    )}
                  >
                    <div
                      className={cn(
                        'text-sm font-semibold mb-1',
                        isCurrentDay ? 'text-emerald-600' : 'text-neutral-700'
                      )}
                    >
                      {format(day, 'd')}
                    </div>
                    <div className="space-y-1">
                      {daySessions.slice(0, 2).map((session) => (
                        <Link
                          key={session.id}
                          href={`/clubs/${params.clubId}/sessions/${session.id}`}
                          className="block text-xs p-1.5 rounded bg-emerald-100 text-emerald-700 truncate hover:bg-emerald-200 transition-colors"
                        >
                          {session.title}
                        </Link>
                      ))}
                      {daySessions.length > 2 && (
                        <div className="text-xs text-neutral-500 text-center">
                          +{daySessions.length - 2} อื่นๆ
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </main>
    </ProtectedLayout>
  );
}