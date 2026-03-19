/**
 * KpiCard 컴포넌트 테스트
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { KpiCard } from '@/components/dashboard/KpiCard';

const mockIcon = <span data-testid="kpi-icon">icon</span>;

describe('KpiCard', () => {
  it('숫자, 라벨을 렌더링한다', () => {
    render(
      <KpiCard
        icon={mockIcon}
        value="12"
        label="이번 달 참여"
        iconBgClass="bg-blue-50"
        iconColorClass="text-blue-500"
      />
    );
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('이번 달 참여')).toBeInTheDocument();
  });

  it('서브텍스트를 렌더링한다', () => {
    render(
      <KpiCard
        icon={mockIcon}
        value="3"
        label="낙찰"
        subText="15억원"
        iconBgClass="bg-green-50"
        iconColorClass="text-green-500"
      />
    );
    expect(screen.getByText('15억원')).toBeInTheDocument();
  });

  it('isLoading=true 이면 스켈레톤을 렌더링한다', () => {
    const { container } = render(
      <KpiCard
        icon={mockIcon}
        value="12"
        label="이번 달 참여"
        iconBgClass="bg-blue-50"
        iconColorClass="text-blue-500"
        isLoading
      />
    );
    // animate-pulse 클래스가 있는 스켈레톤 요소 존재
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
    // 숫자는 없어야 함
    expect(screen.queryByText('12')).not.toBeInTheDocument();
  });

  it('onClick prop 전달 시 클릭 핸들러가 호출된다', () => {
    const handleClick = jest.fn();
    render(
      <KpiCard
        icon={mockIcon}
        value="3"
        label="낙찰"
        iconBgClass="bg-green-50"
        iconColorClass="text-green-500"
        onClick={handleClick}
      />
    );
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('아이콘이 렌더링된다', () => {
    render(
      <KpiCard
        icon={mockIcon}
        value="8"
        label="제출 완료"
        iconBgClass="bg-neutral-50"
        iconColorClass="text-neutral-500"
      />
    );
    expect(screen.getByTestId('kpi-icon')).toBeInTheDocument();
  });
});
