/**
 * F-05 제안서 편집기 - EvaluationPanel 컴포넌트 테스트
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EvaluationPanel } from '@/components/proposals/sidebar/EvaluationPanel';

describe('EvaluationPanel', () => {
  const defaultProps = {
    checklist: {
      technical_capability: { checked: false, weight: 30 },
      price_competitiveness: { checked: false, weight: 25 },
      past_performance: { checked: false, weight: 20 },
      project_schedule: { checked: false, weight: 15 },
      organization: { checked: false, weight: 10 }
    },
    onChecklistChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('체크리스트 항목을 렌더링한다', () => {
    render(<EvaluationPanel {...defaultProps} />);

    expect(screen.getByText('기술 역량')).toBeInTheDocument();
    expect(screen.getByText('가격 경쟁력')).toBeInTheDocument();
    expect(screen.getByText('수행 실적')).toBeInTheDocument();
    expect(screen.getByText('프로젝트 일정')).toBeInTheDocument();
    expect(screen.getByText('조직 구성')).toBeInTheDocument();
  });

  it('초기 달성률 0%를 표시한다', () => {
    render(<EvaluationPanel {...defaultProps} />);

    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('체크박스 토글 시 onChecklistChange를 호출한다', async () => {
    render(<EvaluationPanel {...defaultProps} />);

    // label 내부의 checkbox를 텍스트로 가장 가까운 것을 찾아 클릭
    const labels = screen.getAllByRole('checkbox');
    fireEvent.click(labels[0]);

    await waitFor(() => {
      expect(defaultProps.onChecklistChange).toHaveBeenCalled();
    });
  });

  it('전체 체크 시 100% 달성률을 표시한다', () => {
    const fullyCheckedChecklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: true, weight: 25 },
      past_performance: { checked: true, weight: 20 },
      project_schedule: { checked: true, weight: 15 },
      organization: { checked: true, weight: 10 }
    };

    render(<EvaluationPanel {...defaultProps} checklist={fullyCheckedChecklist} />);

    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('부분 체크 시 가중치 기반 달성률을 표시한다', () => {
    const partialChecklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: true, weight: 25 },
      past_performance: { checked: false, weight: 20 },
      project_schedule: { checked: false, weight: 15 },
      organization: { checked: false, weight: 10 }
    };

    render(<EvaluationPanel {...defaultProps} checklist={partialChecklist} />);

    expect(screen.getByText('55%')).toBeInTheDocument();
  });

  it('체크박스 클릭 시 onChecklistChange에 올바른 데이터를 전달한다', async () => {
    render(<EvaluationPanel {...defaultProps} />);

    // 첫 번째 체크박스(technical_capability)를 클릭
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    await waitFor(() => {
      expect(defaultProps.onChecklistChange).toHaveBeenCalledWith(
        expect.objectContaining({
          technical_capability: expect.objectContaining({
            checked: true,
            weight: 30
          })
        })
      );
    });
  });

  it('체크박스 해제 시 onChecklistChange에 올바른 데이터를 전달한다', async () => {
    const checkedChecklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: false, weight: 25 },
      past_performance: { checked: false, weight: 20 },
      project_schedule: { checked: false, weight: 15 },
      organization: { checked: false, weight: 10 }
    };

    render(<EvaluationPanel {...defaultProps} checklist={checkedChecklist} />);

    // 첫 번째 체크박스(technical_capability, checked=true)를 클릭하여 해제
    const checkboxes = screen.getAllByRole('checkbox');
    fireEvent.click(checkboxes[0]);

    await waitFor(() => {
      expect(defaultProps.onChecklistChange).toHaveBeenCalledWith(
        expect.objectContaining({
          technical_capability: expect.objectContaining({
            checked: false,
            weight: 30
          })
        })
      );
    });
  });

  it('달성률 프로그레스 바를 올바르게 렌더링한다', () => {
    const { container } = render(<EvaluationPanel {...defaultProps} />);

    // 프로그레스 바는 일반 div에 style width로 구현됨 (role="progressbar" 없음)
    const progressBarContainer = container.querySelector('.w-full.h-2');
    expect(progressBarContainer).toBeInTheDocument();

    const progressBarFill = progressBarContainer?.querySelector('div');
    expect(progressBarFill).toHaveStyle({ width: '0%' });
  });

  it('달성률에 따른 색상 클래스를 적용한다', () => {
    // 80% 이상: bg-success-500 (초록)
    const highProps = {
      ...defaultProps,
      checklist: { item1: { checked: true, weight: 90 } }
    };
    const { container } = render(<EvaluationPanel {...highProps} />);

    const progressBarContainer = container.querySelector('.w-full.h-2');
    const progressBarFill = progressBarContainer?.querySelector('div');
    expect(progressBarFill).toHaveClass('bg-success-500');
  });

  it('빈 체크리스트에서는 에러가 발생하지 않는다', () => {
    expect(() => {
      render(<EvaluationPanel {...defaultProps} checklist={{}} />);
    }).not.toThrow();
  });

  it('체크박스 비활성화 prop이 있으면 체크박스가 비활성화된다', () => {
    render(<EvaluationPanel {...defaultProps} disabled />);

    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeDisabled();
    });
  });

  it('가중치를 텍스트로 표시한다', () => {
    render(<EvaluationPanel {...defaultProps} />);

    // 각 항목의 가중치 텍스트 확인
    expect(screen.getByText('가중치: 30%')).toBeInTheDocument();
    expect(screen.getByText('가중치: 25%')).toBeInTheDocument();
  });

  it('평가 기준 제목을 표시한다', () => {
    render(<EvaluationPanel {...defaultProps} />);

    expect(screen.getByText('평가 기준 달성률')).toBeInTheDocument();
    expect(screen.getByText('평가 기준')).toBeInTheDocument();
  });
});
