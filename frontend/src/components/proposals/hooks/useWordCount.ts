/**
 * F-05 제안서 편집기 - 단어 수 계산 커스텀 훅
 */

import { useMemo } from 'react';
import { countWordsFromHtml } from '@/lib/tiptap/utils';

/**
 * HTML 콘텐츠의 단어 수 계산 훅
 */
export function useWordCount(htmlContent: string | null): number {
  return useMemo(() => {
    if (!htmlContent) return 0;
    return countWordsFromHtml(htmlContent);
  }, [htmlContent]);
}
