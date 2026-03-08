/**
 * 공고 첨부파일 목록 컴포넌트
 */

import type { BidAttachment } from '@/types/bid';

interface BidAttachmentListProps {
  attachments: BidAttachment[];
}

function FileTypeIcon({ fileType }: { fileType: string }) {
  const type = fileType.toUpperCase();

  if (type === 'PDF') {
    return (
      <div className="w-9 h-9 rounded-md bg-[#FFEBEE] flex items-center justify-center flex-shrink-0">
        <span className="text-xs font-bold text-[#C62828]">PDF</span>
      </div>
    );
  }

  if (type === 'HWP') {
    return (
      <div className="w-9 h-9 rounded-md bg-neutral-100 flex items-center justify-center flex-shrink-0">
        <span className="text-xs font-bold text-neutral-500">HWP</span>
      </div>
    );
  }

  return (
    <div className="w-9 h-9 rounded-md bg-blue-50 flex items-center justify-center flex-shrink-0">
      <span className="text-xs font-bold text-blue-600">{type.slice(0, 3)}</span>
    </div>
  );
}

function ParseStatusBadge({ hasExtractedText, fileType }: { hasExtractedText: boolean; fileType: string }) {
  if (hasExtractedText) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[#2E7D32]">
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        텍스트 추출 완료
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-neutral-400">
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      텍스트 추출 불가 ({fileType.toUpperCase()})
    </span>
  );
}

export function BidAttachmentList({ attachments }: BidAttachmentListProps) {
  if (attachments.length === 0) {
    return (
      <p className="text-sm text-neutral-400 py-2">첨부파일이 없습니다.</p>
    );
  }

  return (
    <div className="divide-y divide-neutral-100">
      {attachments.map((attachment) => (
        <div key={attachment.id} className="px-5 py-3.5 flex items-center gap-3">
          <FileTypeIcon fileType={attachment.fileType} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-neutral-800 truncate">{attachment.filename}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <ParseStatusBadge
                hasExtractedText={attachment.hasExtractedText}
                fileType={attachment.fileType}
              />
            </div>
          </div>
          <a
            href={attachment.fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 inline-flex items-center gap-1 text-xs font-medium text-[#486581] hover:text-[#334E68] transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            다운로드
          </a>
        </div>
      ))}
    </div>
  );
}
