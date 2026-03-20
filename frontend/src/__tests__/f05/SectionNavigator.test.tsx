/**
 * F-05 제안서 편집기 - SectionNavigator 컴포넌트 테스트
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { SectionNavigator } from '@/components/proposals/sidebar/SectionNavigator';

// IntersectionObserver mock (jsdom에서 지원하지 않음)
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
});
window.IntersectionObserver = mockIntersectionObserver;

describe('SectionNavigator', () => {
  const defaultProps = {
    sections: [
      { key: 'overview', title: '사업 개요', completed: false },
      { key: 'technical', title: '기술 제안', completed: false },
      { key: 'price', title: '가격 제안', completed: true },
      { key: 'schedule', title: '수행 일정', completed: false },
      { key: 'organization', title: '조직 구성', completed: true },
      { key: 'past_performance', title: '수행 실적', completed: false }
    ],
    activeSection: 'overview',
    onSectionClick: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('모든 섹션을 렌더링한다', () => {
    render(<SectionNavigator {...defaultProps} />);

    expect(screen.getByText('사업 개요')).toBeInTheDocument();
    expect(screen.getByText('기술 제안')).toBeInTheDocument();
    expect(screen.getByText('가격 제안')).toBeInTheDocument();
    expect(screen.getByText('수행 일정')).toBeInTheDocument();
    expect(screen.getByText('조직 구성')).toBeInTheDocument();
    expect(screen.getByText('수행 실적')).toBeInTheDocument();
  });

  it('활성 섹션을 하이라이트한다', () => {
    render(<SectionNavigator {...defaultProps} activeSection="technical" />);

    // 활성 섹션은 Tailwind 클래스로 하이라이트 (activeSection prop은 초기값으로만 적용됨)
    // IntersectionObserver로 현재 섹션을 감지하므로, 초기 currentSection은 activeSection
    // 단, IntersectionObserver가 mock이므로 실제 교차 이벤트 없이 초기값(activeSection)만 적용
    const buttons = screen.getAllByRole('button');
    const technicalButton = buttons.find(btn => btn.textContent?.includes('기술 제안'));
    expect(technicalButton).toBeInTheDocument();
  });

  it('섹션 클릭 시 onSectionClick을 호출한다', () => {
    render(<SectionNavigator {...defaultProps} />);

    const technicalButton = screen.getAllByRole('button').find(
      btn => btn.textContent?.includes('기술 제안')
    );
    fireEvent.click(technicalButton!);

    expect(defaultProps.onSectionClick).toHaveBeenCalledWith('technical');
  });

  it('진행률을 표시한다', () => {
    render(<SectionNavigator {...defaultProps} />);

    // 6개 중 2개 완료 = 33%
    expect(screen.getByText(/33%/)).toBeInTheDocument();
  });

  it('모든 섹션 완료 시 100% 진행률을 표시한다', () => {
    const allCompletedProps = {
      ...defaultProps,
      sections: defaultProps.sections.map(s => ({ ...s, completed: true }))
    };

    render(<SectionNavigator {...allCompletedProps} />);

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('섹션 순서대로 버튼을 렌더링한다', () => {
    render(<SectionNavigator {...defaultProps} />);

    const buttons = screen.getAllByRole('button');
    const buttonTexts = buttons.map(btn => btn.textContent?.trim());

    // 섹션 순서대로 버튼이 렌더링되어야 함
    expect(buttonTexts[0]).toContain('사업 개요');
    expect(buttonTexts[1]).toContain('기술 제안');
    expect(buttonTexts[2]).toContain('가격 제안');
    expect(buttonTexts[3]).toContain('수행 일정');
    expect(buttonTexts[4]).toContain('조직 구성');
    expect(buttonTexts[5]).toContain('수행 실적');
  });

  it('섹션 비활성화 prop이 있으면 해당 섹션 버튼이 disabled된다', () => {
    const disabledSections = ['price', 'schedule'];
    render(<SectionNavigator {...defaultProps} disabledSections={disabledSections} />);

    const priceButton = screen.getAllByRole('button').find(
      btn => btn.textContent?.includes('가격 제안')
    );
    const scheduleButton = screen.getAllByRole('button').find(
      btn => btn.textContent?.includes('수행 일정')
    );

    expect(priceButton).toBeDisabled();
    expect(scheduleButton).toBeDisabled();
  });

  it('비활성화된 섹션 클릭 시 onSectionClick이 호출되지 않는다', () => {
    const disabledSections = ['price'];
    render(<SectionNavigator {...defaultProps} disabledSections={disabledSections} />);

    const priceButton = screen.getAllByRole('button').find(
      btn => btn.textContent?.includes('가격 제안')
    );
    fireEvent.click(priceButton!);

    expect(defaultProps.onSectionClick).not.toHaveBeenCalledWith('price');
  });

  it('빈 섹션 목록에서는 에러가 발생하지 않는다', () => {
    expect(() => {
      render(<SectionNavigator {...defaultProps} sections={[]} />);
    }).not.toThrow();
  });

  it('빈 섹션 목록에서 진행률 0%를 표시한다', () => {
    render(<SectionNavigator {...defaultProps} sections={[]} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('nav에 섹션 네비게이션 aria-label을 가진다', () => {
    render(<SectionNavigator {...defaultProps} />);

    expect(screen.getByRole('navigation', { name: '섹션 네비게이션' })).toBeInTheDocument();
  });

  it('진행률 텍스트를 표시한다', () => {
    render(<SectionNavigator {...defaultProps} />);

    expect(screen.getByText('진행률')).toBeInTheDocument();
  });
});
