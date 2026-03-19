/**
 * 섹션 네비게이션 컴포넌트
 */

'use client';

import { useState, useEffect } from 'react';
import type { ProposalSection, SectionKey } from '@/types/proposal';
import { SECTION_LABELS } from '@/types/proposal';

interface SectionNavigationProps {
  sections: ProposalSection[];
}

export function SectionNavigation({ sections }: SectionNavigationProps) {
  const [activeSection, setActiveSection] = useState<SectionKey | null>(null);

  // 현재 보이는 섹션 감지
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const sectionId = entry.target.id;
            const sectionKey = sectionId.replace('section-', '') as SectionKey;
            setActiveSection(sectionKey);
          }
        });
      },
      { threshold: 0.3 }
    );

    sections.forEach((section) => {
      const element = document.getElementById(`section-${section.sectionKey}`);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [sections]);

  const handleClick = (sectionKey: SectionKey) => {
    const element = document.getElementById(`section-${sectionKey}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="space-y-1">
      <h3 className="px-2 py-1 text-xs font-semibold text-neutral-400 uppercase tracking-wider">
        섹션
      </h3>
      {sections
        .sort((a, b) => a.order - b.order)
        .map((section) => (
          <button
            key={section.sectionKey}
            onClick={() => handleClick(section.sectionKey)}
            className={`w-full text-left px-2 py-1.5 rounded-md text-sm transition-colors ${
              activeSection === section.sectionKey
                ? 'bg-primary-50 text-primary-700 font-medium'
                : 'text-neutral-600 hover:bg-neutral-100'
            }`}
          >
            {section.order}. {section.title}
          </button>
        ))}
    </div>
  );
}
