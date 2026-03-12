# BidMaster 로드맵

## 마일스톤 현황

### M0: 인증/프로필 ✅ 완료
- F-07: 사용자 인증 ✅
- F-08: 회사 프로필 ✅

### M1: 공고 수집/분석 ✅ 완료
- F-01: 공고 자동 수집 및 매칭 ✅
- F-02: 낙찰 가능성 스코어링 ✅
- F-04: 낙찰가 예측 및 투찰 전략 ✅

### M2: 제안서/대시보드/알림 🔄 진행 중
- F-03: 제안서 AI 초안 생성 ✅ (백엔드 완료)
- F-06: 입찰 현황 대시보드 ✅ (백엔드 완료)
- F-10: 알림 시스템 ✅ (백엔드 완료)
- F-05: 제안서 편집기 ⏳ (프론트엔드 대기)
- F-09: 결제 및 구독 관리 ⏳ (계획 중)

### M3~M5: 대기 중
- F-11: 팀 협업 ⏳
- F-12: 히스토리 및 분석 ⏳
- F-13: 제안서 템플릿 ⏳
- F-14: PDF/DOCX 내보내기 ⏳
- F-15~F-36: 추가 기능 (계획 중)

---

## F-03 제안서 AI 초안 생성

### 구현 완료 항목
| 파일 | 설명 |
|------|------|
| `models/proposal.py` | Proposal 모델 |
| `models/proposal_section.py` | ProposalSection 모델 (6개 기본 섹션) |
| `models/proposal_version.py` | ProposalVersion 모델 (버전 스냅샷) |
| `schemas/proposal.py` | Pydantic 스키마 (요청/응답) |
| `services/proposal_service.py` | CRUD 서비스 |
| `services/proposal_generator_service.py` | AI 생성 서비스 (GLM API) |
| `api/v1/proposals.py` | API 엔드포인트 (SSE 스트리밍) |
| `templates/prompts/*.jinja2` | Jinja2 프롬프트 템플릿 |
| `alembic/versions/002_add_f03_proposals.py` | DB 마이그레이션 |
| `tests/f03/test_proposal_service.py` | 테스트 코드 |

### 기술 스택
- **AI 모델**: GLM API (`zhipuai>=2.0.0`)
- **스트리밍**: SSE (Server-Sent Events)
- **버전 관리**: 제안서 버전 생성/복원
- **상태 전환**: draft → generating → ready → submitted
- **섹션**: overview, technical, methodology, schedule, organization, budget

### 코드 리뷰 완료 사항 (2026-03-12)
| 항목 | 상태 | 설명 |
|------|------|------|
| `word_count` | ✅ 적절 | 한국어 텍스트는 글자 수(`len()`) 사용이 적절 |
| `section_metadata` | ✅ 해결 | `mapped_column("metadata", ...)`로 SQLAlchemy 충돌 방지 |
| `bid.requirements` | ✅ 해결 | `bid.requirements or []`로 null 체크 구현됨 |
| `bid.deadline` | ✅ 해결 | `if bid.deadline else ""`로 null 체크 구현됨 |

### API 엔드포인트
- `GET /api/v1/proposals` - 제안서 목록 조회
- `POST /api/v1/proposals` - 빈 제안서 생성
- `GET /api/v1/proposals/{id}` - 제안서 상세 조회
- `PATCH /api/v1/proposals/{id}` - 제안서 수정
- `DELETE /api/v1/proposals/{id}` - 제안서 삭제
- `POST /api/v1/proposals/{id}/generate` - AI 생성 (SSE)
- `PATCH /api/v1/proposals/{id}/sections/{key}` - 섹션 수정
- `POST /api/v1/proposals/{id}/sections/{key}/regenerate` - 섹션 재생성
- `POST /api/v1/proposals/{id}/versions` - 버전 생성
- `POST /api/v1/proposals/{id}/versions/{n}/restore` - 버전 복원
- `POST /api/v1/proposals/{id}/submit` - 제안서 제출
- `POST /api/v1/proposals/{id}/export` - 내보내기 (스텁)

### 내보내기 (스텁)
PDF/DOCX/HWP 내보내기 기능은 추후 구현 예정

---

## F-06 입찰 현황 대시보드

백엔드 완료, 프론트엔드 대기

---

## F-10 알림 시스템

백엔드 완료, 프론트엔드 대기
