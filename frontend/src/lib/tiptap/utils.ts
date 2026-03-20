/**
 * F-05 제안서 편집기 - TipTap 유틸리티 함수
 */

/**
 * HTML에서 텍스트만 추출 (HTML 태그 제거)
 */
export function extractTextFromHtml(html: string): string {
  if (!html) return '';

  // DOMParser 사용 (서버 사이드 렌더링 시에도 동작)
  if (typeof window !== 'undefined') {
    const div = document.createElement('div');
    div.innerHTML = html;

    // script와 style 태그 제거
    const scripts = div.querySelectorAll('script, style');
    scripts.forEach((script) => script.remove());

    return div.textContent || '';
  }

  // 서버 사이드: 간단한 태그 제거 (정규식)
  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .trim();
}

/**
 * 한글과 영어가 섞인 텍스트의 단어 수 계산
 * 한글: 글자 수 (자소 분리 없음)
 * 영어: 단어 수 (공백 기준)
 */
export function countWords(text: string): number {
  if (!text) return 0;

  const trimmedText = text.trim();
  if (!trimmedText) return 0;

  let count = 0;

  // 한글 문자 수 (자음/모음 제외, 완성된 한글만)
  const koreanChars = trimmedText.match(/[\uAC00-\uD7AF\u3131-\u3163]/g);
  if (koreanChars) {
    count += koreanChars.length;
  }

  // 영어 단어 수 (연속된 알파벳을 단어로 간주)
  const englishWords = trimmedText.match(/[a-zA-Z]+/g);
  if (englishWords) {
    count += englishWords.length;
  }

  // 숫자 및 기호 (하나씩 카운트)
  const otherChars = trimmedText.match(/[0-9\p{P}\p{S}]/gu);
  if (otherChars) {
    count += otherChars.length;
  }

  return count;
}

/**
 * HTML에서 단어 수 계산
 */
export function countWordsFromHtml(html: string): number {
  const text = extractTextFromHtml(html);
  return countWords(text);
}

/**
 * 페이지 수 추정 (단어 수 기준)
 * 1페이지 ≈ 250단어 (A4 기준)
 */
export function estimatePages(wordCount: number, wordsPerPage: number = 250): number {
  return Math.ceil(wordCount / wordsPerPage);
}

/**
 * HTML에서 이미지 URL 추출
 */
export function extractImageUrls(html: string): string[] {
  if (!html) return [];

  const imgRegex = /<img[^>]+src=["']([^"']+)["'][^>]*>/gi;
  const urls: string[] = [];
  let match;

  while ((match = imgRegex.exec(html)) !== null) {
    urls.push(match[1]);
  }

  return urls;
}

/**
 * Markdown을 HTML로 변환 (간단한 변환)
 * TipTap의 Markdown 확장이 설치되지 않은 경우 사용
 */
export function simpleMarkdownToHtml(markdown: string): string {
  if (!markdown) return '';

  return markdown
    // 제목
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // 굵은 글씨
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    // 기울임꼴
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    // 취소선
    .replace(/~~(.*)~~/gim, '<s>$1</s>')
    // 코드
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    // 링크
    .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    // 줄바꿈
    .replace(/\n/gim, '<br />');
}

/**
 * HTML에서 Markdown으로 변환 (간단한 변환)
 */
export function simpleHtmlToMarkdown(html: string): string {
  if (!html) return '';

  return html
    // 제목
    .replace(/<h3>(.*?)<\/h3>/gim, '### $1\n\n')
    .replace(/<h2>(.*?)<\/h2>/gim, '## $1\n\n')
    .replace(/<h1>(.*?)<\/h1>/gim, '# $1\n\n')
    // 굵은 글씨
    .replace(/<strong>(.*?)<\/strong>/gim, '**$1**')
    .replace(/<b>(.*?)<\/b>/gim, '**$1**')
    // 기울임꼴
    .replace(/<em>(.*?)<\/em>/gim, '*$1*')
    .replace(/<i>(.*?)<\/i>/gim, '*$1*')
    // 취소선
    .replace(/<s>(.*?)<\/s>/gim, '~~$1~~')
    // 코드
    .replace(/<code>(.*?)<\/code>/gim, '`$1`')
    // 링크
    .replace(/<a href="(.*?)"[^>]*>(.*?)<\/a>/gim, '[$2]($1)')
    // 줄바꿈
    .replace(/<br\s*\/?>/gim, '\n')
    .replace(/<\/p>/gim, '\n\n')
    // 나머지 태그 제거
    .replace(/<[^>]+>/gim, '')
    .trim();
}
