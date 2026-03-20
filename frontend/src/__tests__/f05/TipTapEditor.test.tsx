/**
 * F-05 제안서 편집기 - TipTapEditor 컴포넌트 테스트
 *
 * jsdom 환경에서 @tiptap/react의 useEditor는 null을 반환합니다.
 * 따라서 에디터가 null일 때 로딩 스켈레톤 UI를 표시하는 동작을 테스트합니다.
 * 실제 에디터 기능 테스트는 useEditor를 mock하여 진행합니다.
 */
import { render, screen } from '@testing-library/react';

// TipTap 관련 모듈 전체 mock
jest.mock('@tiptap/react', () => ({
  useEditor: jest.fn(),
  EditorContent: ({ editor }: { editor: unknown }) => (
    <div data-testid="editor-content">{editor ? '에디터 콘텐츠' : null}</div>
  ),
}));

jest.mock('@tiptap/starter-kit', () => ({
  __esModule: true,
  default: {
    configure: jest.fn().mockReturnValue({}),
  },
}));

jest.mock('@tiptap/extension-table', () => ({
  Table: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@tiptap/extension-table/row', () => ({
  TableRow: {},
}));

jest.mock('@tiptap/extension-table/cell', () => ({
  TableCell: {},
}));

jest.mock('@tiptap/extension-table/header', () => ({
  TableHeader: {},
}));

jest.mock('@tiptap/extension-image', () => ({
  __esModule: true,
  default: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@tiptap/extension-link', () => ({
  __esModule: true,
  default: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@tiptap/extension-text-align', () => ({
  __esModule: true,
  default: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@tiptap/extension-underline', () => ({
  __esModule: true,
  default: {},
}));

jest.mock('@tiptap/extension-highlight', () => ({
  __esModule: true,
  default: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@tiptap/extension-placeholder', () => ({
  __esModule: true,
  default: { configure: jest.fn().mockReturnValue({}) },
}));

jest.mock('@/components/proposals/editor/EditorToolbar', () => ({
  EditorToolbar: () => <div data-testid="editor-toolbar">도구 모음</div>,
}));

import { useEditor } from '@tiptap/react';
import { TipTapEditor } from '@/components/proposals/editor/TipTapEditor';

const mockUseEditor = useEditor as jest.Mock;

describe('TipTapEditor', () => {
  const defaultProps = {
    content: '',
    onChange: jest.fn(),
    placeholder: '내용을 입력하세요...',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    // 기본값: useEditor가 null 반환 (jsdom 환경)
    mockUseEditor.mockReturnValue(null);
  });

  it('에디터 로딩 중에는 스켈레톤 UI를 표시한다', () => {
    mockUseEditor.mockReturnValue(null);
    const { container } = render(<TipTapEditor {...defaultProps} />);

    // 로딩 스켈레톤 확인
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });

  it('에디터가 준비되면 에디터 콘텐츠를 표시한다', () => {
    const mockEditor = {
      getHTML: jest.fn().mockReturnValue('<p>테스트</p>'),
      commands: {},
      isEditable: true,
    };
    mockUseEditor.mockReturnValue(mockEditor);

    render(<TipTapEditor {...defaultProps} />);

    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('에디터가 준비되면 도구 모음을 표시한다', () => {
    const mockEditor = {
      getHTML: jest.fn().mockReturnValue(''),
      commands: {},
      isEditable: true,
    };
    mockUseEditor.mockReturnValue(mockEditor);

    render(<TipTapEditor {...defaultProps} />);

    expect(screen.getByTestId('editor-toolbar')).toBeInTheDocument();
  });

  it('readOnly=true일 때 도구 모음을 표시하지 않는다', () => {
    const mockEditor = {
      getHTML: jest.fn().mockReturnValue(''),
      commands: {},
      isEditable: false,
    };
    mockUseEditor.mockReturnValue(mockEditor);

    render(<TipTapEditor {...defaultProps} readOnly />);

    expect(screen.queryByTestId('editor-toolbar')).not.toBeInTheDocument();
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('onChange prop 없으면 에러가 발생하지 않는다', () => {
    mockUseEditor.mockReturnValue(null);

    expect(() => {
      render(<TipTapEditor content="" placeholder="테스트" />);
    }).not.toThrow();
  });

  it('에디터가 null일 때 min-h-[200px]를 가진 컨테이너를 렌더링한다', () => {
    mockUseEditor.mockReturnValue(null);
    const { container } = render(<TipTapEditor {...defaultProps} />);

    // 로딩 컨테이너 확인
    const loadingContainer = container.querySelector('.min-h-\\[200px\\]');
    expect(loadingContainer).toBeInTheDocument();
  });

  it('에디터가 준비되면 border를 가진 컨테이너를 렌더링한다', () => {
    const mockEditor = {
      getHTML: jest.fn().mockReturnValue(''),
      commands: {},
      isEditable: true,
    };
    mockUseEditor.mockReturnValue(mockEditor);

    const { container } = render(<TipTapEditor {...defaultProps} />);

    const editorWrapper = container.querySelector('.border.border-neutral-200');
    expect(editorWrapper).toBeInTheDocument();
  });

  it('onEditorReady 콜백으로 에디터 인스턴스를 전달한다', () => {
    const mockEditor = {
      getHTML: jest.fn().mockReturnValue(''),
      commands: {},
      isEditable: true,
    };
    mockUseEditor.mockReturnValue(mockEditor);

    const onEditorReady = jest.fn();
    render(<TipTapEditor {...defaultProps} onEditorReady={onEditorReady} />);

    expect(onEditorReady).toHaveBeenCalledWith(mockEditor);
  });
});
