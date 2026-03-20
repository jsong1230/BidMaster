/**
 * F-05 제안서 편집기 - TipTap 에디터 컴포넌트
 */

'use client';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table/row';
import { TableCell } from '@tiptap/extension-table/cell';
import { TableHeader } from '@tiptap/extension-table/header';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import Highlight from '@tiptap/extension-highlight';
import Placeholder from '@tiptap/extension-placeholder';
import { EditorToolbar } from './EditorToolbar';

interface TipTapEditorProps {
  /** 초기 콘텐츠 */
  content: string;
  /** 콘텐츠 변경 콜백 */
  onChange?: (content: string) => void;
  /** placeholder */
  placeholder?: string;
  /** 읽기 전용 모드 */
  readOnly?: boolean;
  /** 에디터 인스턴스 전달 (부모 컴포넌트에서 제어용) */
  onEditorReady?: (editor: ReturnType<typeof useEditor> | null) => void;
}

/**
 * TipTap 기반 리치텍스트 에디터
 */
export function TipTapEditor({
  content,
  onChange,
  placeholder = '내용을 입력하세요...',
  readOnly = false,
  onEditorReady,
}: TipTapEditorProps) {
  const editor = useEditor({
    extensions: [
      // 기본 에디터 기능
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
        bulletList: { keepMarks: true },
        orderedList: { keepMarks: true },
      }),

      // 표 기능
      Table.configure({
        resizable: true,
        allowTableNodeSelection: true,
      }),
      TableRow,
      TableCell,
      TableHeader,

      // 이미지
      Image.configure({
        inline: true,
        allowBase64: true,
      }),

      // 링크
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          rel: 'noopener noreferrer',
          target: '_blank',
        },
      }),

      // 텍스트 정렬
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),

      // 밑줄
      Underline,

      // 하이라이트
      Highlight.configure({
        multicolor: true,
      }),

      // Placeholder
      Placeholder.configure({
        placeholder,
      }),
    ],
    content,
    editable: !readOnly,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm max-w-none focus:outline-none min-h-[200px] px-3 py-2',
      },
    },
  });

  // 에디터 인스턴스 전달
  if (onEditorReady && editor !== undefined) {
    onEditorReady(editor);
  }

  if (!editor) {
    return (
      <div className="border border-neutral-200 rounded-md p-4 min-h-[200px]">
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-neutral-200 rounded"></div>
          <div className="h-4 bg-neutral-200 rounded"></div>
          <div className="h-4 bg-neutral-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-neutral-200 rounded-md overflow-hidden">
      {!readOnly && <EditorToolbar editor={editor} />}
      <EditorContent editor={editor} />
    </div>
  );
}
