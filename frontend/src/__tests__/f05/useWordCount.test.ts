/**
 * F-05 제안서 편집기 - 단어 수 계산 유틸리티 테스트
 */
import { countWordsFromHtml } from '@/lib/tiptap/utils';

describe('countWordsFromHtml', () => {
  it('빈 콘텐츠에서는 단어 수 0을 반환한다', () => {
    expect(countWordsFromHtml('')).toBe(0);
  });

  it('null 콘텐츠에서는 단어 수 0을 반환한다', () => {
    expect(countWordsFromHtml(null as any)).toBe(0);
  });

  it('HTML 태그를 제외하고 단어 수를 계산한다', () => {
    const htmlContent = '<h1>제목</h1><p>내용입니다.</p>';
    // "제목" 2글자 + "내용입니다" 5글자 + "." 1개 = 8
    expect(countWordsFromHtml(htmlContent)).toBe(8);
  });

  it('한글 글자 수를 정확히 계산한다', () => {
    const koreanText = '<p>안녕하세요 테스트입니다.</p>';
    // "안녕하세요" 5글자 + "테스트입니다" 6글자 = 11글자 + "." 1개(구두점) = 12
    expect(countWordsFromHtml(koreanText)).toBe(12);
  });

  it('영어 단어 수를 정확히 계산한다', () => {
    const englishText = '<p>Hello World This is a test</p>';
    // 6단어
    expect(countWordsFromHtml(englishText)).toBe(6);
  });

  it('한글과 영어가 섞인 콘텐츠의 단어 수를 계산한다', () => {
    const mixedText = '<p>안녕하세요 Hello 테스트 World입니다</p>';
    // 한글: "안녕하세요" 5 + "테스트" 3 + "입니다" 3 = 11
    // 영어: "Hello" 1 + "World" 1 = 2
    // 총: 13
    expect(countWordsFromHtml(mixedText)).toBe(13);
  });

  it('복잡한 HTML 구조에서 단어 수를 계산한다', () => {
    const complexHtml = `
      <div>
        <h1>제목</h1>
        <ul>
          <li>항목 1</li>
          <li>항목 2</li>
          <li>항목 3</li>
        </ul>
        <p>문단 내용입니다.</p>
        <table>
          <tr><td>셀1</td><td>셀2</td></tr>
          <tr><td>셀3</td><td>셀4</td></tr>
        </table>
      </div>
    `;
    // 실제 구현에서 숫자(1,2,3)와 구두점(.)도 카운트됨
    // 제목(2) + 항목(2)*3=6 + 숫자(1,2,3)=3 + 문단(2) + 내용입니다(4) + .(1) + 셀(1)*4=4 + 숫자(1,2,3,4)=4 = 27
    expect(countWordsFromHtml(complexHtml)).toBe(27);
  });

  it('공백과 줄바꿈을 무시한다', () => {
    const whitespaceText = `
      <p>
        테스트
        내용
        입
        니
        다
      </p>
    `;
    // jsdom의 textContent로 추출하면 각 줄이 독립적으로 추출됨
    // "테스트"(3) + "내용"(2) + "입"(1) + "니"(1) + "다"(1) = 8글자
    expect(countWordsFromHtml(whitespaceText)).toBe(8);
  });

  it('script 태그 내용을 무시한다', () => {
    const scriptText = `
      <p>일반 내용입니다</p>
      <script>alert('ignored')</script>
    `;
    // "일반 내용입니다" 7글자만 계산
    expect(countWordsFromHtml(scriptText)).toBe(7);
  });

  it('style 태그 내용을 무시한다', () => {
    const styleText = `
      <p>스타일 테스트</p>
      <style>.class { color: red; }</style>
    `;
    // "스타일 테스트" 6글자만 계산
    expect(countWordsFromHtml(styleText)).toBe(6);
  });

  it('특수 문자와 이모지를 포함한 콘텐츠의 단어 수를 계산한다', () => {
    const specialText = '<p>안녕! 👋 테스트입니다. 🎉</p>';
    // "안녕"(2) + "테스트입니다"(6) = 한글 8
    // "!"(1) + "👋"(1) + "."(1) + "🎉"(1) = 기호/이모지 4 (unicode \p{S} 매칭)
    // 총: 12
    expect(countWordsFromHtml(specialText)).toBe(12);
  });

  it('대용량 콘텐츠의 단어 수를 효율적으로 계산한다', () => {
    const largeContent = Array(1000).fill('<p>테스트 단락입니다.</p>').join('');
    const startTime = performance.now();
    const result = countWordsFromHtml(largeContent);
    const endTime = performance.now();
    const executionTime = endTime - startTime;

    // "테스트 단락입니다." 반복
    // 테스트(3) + 단락입니다(5) + .(1) = 9 per iteration x 1000 = 9000
    expect(result).toBe(9000);
    // 성능 기준: 100ms 이내
    expect(executionTime).toBeLessThan(100);
  });
});
