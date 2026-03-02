'use client';

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

type ToastType = 'success' | 'error';

interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

// 간단한 전역 토스트 상태
let toastListeners: ((toasts: ToastMessage[]) => void)[] = [];
let toastList: ToastMessage[] = [];

function notify(listeners: typeof toastListeners, list: ToastMessage[]) {
  listeners.forEach((fn) => fn([...list]));
}

export function showToast(message: string, type: ToastType = 'success') {
  const id = Math.random().toString(36).slice(2);
  toastList = [...toastList, { id, type, message }];
  notify(toastListeners, toastList);

  const duration = type === 'success' ? 2000 : 4000;
  setTimeout(() => {
    toastList = toastList.filter((t) => t.id !== id);
    notify(toastListeners, toastList);
  }, duration);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const listener = (list: ToastMessage[]) => setToasts(list);
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== listener);
    };
  }, []);

  if (typeof window === 'undefined' || toasts.length === 0) return null;

  return createPortal(
    <div className="fixed bottom-4 left-4 z-[9999] flex flex-col gap-2" aria-live="polite">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-md text-sm font-medium max-w-sm animate-fade-in-up
            ${
              toast.type === 'success'
                ? 'bg-green-50 border-green-500 text-green-700'
                : 'bg-red-50 border-red-500 text-red-700'
            }`}
        >
          {toast.type === 'success' ? (
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
          <span>{toast.message}</span>
        </div>
      ))}
    </div>,
    document.body
  );
}
