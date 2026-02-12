'use client';

interface LoadingSkeletonProps {
  type?: 'card' | 'table' | 'text' | 'avatar' | 'page';
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ type = 'card', count = 1, className = '' }: LoadingSkeletonProps) {
  if (type === 'page') {
    return (
      <div className={`space-y-6 ${className}`}>
        {/* Header skeleton */}
        <div className="space-y-3">
          <div className="h-8 w-1/3 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-4 w-1/2 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        
        {/* Content skeleton */}
        <div className="grid gap-4 md:grid-cols-3">
          <LoadingSkeleton type="card" count={3} />
        </div>
        <div className="h-64 bg-gray-200 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div className={`space-y-4 ${className}`}>
        {/* Search bar */}
        <div className="h-12 bg-gray-200 rounded-xl animate-pulse" />
        
        {/* Table rows */}
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex gap-4 p-4">
            <div className="h-12 w-12 bg-gray-200 rounded-lg animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-1/4 bg-gray-200 rounded animate-pulse" />
              <div className="h-3 w-1/3 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-8 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <>
        {Array.from({ length: count }).map((_, i) => (
          <div 
            key={i} 
            className={`card-modern p-5 space-y-4 ${className}`}
          >
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                <div className="h-8 w-24 bg-gray-200 rounded animate-pulse" />
              </div>
              <div className="h-12 w-12 bg-gray-200 rounded-xl animate-pulse" />
            </div>
          </div>
        ))}
      </>
    );
  }

  if (type === 'text') {
    return (
      <>
        {Array.from({ length: count }).map((_, i) => (
          <div 
            key={i} 
            className={`h-4 bg-gray-200 rounded animate-pulse ${className}`}
            style={{ width: `${Math.random() * 40 + 60}%` }}
          />
        ))}
      </>
    );
  }

  if (type === 'avatar') {
    return (
      <>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className={`flex items-center gap-3 ${className}`}>
            <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
            <div className="space-y-2 flex-1">
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
              <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </>
    );
  }

  return null;
}

// Club card skeleton
export function ClubCardSkeleton() {
  return (
    <div className="card-modern p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="h-6 w-2/3 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-1/3 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="h-6 w-16 bg-gray-200 rounded-full animate-pulse" />
      </div>
      <div className="space-y-2">
        <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex gap-4">
          <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
      </div>
    </div>
  );
}

// Session card skeleton
export function SessionCardSkeleton() {
  return (
    <div className="card-modern p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="h-5 w-3/4 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="h-6 w-20 bg-gray-200 rounded-full animate-pulse" />
      </div>
      <div className="space-y-2">
        <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-2/3 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="h-8 w-24 bg-gray-200 rounded-lg animate-pulse" />
        <div className="h-8 w-20 bg-gray-200 rounded-lg animate-pulse" />
      </div>
    </div>
  );
}

// Chart skeleton
export function ChartSkeleton({ height = 250 }: { height?: number }) {
  return (
    <div className="card-modern p-4">
      <div className="h-6 w-40 bg-gray-200 rounded animate-pulse mb-4" />
      <div 
        className="w-full bg-gray-200 rounded-xl animate-pulse" 
        style={{ height }}
      />
    </div>
  );
}
