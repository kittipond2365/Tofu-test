'use client';

import { LucideIcon } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    href: string;
  };
  actionButton?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  actionButton,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-12 sm:py-16 px-4',
        className
      )}
    >
      {Icon && (
        <div className="w-20 h-20 rounded-2xl bg-neutral-100 flex items-center justify-center mb-5">
          <Icon className="w-10 h-10 text-neutral-400" />
        </div>
      )}

      <h3 className="text-lg sm:text-xl font-bold text-neutral-900 mb-2">{title}</h3>

      {description && (
        <p className="text-neutral-500 max-w-sm mb-6">{description}</p>
      )}

      {action && (
        <Link href={action.href} className="btn-primary">
          {action.label}
        </Link>
      )}

      {actionButton && <div>{actionButton}</div>}
    </div>
  );
}