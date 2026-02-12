'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface Toast {
  id: string;
  title: string;
  message?: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

interface ToastContextType {
  toasts: Toast[];
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  addToast: (message: string, type?: Toast['type']) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const createToast = useCallback((title: string, message: string | undefined, type: Toast['type']) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const success = useCallback((title: string, message?: string) => createToast(title, message, 'success'), [createToast]);
  const error = useCallback((title: string, message?: string) => createToast(title, message, 'error'), [createToast]);
  const info = useCallback((title: string, message?: string) => createToast(title, message, 'info'), [createToast]);
  const warning = useCallback((title: string, message?: string) => createToast(title, message, 'warning'), [createToast]);
  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => createToast(message, undefined, type), [createToast]);

  const typeStyles: Record<Toast['type'], string> = {
    success: 'bg-emerald-500/90 border-emerald-400',
    error: 'bg-red-500/90 border-red-400',
    info: 'bg-blue-500/90 border-blue-400',
    warning: 'bg-amber-500/90 border-amber-400',
  };

  const icons: Record<Toast['type'], string> = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
    warning: '⚠',
  };

  return (
    <ToastContext.Provider value={{ toasts, success, error, info, warning, addToast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-xl px-4 py-3 shadow-2xl backdrop-blur-md text-white border cursor-pointer transition-all duration-300 animate-slide-up ${typeStyles[toast.type]}`}
            onClick={() => removeToast(toast.id)}
          >
            <div className="flex items-start gap-2">
              <span className="text-lg leading-none mt-0.5">{icons[toast.type]}</span>
              <div>
                <p className="font-semibold text-sm">{toast.title}</p>
                {toast.message && <p className="text-xs opacity-90 mt-0.5">{toast.message}</p>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
