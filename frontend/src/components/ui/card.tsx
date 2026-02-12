'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const cardVariants = cva(
  // Base styles
  'relative overflow-hidden transition-all duration-300 ease-smooth',
  {
    variants: {
      variant: {
        default: 'glass-card',
        flat: 'bg-white rounded-2xl border border-neutral-200 shadow-sm',
        dark: 'glass-card-dark',
        interactive: 'card-interactive',
        elevated: 'glass-card shadow-soft-xl',
      },
      padding: {
        none: '',
        sm: 'p-4',
        default: 'p-5 sm:p-6',
        lg: 'p-6 sm:p-8',
        xl: 'p-8 sm:p-10',
      },
      hover: {
        true: 'cursor-pointer',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'default',
      hover: false,
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  as?: keyof JSX.IntrinsicElements;
}

export function Card({
  className,
  variant,
  padding,
  hover,
  children,
  as: Component = 'div',
  ...props
}: CardProps) {
  return (
    <Component
      className={cn(cardVariants({ variant, padding, hover, className }))}
      {...props}
    >
      {children}
    </Component>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('text-lg font-semibold text-neutral-900', className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('text-sm text-neutral-500', className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex items-center gap-3 pt-4 mt-4 border-t border-neutral-100',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export { cardVariants };