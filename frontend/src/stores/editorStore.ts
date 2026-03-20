/**
 * F-05 제안서 편집기 - 에디터 상태 스토어
 */

import { create } from 'zustand';
import type { SectionKey } from '@/types/proposal';

interface EditorState {
  /** 활성 섹션 키 */
  activeSection: SectionKey | null;
  /** 에디터 모드 */
  mode: 'view' | 'edit';
  /** 저장 중 여부 */
  isSaving: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 마지막 저장 시간 */
  lastSavedAt: Date | null;
}

interface EditorActions {
  /** 활성 섹션 설정 */
  setActiveSection: (section: SectionKey | null) => void;
  /** 에디터 모드 설정 */
  setMode: (mode: 'view' | 'edit') => void;
  /** 저장 상태 설정 */
  setSaving: (isSaving: boolean) => void;
  /** 에러 설정 */
  setError: (error: string | null) => void;
  /** 마지막 저장 시간 설정 */
  setLastSavedAt: (time: Date | null) => void;
  /** 에디터 상태 초기화 */
  reset: () => void;
}

/**
 * 에디터 상태 관리 스토어
 */
export const useEditorStore = create<EditorState & EditorActions>((set) => ({
  // 초기 상태
  activeSection: null,
  mode: 'edit',
  isSaving: false,
  error: null,
  lastSavedAt: null,

  // 액션
  setActiveSection: (section) => set({ activeSection: section }),
  setMode: (mode) => set({ mode }),
  setSaving: (isSaving) => set({ isSaving }),
  setError: (error) => set({ error }),
  setLastSavedAt: (time) => set({ lastSavedAt: time }),
  reset: () =>
    set({
      activeSection: null,
      mode: 'edit',
      isSaving: false,
      error: null,
      lastSavedAt: null,
    }),
}));
