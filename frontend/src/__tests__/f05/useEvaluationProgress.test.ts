/**
 * F-05 제안서 편집기 - useEvaluationProgress 커스텀 훅 테스트
 */
import { renderHook, act } from '@testing-library/react';
import { useEvaluationProgress } from '@/components/proposals/hooks/useEvaluationProgress';

describe('useEvaluationProgress', () => {
  it('빈 체크리스트에서는 달성률 0%를 반환한다', () => {
    const { result } = renderHook(() => useEvaluationProgress({}));
    expect(result.current.achievementRate).toBe(0);
  });

  it('null 체크리스트에서는 달성률 0%를 반환한다', () => {
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: null }));
    expect(result.current.achievementRate).toBe(0);
  });

  it('모든 항목 체크 시 달성률 100%를 반환한다', () => {
    const checklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: true, weight: 25 },
      past_performance: { checked: true, weight: 20 },
      project_schedule: { checked: true, weight: 15 },
      organization: { checked: true, weight: 10 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    expect(result.current.achievementRate).toBe(100);
  });

  it('일부 항목 체크 시 가중치 기반 달성률을 계산한다', () => {
    const checklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: true, weight: 25 },
      past_performance: { checked: false, weight: 20 },
      project_schedule: { checked: false, weight: 15 },
      organization: { checked: false, weight: 10 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    // 체크된 가중치: 30 + 25 = 55
    // 전체 가중치: 100
    // 달성률: 55%
    expect(result.current.achievementRate).toBe(55);
  });

  it('모든 항목 미체크 시 달성률 0%를 반환한다', () => {
    const checklist = {
      technical_capability: { checked: false, weight: 30 },
      price_competitiveness: { checked: false, weight: 25 },
      past_performance: { checked: false, weight: 20 },
      project_schedule: { checked: false, weight: 15 },
      organization: { checked: false, weight: 10 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    expect(result.current.achievementRate).toBe(0);
  });

  it('불균형 가중치에서 올바른 달성률을 계산한다', () => {
    const checklist = {
      item1: { checked: true, weight: 50 },
      item2: { checked: false, weight: 30 },
      item3: { checked: true, weight: 20 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    // 체크된 가중치: 50 + 20 = 70
    // 전체 가중치: 100
    // 달성률: 70%
    expect(result.current.achievementRate).toBe(70);
  });

  it('updateChecklist 함수로 체크리스트를 업데이트한다', () => {
    const { result } = renderHook(() => useEvaluationProgress({
      initialChecklist: {
        technical_capability: { checked: false, weight: 30 },
        price_competitiveness: { checked: false, weight: 25 }
      }
    }));

    act(() => {
      result.current.updateChecklist({
        technical_capability: { checked: true, weight: 30 },
        price_competitiveness: { checked: true, weight: 25 }
      });
    });

    expect(result.current.achievementRate).toBe(100);
  });

  it('toggleItem 함수로 개별 항목을 토글한다', () => {
    const { result } = renderHook(() => useEvaluationProgress({
      initialChecklist: {
        technical_capability: { checked: false, weight: 30 },
        price_competitiveness: { checked: false, weight: 25 }
      }
    }));

    act(() => {
      result.current.toggleItem('technical_capability');
    });

    // 체크된 가중치: 30 / 전체 가중치: 55 => round(30/55 * 100) = 55
    expect(result.current.achievementRate).toBe(55);

    act(() => {
      result.current.toggleItem('price_competitiveness');
    });

    // 둘 다 체크: 55 / 55 = 100
    expect(result.current.achievementRate).toBe(100);
  });

  it('toggleItem 함수로 체크된 항목을 해제한다', () => {
    const { result } = renderHook(() => useEvaluationProgress({
      initialChecklist: {
        technical_capability: { checked: true, weight: 30 },
        price_competitiveness: { checked: true, weight: 25 }
      }
    }));

    act(() => {
      result.current.toggleItem('technical_capability');
    });

    // price만 남음: 25 / 55 => round(25/55 * 100) = 45
    expect(result.current.achievementRate).toBe(45);
  });

  it('resetChecklist 함수로 모든 항목을 미체크로 초기화한다', () => {
    const initialChecklist = {
      technical_capability: { checked: true, weight: 30 },
      price_competitiveness: { checked: true, weight: 25 },
      past_performance: { checked: true, weight: 20 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist }));

    // 전부 체크: 75 / 75 = 100%
    expect(result.current.achievementRate).toBe(100);

    act(() => {
      result.current.resetChecklist();
    });

    expect(result.current.achievementRate).toBe(0);
  });

  it('updateChecklist 호출 후 달성률이 자동으로 재계산된다', () => {
    const { result } = renderHook(() =>
      useEvaluationProgress({ initialChecklist: { item1: { checked: true, weight: 50 } } })
    );

    expect(result.current.achievementRate).toBe(100);

    act(() => {
      result.current.updateChecklist({ item1: { checked: false, weight: 50 } });
    });

    expect(result.current.achievementRate).toBe(0);
  });

  it('존재하지 않는 항목 토글 시 에러가 발생하지 않는다', () => {
    const { result } = renderHook(() => useEvaluationProgress({
      initialChecklist: { item1: { checked: true, weight: 50 } }
    }));

    act(() => {
      result.current.toggleItem('non_existent_item' as any);
    });

    // 달성률은 그대로 유지되어야 함: item1만 체크(50/50 = 100%)
    expect(result.current.achievementRate).toBe(100);
  });

  it('소수점 달성률을 올바르게 반올림한다', () => {
    const checklist = {
      item1: { checked: true, weight: 33 },
      item2: { checked: true, weight: 33 },
      item3: { checked: true, weight: 34 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    // 33 + 33 + 34 = 100, 정확히 100%
    expect(result.current.achievementRate).toBe(100);

    const partialChecklist = {
      item1: { checked: true, weight: 33 },
      item2: { checked: false, weight: 33 },
      item3: { checked: false, weight: 34 }
    };
    const { result: result2 } = renderHook(() => useEvaluationProgress({ initialChecklist: partialChecklist }));
    // 33 / 100 * 100 = 33%
    expect(result2.current.achievementRate).toBe(33);
  });

  it('checked 필드가 없는 항목은 미체크로 처리한다', () => {
    const checklist = {
      item1: { checked: true, weight: 50 },
      item2: { weight: 30 } as any, // checked 필드 누락
      item3: { checked: false, weight: 20 }
    };
    const { result } = renderHook(() => useEvaluationProgress({ initialChecklist: checklist }));
    // item1만 체크: 50 / 100 * 100 = 50%
    expect(result.current.achievementRate).toBe(50);
  });
});
