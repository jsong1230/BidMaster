'use client';

import { useState } from 'react';
import { useCompanyStore } from '@/lib/stores/company-store';
import BusinessNumberInput from '@/components/ui/BusinessNumberInput';
import { showToast } from '@/components/ui/Toast';
import type { CompanyCreateRequest, CompanyUpdateRequest, CompanyScale, MemberRole } from '@/types/company';
import { HttpError } from '@/lib/api/client';

const INDUSTRY_OPTIONS = [
  '소프트웨어 개발업',
  '정보기술서비스업',
  '컴퓨터 시스템 통합 자문 및 구축 서비스업',
  '데이터 처리, 호스팅 및 관련 서비스업',
  '포털 및 기타 인터넷 정보매개 서비스업',
  '건설업',
  '제조업',
  '기타',
];

const SCALE_OPTIONS: { value: CompanyScale; label: string }[] = [
  { value: 'small', label: '소기업' },
  { value: 'medium', label: '중기업' },
  { value: 'large', label: '대기업' },
];

interface CompanyBasicInfoTabProps {
  currentUserRole: MemberRole | null;
}

function SkeletonCard() {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-sm p-6 animate-pulse">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="flex gap-4 py-3 border-b border-neutral-100 last:border-0">
          <div className="h-4 w-28 bg-neutral-200 rounded" />
          <div className="h-4 flex-1 bg-neutral-200 rounded" />
        </div>
      ))}
    </div>
  );
}

export default function CompanyBasicInfoTab({ currentUserRole }: CompanyBasicInfoTabProps) {
  const { company, isLoading, createCompany, updateCompany } = useCompanyStore();
  const [isEditMode, setIsEditMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // 등록 폼 상태
  const [regForm, setRegForm] = useState<CompanyCreateRequest>({
    businessNumber: '',
    name: '',
    ceoName: '',
    address: '',
    phone: '',
    industry: '',
    scale: undefined,
    description: '',
  });

  // 수정 폼 상태 (company로 초기화)
  const [editForm, setEditForm] = useState<CompanyUpdateRequest>({
    name: company?.name ?? '',
    ceoName: company?.ceoName ?? '',
    address: company?.address ?? '',
    phone: company?.phone ?? '',
    industry: company?.industry ?? '',
    scale: company?.scale,
    description: company?.description ?? '',
  });

  const canEdit = currentUserRole === 'owner' || currentUserRole === 'admin';

  if (isLoading) {
    return <SkeletonCard />;
  }

  // ===== 미등록 상태: 등록 폼 =====
  if (!company) {
    const handleRegSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setFieldErrors({});
      setFormError(null);

      // 유효성 검사
      const errors: Record<string, string> = {};
      if (!regForm.businessNumber || regForm.businessNumber.length !== 10) {
        errors.businessNumber = '사업자등록번호 10자리를 입력해주세요.';
      }
      if (!regForm.name.trim()) {
        errors.name = '회사명을 입력해주세요.';
      }
      if (Object.keys(errors).length > 0) {
        setFieldErrors(errors);
        return;
      }

      setIsSaving(true);
      try {
        await createCompany(regForm);
        showToast('회사 정보가 등록되었습니다.');
      } catch (err: unknown) {
        const httpErr = err as HttpError;
        if (httpErr?.code === 'COMPANY_002') {
          setFieldErrors({ businessNumber: '이미 등록된 사업자등록번호입니다.' });
        } else if (httpErr?.code === 'COMPANY_003') {
          setFieldErrors({ businessNumber: '사업자등록번호 형식이 올바르지 않습니다.' });
        } else if (httpErr?.code === 'COMPANY_004') {
          setFormError('이미 다른 회사에 소속되어 있습니다.');
        } else {
          setFormError(httpErr?.message ?? '등록에 실패했습니다.');
        }
      } finally {
        setIsSaving(false);
      }
    };

    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm p-6">
        <div className="mb-6">
          <h3 className="text-base font-semibold text-neutral-900">회사 정보 등록</h3>
          <p className="text-sm text-neutral-500 mt-1">
            회사 기본 정보를 입력하여 프로필을 등록하세요.
          </p>
        </div>

        {formError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-300 rounded-md text-sm text-red-700">
            {formError}
          </div>
        )}

        <form onSubmit={handleRegSubmit} className="space-y-4">
          <BusinessNumberInput
            value={regForm.businessNumber}
            onChange={(v) => setRegForm((f) => ({ ...f, businessNumber: v }))}
            error={fieldErrors.businessNumber}
            required
          />

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              회사명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={regForm.name}
              onChange={(e) => setRegForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="주식회사 비드마스터"
              className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${fieldErrors.name ? 'border-red-500' : 'border-neutral-200'}`}
            />
            {fieldErrors.name && <p className="mt-1 text-sm text-red-600">{fieldErrors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">대표자명</label>
            <input
              type="text"
              value={regForm.ceoName}
              onChange={(e) => setRegForm((f) => ({ ...f, ceoName: e.target.value }))}
              placeholder="홍길동"
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">업종</label>
            <select
              value={regForm.industry}
              onChange={(e) => setRegForm((f) => ({ ...f, industry: e.target.value }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 bg-white"
            >
              <option value="">선택 안함</option>
              {INDUSTRY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">기업 규모</label>
            <div className="flex gap-4">
              {SCALE_OPTIONS.map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="scale"
                    value={opt.value}
                    checked={regForm.scale === opt.value}
                    onChange={() => setRegForm((f) => ({ ...f, scale: opt.value }))}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-neutral-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">주소</label>
            <input
              type="text"
              value={regForm.address}
              onChange={(e) => setRegForm((f) => ({ ...f, address: e.target.value }))}
              placeholder="서울특별시 강남구 테헤란로 123"
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">전화번호</label>
            <input
              type="tel"
              value={regForm.phone}
              onChange={(e) => setRegForm((f) => ({ ...f, phone: e.target.value }))}
              placeholder="02-1234-5678"
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">회사 소개</label>
            <textarea
              value={regForm.description}
              onChange={(e) => setRegForm((f) => ({ ...f, description: e.target.value }))}
              rows={4}
              placeholder="회사 소개를 입력하세요..."
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? '등록 중...' : '등록'}
            </button>
          </div>
        </form>
      </div>
    );
  }

  // ===== 등록 완료: 카드 뷰 또는 수정 폼 =====

  const handleEditClick = () => {
    setEditForm({
      name: company.name,
      ceoName: company.ceoName ?? '',
      address: company.address ?? '',
      phone: company.phone ?? '',
      industry: company.industry ?? '',
      scale: company.scale,
      description: company.description ?? '',
    });
    setFormError(null);
    setFieldErrors({});
    setIsEditMode(true);
  };

  const handleEditCancel = () => {
    setIsEditMode(false);
    setFormError(null);
    setFieldErrors({});
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});
    setFormError(null);

    if (!editForm.name.trim()) {
      setFieldErrors({ name: '회사명을 입력해주세요.' });
      return;
    }

    setIsSaving(true);
    try {
      await updateCompany(company.id, editForm);
      setIsEditMode(false);
      showToast('회사 정보가 수정되었습니다.');
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      setFormError(httpErr?.message ?? '수정에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  const scaleLabel: Record<string, string> = {
    small: '소기업',
    medium: '중기업',
    large: '대기업',
  };

  const formatBizNum = (num: string) => {
    if (num.length === 10) return `${num.slice(0, 3)}-${num.slice(3, 5)}-${num.slice(5)}`;
    return num;
  };

  if (isEditMode) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm p-6">
        <h3 className="text-base font-semibold text-neutral-900 mb-5">회사 기본 정보 수정</h3>

        {formError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-300 rounded-md text-sm text-red-700">
            {formError}
          </div>
        )}

        <form onSubmit={handleEditSubmit} className="space-y-4">
          <BusinessNumberInput
            value={company.businessNumber}
            onChange={() => {}}
            disabled
          />

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">
              회사명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={editForm.name}
              onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
              className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${fieldErrors.name ? 'border-red-500' : 'border-neutral-200'}`}
            />
            {fieldErrors.name && <p className="mt-1 text-sm text-red-600">{fieldErrors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">대표자명</label>
            <input
              type="text"
              value={editForm.ceoName}
              onChange={(e) => setEditForm((f) => ({ ...f, ceoName: e.target.value }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">업종</label>
            <select
              value={editForm.industry}
              onChange={(e) => setEditForm((f) => ({ ...f, industry: e.target.value }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 bg-white"
            >
              <option value="">선택 안함</option>
              {INDUSTRY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">기업 규모</label>
            <div className="flex gap-4">
              {SCALE_OPTIONS.map((opt) => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="editScale"
                    value={opt.value}
                    checked={editForm.scale === opt.value}
                    onChange={() => setEditForm((f) => ({ ...f, scale: opt.value }))}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-neutral-700">{opt.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">주소</label>
            <input
              type="text"
              value={editForm.address}
              onChange={(e) => setEditForm((f) => ({ ...f, address: e.target.value }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">전화번호</label>
            <input
              type="tel"
              value={editForm.phone}
              onChange={(e) => setEditForm((f) => ({ ...f, phone: e.target.value }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">회사 소개</label>
            <textarea
              value={editForm.description}
              onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
              rows={4}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? '저장 중...' : '저장'}
            </button>
            <button
              type="button"
              onClick={handleEditCancel}
              className="px-5 py-2.5 border border-neutral-300 text-neutral-700 text-sm font-medium rounded-md hover:bg-neutral-50 transition-colors"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    );
  }

  // 카드 뷰
  const infoRows = [
    { label: '사업자등록번호', value: formatBizNum(company.businessNumber) },
    { label: '회사명', value: company.name },
    { label: '대표자명', value: company.ceoName },
    { label: '업종', value: company.industry },
    { label: '기업 규모', value: company.scale ? scaleLabel[company.scale] : undefined },
    { label: '주소', value: company.address },
    { label: '전화번호', value: company.phone },
  ];

  return (
    <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-100">
        <h3 className="text-base font-semibold text-neutral-900">회사 기본 정보</h3>
        {canEdit && (
          <button
            type="button"
            onClick={handleEditClick}
            className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors"
          >
            수정
          </button>
        )}
      </div>

      <div className="divide-y divide-neutral-100">
        {infoRows.map((row) => (
          <div key={row.label} className="flex px-6 py-3">
            <span className="w-36 flex-shrink-0 text-sm text-neutral-500">{row.label}</span>
            <span className="text-sm text-neutral-900">{row.value ?? '-'}</span>
          </div>
        ))}
      </div>

      {company.description && (
        <div className="px-6 py-4 border-t border-neutral-100">
          <p className="text-sm text-neutral-500 mb-1">회사 소개</p>
          <p className="text-sm text-neutral-900 whitespace-pre-wrap">{company.description}</p>
        </div>
      )}
    </div>
  );
}
