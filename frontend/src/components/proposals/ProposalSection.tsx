/**
 * 제안서 섹션 컴포넌트
 */

'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ProposalSection } from '@/types/proposal';
import { RegenerateModal } from './RegenerateModal';

interface ProposalSectionProps {
  section: ProposalSection;
  proposalId: string;
  onRegenerate?: (sectionKey: string) => void;
}

export function ProposalSection({ section, proposalId, onRegenerate }: ProposalSectionProps) {
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);

  const handleRegenerateClick = () => {
    setShowRegenerateModal(true);
  };

  return (
    <div id={`section-${section.sectionKey}`} className="scroll-mt-8">
      {/* 섹션 헤더 */}
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-xl font-bold text-neutral-900">
          {section.order}. {section.title}
        </h2>
        <button
          onClick={handleRegenerateClick}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
          title="AI 재생성"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          재생성
        </button>
      </div>

      {/* 섹션 내용 (마크다운 렌더링) */}
      <div className="bg-white border border-neutral-200 rounded-lg p-6 prose prose-sm max-w-none">
        {section.content ? (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              // 링크 스타일링
              a: ({ href, children, ...props }) => (
                <a {...props} href={href} className="text-primary-600 hover:text-primary-700 underline" target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
              // 코드 블록 스타일링
              pre: ({ children, ...props }) => (
                <pre {...props} className="bg-neutral-100 p-4 rounded-md overflow-x-auto">
                  {children}
                </pre>
              ),
              // 인라인 코드 스타일링
              code: ({ className, ...props }) => {
                // className이 없으면 인라인 코드, 있으면 코드 블록
                const isInline = !className;
                return isInline ? (
                  <code {...props} className="bg-neutral-100 px-1.5 py-0.5 rounded text-sm" />
                ) : (
                  <code {...props} className={className} />
                );
              },
            }}
          >
            {section.content}
          </ReactMarkdown>
        ) : (
          <p className="text-neutral-500 italic">내용이 없습니다.</p>
        )}
      </div>

      {/* 섹션 메타 정보 */}
      <div className="flex items-center gap-4 mt-3 text-xs text-neutral-400">
        {section.isAiGenerated && (
          <span className="flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            AI 생성됨
          </span>
        )}
        <span>{section.wordCount.toLocaleString()}자</span>
        <span>{new Date(section.updatedAt).toLocaleString('ko-KR')}</span>
      </div>

      {/* 재생성 모달 */}
      <RegenerateModal
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        proposalId={proposalId}
        sectionKey={section.sectionKey}
        sectionTitle={section.title}
        onComplete={(updatedSection) => {
          setShowRegenerateModal(false);
          onRegenerate?.(section.sectionKey);
        }}
      />
    </div>
  );
}
