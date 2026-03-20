/**
 * F-05 제안서 편집기 - TipTap 확장 설정
 */

import StarterKit from '@tiptap/starter-kit';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table/row';
import { TableCell } from '@tiptap/extension-table/cell';
import { TableHeader } from '@tiptap/extension-table/header';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import { Highlight } from '@tiptap/extension-highlight';
import Placeholder from '@tiptap/extension-placeholder';

/**
 * TipTap 기본 확장 설정
 * 제안서 편집기에 필요한 모든 기능을 포함
 */
export const editorExtensions = [
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
    placeholder: '내용을 입력하세요...',
  }),
];
