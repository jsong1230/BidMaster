/**
 * 공통 포맷 유틸리티
 */

/** 금액 포맷 (억/만원 단위) */
export function formatAmount(amount: number | null | undefined): string {
  if (amount == null) return '-';
  if (amount >= 100_000_000) {
    const eok = amount / 100_000_000;
    return eok % 1 === 0 ? `${eok}억원` : `${eok.toFixed(1)}억원`;
  }
  if (amount >= 10_000) {
    const man = Math.round(amount / 10_000);
    return `${man.toLocaleString()}만원`;
  }
  return `${amount.toLocaleString()}원`;
}

/** 날짜 포맷 (YYYY.MM.DD) */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}.${m}.${d}`;
}

/** D-day 계산 (deadline - today) */
export function getDaysLeft(deadline: string): number {
  const now = new Date();
  const deadlineDate = new Date(deadline);
  const diffMs = deadlineDate.getTime() - now.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}

/** 낙찰률 포맷 (소수점 1자리 %) */
export function formatWinRate(rate: number | null | undefined): string {
  if (rate == null) return '-';
  return `${rate.toFixed(1)}%`;
}

/** 월 포맷 (YYYY-MM -> YYYY.MM) */
export function formatMonth(month: string): string {
  return month.replace('-', '.');
}
