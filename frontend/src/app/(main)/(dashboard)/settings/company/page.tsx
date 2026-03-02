'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useCompanyStore } from '@/lib/stores/company-store';
import { useMemberStore } from '@/lib/stores/member-store';
import CompanyBasicInfoTab from '@/components/company/CompanyBasicInfoTab';
import PerformanceTab from '@/components/company/PerformanceTab';
import CertificationTab from '@/components/company/CertificationTab';
import MemberTab from '@/components/company/MemberTab';

type TabKey = 'basic' | 'performance' | 'certification' | 'member';

const TABS: { key: TabKey; label: string }[] = [
  { key: 'basic', label: '기본 정보' },
  { key: 'performance', label: '수행 실적' },
  { key: 'certification', label: '보유 인증' },
  { key: 'member', label: '멤버 관리' },
];

function Breadcrumb() {
  return (
    <nav className="flex items-center gap-2 text-sm text-neutral-500 mb-4">
      <Link href="/dashboard" className="hover:text-neutral-700 transition-colors">
        대시보드
      </Link>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
      <span className="text-neutral-400">설정</span>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
      <span className="text-neutral-900 font-medium">회사 프로필</span>
    </nav>
  );
}

export default function CompanyProfilePage() {
  const { company, isLoading, currentUserRole, fetchMyCompany, setCurrentUserRole } =
    useCompanyStore();
  const { members } = useMemberStore();

  const [activeTab, setActiveTab] = useState<TabKey>('basic');

  // URL hash 기반 탭 동기화
  useEffect(() => {
    const hash = window.location.hash.replace('#', '') as TabKey;
    if (TABS.some((t) => t.key === hash)) {
      setActiveTab(hash);
    }
  }, []);

  const handleTabChange = useCallback((tab: TabKey) => {
    setActiveTab(tab);
    window.history.replaceState(null, '', `#${tab}`);
  }, []);

  // 회사 정보 및 역할 초기화
  useEffect(() => {
    fetchMyCompany();
  }, [fetchMyCompany]);

  // members에서 현재 사용자 역할 감지 (임시: 가장 먼저 나온 owner)
  useEffect(() => {
    if (company && members.length > 0) {
      // TODO: 실제 currentUserId를 auth store에서 가져와서 비교
      // 현재는 첫 owner를 기준으로 임시 설정
      const ownerMember = members.find((m) => m.role === 'owner');
      if (ownerMember) {
        setCurrentUserRole('owner');
      }
    } else if (!currentUserRole) {
      // 회사 등록 시 owner로 설정
      setCurrentUserRole(null);
    }
  }, [company, members, setCurrentUserRole, currentUserRole]);

  return (
    <div className="px-6 py-8 max-w-[960px] mx-auto">
      <Breadcrumb />

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-neutral-900">회사 프로필</h1>
        <p className="text-sm text-neutral-500 mt-1">
          회사 기본 정보, 수행 실적, 인증을 관리합니다.
        </p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="border-b border-neutral-200 mb-6 overflow-x-auto">
        <div className="flex gap-1 min-w-max">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleTabChange(tab.key)}
              className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 탭 콘텐츠 */}
      <div>
        {activeTab === 'basic' && (
          <CompanyBasicInfoTab currentUserRole={currentUserRole} />
        )}

        {activeTab === 'performance' && (
          company ? (
            <PerformanceTab companyId={company.id} currentUserRole={currentUserRole} />
          ) : (
            <div className="text-sm text-neutral-500 py-8 text-center">
              먼저 기본 정보 탭에서 회사를 등록해주세요.
            </div>
          )
        )}

        {activeTab === 'certification' && (
          company ? (
            <CertificationTab companyId={company.id} currentUserRole={currentUserRole} />
          ) : (
            <div className="text-sm text-neutral-500 py-8 text-center">
              먼저 기본 정보 탭에서 회사를 등록해주세요.
            </div>
          )
        )}

        {activeTab === 'member' && (
          company ? (
            <MemberTab
              companyId={company.id}
              currentUserRole={currentUserRole}
            />
          ) : (
            <div className="text-sm text-neutral-500 py-8 text-center">
              먼저 기본 정보 탭에서 회사를 등록해주세요.
            </div>
          )
        )}
      </div>

      {/* 로딩 오버레이 (초기 로딩 시) */}
      {isLoading && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-white bg-opacity-70">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
