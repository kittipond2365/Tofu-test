'use client';

import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  action?: React.ReactNode;
  className?: string;
  align?: 'left' | 'center';
}

export function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  action,
  className,
  align = 'left',
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'section-header',
        align === 'center' && 'text-center',
        className
      )}
    >
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav
          className={cn(
            'flex items-center gap-2 text-sm text-neutral-500 mb-3',
            align === 'center' && 'justify-center'
          )}
        >
          <Link
            href="/clubs"
            className="flex items-center gap-1 hover:text-emerald-600 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span className="hidden sm:inline">หน้าหลัก</span>
          </Link>
          {breadcrumbs.map((crumb, index) => (
            <span key={index} className="flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-neutral-300" />
              {crumb.href ? (
                <Link
                  href={crumb.href}
                  className="hover:text-emerald-600 transition-colors"
                >
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-neutral-900 font-medium">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}

      {/* Title Row */}
      <div
        className={cn(
          'flex flex-col sm:flex-row sm:items-center gap-4',
          align === 'left' && 'sm:justify-between',
          align === 'center' && 'items-center'
        )}
      >
        <div className={cn(align === 'center' && 'order-1')}>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gradient">
            {title}
          </h1>
          {subtitle && (
            <p className="text-neutral-500 mt-1.5 text-base sm:text-lg">{subtitle}</p>
          )}
        </div>
        {action && (
          <div
            className={cn(
              'flex-shrink-0',
              align === 'center' && 'order-2 mt-2'
            )}
          >
            {action}
          </div>
        )}
      </div>
    </div>
  );
}