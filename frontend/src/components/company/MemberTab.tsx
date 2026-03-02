'use client';

import { useEffect, useState } from 'react';
import { useMemberStore } from '@/lib/stores/member-store';
import RoleBadge from '@/components/ui/RoleBadge';
import { showToast } from '@/components/ui/Toast';
import type { MemberInviteRequest, MemberRole } from '@/types/company';
import { HttpError } from '@/lib/api/client';

interface MemberTabProps {
  companyId: string;
  currentUserRole: MemberRole | null;
  currentUserId?: string;
}

function InviteModal({
  isOpen,
  onClose,
  companyId,
}: {
  isOpen: boolean;
  onClose: () => void;
  companyId: string;
}) {
  const { inviteMember, isInviting } = useMemberStore();
  const [form, setForm] = useState<MemberInviteRequest>({ email: '', role: 'member' });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (isOpen) {
      setForm({ email: '', role: 'member' });
      setErrors({});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.email.trim()) errs.email = '이메일을 입력해주세요.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = '유효한 이메일 주소를 입력해주세요.';
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    try {
      await inviteMember(companyId, form);
      showToast('팀원이 초대되었습니다.');
      onClose();
    } catch (err: unknown) {
      const httpErr = err as HttpError;
      if (httpErr?.code === 'COMPANY_008') {
        setErrors({ email: '해당 이메일로 등록된 사용자를 찾을 수 없습니다.' });
      } else if (httpErr?.code === 'COMPANY_009') {
        setErrors({ email: '이미 해당 회사의 멤버입니다.' });
      } else if (httpErr?.code === 'COMPANY_010') {
        setErrors({ email: '대상 사용자가 이미 다른 회사에 소속되어 있습니다.' });
      } else {
        showToast(httpErr?.message ?? '초대에 실패했습니다.', 'error');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black opacity-40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200">
          <h2 className="text-lg font-bold text-neutral-900">팀원 초대</h2>
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
              이메일 <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              placeholder="member@example.com"
              className={`block w-full px-3 py-2.5 border rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 ${errors.email ? 'border-red-500' : 'border-neutral-200'}`}
            />
            {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-1">역할</label>
            <select
              value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as 'admin' | 'member' }))}
              className="block w-full px-3 py-2.5 border border-neutral-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:border-blue-500 focus:ring-blue-500 bg-white"
            >
              <option value="member">멤버</option>
              <option value="admin">관리자</option>
            </select>
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
              disabled={isInviting}
              className="flex-1 px-4 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isInviting ? '초대 중...' : '초대'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function MemberTab({ companyId, currentUserRole, currentUserId }: MemberTabProps) {
  const {
    members,
    isLoading,
    isInviteModalOpen,
    fetchMembers,
    openInviteModal,
    closeInviteModal,
  } = useMemberStore();

  const canInvite = currentUserRole === 'owner' || currentUserRole === 'admin';

  useEffect(() => {
    fetchMembers(companyId);
  }, [companyId, fetchMembers]);

  if (isLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm animate-pulse">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex items-center px-6 py-4 border-b border-neutral-100 last:border-0 gap-4">
            <div className="h-10 w-10 bg-neutral-200 rounded-full" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-32 bg-neutral-200 rounded" />
              <div className="h-3 w-48 bg-neutral-200 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-neutral-500">총 {members.length}명</span>
        {canInvite && (
          <button
            type="button"
            onClick={openInviteModal}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 transition-colors"
          >
            + 팀원 초대
          </button>
        )}
      </div>

      {!canInvite && currentUserRole === 'member' && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-700">
          목록 조회만 가능합니다. 초대/제거는 관리자에게 문의하세요.
        </div>
      )}

      <div className="bg-white border border-neutral-200 rounded-lg shadow-sm">
        {/* 데스크탑 테이블 */}
        <div className="hidden md:block">
          <table className="w-full">
            <thead className="bg-neutral-50 border-b border-neutral-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-neutral-500">이름</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-neutral-500">이메일</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-neutral-500">역할</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-neutral-500">가입일</th>
                {canInvite && <th className="px-6 py-3" />}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {members.map((member) => {
                const isCurrentUser = member.userId === currentUserId;
                const isOwner = member.role === 'owner';
                const canRemove =
                  canInvite &&
                  !isOwner &&
                  !isCurrentUser &&
                  (currentUserRole === 'owner' ||
                    (currentUserRole === 'admin' && member.role !== 'owner'));

                return (
                  <tr key={member.id}>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-700">
                          {member.name.charAt(0)}
                        </div>
                        <span className="text-sm font-medium text-neutral-900">
                          {member.name}
                          {isCurrentUser && (
                            <span className="ml-1 text-xs text-neutral-400">(나)</span>
                          )}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-600">{member.email}</td>
                    <td className="px-6 py-4">
                      <RoleBadge role={member.role} />
                    </td>
                    <td className="px-6 py-4 text-sm text-neutral-500">
                      {member.joinedAt ? member.joinedAt.slice(0, 10) : '-'}
                    </td>
                    {canInvite && (
                      <td className="px-6 py-4">
                        {canRemove && (
                          <button
                            type="button"
                            className="text-xs text-red-500 hover:text-red-600 font-medium"
                          >
                            제거
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 모바일 카드형 */}
        <div className="md:hidden divide-y divide-neutral-100">
          {members.map((member) => {
            const isCurrentUser = member.userId === currentUserId;
            return (
              <div key={member.id} className="flex items-center gap-3 px-4 py-4">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-sm font-semibold text-blue-700 flex-shrink-0">
                  {member.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-neutral-900 truncate">{member.name}</p>
                    {isCurrentUser && <span className="text-xs text-neutral-400">(나)</span>}
                  </div>
                  <p className="text-xs text-neutral-500 truncate">{member.email}</p>
                </div>
                <RoleBadge role={member.role} />
              </div>
            );
          })}
        </div>
      </div>

      <InviteModal
        isOpen={isInviteModalOpen}
        onClose={closeInviteModal}
        companyId={companyId}
      />
    </div>
  );
}
