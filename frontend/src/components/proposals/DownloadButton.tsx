/**
 * 다운로드 버튼 컴포넌트
 */

'use client';

import { useState } from 'react';
import { proposalApi } from '@/lib/api/proposal';
import type { DownloadFormat } from '@/types/proposal';
import { toast } from '@/components/ui/Toast';

interface DownloadButtonProps {
  proposalId: string;
  format: DownloadFormat;
  label: string;
  onComplete?: () => void;
}

export function DownloadButton({ proposalId, format, label, onComplete }: DownloadButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleDownload = async () => {
    setIsLoading(true);
    try {
      const result = await proposalApi.download(proposalId, format);

      // 파일 다운로드
      const url = URL.createObjectURL(result.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(`${format.toUpperCase()} 파일 다운로드가 완료되었습니다.`);
      onComplete?.();
    } catch (error) {
      console.error('다운로드 실패:', error);
      toast.error(error instanceof Error ? error.message : '다운로드에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleDownload}
      disabled={isLoading}
      className="w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
    >
      {isLoading ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          <span>변환 중...</span>
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {label}
        </>
      )}
    </button>
  );
}
