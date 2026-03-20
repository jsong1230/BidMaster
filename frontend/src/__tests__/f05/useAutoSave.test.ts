/**
 * F-05 제안서 편집기 - useAutoSave 커스텀 훅 테스트
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAutoSave } from '@/components/proposals/hooks/useAutoSave';

describe('useAutoSave', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('30초 debounce 후 saveCallback 호출한다', async () => {
    const saveCallback = jest.fn().mockResolvedValue({ success: true });
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    // 변경사항 트리거
    act(() => {
      result.current.triggerSave();
    });

    // 30초 경과
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(saveCallback).toHaveBeenCalledTimes(1);
    });
  });

  it('중간 변경 시 타이머가 리셋된다', async () => {
    const saveCallback = jest.fn().mockResolvedValue({ success: true });
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    // 첫 번째 변경
    act(() => {
      result.current.triggerSave();
    });

    // 15초 경과
    act(() => {
      jest.advanceTimersByTime(15000);
    });

    // 두 번째 변경 (타이머 리셋)
    act(() => {
      result.current.triggerSave();
    });

    // 추가 15초 경과 (총 30초가 아님)
    act(() => {
      jest.advanceTimersByTime(15000);
    });

    // 저장이 호출되지 않아야 함
    expect(saveCallback).not.toHaveBeenCalled();

    // 30초 더 경과
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(saveCallback).toHaveBeenCalledTimes(1);
    });
  });

  it('언마운트 시 pending 변경사항을 저장한다', async () => {
    const saveCallback = jest.fn().mockResolvedValue({ success: true });
    const { result, unmount } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    // 변경사항 트리거 후 즉시 언마운트
    act(() => {
      result.current.triggerSave();
    });

    unmount();

    await waitFor(() => {
      expect(saveCallback).toHaveBeenCalledTimes(1);
    });
  });

  it('저장 실패 시 에러 상태를 설정한다', async () => {
    const saveCallback = jest.fn().mockRejectedValue(new Error('Network Error'));
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    act(() => {
      result.current.triggerSave();
    });

    act(() => {
      jest.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(result.current.isSaving).toBe(false);
      expect(result.current.error).toBe('Network Error');
    });
  });

  it('저장 성공 시 에러 상태를 초기화한다', async () => {
    const saveCallback = jest.fn()
      .mockRejectedValueOnce(new Error('Network Error'))
      .mockResolvedValueOnce({ success: true });
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    // 첫 번째 저장 실패
    act(() => {
      result.current.triggerSave();
    });

    act(() => {
      jest.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Network Error');
    });

    // 두 번째 저장 성공
    act(() => {
      result.current.triggerSave();
    });

    act(() => {
      jest.advanceTimersByTime(30000);
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
  });

  it('isSaving 상태가 올바르게 변경된다', async () => {
    const saveCallback = jest.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 1000))
    );
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: 30000 })
    );

    // 초기 상태
    expect(result.current.isSaving).toBe(false);

    // 변경사항 트리거
    act(() => {
      result.current.triggerSave();
    });

    // 저장 시작 전 (타이머 대기 중)
    expect(result.current.isSaving).toBe(false);

    // 30초 경과
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    // 저장 중
    expect(result.current.isSaving).toBe(true);

    // 내부 저장 Promise 타이머 완료 (1초 setTimeout)
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    // 저장 완료 대기
    await waitFor(() => {
      expect(result.current.isSaving).toBe(false);
    });
  });

  it('debounce 시간을 커스터마이징할 수 있다', async () => {
    const saveCallback = jest.fn().mockResolvedValue({ success: true });
    const customDebounce = 5000; // 5초
    const { result } = renderHook(() =>
      useAutoSave({ onSave: saveCallback, debounceMs: customDebounce })
    );

    act(() => {
      result.current.triggerSave();
    });

    // 4초 경과 (저장되지 않음)
    act(() => {
      jest.advanceTimersByTime(4000);
    });

    expect(saveCallback).not.toHaveBeenCalled();

    // 1초 더 경과 (총 5초)
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    await waitFor(() => {
      expect(saveCallback).toHaveBeenCalledTimes(1);
    });
  });

  it('onSave가 없으면 에러가 발생하지 않는다', () => {
    expect(() => {
      renderHook(() => useAutoSave({ onSave: undefined, debounceMs: 30000 }));
    }).not.toThrow();
  });
});
