/**
 * DeadlineWidget 컴포넌트 테스트
 */
import { render, screen } from '@testing-library/react';
import { DeadlineWidget } from '@/components/dashboard/DeadlineWidget';
import type { UpcomingDeadline } from '@/types/dashboard';

const mockDeadlines: UpcomingDeadline[] = [
  {
    bidId: 'bid-1',
    title: '정보시스템 고도화 사업',
    deadline: '2026-03-22T17:00:00Z',
    daysLeft: 2,
    trackingStatus: 'participating',
  },
  {
    bidId: 'bid-2',
    title: 'AI 행정 서비스',
    deadline: '2026-03-26T17:00:00Z',
    daysLeft: 6,
    trackingStatus: 'interested',
  },
];

describe('DeadlineWidget', () => {
  it('마감 임박 공고 목록을 렌더링한다', () => {
    render(<DeadlineWidget deadlines={mockDeadlines} />);
    expect(screen.getByText('정보시스템 고도화 사업')).toBeInTheDocument();
    expect(screen.getByText('AI 행정 서비스')).toBeInTheDocument();
  });

  it('D-2는 error 색상 배지를 렌더링한다', () => {
    render(<DeadlineWidget deadlines={mockDeadlines} />);
    const badge = screen.getByText('D-2');
    expect(badge.className).toContain('bg-[#FFEBEE]');
  });

  it('D-6은 warning 색상 배지를 렌더링한다', () => {
    render(<DeadlineWidget deadlines={mockDeadlines} />);
    const badge = screen.getByText('D-6');
    expect(badge.className).toContain('bg-[#FFF8E1]');
  });

  it('빈 배열이면 "마감 임박 공고가 없습니다" 메시지를 렌더링한다', () => {
    render(<DeadlineWidget deadlines={[]} />);
    expect(screen.getByText('마감 임박 공고가 없습니다')).toBeInTheDocument();
  });

  it('isLoading=true 이면 스켈레톤을 렌더링한다', () => {
    const { container } = render(<DeadlineWidget deadlines={[]} isLoading />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('"마감 임박" 헤더를 렌더링한다', () => {
    render(<DeadlineWidget deadlines={mockDeadlines} />);
    expect(screen.getByText('마감 임박')).toBeInTheDocument();
  });

  it('건수를 표시한다', () => {
    render(<DeadlineWidget deadlines={mockDeadlines} />);
    expect(screen.getByText('2건')).toBeInTheDocument();
  });
});
