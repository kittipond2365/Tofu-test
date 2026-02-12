'use client';

import Link from 'next/link';
import { Users, MapPin, ChevronRight, Crown, Shield, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ClubResponse } from '@/lib/types';

interface ClubCardProps {
  club: ClubResponse;
  view?: 'grid' | 'list';
}

// Generate a gradient based on club name
function getClubGradient(name: string): string {
  const gradients = [
    'from-emerald-500 to-teal-600',
    'from-blue-500 to-indigo-600',
    'from-violet-500 to-purple-600',
    'from-amber-500 to-orange-600',
    'from-rose-500 to-pink-600',
    'from-cyan-500 to-blue-600',
  ];
  const index = name.charCodeAt(0) % gradients.length;
  return gradients[index];
}

// Get first letter for avatar
function getInitials(name: string): string {
  return name.charAt(0).toUpperCase();
}

export function ClubCard({ club, view = 'grid' }: ClubCardProps) {
  const gradient = getClubGradient(club.name);
  const isFull = club.member_count >= club.max_members;

  if (view === 'list') {
    return (
      <Link
        href={`/clubs/${club.id}`}
        className="glass-card p-4 flex items-center gap-4 group hover:border-emerald-200/50 transition-all duration-300"
      >
        {/* Avatar */}
        <div
          className={cn(
            'w-14 h-14 rounded-xl bg-gradient-to-br flex items-center justify-center text-xl font-bold text-white flex-shrink-0',
            gradient
          )}
        >
          {getInitials(club.name)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-bold text-neutral-900 group-hover:text-emerald-600 transition-colors truncate">
              {club.name}
            </h3>
            <span
              className={cn(
                'badge flex-shrink-0',
                isFull ? 'badge-rose' : 'badge-emerald'
              )}
            >
              {isFull ? 'เต็ม' : 'รับสมาชิก'}
            </span>
          </div>
          <p className="text-sm text-neutral-500 truncate">@{club.slug}</p>
          <div className="flex items-center gap-4 mt-1.5 text-sm text-neutral-400">
            <span className="flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {club.member_count}/{club.max_members}
            </span>
            {club.location && (
              <span className="flex items-center gap-1 truncate">
                <MapPin className="w-3.5 h-3.5" />
                {club.location}
              </span>
            )}
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight className="w-5 h-5 text-neutral-300 group-hover:text-emerald-500 group-hover:translate-x-1 transition-all" />
      </Link>
    );
  }

  // Grid view
  return (
    <Link href={`/clubs/${club.id}`} className="block group">
      <div className="glass-card overflow-hidden h-full transition-all duration-300 hover:-translate-y-1 hover:border-emerald-200/50">
        {/* Banner with gradient */}
        <div className={cn('h-24 bg-gradient-to-r relative', gradient)}>
          <div className="absolute inset-0 bg-black/10" />
          <div className="absolute -bottom-6 left-5">
            <div className="w-16 h-16 rounded-2xl bg-white shadow-lg flex items-center justify-center text-2xl font-bold text-neutral-700 border-4 border-white">
              {getInitials(club.name)}
            </div>
          </div>
          <div className="absolute top-4 right-4">
            <span className={cn('badge', isFull ? 'badge-rose' : 'badge-emerald')}>
              {isFull ? 'เต็ม' : 'รับสมาชิก'}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="pt-8 pb-5 px-5">
          {/* Header */}
          <div className="mb-3">
            <h3 className="text-lg font-bold text-neutral-900 group-hover:text-emerald-600 transition-colors line-clamp-1">
              {club.name}
            </h3>
            <p className="text-sm text-neutral-400">@{club.slug}</p>
          </div>

          {/* Description */}
          <p className="text-neutral-600 mb-4 line-clamp-2 text-sm min-h-[40px]">
            {club.description || 'ไม่มีคำอธิบาย'}
          </p>

          {/* Stats */}
          <div className="flex items-center gap-4 mb-4 text-sm text-neutral-500">
            <div className="flex items-center gap-1.5 bg-neutral-50 px-2.5 py-1 rounded-lg">
              <Users className="w-4 h-4 text-emerald-500" />
              <span className="font-medium text-neutral-700">{club.member_count}</span>
              <span className="text-neutral-400">/{club.max_members}</span>
            </div>
            {club.location && (
              <div className="flex items-center gap-1.5 text-neutral-500 truncate">
                <MapPin className="w-4 h-4 flex-shrink-0" />
                <span className="truncate max-w-[100px]">{club.location}</span>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-neutral-100">
            <div className="text-xs text-neutral-400">
              สร้างเมื่อ{' '}
              {new Date(club.created_at).toLocaleDateString('th-TH', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </div>

            <span className="flex items-center gap-1 text-sm font-medium text-emerald-600 group-hover:text-emerald-700">
              เข้าชม
              <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}

// Member badge component
export function MemberBadge({ role }: { role: string }) {
  const configs = {
    admin: {
      icon: Crown,
      className: 'bg-purple-100 text-purple-700 border-purple-200',
      label: 'แอดมิน',
    },
    organizer: {
      icon: Shield,
      className: 'bg-blue-100 text-blue-700 border-blue-200',
      label: 'ผู้จัด',
    },
    member: {
      icon: User,
      className: 'bg-neutral-100 text-neutral-700 border-neutral-200',
      label: 'สมาชิก',
    },
  };

  const config = configs[role as keyof typeof configs] || configs.member;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border',
        config.className
      )}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}