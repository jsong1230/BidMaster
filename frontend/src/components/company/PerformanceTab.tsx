'use client';

import { useState, useEffect, useRef } from 'react';
import { usePerformanceStore } from '@/lib/stores/performance-store';
import SlideOverPanel from '@/components/ui/SlideOverPanel';
import RepresentativeBadge from '@/components/ui/RepresentativeBadge';
import AmountInput from '@/components/ui/AmountInput';
import { showToast } from '@/components/ui/Toast';
import type {
  Performance,
  PerformanceCreateRequest,
  ClientType,
  PerformanceStatus,
  MemberRole,
} from '@/types/company';
import { HttpError } from '@/lib/api/client';

interface PerformanceTabProps {
  companyId: string;
  currentUserRole: MemberRole | null;
}

const canManage = (role: MemberRole | null) =>
  role === 'owner' || role === 'admin';

function StatusBadge({ status }: { status: PerformanceStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${
        status === 'completed'
          ? 'bg-green-50 text-green-700'
          : 'bg-yellow-50 text-yellow-700'
      }`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'
        }`}
      />
      {status === 'completed' ? '완료' : '진행중'}
    </span>
  );
}

function ClientTypeBadge({ clientType }: { clientType?: ClientType }) {
  if (!clientType) return null;
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
        clientType === 'public'
          ? 'bg-blue-50 text-blue-700'
          : 'bg-purple-50 text-purple-700'
      }`}
    >
      {clientType === 'public' ? '공공' : '민간'}
    </span>
  );
}

function PerformanceCard({
  perf,
  canManage: manage,
  representativeCount,
  companyId,
}: {
  perf: Performance;
  canManage: boolean;
  representativeCount: number;
  companyId: string;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { openSlideOver, setDeletingId, setRepresentative } = usePerformanceStore();

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const handleRepresentativeToggle = async () => {
    setMenuOpen(false);
    const newValue = !perf.isRepresentative;
    if (newValue && representativeCount >= 5) {
      showToast('대표 실적은 최대 5개까지 지정할 수 있습니다.', 'error');
      return;
    }
    try {
      await setRepresentative(companyId, perf.id, newValue);
      showToast(newValue ? '대표 실적으로 지정되었습니다.' : '대표 실적이 해제되었습니다.');
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      showToast(httpErr?.message ?? '처리에 실패했습니다.', 'error');
    }
  };

  const formatAmount = (n: number) =>
    n.toLocaleString('ko-KR') + '원';

  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-sm p-5 hover:shadow-md transition-shadow relative">
      <div className="flex items-start justify-between mb-3">
        <div className="flex flex-wrap gap-2">
          {perf.isRepresentative && <RepresentativeBadge />}
          <StatusBadge status={perf.status} />
          <ClientTypeBadge clientType={perf.clientType} />
        </div>

        {manage && (
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-1.5 rounded-md text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
              aria-label="더보기"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
              </svg>
            </button>

            {menuOpen && (
              <div className="absolute right-0 top-8 w-40 bg-white border border-neutral-200 rounded-lg shadow-lg z-10 py-1">
                <button
                  type="button"
                  onClick={() => { setMenuOpen(false); openSlideOver(perf); }}
                  className="w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
                >
                  수정
                </button>
                <button
                  type="button"
                  onClick={handleRepresentativeToggle}
                  className="w-full text-left px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
                >
                  {perf.isRepresentative ? '대표 실적 해제' : '대표 실적 지정'}
                </button>
                <button
                  type="button"
                  onClick={() => { setMenuOpen(false); setDeletingId(perf.id); }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  삭제
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <h4 className="font-semibold text-neutral-900 mb-1">{perf.projectName}</h4>
      <p className="text-sm text-neutral-500 mb-3">{perf.clientName}</p>

      <div className="space-y-1 text-sm">
        <div className="flex gap-2">
          <span className="text-neutral-400 w-20">계약 금액</span>
          <span className="text-neutral-900 font-medium">{formatAmount(perf.contractAmount)}</span>
        </div>
        <div className="flex gap-2">
          <span className="text-neutral-400 w-20">기간</span>
          <span className="text-neutral-900">
            {perf.startDate} ~ {perf.endDate}
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg
        className="w-16 h-16 text-neutral-300 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <p className="text-neutral-700 font-medium mb-2">아직 등록된 수행 실적이 없습니다</p>
      <p className="text-sm text-neutral-500 mb-6">
        과거 사업 경험을 등록하면 제안서 생성 시 자동으로 활용됩니다.
      </p>
      <button
        type="button"
        onClick={onAdd}
        className="px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors"
      >
        수행 실적 등록하기
      </button>
    </div>
  );
}

function PerformanceForm({
  initial,
  companyId,
  representativeCount,
  onClose,
}: {
  initial: Performance | null;
  companyId: string;
  representativeCount: number;
  onClose: () => void;
}) {
  const { createPerformance, updatePerformance } = usePerformanceStore();
  const isEdit = !!initial;

  const [form, setForm] = useState<PerformanceCreateRequest>({
    projectName: initial?.projectName ?? '',
    clientName: initial?.clientName ?? '',
    clientType: initial?.clientType,
    contractAmount: initial?.contractAmount ?? 0,
    startDate: initial?.startDate ?? '',
    endDate: initial?.endDate ?? '',
    status: initial?.status ?? 'completed',
    description: initial?.description ?? '',
    isRepresentative: initial?.isRepresentative ?? false,
    documentUrl: initial?.documentUrl ?? '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  const repLimit = representativeCount >= 5 && !initial?.isRepresentative;

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.projectName.trim()) e.projectName = '프로젝트명을 입력해주세요.';
    if (!form.clientName.trim()) e.clientName = '발주처명을 입력해주세요.';
    if (!form.contractAmount || form.contractAmount <= 0) e.contractAmount = '계약 금액을 입력해주세요.';
    if (!form.startDate) e.startDate = '시작일을 입력해주세요.';
    if (!form.endDate) e.endDate = '종료일을 입력해주세요.';
    if (form.startDate && form.endDate && form.endDate < form.startDate) {
      e.endDate = '종료일이 시작일보다 이전입니다.';
    }
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setIsSaving(true);
    try {
      if (isEdit && initial) {
        await updatePerformance(companyId, initial.id, form);
        showToast('수행 실적이 수정되었습니다.');
      } else {
        await createPerformance(companyId, form);
        showToast('수행 실적이 등록되었습니다.');
      }
      onClose();
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      if (httpErr?.code === 'COMPANY_005') {
        showToast('대표 실적은 최대 5개까지 지정할 수 있습니다.', 'error');
      } else {
        showToast(httpErr?.message ?? '저장에 실패했습니다.', 'error');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          프로젝트명 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={form.projectName}
          onChange={(e) => setForm((f) => ({ ...f, projectName: e.target.value }))}
          className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.projectName ? 'border-red-500' : 'border-neutral-200'}`}
        />
        {errors.projectName && <p className="mt-1 text-sm text-red-600">{errors.projectName}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          발주처명 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={form.clientName}
          onChange={(e) => setForm((f) => ({ ...f, clientName: e.target.value }))}
          className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.clientName ? 'border-red-500' : 'border-neutral-200'}`}
        />
        {errors.clientName && <p className="mt-1 text-sm text-red-600">{errors.clientName}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">발주처 유형</label>
        <div className="flex gap-4">
          {([
            { value: 'public', label: '공공기관' },
            { value: 'private', label: '민간기업' },
          ] as { value: ClientType; label: string }[]).map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="clientType"
                value={opt.value}
                checked={form.clientType === opt.value}
                onChange={() => setForm((f) => ({ ...f, clientType: opt.value }))}
                className="text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-neutral-700">{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      <AmountInput
        value={form.contractAmount || ''}
        onChange={(v) => setForm((f) => ({ ...f, contractAmount: v === '' ? 0 : v }))}
        error={errors.contractAmount}
        required
      />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            시작일 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={form.startDate}
            onChange={(e) => setForm((f) => ({ ...f, startDate: e.target.value }))}
            className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.startDate ? 'border-red-500' : 'border-neutral-200'}`}
          />
          {errors.startDate && <p className="mt-1 text-sm text-red-600">{errors.startDate}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            종료일 <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={form.endDate}
            onChange={(e) => setForm((f) => ({ ...f, endDate: e.target.value }))}
            className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.endDate ? 'border-red-500' : 'border-neutral-200'}`}
          />
          {errors.endDate && <p className="mt-1 text-sm text-red-600">{errors.endDate}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">
          상태 <span className="text-red-500">*</span>
        </label>
        <select
          value={form.status}
          onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as PerformanceStatus }))}
          className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 bg-white"
        >
          <option value="completed">완료</option>
          <option value="ongoing">진행중</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">설명</label>
        <textarea
          value={form.description}
          onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          rows={3}
          className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 resize-none"
        />
      </div>

      <div className="p-4 bg-neutral-50 rounded-lg">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-neutral-700">대표 실적 지정</span>
          <button
            type="button"
            disabled={repLimit && !form.isRepresentative}
            onClick={() =>
              setForm((f) => ({ ...f, isRepresentative: !f.isRepresentative }))
            }
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${form.isRepresentative ? 'bg-blue-600' : 'bg-neutral-300'}
              ${repLimit && !form.isRepresentative ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
                form.isRepresentative ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-xs text-neutral-500">
          대표 실적은 제안서 생성 시 우선 활용됩니다.
          {` (현재 ${representativeCount}/5)`}
        </p>
        {repLimit && (
          <p className="text-xs text-red-500 mt-1">대표 실적은 최대 5개까지 지정할 수 있습니다.</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-1">첨부파일 URL</label>
        <input
          type="url"
          value={form.documentUrl}
          onChange={(e) => setForm((f) => ({ ...f, documentUrl: e.target.value }))}
          placeholder="https://..."
          className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div className="flex gap-3 pt-2">
        <button
          type="button"
          onClick={onClose}
          className="flex-1 px-4 py-2.5 border border-neutral-300 text-neutral-700 text-sm font-medium rounded-md hover:bg-neutral-50 transition-colors"
        >
          취소
        </button>
        <button
          type="submit"
          disabled={isSaving}
          className="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isSaving ? '저장 중...' : '저장'}
        </button>
      </div>
    </form>
  );
}

function DeleteModal({
  onConfirm,
  onCancel,
  isDeleting,
}: {
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black opacity-40" onClick={onCancel} />
      <div className="relative bg-white rounded-xl shadow-xl p-6 max-w-sm w-full mx-4">
        <h3 className="text-base font-semibold text-neutral-900 mb-2">수행 실적 삭제</h3>
        <p className="text-sm text-neutral-600 mb-6">
          이 실적을 삭제하면 복구할 수 없습니다. 삭제할까요?
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2.5 border border-neutral-300 text-neutral-700 text-sm font-medium rounded-md hover:bg-neutral-50 transition-colors"
          >
            취소
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 px-4 py-2.5 bg-red-600 text-white text-sm font-semibold rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {isDeleting ? '삭제 중...' : '삭제'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PerformanceTab({ companyId, currentUserRole }: PerformanceTabProps) {
  const {
    performances,
    isLoading,
    isSlideOverOpen,
    editingPerformance,
    deletingPerformanceId,
    representativeCount,
    filterStatus,
    fetchPerformances,
    openSlideOver,
    closeSlideOver,
    setDeletingId,
    deletePerformance,
    setFilterStatus,
  } = usePerformanceStore();

  const [isDeleting, setIsDeleting] = useState(false);
  const manage = canManage(currentUserRole);

  useEffect(() => {
    fetchPerformances(companyId);
  }, [companyId, fetchPerformances]);

  const filtered =
    filterStatus === 'all'
      ? performances
      : performances.filter((p) => p.status === filterStatus);

  const handleDelete = async () => {
    if (!deletingPerformanceId) return;
    setIsDeleting(true);
    try {
      await deletePerformance(companyId, deletingPerformanceId);
      showToast('수행 실적이 삭제되었습니다.');
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      showToast(httpErr?.message ?? '삭제에 실패했습니다.', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white border border-neutral-200 rounded-lg p-5 animate-pulse">
            <div className="h-4 w-24 bg-neutral-200 rounded mb-3" />
            <div className="h-5 w-48 bg-neutral-200 rounded mb-2" />
            <div className="h-4 w-32 bg-neutral-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          {(['all', 'completed', 'ongoing'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setFilterStatus(status)}
              className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                filterStatus === status
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-neutral-500 hover:bg-neutral-100'
              }`}
            >
              {status === 'all' ? '전체' : status === 'completed' ? '완료' : '진행중'}
            </button>
          ))}
        </div>

        {manage && (
          <button
            type="button"
            onClick={() => openSlideOver()}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors"
          >
            + 실적 등록
          </button>
        )}
      </div>

      {filtered.length === 0 ? (
        <EmptyState onAdd={() => openSlideOver()} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((perf) => (
            <PerformanceCard
              key={perf.id}
              perf={perf}
              canManage={manage}
              representativeCount={representativeCount}
              companyId={companyId}
            />
          ))}
        </div>
      )}

      <SlideOverPanel
        isOpen={isSlideOverOpen}
        onClose={closeSlideOver}
        title={editingPerformance ? '수행 실적 수정' : '수행 실적 등록'}
      >
        <PerformanceForm
          initial={editingPerformance}
          companyId={companyId}
          representativeCount={representativeCount}
          onClose={closeSlideOver}
        />
      </SlideOverPanel>

      {deletingPerformanceId && (
        <DeleteModal
          onConfirm={handleDelete}
          onCancel={() => setDeletingId(null)}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
