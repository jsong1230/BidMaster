'use client';

import { useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';

interface SlideOverPanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * 오른쪽에서 슬라이드인 패널 컴포넌트
 * - 모바일: 전체 너비 (100vw)
 * - 태블릿(md): 480px
 * - 데스크톱(lg): 520px
 */
export default function SlideOverPanel({
  isOpen,
  onClose,
  title,
  children,
  footer,
}: SlideOverPanelProps) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (typeof window === 'undefined') return null;

  const panel = (
    <div
      className={`fixed inset-0 z-50 ${isOpen ? 'pointer-events-auto' : 'pointer-events-none'}`}
      aria-modal="true"
      role="dialog"
      aria-label={title}
    >
      {/* 배경 오버레이 */}
      <div
        className={`absolute inset-0 bg-black transition-opacity duration-300 ${
          isOpen ? 'opacity-40' : 'opacity-0'
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* 슬라이드 패널 */}
      <div
        className={`absolute top-0 right-0 h-full w-full md:w-[480px] lg:w-[520px] bg-white shadow-xl flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 flex-shrink-0">
          <h2 className="text-lg font-bold text-neutral-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-md text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
            aria-label="닫기"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 본문 */}
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>

        {/* 푸터 */}
        {footer && (
          <div className="flex-shrink-0 px-6 py-4 border-t border-neutral-200 bg-neutral-50">
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(panel, document.body);
}
