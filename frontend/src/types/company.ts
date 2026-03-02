/**
 * F-08 회사 프로필 관련 TypeScript 타입 정의
 */

export type CompanyScale = 'small' | 'medium' | 'large';
export type ClientType = 'public' | 'private';
export type PerformanceStatus = 'completed' | 'ongoing';
export type MemberRole = 'owner' | 'admin' | 'member';

// ========== Company ==========

export interface Company {
  id: string;
  businessNumber: string;
  name: string;
  ceoName?: string;
  address?: string;
  phone?: string;
  industry?: string;
  scale?: CompanyScale;
  description?: string;
  memberCount: number;
  performanceCount: number;
  certificationCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CompanyCreateRequest {
  businessNumber: string;
  name: string;
  ceoName?: string;
  address?: string;
  phone?: string;
  industry?: string;
  scale?: CompanyScale;
  description?: string;
}

export interface CompanyUpdateRequest {
  name: string;
  ceoName?: string;
  address?: string;
  phone?: string;
  industry?: string;
  scale?: CompanyScale;
  description?: string;
}

// ========== Performance (수행 실적) ==========

export interface Performance {
  id: string;
  companyId: string;
  projectName: string;
  clientName: string;
  clientType?: ClientType;
  contractAmount: number;
  startDate: string;
  endDate: string;
  status: PerformanceStatus;
  description?: string;
  isRepresentative: boolean;
  documentUrl?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface PerformanceCreateRequest {
  projectName: string;
  clientName: string;
  clientType?: ClientType;
  contractAmount: number;
  startDate: string;
  endDate: string;
  status: PerformanceStatus;
  description?: string;
  isRepresentative?: boolean;
  documentUrl?: string;
}

export type PerformanceUpdateRequest = PerformanceCreateRequest;

export interface ListPerformancesParams {
  page?: number;
  pageSize?: number;
  status?: PerformanceStatus | 'all';
  isRepresentative?: boolean;
  sortBy?: 'createdAt' | 'contractAmount' | 'startDate';
  sortOrder?: 'asc' | 'desc';
}

// ========== Certification (보유 인증) ==========

export interface Certification {
  id: string;
  companyId: string;
  name: string;
  issuer?: string;
  certNumber?: string;
  issuedDate?: string;
  expiryDate?: string;
  documentUrl?: string;
  isExpired?: boolean;
  createdAt: string;
  updatedAt?: string;
}

export interface CertificationCreateRequest {
  name: string;
  issuer?: string;
  certNumber?: string;
  issuedDate?: string;
  expiryDate?: string;
  documentUrl?: string;
}

export type CertificationUpdateRequest = CertificationCreateRequest;

export interface ListCertificationsParams {
  page?: number;
  pageSize?: number;
  sortBy?: 'createdAt' | 'expiryDate' | 'name';
  sortOrder?: 'asc' | 'desc';
}

// ========== Member (멤버) ==========

export interface Member {
  id: string;
  userId: string;
  email: string;
  name: string;
  role: MemberRole;
  invitedAt?: string;
  joinedAt?: string;
}

export interface MemberInviteRequest {
  email: string;
  role: 'admin' | 'member';
}

export interface ListMembersParams {
  page?: number;
  pageSize?: number;
}

// ========== Common ==========

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
