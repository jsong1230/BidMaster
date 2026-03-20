/**
 * F-05 제안서 편집기 - AutoSaveIndicator 컴포넌트 테스트
 *
 * AutoSaveIndicator는 저장 상태 표시만 담당합니다.
 * 30초 타이머 및 Ctrl+S 단축키 로직은 useAutoSave 훅에 있습니다.
 * 이 컴포넌트는 isEditing prop, 수동 저장 버튼, 재시도 버튼을 테스트합니다.
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { AutoSaveIndicator } from '@/components/proposals/editor/AutoSaveIndicator';

describe('AutoSaveIndicator', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('초기 상태에서는 "저장됨"을 표시한다', () => {
    render(<AutoSaveIndicator />);
    expect(screen.getByText('저장됨')).toBeInTheDocument();
  });

  it('isEditing=true일 때 "편집 중..."을 표시한다', () => {
    render(<AutoSaveIndicator isEditing />);
    expect(screen.getByText('편집 중...')).toBeInTheDocument();
  });

  it('isEditing이 false에서 true로 변경되면 "편집 중..."을 표시한다', () => {
    const { rerender } = render(<AutoSaveIndicator isEditing={false} />);
    expect(screen.getByText('저장됨')).toBeInTheDocument();

    rerender(<AutoSaveIndicator isEditing />);
    expect(screen.getByText('편집 중...')).toBeInTheDocument();
  });

  it('onSave prop이 있으면 수동 저장 버튼을 표시한다', () => {
    const onSave = jest.fn().mockResolvedValue({ success: true });
    render(<AutoSaveIndicator onSave={onSave} />);

    expect(screen.getByText('저장')).toBeInTheDocument();
  });

  it('onSave prop이 없으면 수동 저장 버튼을 표시하지 않는다', () => {
    render(<AutoSaveIndicator />);
    expect(screen.queryByText('저장')).not.toBeInTheDocument();
  });

  it('수동 저장 버튼 클릭 시 onSave를 호출한다', async () => {
    const onSave = jest.fn().mockResolvedValue({ success: true });
    render(<AutoSaveIndicator onSave={onSave} />);

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(1);
    });
  });

  it('수동 저장 성공 시 "저장됨"으로 상태가 변경된다', async () => {
    const onSave = jest.fn().mockResolvedValue({ success: true });
    render(<AutoSaveIndicator isEditing onSave={onSave} />);

    expect(screen.getByText('편집 중...')).toBeInTheDocument();

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('저장됨')).toBeInTheDocument();
    });
  });

  it('수동 저장 중에는 "저장 중..." 상태 텍스트를 표시한다', async () => {
    let resolvePromise: (value: unknown) => void;
    const onSave = jest.fn().mockImplementation(
      () => new Promise((resolve) => { resolvePromise = resolve; })
    );

    render(<AutoSaveIndicator onSave={onSave} />);

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      // "저장 중..." 텍스트가 span으로 표시됨 (상태 표시 영역)
      const savingElements = screen.getAllByText('저장 중...');
      expect(savingElements.length).toBeGreaterThan(0);
    });

    // 저장 완료
    act(() => {
      resolvePromise({ success: true });
    });

    await waitFor(() => {
      expect(screen.getByText('저장됨')).toBeInTheDocument();
    });
  });

  it('저장 실패 시 "저장 실패"와 재시도 버튼을 표시한다', async () => {
    const onSave = jest.fn().mockRejectedValue(new Error('Network Error'));
    render(<AutoSaveIndicator onSave={onSave} />);

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('저장 실패')).toBeInTheDocument();
      expect(screen.getByText('재시도')).toBeInTheDocument();
    });
  });

  it('재시도 버튼 클릭 시 onSave를 다시 호출한다', async () => {
    let saveAttempts = 0;
    const onSave = jest.fn().mockImplementation(() => {
      saveAttempts++;
      if (saveAttempts === 1) {
        return Promise.reject(new Error('Network Error'));
      }
      return Promise.resolve({ success: true });
    });

    render(<AutoSaveIndicator onSave={onSave} />);

    // 첫 번째 저장 실패
    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('저장 실패')).toBeInTheDocument();
    });

    // 재시도 버튼 클릭
    const retryButton = screen.getByText('재시도');
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(2);
      expect(screen.getByText('저장됨')).toBeInTheDocument();
    });
  });

  it('저장 성공 시 마지막 저장 시간을 표시한다', async () => {
    const onSave = jest.fn().mockResolvedValue({ success: true });
    render(<AutoSaveIndicator onSave={onSave} />);

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('저장됨')).toBeInTheDocument();
      // "방금 전" 텍스트 표시
      expect(screen.getByText(/방금 전/)).toBeInTheDocument();
    });
  });

  it('lastSavedAt prop으로 마지막 저장 시간을 표시한다', () => {
    const oneMinuteAgo = new Date(Date.now() - 60000);
    render(<AutoSaveIndicator lastSavedAt={oneMinuteAgo} />);

    expect(screen.getByText(/1분 전/)).toBeInTheDocument();
  });

  it('저장 에러 상태에서는 수동 저장 버튼이 숨겨진다', async () => {
    const onSave = jest.fn().mockRejectedValue(new Error('Network Error'));
    render(<AutoSaveIndicator onSave={onSave} />);

    const saveButton = screen.getByText('저장');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('저장 실패')).toBeInTheDocument();
    });

    // 에러 상태에서는 수동 저장 버튼이 숨겨짐 (재시도 버튼만 표시)
    expect(screen.queryByText('저장')).not.toBeInTheDocument();
    expect(screen.getByText('재시도')).toBeInTheDocument();
  });
});
