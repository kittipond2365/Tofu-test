'use client';

import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  subtitle?: string;
  color?: 'emerald' | 'blue' | 'amber' | 'rose' | 'purple' | 'neutral';
  className?: string;
  onClick?: () => void;
}

const colorVariants = {
  emerald: {
    gradient: 'from-emerald-500 to-teal-500',
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    border: 'border-emerald-100',
  },
  blue: {
    gradient: 'from-blue-500 to-indigo-500',
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-100',
  },
  amber: {
    gradient: 'from-amber-500 to-orange-500',
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-100',
  },
  rose: {
    gradient: 'from-rose-500 to-pink-500',
    bg: 'bg-rose-50',
    text: 'text-rose-600',
    border: 'border-rose-100',
  },
  purple: {
    gradient: 'from-violet-500 to-purple-500',
    bg: 'bg-purple-50',
    text: 'text-purple-600',
    border: 'border-purple-100',
  },
  neutral: {
    gradient: 'from-neutral-500 to-neutral-600',
    bg: 'bg-neutral-50',
    text: 'text-neutral-600',
    border: 'border-neutral-100',
  },
};

export function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  subtitle,
  color = 'emerald',
  className,
  onClick,
}: StatsCardProps) {
  const colors = colorVariants[color];
  const TrendIcon = trend?.isPositive ? TrendingUp : trend?.isPositive === false ? TrendingDown : Minus;
  const trendColor = trend?.isPositive ? 'text-emerald-600' : trend?.isPositive === false ? 'text-rose-600' : 'text-neutral-400';

  return (
    <div
      onClick={onClick}
      className={cn(
        'glass-card p-5 transition-all duration-300',
        onClick && 'cursor-pointer hover:-translate-y-0.5',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-neutral-500 mb-1">{title}</p>
          <h3
            className={cn(
              'text-2xl sm:text-3xl font-bold bg-gradient-to-r bg-clip-text text-transparent truncate',
              colors.gradient
            )}
          >
            {value}
          </h3>

          {/* Trend indicator */}
          {trend && (
            <div className="flex items-center gap-1.5 mt-2">
              <TrendIcon className={cn('w-4 h-4', trendColor)} />
              <span className={cn('text-sm font-semibold', trendColor)}>
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
              <span className="text-xs text-neutral-400">vs เดือนที่แล้ว</span>
            </div>
          )}

          {/* Subtitle */}
          {subtitle && <p className="text-xs text-neutral-400 mt-2">{subtitle}</p>}
        </div>

        {/* Icon */}
        {Icon && (
          <div
            className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ml-4',
              colors.bg,
              colors.text
            )}
          >
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
    </div>
  );
}