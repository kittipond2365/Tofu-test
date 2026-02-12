import { ReactNode } from 'react';
export function Modal({ open, onClose, children }: { open: boolean; onClose: () => void; children: ReactNode }) { if (!open) return null; return <div className="fixed inset-0 z-50 grid place-items-center bg-black/40" onClick={onClose}><div className="w-full max-w-lg rounded-xl bg-white p-4" onClick={(e) => e.stopPropagation()}>{children}</div></div>; }
