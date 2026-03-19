/**
 * 섹션 선택 컴포넌트
 */

'use client';

import { SECTION_LABELS, type SectionKey } from '@/types/proposal';

interface SectionSelectorProps {
  selected: SectionKey[];
  onChange: (sections: SectionKey[]) => void;
}

const ALL_SECTIONS: SectionKey[] = ['overview', 'technical', 'methodology', 'schedule', 'organization', 'budget'];

export function SectionSelector({ selected, onChange }: SectionSelectorProps) {
  const handleToggle = (sectionKey: SectionKey) => {
    if (selected.includes(sectionKey)) {
      onChange(selected.filter((key) => key !== sectionKey));
    } else {
      onChange([...selected, sectionKey]);
    }
  };

  const handleSelectAll = () => {
    if (selected.length === ALL_SECTIONS.length) {
      onChange([]);
    } else {
      onChange(ALL_SECTIONS);
    }
  };

  const isAllSelected = selected.length === ALL_SECTIONS.length;

  return (
    <div className="space-y-3">
      {/* 전체 선택 */}
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={isAllSelected}
          onChange={handleSelectAll}
          className="w-4 h-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500"
        />
        <span className="text-sm font-medium text-neutral-700">전체 선택</span>
      </label>

      {/* 섹션 목록 */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {ALL_SECTIONS.map((sectionKey) => (
          <label
            key={sectionKey}
            className="flex items-center gap-2 p-3 border border-neutral-200 rounded-md cursor-pointer hover:bg-neutral-50 transition-colors"
          >
            <input
              type="checkbox"
              checked={selected.includes(sectionKey)}
              onChange={() => handleToggle(sectionKey)}
              className="w-4 h-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-neutral-700">{SECTION_LABELS[sectionKey]}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
