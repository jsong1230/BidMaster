/**
 * F-05 제안서 편집기 - 섹션 네비게이터 컴포넌트
 */

'use client';

import { useEffect, useState, useCallback } from 'react';

interface SectionItem {
  key: string;
  title: string;
  completed: boolean;
}

interface SectionNavigatorProps {
  /** 섹션 목록 */
  sections: SectionItem[];
  /** 활성 섹션 키 */
  activeSection?: string;
  /** 섹션 클릭 콜백 */
  onSectionClick?: (key: string) => void;
  /** 비활성화된 섹션 목록 */
  disabledSections?: string[];
}

const CheckCircleIcon = () => (
  <svg className="w-4 h-4 flex-shrink-0 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
);

const CircleIcon = () => (
  <svg className="w-4 h-4 flex-shrink-0 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
  </svg>
);

/**
 * 섹션 네비게이션 컴포넌트
 * 섹션 간 이동을 돕는 사이드바 네비게이션
 */
export function SectionNavigator({
  sections,
  activeSection,
  onSectionClick,
  disabledSections = [],
}: SectionNavigatorProps) {
  const [currentSection, setCurrentSection] = useState<string>(activeSection || '');

  // 스크롤로 현재 섹션 감지
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const sectionKey = entry.target.getAttribute('data-section-key');
            if (sectionKey) {
              setCurrentSection(sectionKey);
            }
          }
        });
      },
      {
        threshold: 0.5,
      }
    );

    // 모든 섹션 요소 감지
    sections.forEach((section) => {
      const element = document.querySelector(`[data-section-key="${section.key}"]`);
      if (element) {
        observer.observe(element);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, [sections]);

  // 섹션 클릭 핸들러
  const handleSectionClick = useCallback(
    (key: string) => {
      if (disabledSections.includes(key) || !onSectionClick) return;

      onSectionClick(key);

      // 해당 섹션으로 스크롤
      const element = document.querySelector(`[data-section-key="${key}"]`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    [disabledSections, onSectionClick]
  );

  const completedCount = sections.filter((s) => s.completed).length;
  const progress = sections.length > 0 ? Math.round((completedCount / sections.length) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* 진행률 */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-neutral-600">진행률</span>
        <span className="font-semibold text-neutral-900">{progress}%</span>
      </div>
      <div className="w-full h-1.5 bg-neutral-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-primary-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 섹션 목록 */}
      <nav className="space-y-1" aria-label="섹션 네비게이션">
        {sections.map((section) => {
          const isActive = currentSection === section.key;
          const isDisabled = disabledSections.includes(section.key);

          return (
            <button
              key={section.key}
              type="button"
              onClick={() => handleSectionClick(section.key)}
              disabled={isDisabled}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-left text-sm transition-colors ${
                isActive
                  ? 'bg-primary-100 text-primary-900 font-medium'
                  : isDisabled
                  ? 'text-neutral-400 cursor-not-allowed'
                  : 'text-neutral-700 hover:bg-neutral-100'
              }`}
            >
              {section.completed ? <CheckCircleIcon /> : <CircleIcon />}
              <span className="truncate">{section.title}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
