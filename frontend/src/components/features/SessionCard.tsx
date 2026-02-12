'use client';

import Link from 'next/link';
import { format, formatDistanceToNow } from 'date-fns';
import { th } from 'date-fns/locale';
import {
  Calendar,
  Clock,
  MapPin,
  Users,
  ChevronRight,
  Trophy,
  CheckCircle,
  XCircle,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { SessionResponse, SessionStatus } from '@/lib/types';

interface SessionCardProps {
  session: SessionResponse;
  clubId: string;
}

const statusConfig: Record<
  SessionStatus,
  {
    label: string;
    className: string;
    icon: typeof CheckCircle;
  }
> = {
  draft: {
    label: 'ร่าง',
    className: 'badge-neutral',
    icon: HelpCircle,
  },
  open: {
    label: 'เปิดรับ',
    className: 'badge-emerald',
    icon: CheckCircle,
  },
  full: {
    label: 'เต็ม',
    className: 'badge-amber',
    icon: Users,
  },
  ongoing: {
    label: 'กำลังแข่ง',
    className: 'badge-live',
    icon: Clock,
  },
  completed: {
    label: 'เสร็จสิ้น',
    className: 'badge-blue',
    icon: Trophy,
  },
  cancelled: {
    label: 'ยกเลิก',
    className: 'badge-rose',
    icon: XCircle,
  },
};

export function SessionCard({ session, clubId }: SessionCardProps) {
  const status = statusConfig[session.status];
  const StatusIcon = status.icon;
  const startDate = new Date(session.start_time);
  const isPast = startDate < new Date();

  return (
    <Link href={`/clubs/${clubId}/sessions/${session.id}`} className="block group">
      <div className="glass-card overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:border-emerald-200/50">
        <div className="p-5">
          <div className="flex items-start justify-between gap-4">
            {/* Date Badge */}
            <div className="flex-shrink-0">
              <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex flex-col items-center justify-center text-white shadow-lg shadow-emerald-500/20">
                <span className="text-xs font-medium opacity-90">
                  {format(startDate, 'MMM', { locale: th })}
                </span>
                <span className="text-2xl font-bold">{format(startDate, 'd')}</span>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2 mb-1">
                <h3 className="font-bold text-neutral-900 group-hover:text-emerald-600 transition-colors line-clamp-1">
                  {session.title}
                </h3>
                <span className={cn('badge flex-shrink-0', status.className)}>
                  <StatusIcon className="w-3 h-3" />
                  {status.label}
                </span>
              </div>

              <p className="text-sm text-neutral-500 mb-3 line-clamp-1">
                {session.description || 'ยังไม่มีรายละเอียด'}
              </p>

              {/* Meta info */}
              <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-400">
                <span className="flex items-center gap-1.5">
                  <Clock className="w-4 h-4" />
                  {format(startDate, 'HH:mm', { locale: th })}
                </span>
                {session.location && (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="w-4 h-4" />
                    {session.location}
                  </span>
                )}
                <span className="flex items-center gap-1.5">
                  <Users className="w-4 h-4" />
                  {session.participant_count || 0} / {session.max_participants || '-'} คน
                </span>
              </div>

              {/* Time ago */}
              <p className="text-xs text-neutral-400 mt-2">
                {formatDistanceToNow(startDate, {
                  addSuffix: true,
                  locale: th,
                })}
              </p>
            </div>

            {/* Arrow */}
            <div className="flex-shrink-0 self-center">
              <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-emerald-500 group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}