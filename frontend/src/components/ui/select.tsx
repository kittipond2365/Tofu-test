'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import { ChevronDown, Check } from 'lucide-react';
import { forwardRef, useState } from 'react';

const selectVariants = cva(
  'w-full px-4 min-h-[48px] rounded-xl border bg-white text-neutral-900 appearance-none cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:bg-neutral-50 disabled:text-neutral-400',
  {
    variants: {
      variant: {
        default: 'border-neutral-200 focus:border-emerald-500',
        glass: 'bg-white/60 backdrop-blur-sm border-white/50 focus:bg-white/80 focus:border-emerald-500',
        error: 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'>,
    VariantProps<typeof selectVariants> {
  options: SelectOption[];
  label?: string;
  errorMessage?: string;
  helpText?: string;
  placeholder?: string;
  leftIcon?: React.ReactNode;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      variant,
      options,
      label,
      errorMessage,
      helpText,
      placeholder,
      leftIcon,
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
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
          <select
            id={selectId}
            ref={ref}
            className={cn(
              selectVariants({ variant: errorMessage ? 'error' : variant }),
              leftIcon && 'pl-12',
              'pr-12',
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          <div className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
            <ChevronDown className="w-5 h-5" />
          </div>
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

Select.displayName = 'Select';

export { selectVariants };