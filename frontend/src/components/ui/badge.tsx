'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
        secondary: 'bg-neutral-100 text-neutral-700 border border-neutral-200',
        success: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
        warning: 'bg-amber-100 text-amber-700 border border-amber-200',
        danger: 'bg-rose-100 text-rose-700 border border-rose-200',
        info: 'bg-blue-100 text-blue-700 border border-blue-200',
        purple: 'bg-purple-100 text-purple-700 border border-purple-200',
        live: 'badge-live',
        outline: 'border-2 border-current bg-transparent',
        ghost: 'bg-transparent text-neutral-600',
      },
      size: {
        default: 'px-3 py-1 text-xs',
        sm: 'px-2 py-0.5 text-2xs',
        lg: 'px-4 py-1.5 text-sm',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
  dotColor?: string;
}

export function Badge({
  className,
  variant,
  size,
  dot,
  dotColor,
  children,
  ...props
}: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size, className }))} {...props}>
      {dot && (
        <span
          className={cn(
            'w-1.5 h-1.5 rounded-full',
            dotColor || (variant === 'live' ? 'bg-white' : 'bg-current')
          )}
        />
      )}
      {children}
    </span>
  );
}

export { badgeVariants };