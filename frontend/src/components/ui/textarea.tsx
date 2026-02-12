'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef } from 'react';

const textareaVariants = cva(
  'w-full px-4 py-3 min-h-[120px] rounded-xl border bg-white text-neutral-900 placeholder:text-neutral-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:cursor-not-allowed disabled:bg-neutral-50 disabled:text-neutral-400 resize-y',
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

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof textareaVariants> {
  errorMessage?: string;
  helpText?: string;
  label?: string;
  maxLength?: number;
  showCharacterCount?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      variant,
      errorMessage,
      helpText,
      label,
      id,
      maxLength,
      showCharacterCount,
      value,
      ...props
    },
    ref
  ) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');
    const currentLength = typeof value === 'string' ? value.length : 0;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-neutral-700 mb-2"
          >
            {label}
          </label>
        )}
        <textarea
          id={textareaId}
          ref={ref}
          value={value}
          maxLength={maxLength}
          className={cn(
            textareaVariants({ variant: errorMessage ? 'error' : variant }),
            className
          )}
          {...props}
        />
        <div className="flex items-center justify-between mt-1.5">
          {(errorMessage || helpText) && (
            <p
              className={cn(
                'text-sm',
                errorMessage ? 'text-rose-600' : 'text-neutral-500'
              )}
            >
              {errorMessage || helpText}
            </p>
          )}
          {showCharacterCount && maxLength && (
            <p
              className={cn(
                'text-sm ml-auto',
                currentLength >= maxLength ? 'text-rose-500' : 'text-neutral-400'
              )}
            >
              {currentLength}/{maxLength}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { textareaVariants };