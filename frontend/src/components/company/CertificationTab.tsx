'use client';

import { useEffect, useState } from 'react';
import { useCertificationStore } from '@/lib/stores/certification-store';
import { showToast } from '@/components/ui/Toast';
import type {
  Certification,
  CertificationCreateRequest,
  MemberRole,
} from '@/types/company';
import { HttpError } from '@/lib/api/client';

interface CertificationTabProps {
  companyId: string;
  currentUserRole: MemberRole | null;
}

const canManage = (role: MemberRole | null) => role === 'owner' || role === 'admin';

const EXPIRY_SOON_DAYS = 30;

function getDaysUntilExpiry(expiryDate?: string): number | null {
  if (!expiryDate) return null;
  const today = new Date();
  const expiry = new Date(expiryDate);
  const diff = Math.floor((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  return diff;
}

function ExpiryBadge({ expiryDate }: { expiryDate?: string }) {
  const days = getDaysUntilExpiry(expiryDate);
  if (days === null) return null;
  if (days < 0) {
    return (
      <span className="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
        만료됨
      </span>
    );
  }
  if (days <= EXPIRY_SOON_DAYS) {
    return (
      <span className="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-yellow-50 text-yellow-700 border border-yellow-200">
        만료 임박
      </span>
    );
  }
  return null;
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
          d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
        />
      </svg>
      <p className="text-neutral-700 font-medium mb-2">아직 등록된 보유 인증이 없습니다</p>
      <p className="text-sm text-neutral-500 mb-6">
        GS인증, ISO, 벤처기업인증 등 보유 인증을 등록하면 제안서의 전문성이 강화됩니다.
      </p>
      <button
        type="button"
        onClick={onAdd}
        className="px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors"
      >
        인증 등록하기
      </button>
    </div>
  );
}

function CertificationModal({
  isOpen,
  onClose,
  initial,
  companyId,
}: {
  isOpen: boolean;
  onClose: () => void;
  initial: Certification | null;
  companyId: string;
}) {
  const { createCertification, updateCertification } = useCertificationStore();
  const isEdit = !!initial;

  const [form, setForm] = useState<CertificationCreateRequest>({
    name: initial?.name ?? '',
    issuer: initial?.issuer ?? '',
    certNumber: initial?.certNumber ?? '',
    issuedDate: initial?.issuedDate ?? '',
    expiryDate: initial?.expiryDate ?? '',
    documentUrl: initial?.documentUrl ?? '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  // modal이 열릴 때 초기화
  useEffect(() => {
    if (isOpen) {
      setForm({
        name: initial?.name ?? '',
        issuer: initial?.issuer ?? '',
        certNumber: initial?.certNumber ?? '',
        issuedDate: initial?.issuedDate ?? '',
        expiryDate: initial?.expiryDate ?? '',
        documentUrl: initial?.documentUrl ?? '',
      });
      setErrors({});
    }
  }, [isOpen, initial]);

  if (!isOpen) return null;

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = '인증명을 입력해주세요.';
    if (
      form.issuedDate &&
      form.expiryDate &&
      form.expiryDate < form.issuedDate
    ) {
      e.expiryDate = '만료일이 발급일보다 이전입니다.';
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
        await updateCertification(companyId, initial.id, form);
        showToast('인증 정보가 수정되었습니다.');
      } else {
        await createCertification(companyId, form);
        showToast('인증 정보가 등록되었습니다.');
      }
      onClose();
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      showToast(httpErr?.message ?? '저장에 실패했습니다.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black opacity-40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-[560px] max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
          <h2 className="text-lg font-bold text-neutral-900">
            {isEdit ? '인증 수정' : '인증 등록'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-md text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              인증명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="GS인증 1등급"
              className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.name ? 'border-red-500' : 'border-neutral-200'}`}
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">발급기관</label>
            <input
              type="text"
              value={form.issuer}
              onChange={(e) => setForm((f) => ({ ...f, issuer: e.target.value }))}
              placeholder="한국정보통신기술협회(TTA)"
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">인증번호</label>
            <input
              type="text"
              value={form.certNumber}
              onChange={(e) => setForm((f) => ({ ...f, certNumber: e.target.value }))}
              placeholder="GS-2024-0123"
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">발급일</label>
              <input
                type="date"
                value={form.issuedDate}
                onChange={(e) => setForm((f) => ({ ...f, issuedDate: e.target.value }))}
                className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">만료일</label>
              <input
                type="date"
                value={form.expiryDate}
                onChange={(e) => setForm((f) => ({ ...f, expiryDate: e.target.value }))}
                className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.expiryDate ? 'border-red-500' : 'border-neutral-200'}`}
              />
              {errors.expiryDate && <p className="mt-1 text-sm text-red-600">{errors.expiryDate}</p>}
            </div>
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
      </div>
    </div>
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
        <h3 className="text-base font-semibold text-neutral-900 mb-2">인증 삭제</h3>
        <p className="text-sm text-neutral-600 mb-6">
          이 인증을 삭제하면 복구할 수 없습니다. 삭제할까요?
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

export default function CertificationTab({ companyId, currentUserRole }: CertificationTabProps) {
  const {
    certifications,
    isLoading,
    isModalOpen,
    editingCert,
    deletingCertId,
    fetchCertifications,
    openModal,
    closeModal,
    setDeletingId,
    deleteCertification,
  } = useCertificationStore();

  const [isDeleting, setIsDeleting] = useState(false);
  const manage = canManage(currentUserRole);

  useEffect(() => {
    fetchCertifications(companyId);
  }, [companyId, fetchCertifications]);

  const handleDelete = async () => {
    if (!deletingCertId) return;
    setIsDeleting(true);
    try {
      await deleteCertification(companyId, deletingCertId);
      showToast('인증이 삭제되었습니다.');
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      showToast(httpErr?.message ?? '삭제에 실패했습니다.', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm animate-pulse">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center px-6 py-4 border-b border-neutral-100 last:border-0 gap-4">
            <div className="h-4 flex-1 bg-neutral-200 rounded" />
            <div className="h-4 w-24 bg-neutral-200 rounded" />
            <div className="h-4 w-24 bg-neutral-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-neutral-500">총 {certifications.length}개</span>
        <button
          type="button"
          onClick={() => openModal()}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors"
        >
          + 인증 등록
        </button>
      </div>

      {certifications.length === 0 ? (
        <EmptyState onAdd={() => openModal()} />
      ) : (
        <>
          {/* 데스크탑 테이블 */}
          <div className="hidden md:block bg-white border border-neutral-200 rounded-lg shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-neutral-50 border-b border-neutral-200">
                <tr>
                  {['인증명', '발급기관', '인증번호', '발급일', '만료일', ''].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-neutral-500">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {certifications.map((cert) => {
                  const days = getDaysUntilExpiry(cert.expiryDate);
                  const isExpired = days !== null && days < 0;
                  const isExpiringSoon = days !== null && days >= 0 && days <= EXPIRY_SOON_DAYS;

                  return (
                    <tr
                      key={cert.id}
                      className={isExpiringSoon ? 'bg-yellow-50' : isExpired ? '' : ''}
                    >
                      <td className={`px-4 py-3 text-sm font-medium ${isExpired ? 'text-neutral-400' : 'text-neutral-900'}`}>
                        {cert.name}
                      </td>
                      <td className={`px-4 py-3 text-sm ${isExpired ? 'text-neutral-400' : 'text-neutral-700'}`}>
                        {cert.issuer ?? '-'}
                      </td>
                      <td className={`px-4 py-3 text-sm ${isExpired ? 'text-neutral-400' : 'text-neutral-700'}`}>
                        {cert.certNumber ?? '-'}
                      </td>
                      <td className={`px-4 py-3 text-sm ${isExpired ? 'text-neutral-400' : 'text-neutral-700'}`}>
                        {cert.issuedDate ?? '-'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="flex items-center gap-2">
                          <span className={isExpired ? 'text-neutral-400' : 'text-neutral-700'}>
                            {cert.expiryDate ?? '-'}
                          </span>
                          <ExpiryBadge expiryDate={cert.expiryDate} />
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {manage && (
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => openModal(cert)}
                              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                            >
                              수정
                            </button>
                            <button
                              type="button"
                              onClick={() => setDeletingId(cert.id)}
                              className="text-xs text-red-500 hover:text-red-600 font-medium"
                            >
                              삭제
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* 모바일 카드형 */}
          <div className="md:hidden space-y-3">
            {certifications.map((cert) => {
              const days = getDaysUntilExpiry(cert.expiryDate);
              const isExpired = days !== null && days < 0;

              return (
                <div
                  key={cert.id}
                  className={`bg-white border border-neutral-200 rounded-lg p-4 ${isExpired ? 'opacity-70' : ''}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-neutral-900 text-sm">{cert.name}</p>
                      {cert.issuer && <p className="text-xs text-neutral-500">{cert.issuer}</p>}
                    </div>
                    <ExpiryBadge expiryDate={cert.expiryDate} />
                  </div>
                  {cert.certNumber && (
                    <p className="text-xs text-neutral-500 mb-1">번호: {cert.certNumber}</p>
                  )}
                  {cert.expiryDate && (
                    <p className="text-xs text-neutral-500">만료: {cert.expiryDate}</p>
                  )}
                  {manage && (
                    <div className="flex gap-3 mt-3 pt-3 border-t border-neutral-100">
                      <button
                        type="button"
                        onClick={() => openModal(cert)}
                        className="text-xs text-blue-600 font-medium"
                      >
                        수정
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingId(cert.id)}
                        className="text-xs text-red-500 font-medium"
                      >
                        삭제
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      <CertificationModal
        isOpen={isModalOpen}
        onClose={closeModal}
        initial={editingCert}
        companyId={companyId}
      />

      {deletingCertId && (
        <DeleteModal
          onConfirm={handleDelete}
          onCancel={() => setDeletingId(null)}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
