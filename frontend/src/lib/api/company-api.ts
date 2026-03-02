/**
 * F-08 회사 프로필 API 클라이언트
 */
import { apiClient, PaginationMeta } from './client';
import type {
  Company,
  CompanyCreateRequest,
  CompanyUpdateRequest,
  Performance,
  PerformanceCreateRequest,
  PerformanceUpdateRequest,
  Certification,
  CertificationCreateRequest,
  CertificationUpdateRequest,
  Member,
  MemberInviteRequest,
  ListPerformancesParams,
  ListCertificationsParams,
  ListMembersParams,
} from '@/types/company';

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  }
  const qs = searchParams.toString();
  return qs ? `?${qs}` : '';
}

export const companyApi = {
  // ===== Company =====

  createCompany: async (data: CompanyCreateRequest): Promise<Company> => {
    return apiClient.post<Company>('/companies', data);
  },

  getMyCompany: async (): Promise<Company> => {
    return apiClient.get<Company>('/companies/my');
  },

  updateCompany: async (id: string, data: CompanyUpdateRequest): Promise<Company> => {
    return apiClient.put<Company>(`/companies/${id}`, data);
  },

  // ===== Performance (수행 실적) =====

  createPerformance: async (
    companyId: string,
    data: PerformanceCreateRequest
  ): Promise<Performance> => {
    return apiClient.post<Performance>(`/companies/${companyId}/performances`, data);
  },

  listPerformances: async (
    companyId: string,
    params?: ListPerformancesParams
  ): Promise<{ items: Performance[]; meta?: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      status: params?.status !== 'all' ? params?.status : undefined,
      isRepresentative: params?.isRepresentative,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    return apiClient.getList<Performance>(`/companies/${companyId}/performances${query}`);
  },

  updatePerformance: async (
    companyId: string,
    perfId: string,
    data: PerformanceUpdateRequest
  ): Promise<Performance> => {
    return apiClient.put<Performance>(`/companies/${companyId}/performances/${perfId}`, data);
  },

  deletePerformance: async (companyId: string, perfId: string): Promise<void> => {
    await apiClient.delete(`/companies/${companyId}/performances/${perfId}`);
  },

  setRepresentative: async (
    companyId: string,
    perfId: string,
    isRepresentative: boolean
  ): Promise<Performance> => {
    return apiClient.patch<Performance>(
      `/companies/${companyId}/performances/${perfId}/representative`,
      { isRepresentative }
    );
  },

  // ===== Certification (보유 인증) =====

  createCertification: async (
    companyId: string,
    data: CertificationCreateRequest
  ): Promise<Certification> => {
    return apiClient.post<Certification>(`/companies/${companyId}/certifications`, data);
  },

  listCertifications: async (
    companyId: string,
    params?: ListCertificationsParams
  ): Promise<{ items: Certification[]; meta?: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
      sortBy: params?.sortBy,
      sortOrder: params?.sortOrder,
    });
    return apiClient.getList<Certification>(`/companies/${companyId}/certifications${query}`);
  },

  updateCertification: async (
    companyId: string,
    certId: string,
    data: CertificationUpdateRequest
  ): Promise<Certification> => {
    return apiClient.put<Certification>(
      `/companies/${companyId}/certifications/${certId}`,
      data
    );
  },

  deleteCertification: async (companyId: string, certId: string): Promise<void> => {
    await apiClient.delete(`/companies/${companyId}/certifications/${certId}`);
  },

  // ===== Member (멤버) =====

  inviteMember: async (companyId: string, data: MemberInviteRequest): Promise<Member> => {
    return apiClient.post<Member>(`/companies/${companyId}/members`, data);
  },

  listMembers: async (
    companyId: string,
    params?: ListMembersParams
  ): Promise<{ items: Member[]; meta?: PaginationMeta }> => {
    const query = buildQuery({
      page: params?.page,
      pageSize: params?.pageSize,
    });
    return apiClient.getList<Member>(`/companies/${companyId}/members${query}`);
  },
};
