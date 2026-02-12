'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef } from 'react';

const inputVariants = cva(
  'w-full px-4 min-h-[48px] rounded-xl border bg-white text-neutral-900 placeholder:text-neutral-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:bg-neutral-50 disabled:text-neutral-400',
  {
    variants: {
      variant: {
        default: 'border-neutral-200 focus:border-emerald-500',
        glass: 'bg-white/60 backdrop-blur-sm border-white/50 focus:bg-white/80 focus:border-emerald-500',
        error: 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20',
        success: 'border-emerald-300 focus:border-emerald-500',
      },
      size: {
        default: 'py-3 text-base',
        sm: 'py-2 text-sm',
        lg: 'py-4 text-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  errorMessage?: string;
  helpText?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      leftIcon,
      rightIcon,
      errorMessage,
      helpText,
      label,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            id={inputId}
            ref={ref}
            className={cn(
              inputVariants({ variant: errorMessage ? 'error' : variant, size }),
              leftIcon && 'pl-12',
              rightIcon && 'pr-12',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400">
              {rightIcon}
            </div>
          )}
        </div>
        {errorMessage && (
          <p className="mt-1.5 text-sm text-rose-600">{errorMessage}</p>
        )}
        {helpText && !errorMessage && (
          <p className="mt-1.5 text-sm text-neutral-500">{helpText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { inputVariants };