/**
 * F-05 제안서 편집기 - 섹션 에디터 컴포넌트
 */

'use client';

import { useState, useCallback } from 'react';
import { TipTapEditor } from './TipTapEditor';
import { AutoSaveIndicator } from './AutoSaveIndicator';
import { useWordCount } from '../hooks/useWordCount';
import { useAutoSave } from '../hooks/useAutoSave';
import { proposalApi } from '@/lib/api/proposal';
import type { ProposalSection } from '@/types/proposal';

interface SectionEditorProps {
  /** 섹션 데이터 */
  section: ProposalSection;
  /** 제안서 ID */
  proposalId: string;
  /** 에디터 모드 */
  mode?: 'view' | 'edit';
  /** 섹션 ID (스크롤용) */
  sectionId?: string;
}

/**
 * 개별 섹션 편집기
 */
export function SectionEditor({
  section,
  proposalId,
  mode = 'edit',
  sectionId,
}: SectionEditorProps) {
  const [content, setContent] = useState(section.content || '');
  const [isEditing, setIsEditing] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  const wordCount = useWordCount(content);

  // 자동 저장 훅
  const autoSave = useAutoSave({
    debounceMs: 30000,
    onSave: async () => {
      await proposalApi.autoSave(proposalId, {
        sections: [
          {
            sectionKey: section.sectionKey,
            content,
            wordCount,
          },
        ],
      });
      setLastSavedAt(new Date());
    },
  });

  // 콘텐츠 변경 핸들러
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    setIsEditing(true);
    autoSave.triggerSave();
  }, [autoSave]);

  const isViewMode = mode === 'view';

  return (
    <section
      id={sectionId}
      data-section-key={section.sectionKey}
      className="bg-white border border-neutral-200 rounded-lg overflow-hidden"
    >
      {/* 섹션 헤더 */}
      <div className="px-6 py-4 bg-neutral-50 border-b border-neutral-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-neutral-900">{section.title}</h2>
          <div className="flex items-center gap-4 text-sm text-neutral-600">
            <span>{wordCount.toLocaleString()}자</span>
            {section.isAiGenerated && (
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-secondary-100 text-secondary-700 text-xs rounded">
                <span className="w-2 h-2 bg-secondary-500 rounded-full"></span>
                AI 생성
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 자동 저장 인디케이터 */}
      {isViewMode ? (
        <AutoSaveIndicator lastSavedAt={lastSavedAt} />
      ) : (
        <AutoSaveIndicator
          isEditing={isEditing}
          onSave={async () => {
            await autoSave.triggerSave();
          }}
          lastSavedAt={lastSavedAt}
        />
      )}

      {/* 에디터 */}
      <div className="px-6 py-4">
        <TipTapEditor
          content={content}
          onChange={handleContentChange}
          placeholder={`${section.title} 내용을 입력하세요...`}
          readOnly={isViewMode}
        />
      </div>
    </section>
  );
}
