'use client';

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'default' | 'circle' | 'text' | 'card' | 'avatar';
  width?: string | number;
  height?: string | number;
  shimmer?: boolean;
}

export function Skeleton({
  className,
  variant = 'default',
  width,
  height,
  shimmer = true,
}: SkeletonProps) {
  const baseStyles = 'bg-neutral-200';
  const shimmerStyles = shimmer && 'skeleton-shimmer';

  const variantStyles = {
    default: 'rounded-lg',
    circle: 'rounded-full',
    text: 'rounded h-4',
    card: 'rounded-2xl',
    avatar: 'rounded-full',
  };

  const dimensions = {
    width: width ? (typeof width === 'number' ? `${width}px` : width) : undefined,
    height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined,
  };

  return (
    <div
      className={cn(baseStyles, shimmerStyles, variantStyles[variant], className)}
      style={dimensions}
    />
  );
}

// Pre-built skeleton components
export function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card p-5 space-y-4', className)}>
      <div className="flex items-center gap-4">
        <Skeleton variant="circle" width={48} height={48} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="text" width="100%" />
      <Skeleton variant="text" width="80%" />
    </div>
  );
}

export function ClubCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card overflow-hidden', className)}>
      <Skeleton variant="default" width="100%" height={96} />
      <div className="p-5 space-y-3">
        <div className="flex items-start gap-3">
          <div className="-mt-8">
            <Skeleton variant="circle" width={64} height={64} />
          </div>
          <div className="flex-1 space-y-2 pt-2">
            <Skeleton variant="text" width="70%" />
            <Skeleton variant="text" width="40%" />
          </div>
        </div>
        <Skeleton variant="text" width="100%" />
        <div className="flex gap-2 pt-2">
          <Skeleton variant="text" width={80} />
          <Skeleton variant="text" width={60} />
        </div>
      </div>
    </div>
  );
}

export function SessionCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card p-5', className)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-3">
            <Skeleton variant="text" width={120} />
            <Skeleton variant="text" width={60} />
          </div>
          <Skeleton variant="text" width="80%" />
          <div className="flex gap-4">
            <Skeleton variant="text" width={100} />
            <Skeleton variant="text" width={80} />
          </div>
        </div>
        <Skeleton variant="circle" width={48} height={48} />
      </div>
    </div>
  );
}

export function MatchCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card p-5', className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Skeleton variant="circle" width={40} height={40} />
          <Skeleton variant="text" width={80} />
        </div>
        <Skeleton variant="text" width={60} />
      </div>
      <div className="flex items-center gap-4">
        <div className="flex-1 space-y-2">
          <Skeleton variant="circle" width={40} height={40} className="mx-auto" />
          <Skeleton variant="text" width="80%" className="mx-auto" />
        </div>
        <Skeleton variant="text" width={40} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="circle" width={40} height={40} className="mx-auto" />
          <Skeleton variant="text" width="80%" className="mx-auto" />
        </div>
      </div>
    </div>
  );
}

export function PageSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Header skeleton */}
      <div className="space-y-3">
        <Skeleton variant="text" width={200} height={32} />
        <Skeleton variant="text" width={300} />
      </div>
      
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
        <CardSkeleton />
      </div>
      
      {/* Content */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    </div>
  );
}

export function StatsCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('glass-card p-5', className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton variant="text" width={80} />
          <Skeleton variant="text" width={60} height={32} />
          <Skeleton variant="text" width={100} />
        </div>
        <Skeleton variant="circle" width={48} height={48} />
      </div>
    </div>
  );
}

export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex items-center gap-4 py-4">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === 0 ? '40px' : `${60 + Math.random() * 40}%`}
          className="flex-1"
        />
      ))}
    </div>
  );
}