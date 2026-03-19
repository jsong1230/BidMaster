/**
 * 포맷 유틸리티 테스트
 */
import { formatAmount, formatDate, getDaysLeft, formatWinRate, formatMonth } from '@/lib/utils/format';

describe('formatAmount', () => {
  it('억원 단위를 처리한다', () => {
    expect(formatAmount(1_500_000_000)).toBe('15억원');
  });

  it('소수점 있는 억원 단위를 처리한다', () => {
    expect(formatAmount(150_000_000)).toBe('1.5억원');
  });

  it('만원 단위를 처리한다', () => {
    expect(formatAmount(45_000_000)).toBe('4,500만원');
  });

  it('null이면 "-"를 반환한다', () => {
    expect(formatAmount(null)).toBe('-');
  });

  it('undefined이면 "-"를 반환한다', () => {
    expect(formatAmount(undefined)).toBe('-');
  });
});

describe('formatDate', () => {
  it('날짜를 YYYY.MM.DD 형식으로 포맷한다', () => {
    expect(formatDate('2026-03-19T10:00:00Z')).toBe('2026.03.19');
  });

  it('null이면 "-"를 반환한다', () => {
    expect(formatDate(null)).toBe('-');
  });
});

describe('formatWinRate', () => {
  it('낙찰률을 소수점 1자리로 포맷한다', () => {
    expect(formatWinRate(42.86)).toBe('42.9%');
  });

  it('정수 낙찰률을 포맷한다', () => {
    expect(formatWinRate(50)).toBe('50.0%');
  });

  it('null이면 "-"를 반환한다', () => {
    expect(formatWinRate(null)).toBe('-');
  });
});

describe('formatMonth', () => {
  it('YYYY-MM을 YYYY.MM으로 변환한다', () => {
    expect(formatMonth('2026-03')).toBe('2026.03');
  });
});

describe('getDaysLeft', () => {
  it('미래 날짜에 대해 양수를 반환한다', () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 5);
    const daysLeft = getDaysLeft(tomorrow.toISOString());
    expect(daysLeft).toBeGreaterThan(0);
  });

  it('과거 날짜에 대해 음수 또는 0을 반환한다', () => {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const daysLeft = getDaysLeft(yesterday.toISOString());
    expect(daysLeft).toBeLessThanOrEqual(0);
  });
});
