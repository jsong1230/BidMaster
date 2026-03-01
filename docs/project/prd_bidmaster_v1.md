# PRD: 비드마스터 (BidMaster)
## AI 기반 공공 입찰 제안서 자동화 SaaS — Product Requirements Document

**버전:** v1.0  
**작성일:** 2026-03-01  
**기술 스택:** Next.js 14 (App Router) + FastAPI (Python 3.12)  
**AI 파이프라인:** Claude Code 멀티에이전트 (기능별 에이전트 분리)  
**초기 집중 도메인:** IT 용역 / SI / 소프트웨어 개발 사업  
**상태:** Development Ready

---

## 목차

1. [제품 개요](#1-제품-개요)
2. [목표 사용자](#2-목표-사용자)
3. [핵심 기능 명세](#3-핵심-기능-명세)
4. [DB 스키마](#4-db-스키마)
5. [API 엔드포인트 명세](#5-api-엔드포인트-명세)
6. [Claude 프롬프트 설계](#6-claude-프롬프트-설계)
7. [Claude Code 멀티에이전트 아키텍처](#7-claude-code-멀티에이전트-아키텍처)
8. [외부 데이터 연동](#8-외부-데이터-연동)
9. [기술 스택 상세](#9-기술-스택-상세)
10. [수익 모델](#10-수익-모델)
11. [마케팅/GTM 전략](#11-마케팅gtm-전략)
12. [리스크 분석](#12-리스크-분석)
13. [성공 지표](#13-성공-지표)
14. [마일스톤](#14-마일스톤)

---

## 1. 제품 개요

### 1.1 제품 비전

> "대한민국 중소기업이 AI를 활용해 공공 입찰 제안서를 스스로 작성하고, 낙찰 가능성을 데이터로 판단할 수 있는 입찰 자동화 플랫폼"

### 1.2 문제 정의

| 문제 | 규모 | 임팩트 |
|------|------|--------|
| 공공조달 시장 연간 200조원 규모 | 나라장터 등록 기업 50만개 이상 | 거대한 타깃 시장 |
| 제안서 대행업체 비용 건당 300만~2,000만원 | 중소기업 연간 수천만원 지출 | 핵심 비용 절감 포인트 |
| 낙찰률 10~30% — 비용 대비 불확실한 ROI | 낙찰 실패 시 비용 전액 손실 | 리스크 집중 |
| 공고 분석에 담당자 1~3일 소요 | 놓치는 적합 공고 다수 발생 | 기회 손실 |
| 제안서 노하우의 개인 의존 | 담당자 퇴사 시 역량 소실 | 조직 리스크 |
| 기존 대행업체: 템플릿 + 경험으로 운영 | AI 대체 가능성 높은 반복 작업 | 진입 기회 |

### 1.3 솔루션 요약

비드마스터는 AI를 활용해 다음 6개 핵심 기능을 제공한다:

1. **공고 자동 수집 및 매칭** — 나라장터 공고 스크래핑 → 회사 역량 기반 적합도 분석
2. **낙찰 가능성 스코어링** — 과거 낙찰 데이터 분석 → 입찰 참여 여부 추천
3. **제안서 AI 초안 생성** — 공고 분석 + 회사 프로필 → 섹션별 제안서 자동 생성
4. **낙찰가 예측** — 유사 낙찰가 분석 → 최적 투찰가 추천
5. **제안서 편집기** — 실시간 AI 어시스턴트 + 평가 기준별 체크리스트
6. **입찰 현황 대시보드** — 참여 중인 공고 현황, 낙찰 이력, ROI 분석

### 1.4 포지셔닝

| 구분 | 기존 대행업체 | 나라장터 기본 | **비드마스터** |
|------|------------|-------------|-------------|
| 제안서 비용 | 300만~2,000만원/건 | 직접 작성 (무료) | **30~100만원/건** |
| 공고 분석 속도 | 2~3일 | 직접 검색 | **실시간 자동 매칭** |
| 낙찰 가능성 분석 | 경험 기반 주관적 | 불가 | **데이터 기반 스코어** |
| 낙찰가 예측 | 경험 기반 | 불가 | **AI 분석** |
| 제안서 품질 편차 | 담당자 의존 | 없음 | **표준화된 고품질** |
| 서비스 속도 | 1~2주 | - | **24시간 이내** |

---

## 2. 목표 사용자

### 2.1 Primary Persona: 중소 IT 기업 대표/영업팀장

- **인구통계:** 직원 10~100명 / IT 용역·SI·소프트웨어 업종 / 연 매출 10억~200억원
- **Pain Points:**
  - "제안서 쓰는 데 일주일을 써요. 다른 일을 못해요."
  - "대행업체에 맡기면 500만원인데 떨어지면 그냥 날리는 거잖아요."
  - "어떤 공고에 들어가야 하는지 판단하기가 어려워요."
  - "비슷한 공고를 매번 처음부터 다시 쓰는 게 너무 비효율적이에요."
  - "심사위원이 뭘 중요하게 보는지 모르겠어요."
- **행동 패턴:** 나라장터 매일 확인, 카테고리별 수기 정리, 영업팀 회의에서 공고 선별

### 2.2 Secondary Persona: 중소기업 입찰 담당자 (1~3년차)

- **인구통계:** 20~35대 / 영업지원·기획팀 소속 / IT 친숙도 높음
- **Pain Points:**
  - "혼자서 5~10개 공고를 동시에 관리해야 해요."
  - "전임자가 만들어 둔 제안서 파일이 어딘지도 모르겠어요."
  - "어디까지 가져다 쓰는 게 표절인지 헷갈려요."
  - "평가 기준을 다 충족했는지 체크하기가 힘들어요."

### 2.3 Tertiary Persona: 제안서 대행 프리랜서

- **역할:** 비드마스터를 도구로 사용해 생산성을 높이는 파트너
- **동기:** 동시에 더 많은 고객 처리 가능, AI 초안으로 고부가가치 작업 집중

---

## 3. 핵심 기능 명세

### Feature 1: 공고 자동 수집 및 매칭

#### 개요
나라장터 및 각 기관 조달 시스템에서 공고를 자동 수집하고, 등록된 회사 프로필과 매칭해 적합도 점수를 산출한다. 서비스의 Daily Active Use를 만드는 핵심 기능.

#### 수집 대상 공고 유형 (MVP: IT 용역 집중)

```
[공고 유형 코드 — 나라장터 분류 기준]
- 용역: IT 용역, 소프트웨어 개발, 시스템 유지보수
- 물품: 소프트웨어 패키지, 하드웨어 (추후)
- 공사: 정보통신 공사 (추후)

[주요 발주 기관 유형]
- 중앙부처 (행안부, 과기부, 복지부 등)
- 지방자치단체
- 공공기관 (공기업, 준정부기관)
- 교육기관 (대학, 연구기관)
```

#### 회사 프로필 매칭 기준

```
매칭 점수 산출 요소 (총 100점):
  - 업종 코드 일치 여부: 30점
  - 과거 수행 사업 유사도: 25점
  - 요구 기술 스택 보유 여부: 20점
  - 규모 적합성 (사업금액 vs 회사 규모): 15점
  - 지역 접근성: 10점
```

#### Happy Path
1. 시스템이 매일 06:00, 12:00, 18:00 나라장터 자동 크롤링
2. 신규 공고 파싱: 제목, 발주기관, 예산금액, 납기, 평가방식, 첨부파일
3. 회사 프로필과 AI 매칭 분석
4. 매칭 점수 70점 이상 공고 → 알림 발송 (이메일/카카오)
5. 대시보드에 "오늘의 추천 공고" 표시

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-001 | 나라장터 공고 자동 크롤링 (1일 3회) | P0 |
| FR-002 | 공고 원문 파싱: 제목, 기관, 예산, 납기, 평가방식, 첨부파일 | P0 |
| FR-003 | 첨부 RFP(PDF/HWP) 자동 텍스트 추출 | P0 |
| FR-004 | 회사 프로필 기반 AI 적합도 점수 산출 | P0 |
| FR-005 | 적합도 70점 이상 공고 실시간 알림 | P1 |
| FR-006 | 공고 키워드 필터 설정 (사용자별 커스텀) | P1 |
| FR-007 | 공고 북마크 및 참여 여부 상태 관리 | P1 |
| FR-008 | 공고 원문 뷰어 (PDF/HWP 인라인 뷰) | P2 |
| FR-009 | 공고 히스토리 검색 (과거 6개월) | P2 |
| FR-010 | 유사 과거 낙찰 공고 함께 표시 | P2 |

#### 수락 기준

- AC-001: 나라장터 신규 공고 수집 지연 4시간 이내 (크롤링 주기 기준)
- AC-002: RFP 텍스트 추출 성공률 95% 이상 (PDF 기준, HWP 별도)
- AC-003: 매칭 점수 산출 시간 30초 이내
- AC-004: 알림 발송 성공률 99% 이상

#### 에러 케이스

| 케이스 | 처리 방식 |
|--------|---------|
| 나라장터 크롤링 차단/타임아웃 | 지수 백오프 재시도 (3회), 실패 시 관리자 알림 |
| HWP 파일 파싱 실패 | "원문 직접 확인" 링크 제공, PDF 변환 시도 |
| 첨부파일 없는 공고 | 공고 제목·본문만으로 분석, 낮은 신뢰도 표시 |
| 중복 공고 감지 | notice_id + 발주기관 복합 키로 중복 제거 |

---

### Feature 2: 낙찰 가능성 스코어링

#### 개요
공고별로 우리 회사의 낙찰 가능성을 데이터 기반으로 점수화한다. 입찰 참여 여부 의사결정의 핵심 근거.

#### 스코어링 모델 설계

```
낙찰 가능성 점수 (0~100점) 산출 요소:

[경쟁 강도 분석: 30점]
  - 해당 기관의 과거 입찰 참여 업체 수 평균
  - 동일 규모 사업 경쟁사 수 추정
  - 제한 경쟁 여부 (지역 제한, 실적 제한 등)

[우리 회사 경쟁력: 35점]
  - 유사 수행 실적 보유 여부 및 점수
  - 요구 인증 보유 여부 (GS인증, ISO, ISMS 등)
  - 과거 동일 기관 수행 이력
  - 기술 점수 예상 (평가 항목 대비 역량)

[사업 적합도: 25점]
  - 예산 규모 vs 회사 역량
  - 납기 실현 가능성
  - 요구 기술 스택 일치도

[시장 환경: 10점]
  - 해당 분야 최근 낙찰가율 트렌드
  - 발주기관 예산 집행 패턴
```

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-020 | 공고별 낙찰 가능성 점수 자동 산출 | P0 |
| FR-021 | 점수 근거 상세 설명 (항목별 점수 분해) | P0 |
| FR-022 | 경쟁사 추정 리스트 (나라장터 낙찰 데이터 기반) | P1 |
| FR-023 | 입찰 참여 추천/비추천 AI 의견 | P0 |
| FR-024 | 유사 공고 과거 낙찰 결과 비교 | P1 |
| FR-025 | 우리 회사 취약 항목 개선 제안 | P2 |

#### 수락 기준

- AC-020: 스코어링 계산 시간 60초 이내
- AC-021: 점수 근거 항목별 100% 표시
- AC-022: 베타 기간 (3개월) 후 스코어 70점 이상 공고 실제 낙찰률 30% 이상 목표

---

### Feature 3: 제안서 AI 초안 생성

#### 개요
공고 RFP 분석 + 회사 프로필 + 과거 제안서를 종합하여 평가 기준에 최적화된 제안서 초안을 자동 생성한다. 서비스의 핵심 가치이자 주 수익원.

#### 제안서 표준 구조 (IT 용역 기준)

```
[필수 섹션]
1. 사업 이해 및 추진 전략
   1.1 발주기관 현황 및 사업 배경 이해
   1.2 사업 추진 전략 및 방법론
   1.3 핵심 성공 요소

2. 기술 방안
   2.1 요구사항 분석 및 구현 방안
   2.2 시스템 아키텍처
   2.3 개발 방법론 및 품질 관리
   2.4 보안 방안

3. 수행 계획
   3.1 사업 수행 조직
   3.2 세부 추진 일정 (WBS)
   3.3 단계별 산출물 목록

4. 유사 수행 실적
   4.1 대표 수행 실적 (상위 3건)
   4.2 수행 역량 요약

5. 회사 현황
   5.1 회사 개요
   5.2 보유 인증 및 수상 이력

[선택 섹션 — 공고 평가 항목에 따라 AI가 추가]
- 교육 훈련 계획
- 유지보수 방안
- 기술 이전 방안
- 오픈소스 활용 방안
```

#### Happy Path
1. 사용자가 공고 선택 → "제안서 생성" 클릭
2. 회사 프로필 확인 (기사업 실적, 보유 인증, 핵심 역량)
3. AI가 RFP 분석: 평가 항목, 배점표, 필수 요구사항 추출
4. 섹션별 AI 초안 생성 (스트리밍)
5. 사용자가 섹션별 편집
6. 평가 기준 체크리스트 자동 검증
7. HWP / Word / PDF 다운로드

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-030 | RFP 분석: 평가항목·배점·필수요구사항 자동 추출 | P0 |
| FR-031 | 섹션별 AI 초안 생성 (스트리밍) | P0 |
| FR-032 | 회사 프로필·과거 제안서 자동 반영 | P0 |
| FR-033 | 평가 기준 달성률 체크리스트 실시간 표시 | P0 |
| FR-034 | 섹션별 재생성 (프롬프트 커스텀) | P1 |
| FR-035 | Word(.docx) / PDF 다운로드 | P0 |
| FR-036 | HWP 변환 지원 (LibreOffice 기반) | P1 |
| FR-037 | 제안서 버전 관리 (자동 저장, v1→v2→...) | P1 |
| FR-038 | 공동 편집 (팀원 초대, 댓글) | P2 |
| FR-039 | 표절 위험 구간 하이라이트 | P2 |
| FR-040 | 유사 공고 제안서 참조 제안 | P1 |

#### 수락 기준

- AC-030: 10페이지 기준 초안 생성 시간 3분 이내
- AC-031: 평가 항목 반영률 90% 이상 (누락 항목 없음)
- AC-032: 생성된 초안 사용자 만족도 4.0/5.0 이상
- AC-033: Word 다운로드 완료 시간 10초 이내

#### 에러 케이스

| 케이스 | 처리 방식 |
|--------|---------|
| RFP 파싱 실패 (손상된 PDF) | 수동 텍스트 입력 폼 제공 |
| Claude API 타임아웃 | 섹션 단위 재시도, 부분 완료 저장 |
| 회사 프로필 미등록 | 프로필 등록 유도 화면 표시 |
| 토큰 한도 초과 (매우 긴 RFP) | RFP 청킹 처리, 요약 후 재시도 |

---

### Feature 4: 낙찰가 예측 및 투찰 전략

#### 개요
유사 공고의 과거 낙찰가 데이터를 분석하여 최적 투찰가 범위를 추천한다. 기술 평가 통과 후 가격 경쟁에서 핵심 역할.

#### 낙찰가 분석 로직

```
[입력 데이터]
- 공고 예산금액
- 사업 유형 (코드)
- 발주기관 유형
- 낙찰 방식 (최저가, 적격심사, 협상)
- 과거 유사 낙찰 데이터 (최근 2년, 동일 유형)

[분석 항목]
1. 낙찰가율 분포
   - 동일 사업 유형 낙찰가율 평균/표준편차
   - 발주기관별 낙찰가율 패턴
   - 최근 6개월 트렌드

2. 경쟁사 투찰 패턴 분석
   - 주요 경쟁사의 과거 투찰가율
   - 업계 평균 투찰가율

3. 추천 투찰 범위
   - 낙찰 확률 80% 이상 범위: 예산의 X%~Y%
   - 최적 투찰가: 예산의 Z%
   - 리스크 경고: 과도한 저가 경고 (하도급 단가 하락 주의)

[낙찰 방식별 전략 차이]
- 최저가 낙찰: 경쟁사 최저 투찰가 예측이 핵심
- 적격심사: 예산의 88~95% 범위가 일반적으로 유리
- 협상에 의한 계약: 기술 점수 + 가격 가중치 최적화
```

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-050 | 공고별 낙찰가율 분포 시각화 | P0 |
| FR-051 | 최적 투찰가 범위 AI 추천 | P0 |
| FR-052 | 낙찰 방식별 전략 가이드 | P1 |
| FR-053 | 경쟁사 과거 투찰 패턴 분석 | P1 |
| FR-054 | 투찰가 시뮬레이션 (X원 투찰 시 낙찰 확률) | P1 |
| FR-055 | 과거 동일 기관 낙찰 이력 조회 | P2 |

---

### Feature 5: 제안서 편집기

#### 개요
AI 초안을 기반으로 사용자가 실시간으로 편집하며 평가 기준 달성률을 확인할 수 있는 전용 편집 환경.

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-060 | 리치텍스트 편집기 (서식, 표, 이미지 삽입) | P0 |
| FR-061 | 우측 패널: 평가 기준 체크리스트 | P0 |
| FR-062 | AI 섹션 재생성 버튼 (커스텀 지시사항 입력) | P0 |
| FR-063 | AI 어시스턴트 사이드바 ("이 섹션 보완해줘") | P1 |
| FR-064 | 단어 수 / 페이지 수 실시간 표시 | P1 |
| FR-065 | 자동 저장 (30초 주기) + 버전 히스토리 | P1 |
| FR-066 | 팀원 공동 편집 (Operational Transformation) | P2 |
| FR-067 | 댓글 및 리뷰 기능 | P2 |
| FR-068 | 분량 제한 초과 시 경고 (공고별 페이지 제한) | P1 |
| FR-069 | 필수 항목 미기재 시 제출 전 경고 | P0 |

#### 수락 기준

- AC-060: 편집 지연(Latency) 100ms 이하 (로컬 기준)
- AC-061: 자동 저장 실패율 0.1% 이하
- AC-062: 버전 복원 성공률 100%

---

### Feature 6: 입찰 현황 대시보드

#### 개요
진행 중인 모든 입찰의 현황을 한눈에 파악하고, 낙찰 이력과 ROI를 분석하는 관리 허브.

#### 대시보드 구성 요소

```
[상단 KPI 카드]
  - 이번 달 참여 공고 수
  - 이번 달 제출 제안서 수
  - 현재 진행 중인 심사
  - 이번 달 낙찰 금액

[공고 파이프라인 (칸반 보드)]
  관심 → 분석 중 → 제안서 작성 → 제출 완료 → 심사 중 → 낙찰/탈락

[낙찰 성과 분석]
  - 월별 낙찰률 추이 그래프
  - 사업 유형별 낙찰률 비교
  - 제안서 점수 vs 낙찰 상관관계
  - ROI: 제안서 작성 비용 대비 낙찰 수익

[이번 주 마감 공고]
  - D-Day 카운트다운
  - 제출 준비 진행률 표시

[AI 인사이트]
  - "이번 달 놓친 적합 공고 N건"
  - "낙찰률 향상을 위한 추천 개선사항"
```

#### 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-070 | 입찰 파이프라인 칸반 보드 | P0 |
| FR-071 | 낙찰/탈락 결과 기록 | P0 |
| FR-072 | 월별 낙찰률 트렌드 시각화 | P1 |
| FR-073 | 마감 임박 공고 알림 (D-7, D-3, D-1) | P0 |
| FR-074 | 제안서 작성 비용 vs 낙찰 수익 ROI 분석 | P1 |
| FR-075 | 사업 유형별 성과 분석 | P2 |
| FR-076 | 팀원별 기여도 분석 | P2 |

---

## 4. DB 스키마

### 4.1 ERD 개요

```
users ─────────── companies ──────── company_profiles
   │                  │
   │              bid_notices ───── notice_attachments
   │                  │
   ├── subscriptions   ├── proposals ──── proposal_sections
   │                  │       │
   └── notifications   │       └── proposal_versions
                       │
                   bid_participations
                       │
                   ├── scoring_results
                   └── price_analyses

competitors ────── competitor_bids
notice_categories (마스터)
evaluation_criteria_templates (마스터)
```

### 4.2 테이블 정의

#### users (사용자)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    name            VARCHAR(100) NOT NULL,
    phone           VARCHAR(20),
    kakao_id        VARCHAR(100) UNIQUE,
    role            VARCHAR(20) NOT NULL DEFAULT 'owner'
                    CHECK (role IN ('owner', 'manager', 'member', 'admin')),
    plan            VARCHAR(20) NOT NULL DEFAULT 'free'
                    CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    plan_expires_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### companies (회사)

```sql
CREATE TABLE companies (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id                UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name            VARCHAR(200) NOT NULL,
    business_number         VARCHAR(20) UNIQUE NOT NULL,         -- 사업자등록번호
    representative_name     VARCHAR(100) NOT NULL,
    industry_codes          TEXT[] NOT NULL,                     -- 나라장터 업종 코드 배열
    employee_count          INTEGER,
    annual_revenue          BIGINT,                              -- 연 매출 (원)
    address                 TEXT,
    phone                   VARCHAR(20),
    website                 VARCHAR(500),
    founded_year            INTEGER,
    certifications          JSONB DEFAULT '[]',                  -- 보유 인증 목록
    -- 입찰 통계 (캐시)
    total_bids              INTEGER DEFAULT 0,
    won_bids                INTEGER DEFAULT 0,
    win_rate                NUMERIC(5,2) DEFAULT 0.00,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 보유 인증 JSONB 구조 예시:
-- [{"name": "GS인증", "grade": "1등급", "issued_at": "2024-01-01", "expires_at": "2026-01-01"},
--  {"name": "ISO9001", "issued_at": "2023-06-01"}]
```

#### company_profiles (회사 역량 프로필)

```sql
CREATE TABLE company_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    -- 핵심 역량
    core_competencies   TEXT NOT NULL,              -- 핵심 역량 서술
    tech_stacks         TEXT[] DEFAULT '{}',         -- 보유 기술 스택
    service_areas       TEXT[] DEFAULT '{}',         -- 서비스 영역
    -- 회사 소개문 (제안서 자동 삽입용)
    company_intro       TEXT,                        -- 회사 소개 (1~2단락)
    ceo_message         TEXT,                        -- 대표 인사말
    -- AI 임베딩 (매칭용)
    profile_embedding   vector(1536),               -- pgvector
    embedding_updated_at TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### past_performances (수행 실적)

```sql
CREATE TABLE past_performances (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    project_name        VARCHAR(300) NOT NULL,       -- 사업명
    client_name         VARCHAR(200) NOT NULL,        -- 발주기관
    client_type         VARCHAR(50)                  -- 'government', 'public', 'private'
                        CHECK (client_type IN ('government', 'public', 'private')),
    contract_amount     BIGINT NOT NULL,              -- 계약금액 (원)
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    description         TEXT,                         -- 사업 내용 요약
    tech_stacks         TEXT[] DEFAULT '{}',
    is_representative   BOOLEAN DEFAULT FALSE,        -- 대표 실적 여부
    reference_doc_url   TEXT,                         -- 실적증명서 파일
    -- AI 임베딩 (유사 실적 검색용)
    performance_embedding vector(1536),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_past_performances_company ON past_performances(company_id);
CREATE INDEX idx_past_performances_embedding ON past_performances
    USING ivfflat (performance_embedding vector_cosine_ops) WITH (lists = 100);
```

#### bid_notices (입찰 공고)

```sql
CREATE TABLE bid_notices (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- 나라장터 원본 데이터
    g2b_notice_id       VARCHAR(50) UNIQUE NOT NULL,    -- 나라장터 공고번호
    g2b_url             VARCHAR(500),
    title               VARCHAR(500) NOT NULL,
    issuer_name         VARCHAR(200) NOT NULL,           -- 발주기관명
    issuer_code         VARCHAR(50),                     -- 발주기관 코드
    issuer_type         VARCHAR(50)                      -- 'central', 'local', 'public', 'education'
                        CHECK (issuer_type IN ('central', 'local', 'public', 'education', 'other')),
    -- 사업 정보
    notice_type         VARCHAR(50) NOT NULL             -- 'service', 'goods', 'construction'
                        CHECK (notice_type IN ('service', 'goods', 'construction')),
    budget_amount       BIGINT,                          -- 예산금액 (원)
    contract_method     VARCHAR(50)                      -- 계약 방법
                        CHECK (contract_method IN (
                            'open_bid',                  -- 일반경쟁
                            'limited_bid',               -- 제한경쟁
                            'designated_bid',            -- 지명경쟁
                            'negotiation',               -- 협상에 의한 계약
                            'random_lowest'              -- 적격심사
                        )),
    bid_method          VARCHAR(50)                      -- 낙찰 방법
                        CHECK (bid_method IN (
                            'lowest_price',              -- 최저가 낙찰
                            'qualified_review',          -- 적격심사
                            'negotiation',               -- 협상
                            'comprehensive_evaluation'   -- 종합심사
                        )),
    -- 일정
    notice_date         TIMESTAMPTZ NOT NULL,            -- 공고일
    submission_deadline TIMESTAMPTZ NOT NULL,            -- 제출 마감일
    bid_opening_date    TIMESTAMPTZ,                     -- 개찰일
    contract_period_months INTEGER,                      -- 사업 기간 (개월)
    -- 자격 요건
    required_certifications TEXT[],                      -- 필수 인증
    required_experience TEXT,                            -- 수행 실적 요건
    region_restriction  VARCHAR(100),                    -- 지역 제한
    -- 파싱된 내용
    full_text           TEXT,                            -- RFP 전체 텍스트
    evaluation_criteria JSONB,                           -- 평가 항목·배점 파싱 결과
    key_requirements    TEXT[],                          -- 핵심 요구사항 목록
    -- AI 임베딩
    notice_embedding    vector(1536),
    -- 메타
    status              VARCHAR(20) DEFAULT 'active'
                        CHECK (status IN ('active', 'closed', 'cancelled', 'awarded')),
    awarded_company     VARCHAR(200),                    -- 낙찰 업체명
    awarded_amount      BIGINT,                          -- 낙찰금액
    awarded_rate        NUMERIC(5,2),                    -- 낙찰가율 (%)
    crawled_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bid_notices_g2b_id ON bid_notices(g2b_notice_id);
CREATE INDEX idx_bid_notices_deadline ON bid_notices(submission_deadline) WHERE status = 'active';
CREATE INDEX idx_bid_notices_notice_date ON bid_notices(notice_date DESC);
CREATE INDEX idx_bid_notices_embedding ON bid_notices
    USING ivfflat (notice_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_bid_notices_issuer ON bid_notices(issuer_code);
```

#### notice_attachments (공고 첨부파일)

```sql
CREATE TABLE notice_attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notice_id       UUID NOT NULL REFERENCES bid_notices(id) ON DELETE CASCADE,
    filename        VARCHAR(300) NOT NULL,
    file_type       VARCHAR(20) NOT NULL        -- 'pdf', 'hwp', 'xlsx', 'docx', 'zip'
                    CHECK (file_type IN ('pdf', 'hwp', 'xlsx', 'docx', 'zip', 'other')),
    file_size       BIGINT,
    s3_url          TEXT,
    extracted_text  TEXT,                       -- 추출된 텍스트
    parse_status    VARCHAR(20) DEFAULT 'pending'
                    CHECK (parse_status IN ('pending', 'processing', 'success', 'failed')),
    parse_error     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notice_attachments_notice ON notice_attachments(notice_id);
```

#### bid_participations (입찰 참여 관리)

```sql
CREATE TABLE bid_participations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    notice_id       UUID NOT NULL REFERENCES bid_notices(id),
    -- 상태 관리
    status          VARCHAR(30) NOT NULL DEFAULT 'bookmarked'
                    CHECK (status IN (
                        'bookmarked',       -- 북마크
                        'analyzing',        -- 분석 중
                        'writing',          -- 제안서 작성 중
                        'reviewing',        -- 검토 중
                        'submitted',        -- 제출 완료
                        'under_evaluation', -- 심사 중
                        'won',              -- 낙찰
                        'lost',             -- 탈락
                        'cancelled'         -- 참여 취소
                    )),
    -- 스코어링
    match_score     NUMERIC(5,2),               -- 매칭 점수 (0~100)
    win_probability NUMERIC(5,2),               -- 낙찰 가능성 점수 (0~100)
    -- 투찰 정보
    bid_amount      BIGINT,                     -- 실제 투찰금액
    bid_amount_rate NUMERIC(5,2),               -- 투찰가율
    recommended_amount BIGINT,                  -- AI 추천 투찰금액
    -- 결과
    final_rank      INTEGER,                    -- 최종 순위
    technical_score NUMERIC(5,2),               -- 기술 점수
    price_score     NUMERIC(5,2),               -- 가격 점수
    final_score     NUMERIC(5,2),               -- 최종 점수
    -- 비용 추적
    proposal_cost   BIGINT DEFAULT 0,           -- 제안서 작성 비용 (원)
    awarded_amount  BIGINT,                     -- 낙찰금액 (낙찰 시)
    -- 메모
    internal_memo   TEXT,
    assigned_to     UUID REFERENCES users(id),  -- 담당자
    -- 일정
    submitted_at    TIMESTAMPTZ,
    result_notified_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(company_id, notice_id)
);

CREATE INDEX idx_bid_participations_company ON bid_participations(company_id, status);
CREATE INDEX idx_bid_participations_notice ON bid_participations(notice_id);
```

#### proposals (제안서)

```sql
CREATE TABLE proposals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participation_id    UUID NOT NULL UNIQUE REFERENCES bid_participations(id),
    company_id          UUID NOT NULL REFERENCES companies(id),
    notice_id           UUID NOT NULL REFERENCES bid_notices(id),
    title               VARCHAR(500),                   -- 제안서 제목
    -- 생성 메타
    ai_model            VARCHAR(50),                    -- 생성 모델
    generation_status   VARCHAR(30) DEFAULT 'draft'
                        CHECK (generation_status IN (
                            'draft', 'generating', 'completed', 'submitted'
                        )),
    total_pages         INTEGER,
    word_count          INTEGER,
    -- 평가 달성도
    evaluation_score    NUMERIC(5,2),                   -- AI 자체 평가 점수
    evaluation_detail   JSONB,                          -- 항목별 달성률
    -- 파일
    docx_url            TEXT,
    pdf_url             TEXT,
    hwp_url             TEXT,
    -- 버전
    current_version     INTEGER NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_proposals_company ON proposals(company_id);
CREATE INDEX idx_proposals_notice ON proposals(notice_id);
```

#### proposal_sections (제안서 섹션)

```sql
CREATE TABLE proposal_sections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    section_order   INTEGER NOT NULL,               -- 섹션 순서
    section_key     VARCHAR(100) NOT NULL,           -- 'business_understanding', 'tech_plan' 등
    section_title   VARCHAR(200) NOT NULL,
    content         TEXT NOT NULL,                  -- 섹션 내용 (Markdown)
    ai_generated    BOOLEAN DEFAULT TRUE,
    user_edited     BOOLEAN DEFAULT FALSE,
    word_count      INTEGER,
    -- AI 생성 메타
    generation_prompt TEXT,                         -- 생성에 사용된 프롬프트 (디버깅용)
    tokens_used     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(proposal_id, section_order)
);

CREATE INDEX idx_proposal_sections_proposal ON proposal_sections(proposal_id, section_order);
```

#### proposal_versions (버전 히스토리)

```sql
CREATE TABLE proposal_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id     UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    snapshot        JSONB NOT NULL,                 -- 섹션 전체 스냅샷
    changed_by      UUID REFERENCES users(id),
    change_summary  VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(proposal_id, version_number)
);
```

#### scoring_results (낙찰 가능성 스코어링 결과)

```sql
CREATE TABLE scoring_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participation_id    UUID NOT NULL REFERENCES bid_participations(id) ON DELETE CASCADE,
    -- 종합 점수
    total_score         NUMERIC(5,2) NOT NULL,
    recommendation      VARCHAR(20)                 -- 'highly_recommended', 'recommended', 'caution', 'not_recommended'
                        CHECK (recommendation IN (
                            'highly_recommended', 'recommended', 'caution', 'not_recommended'
                        )),
    -- 항목별 점수
    competition_score   NUMERIC(5,2),               -- 경쟁 강도
    capability_score    NUMERIC(5,2),               -- 우리 역량
    fit_score           NUMERIC(5,2),               -- 사업 적합도
    market_score        NUMERIC(5,2),               -- 시장 환경
    -- 상세 근거
    score_detail        JSONB NOT NULL,             -- 항목별 근거 텍스트
    competitor_estimate TEXT[],                     -- 예상 경쟁사 목록
    risks               TEXT[],                     -- 주요 리스크 목록
    opportunities       TEXT[],                     -- 주요 기회 목록
    ai_comment          TEXT,                       -- AI 종합 의견
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### price_analyses (낙찰가 분석)

```sql
CREATE TABLE price_analyses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    participation_id    UUID NOT NULL REFERENCES bid_participations(id) ON DELETE CASCADE,
    notice_id           UUID NOT NULL REFERENCES bid_notices(id),
    -- 분석 기반 데이터
    reference_notices   UUID[],                     -- 참고한 유사 공고 ID 배열
    sample_size         INTEGER,                    -- 분석 샘플 수
    -- 낙찰가율 통계
    avg_award_rate      NUMERIC(5,2),               -- 평균 낙찰가율
    min_award_rate      NUMERIC(5,2),
    max_award_rate      NUMERIC(5,2),
    std_award_rate      NUMERIC(5,2),               -- 표준편차
    -- 추천
    recommended_rate    NUMERIC(5,2),               -- 추천 투찰가율
    recommended_amount  BIGINT,                     -- 추천 투찰금액
    safe_range_min      NUMERIC(5,2),               -- 안전 범위 하한
    safe_range_max      NUMERIC(5,2),               -- 안전 범위 상한
    -- 전략
    strategy_text       TEXT,                       -- 투찰 전략 설명
    risk_warning        TEXT,                       -- 저가 리스크 경고
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### competitors (경쟁사 DB)

```sql
CREATE TABLE competitors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    VARCHAR(200) NOT NULL,
    business_number VARCHAR(20) UNIQUE,
    industry_codes  TEXT[],
    -- 나라장터 낙찰 통계 (수집 데이터)
    total_bids      INTEGER DEFAULT 0,
    won_bids        INTEGER DEFAULT 0,
    win_rate        NUMERIC(5,2) DEFAULT 0.00,
    avg_bid_rate    NUMERIC(5,2),                   -- 평균 투찰가율
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_competitors_name ON competitors(company_name);
```

#### competitor_bids (경쟁사 과거 입찰 이력 — 나라장터 공개 데이터)

```sql
CREATE TABLE competitor_bids (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competitor_id   UUID NOT NULL REFERENCES competitors(id),
    notice_id       UUID NOT NULL REFERENCES bid_notices(id),
    bid_amount      BIGINT NOT NULL,
    bid_rate        NUMERIC(5,2) NOT NULL,           -- 투찰가율
    final_rank      INTEGER,
    is_winner       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_competitor_bids_competitor ON competitor_bids(competitor_id);
CREATE INDEX idx_competitor_bids_notice ON competitor_bids(notice_id);
```

#### user_notifications (알림)

```sql
CREATE TABLE user_notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL
                    CHECK (type IN (
                        'new_match_notice',         -- 새 매칭 공고
                        'deadline_reminder',        -- 마감 임박
                        'score_updated',            -- 스코어 업데이트
                        'proposal_generated',       -- 제안서 생성 완료
                        'bid_result'               -- 낙찰 결과
                    )),
    title           VARCHAR(200) NOT NULL,
    body            TEXT,
    reference_id    UUID,                           -- 관련 공고/참여 ID
    reference_type  VARCHAR(50),                    -- 'notice', 'participation', 'proposal'
    is_read         BOOLEAN DEFAULT FALSE,
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON user_notifications(user_id, is_read, created_at DESC);
```

#### notice_categories (공고 카테고리 마스터)

```sql
CREATE TABLE notice_categories (
    id              SERIAL PRIMARY KEY,
    g2b_code        VARCHAR(50) UNIQUE NOT NULL,    -- 나라장터 분류 코드
    parent_code     VARCHAR(50),
    name            VARCHAR(200) NOT NULL,
    name_en         VARCHAR(200),
    depth           INTEGER NOT NULL DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE
);
```

#### subscriptions (구독)

```sql
CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan            VARCHAR(20) NOT NULL
                    CHECK (plan IN ('starter', 'pro', 'enterprise')),
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'cancelled', 'expired')),
    starts_at       TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,
    monthly_amount  NUMERIC(10,0) NOT NULL,
    toss_billing_key VARCHAR(200),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 5. API 엔드포인트 명세

### 5.1 공통 규칙

```
Base URL: https://api.bidmaster.co.kr/v1

인증: Bearer Token (JWT)
  Authorization: Bearer <access_token>

응답 포맷:
{
  "success": true,
  "data": { ... },
  "meta": { "page": 1, "per_page": 20, "total": 100 }
}

에러 포맷:
{
  "success": false,
  "error": {
    "code": "NOTICE_NOT_FOUND",
    "message": "공고를 찾을 수 없습니다.",
    "details": {}
  }
}

주요 에러 코드:
  400 VALIDATION_ERROR
  401 UNAUTHORIZED
  403 FORBIDDEN / PLAN_UPGRADE_REQUIRED
  404 NOT_FOUND
  422 PARSING_FAILED
  429 RATE_LIMIT_EXCEEDED
  500 INTERNAL_ERROR
```

---

### 5.2 인증 API

#### POST /auth/register
```json
// Request
{
  "email": "user@company.com",
  "password": "Password123!",
  "name": "홍길동",
  "phone": "010-1234-5678"
}

// Response 201
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

#### POST /auth/login
```json
// Response 200
{
  "success": true,
  "data": {
    "access_token": "eyJ...",     // 만료: 1시간
    "refresh_token": "eyJ...",    // 만료: 30일
    "user": {
      "id": "uuid",
      "name": "홍길동",
      "plan": "pro",
      "company_id": "uuid"
    }
  }
}
```

---

### 5.3 회사 프로필 API

#### POST /companies
회사 등록

```json
// Request
{
  "company_name": "㈜테크솔루션",
  "business_number": "123-45-67890",
  "representative_name": "홍길동",
  "industry_codes": ["SW개발", "IT서비스", "SI"],
  "employee_count": 45,
  "annual_revenue": 5000000000,
  "founded_year": 2015
}

// Response 201
{
  "success": true,
  "data": {
    "id": "uuid",
    "company_name": "㈜테크솔루션",
    "profile_completion": 35,   // 프로필 완성도 %
    "next_steps": [
      "핵심 역량 등록",
      "수행 실적 등록",
      "보유 인증 등록"
    ]
  }
}
```

#### PUT /companies/{company_id}/profile
회사 역량 프로필 저장

```json
// Request
{
  "core_competencies": "금융·공공 SI 전문 기업으로 15년간 ...",
  "tech_stacks": ["Java", "Spring Boot", "Oracle", "AWS", "React"],
  "service_areas": ["공공기관 시스템 구축", "금융 IT", "클라우드 전환"],
  "company_intro": "㈜테크솔루션은 2010년 설립된 ...",
  "certifications": [
    {"name": "GS인증", "grade": "1등급", "issued_at": "2024-01-15"},
    {"name": "ISO27001", "issued_at": "2023-06-01"}
  ]
}
```

#### POST /companies/{company_id}/performances
수행 실적 등록

```json
// Request
{
  "project_name": "행정안전부 행정정보 시스템 고도화",
  "client_name": "행정안전부",
  "client_type": "government",
  "contract_amount": 800000000,
  "start_date": "2023-03-01",
  "end_date": "2023-12-31",
  "description": "레거시 행정정보 시스템을 클라우드 기반으로 전환...",
  "tech_stacks": ["Java", "Spring Boot", "AWS", "Oracle"],
  "is_representative": true
}
```

#### GET /companies/{company_id}/performances
수행 실적 목록 조회

---

### 5.4 공고 API

#### GET /notices
공고 목록 조회 (필터·정렬 지원)

**Query Parameters:**
```
company_id:     UUID    (매칭 점수 포함 여부)
min_match:      int     (최소 매칭 점수, 0~100)
notice_type:    string  (service|goods|construction)
contract_method: string (open_bid|limited_bid|negotiation|random_lowest)
min_budget:     int     (최소 예산금액, 원)
max_budget:     int     (최대 예산금액, 원)
issuer_type:    string  (central|local|public|education)
deadline_from:  date
deadline_to:    date
keyword:        string  (제목 검색)
status:         string  (active|closed|awarded)
sort:           string  (match_score|deadline|budget|notice_date, default: match_score)
page:           int     (default: 1)
per_page:       int     (default: 20, max: 50)
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "g2b_notice_id": "20241115-001",
      "title": "행정안전부 민원 처리 시스템 고도화 용역",
      "issuer_name": "행정안전부",
      "issuer_type": "central",
      "budget_amount": 500000000,
      "submission_deadline": "2026-03-20T18:00:00Z",
      "bid_method": "negotiation",
      "match_score": 82.5,
      "days_left": 19,
      "participation_status": "bookmarked",
      "key_requirements": ["GS인증 보유", "유사 실적 3건 이상"],
      "notice_date": "2026-03-01T09:00:00Z"
    }
  ],
  "meta": { "page": 1, "per_page": 20, "total": 143 }
}
```

#### GET /notices/{notice_id}
공고 상세 조회

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "g2b_notice_id": "20241115-001",
    "title": "행정안전부 민원 처리 시스템 고도화 용역",
    "issuer_name": "행정안전부",
    "budget_amount": 500000000,
    "submission_deadline": "2026-03-20T18:00:00Z",
    "bid_method": "negotiation",
    "contract_period_months": 8,
    "required_certifications": ["GS인증"],
    "required_experience": "유사 시스템 구축 실적 3억 이상 1건",
    "full_text": "...",
    "evaluation_criteria": {
      "total_score": 100,
      "sections": [
        {"name": "사업이해도", "weight": 20},
        {"name": "기술방안", "weight": 35},
        {"name": "수행계획", "weight": 25},
        {"name": "수행실적", "weight": 20}
      ]
    },
    "key_requirements": ["GS인증 보유", "유사 실적 3건 이상"],
    "attachments": [
      {"filename": "RFP_행안부_민원고도화.pdf", "file_type": "pdf", "s3_url": "..."}
    ],
    "match_analysis": {
      "match_score": 82.5,
      "strengths": ["GS인증 보유", "유사 수행 실적 2건"],
      "weaknesses": ["Java 개발 인력 부족 가능성"],
      "missing_requirements": []
    }
  }
}
```

#### POST /notices/{notice_id}/analyze
공고 심층 분석 (AI)

**Response 200 (SSE stream):**
```
data: {"type": "parsing", "message": "RFP 분석 중..."}
data: {"type": "evaluation_criteria", "data": {...}}
data: {"type": "requirements", "data": [...]}
data: {"type": "scoring", "data": {"total": 82.5, "breakdown": {...}}}
data: {"type": "done"}
```

---

### 5.5 입찰 참여 관리 API

#### POST /participations
입찰 참여 등록

```json
// Request
{
  "company_id": "uuid",
  "notice_id": "uuid",
  "status": "analyzing",
  "assigned_to": "uuid"
}

// Response 201
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "analyzing",
    "match_score": 82.5,
    "win_probability": null,
    "proposal_id": null
  }
}
```

#### PATCH /participations/{participation_id}
참여 상태 업데이트

```json
// Request
{
  "status": "submitted",
  "bid_amount": 458000000,
  "submitted_at": "2026-03-19T15:30:00Z"
}
```

#### POST /participations/{participation_id}/result
낙찰 결과 입력

```json
// Request
{
  "result": "won",   // "won" | "lost"
  "final_rank": 1,
  "technical_score": 87.5,
  "price_score": 92.0,
  "final_score": 89.0,
  "awarded_amount": 458000000
}
```

#### GET /companies/{company_id}/participations
입찰 참여 목록 (파이프라인)

**Query:** `?status=writing,reviewing,submitted&sort=deadline`

---

### 5.6 스코어링 API

#### POST /participations/{participation_id}/score
낙찰 가능성 스코어링 실행

**Response 200:**
```json
{
  "success": true,
  "data": {
    "total_score": 71.5,
    "recommendation": "recommended",
    "breakdown": {
      "competition_score": 65.0,
      "capability_score": 80.0,
      "fit_score": 72.0,
      "market_score": 68.0
    },
    "competitor_estimate": ["㈜삼성SDS", "LG CNS", "SK C&C"],
    "risks": [
      "대형 SI 업체 2~3곳 참여 예상",
      "납기 8개월이 다소 타이트함"
    ],
    "opportunities": [
      "행안부 장기 협력사 관계 활용 가능",
      "GS인증 요건 충족"
    ],
    "ai_comment": "경쟁이 치열하지만 보유 실적과 인증 면에서 경쟁 우위가 있습니다. 기술 점수에서 차별화 포인트를 명확히 해야 합니다.",
    "created_at": "2026-03-01T10:00:00Z"
  }
}
```

---

### 5.7 낙찰가 분석 API

#### POST /participations/{participation_id}/price-analysis
낙찰가 분석 실행

**Response 200:**
```json
{
  "success": true,
  "data": {
    "budget_amount": 500000000,
    "sample_size": 23,
    "statistics": {
      "avg_award_rate": 91.2,
      "min_award_rate": 82.5,
      "max_award_rate": 97.8,
      "std_award_rate": 3.8
    },
    "recommendation": {
      "rate": 90.5,
      "amount": 452500000,
      "safe_range_min": 88.0,
      "safe_range_max": 93.0
    },
    "strategy_text": "협상에 의한 계약으로 기술 점수 85점 이상 확보 후 가격 경쟁력 확보가 필요합니다. 유사 공고 낙찰가율 90~92% 구간에 업체가 집중되어 있습니다.",
    "risk_warning": null,
    "reference_notices": [
      {
        "notice_id": "uuid",
        "title": "...",
        "budget_amount": 480000000,
        "awarded_rate": 91.5,
        "awarded_year": 2025
      }
    ]
  }
}
```

---

### 5.8 제안서 API

#### POST /proposals/generate
제안서 AI 생성 시작 (비동기 + SSE)

```json
// Request
{
  "participation_id": "uuid",
  "options": {
    "emphasis_sections": ["tech_plan", "past_performance"],
    "tone": "formal",
    "custom_instructions": "클라우드 네이티브 아키텍처를 강조해주세요"
  }
}

// Response 202 (생성 시작)
{
  "success": true,
  "data": {
    "proposal_id": "uuid",
    "status": "generating",
    "estimated_minutes": 3,
    "stream_url": "/proposals/uuid/stream"
  }
}
```

#### GET /proposals/{proposal_id}/stream
제안서 생성 진행 상황 (SSE)

```
data: {"type": "start", "total_sections": 7}
data: {"type": "section_start", "section": "business_understanding", "title": "사업 이해 및 추진 전략"}
data: {"type": "text", "section": "business_understanding", "content": "1. 사업 배경 및 목적\n\n"}
data: {"type": "text", "section": "business_understanding", "content": "행정안전부는 ..."}
data: {"type": "section_done", "section": "business_understanding", "word_count": 450}
data: {"type": "section_start", "section": "tech_plan", "title": "기술 방안"}
...
data: {"type": "done", "proposal_id": "uuid", "total_word_count": 3200}
```

#### GET /proposals/{proposal_id}
제안서 조회 (섹션 목록 포함)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "행정안전부 민원 처리 시스템 고도화 용역 제안서",
    "generation_status": "completed",
    "evaluation_score": 84.5,
    "current_version": 2,
    "sections": [
      {
        "id": "uuid",
        "section_order": 1,
        "section_key": "business_understanding",
        "section_title": "1. 사업 이해 및 추진 전략",
        "content": "...",
        "word_count": 450,
        "ai_generated": true,
        "user_edited": false
      }
    ],
    "evaluation_detail": {
      "sections": [
        {"name": "사업이해도", "weight": 20, "estimated_score": 17},
        {"name": "기술방안", "weight": 35, "estimated_score": 29},
        {"name": "수행계획", "weight": 25, "estimated_score": 21},
        {"name": "수행실적", "weight": 20, "estimated_score": 18}
      ],
      "missing_items": ["WBS 상세 일정표 보완 필요"]
    }
  }
}
```

#### PATCH /proposals/{proposal_id}/sections/{section_id}
섹션 내용 수정

```json
// Request
{
  "content": "수정된 섹션 내용...",
  "user_edited": true
}
```

#### POST /proposals/{proposal_id}/sections/{section_id}/regenerate
섹션 AI 재생성

```json
// Request
{
  "instructions": "클라우드 네이티브 아키텍처를 중심으로 재작성해주세요. MSA 방식을 강조하고 AWS 서비스를 구체적으로 언급해주세요."
}

// Response: SSE stream
```

#### POST /proposals/{proposal_id}/download
제안서 파일 다운로드

```json
// Request
{
  "format": "docx"    // "docx" | "pdf" | "hwp"
}

// Response 200
{
  "success": true,
  "data": {
    "download_url": "https://s3.../...",
    "expires_at": "2026-03-01T11:00:00Z"
  }
}
```

---

### 5.9 대시보드 API

#### GET /companies/{company_id}/dashboard
메인 대시보드 데이터

**Response 200:**
```json
{
  "success": true,
  "data": {
    "kpis": {
      "this_month_bids": 5,
      "this_month_submitted": 3,
      "ongoing_evaluations": 2,
      "this_month_won_amount": 800000000
    },
    "pipeline": {
      "bookmarked": 8,
      "analyzing": 2,
      "writing": 1,
      "reviewing": 1,
      "submitted": 3,
      "under_evaluation": 2,
      "won_this_month": 1,
      "lost_this_month": 2
    },
    "deadline_alerts": [
      {
        "notice_title": "...",
        "participation_id": "uuid",
        "days_left": 3,
        "status": "writing"
      }
    ],
    "recommended_notices": [
      {
        "notice_id": "uuid",
        "title": "...",
        "match_score": 88.0,
        "budget_amount": 300000000,
        "days_left": 15
      }
    ],
    "performance_summary": {
      "ytd_win_rate": 28.5,
      "avg_technical_score": 82.3,
      "total_won_amount_ytd": 2500000000
    }
  }
}
```

#### GET /companies/{company_id}/analytics
성과 분석

**Query:** `?period=ytd` (ytd|last_12m|last_3m|custom)

---

### 5.10 크롤러 관리 API (내부용, Admin 전용)

#### POST /admin/crawler/run
수동 크롤링 실행

#### GET /admin/crawler/status
크롤러 상태 조회

#### POST /admin/notices/{notice_id}/reparse
공고 재파싱

---

## 6. Claude 프롬프트 설계

### 6.1 프롬프트 설계 원칙

```
1. 역할 고정: 공공입찰 제안서 전문 컨설턴트
2. 컨텍스트 계층화:
   - L1: 회사 프로필 (고정)
   - L2: 공고 RFP 파싱 결과 (공고별)
   - L3: 섹션별 생성 지시사항 (섹션별)
3. 평가 기준 최우선: 배점표를 항상 주입
4. 출력 형식 제어: Markdown 구조 강제
5. 토큰 효율화: 공고 전문 대신 파싱된 핵심만 주입
```

### 6.2 공고 분석 프롬프트

#### System Prompt

```
당신은 대한민국 공공 입찰 전문 분석가입니다.
RFP(제안요청서)를 분석하여 구조화된 정보를 추출하는 것이 목표입니다.

## 분석 원칙
1. 평가 항목과 배점을 정확히 파악하십시오.
2. 필수 자격 요건 (인증, 실적, 인력)을 빠짐없이 추출하십시오.
3. 숨겨진 요구사항 (암묵적 기대, 기관 특성)을 파악하십시오.
4. 제안서 작성 시 반드시 포함해야 할 항목을 정리하십시오.

## 출력 형식 (JSON)
{
  "title": "사업명",
  "core_objective": "사업의 핵심 목적 (1~2문장)",
  "evaluation_criteria": [
    {"name": "평가항목명", "weight": 배점, "sub_items": ["세부항목1", ...]}
  ],
  "mandatory_requirements": [
    {"type": "certification", "name": "필요 인증", "mandatory": true},
    {"type": "experience", "description": "필요 실적", "mandatory": true}
  ],
  "tech_requirements": ["요구 기술 스택 목록"],
  "deliverables": ["산출물 목록"],
  "key_evaluation_points": ["심사위원이 중요하게 볼 포인트 3~5개"],
  "issuer_characteristics": "발주기관 특성 및 선호도 분석",
  "writing_checklist": ["제안서 작성 시 체크해야 할 항목"]
}
```

#### User Prompt Template

```python
def build_rfp_analysis_prompt(rfp_text: str, notice_meta: dict) -> str:
    return f"""다음 입찰 공고 RFP를 분석하십시오.

## 공고 기본 정보
- 사업명: {notice_meta['title']}
- 발주기관: {notice_meta['issuer_name']} ({notice_meta['issuer_type']})
- 예산금액: {notice_meta['budget_amount']:,}원
- 계약방법: {notice_meta['contract_method']}
- 낙찰방법: {notice_meta['bid_method']}
- 사업기간: {notice_meta['contract_period_months']}개월

## RFP 전문
{rfp_text[:8000]}  # 토큰 제한으로 앞부분 우선 처리

위 RFP를 분석하여 지정된 JSON 형식으로 출력하십시오."""
```

---

### 6.3 매칭 스코어링 프롬프트

#### System Prompt

```
당신은 공공 입찰 전략 컨설턴트입니다.
회사의 역량과 공고 요건을 비교 분석하여 입찰 참여 적합도를 평가합니다.

## 평가 기준
각 항목을 100점 만점으로 평가하고 가중치를 적용하십시오:
  - 업종 및 기술 적합도 (30점)
  - 수행 실적 유사도 (25점)
  - 필수 자격 요건 충족도 (20점)
  - 사업 규모 적합성 (15점)
  - 지역 및 기타 조건 (10점)

## 출력 형식 (JSON)
{
  "total_score": 0~100,
  "recommendation": "highly_recommended|recommended|caution|not_recommended",
  "breakdown": {
    "tech_fit": {"score": 0~100, "reason": "평가 근거"},
    "experience_fit": {"score": 0~100, "reason": "평가 근거"},
    "qualification_fit": {"score": 0~100, "reason": "평가 근거"},
    "scale_fit": {"score": 0~100, "reason": "평가 근거"},
    "other_fit": {"score": 0~100, "reason": "평가 근거"}
  },
  "strengths": ["강점 1", "강점 2", "강점 3"],
  "weaknesses": ["약점 1", "약점 2"],
  "missing_requirements": ["미충족 필수 요건"],
  "ai_comment": "종합 의견 (3~5문장)"
}
```

#### User Prompt Template

```python
def build_matching_prompt(company_profile: dict, notice_analysis: dict) -> str:
    return f"""다음 회사 프로필과 공고 요건을 비교하여 입찰 적합도를 평가하십시오.

## 회사 프로필
- 회사명: {company_profile['company_name']}
- 업종 코드: {', '.join(company_profile['industry_codes'])}
- 직원 수: {company_profile['employee_count']}명
- 연 매출: {company_profile['annual_revenue']:,}원
- 보유 인증: {', '.join([c['name'] for c in company_profile['certifications']])}
- 핵심 기술 스택: {', '.join(company_profile['tech_stacks'])}
- 핵심 역량: {company_profile['core_competencies'][:500]}

## 주요 수행 실적 (상위 5건)
{format_performances(company_profile['performances'][:5])}

## 공고 요건
- 사업명: {notice_analysis['title']}
- 핵심 목적: {notice_analysis['core_objective']}
- 필수 요건: {format_requirements(notice_analysis['mandatory_requirements'])}
- 요구 기술: {', '.join(notice_analysis['tech_requirements'])}
- 핵심 평가 포인트: {', '.join(notice_analysis['key_evaluation_points'])}

위 정보를 바탕으로 JSON 형식으로 평가하십시오."""
```

---

### 6.4 제안서 생성 프롬프트

#### System Prompt (전체 제안서)

```
당신은 대한민국 공공기관 입찰 전문 제안서 작성 전문가입니다.
20년 경력의 제안서 작성 전문가로서, 낙찰 가능성을 극대화하는 제안서를 작성합니다.

## 제안서 작성 원칙
1. 평가 배점표에 최적화하십시오. 배점이 높은 항목일수록 더 상세히 기술하십시오.
2. 발주기관의 입장에서 서술하십시오. "우리가 잘한다"가 아닌 "기관의 문제를 이렇게 해결한다"로 접근하십시오.
3. 구체적 수치와 사례를 반드시 포함하십시오. 추상적 표현 사용 금지.
4. 회사의 실제 수행 실적을 자연스럽게 연결하십시오.
5. 심사위원이 체크리스트를 작성하기 쉽도록 명확한 소제목을 사용하십시오.

## 금지 표현
- "최고의", "최상의", "탁월한" 등 근거 없는 수식어
- "노력하겠습니다", "최선을 다하겠습니다" 등 약속 표현
- 경쟁사 비방
- 과도한 자사 자랑

## 출력 형식
각 섹션을 ## 제목과 함께 Markdown으로 작성하십시오.
표, 그림 설명(Figure 캡션), 번호 목록을 적극 활용하십시오.
```

#### 섹션별 생성 프롬프트 설계

```python
SECTION_PROMPTS = {
    "business_understanding": """
## 섹션: 사업 이해 및 추진 전략 (배점: {weight}점)

다음 내용을 포함하여 이 섹션을 작성하십시오:
1. 발주기관의 현황 분석 및 이 사업이 필요한 배경
2. 사업의 핵심 목적과 기대 효과
3. 우리 회사만의 독창적 추진 전략 (3가지 핵심 전략 제시)
4. 성공 사례와 연계한 수행 자신감

발주기관 특성: {issuer_characteristics}
핵심 평가 포인트: {key_points}
관련 수행 실적: {relevant_performances}
목표 분량: 800~1,200단어
""",

    "tech_plan": """
## 섹션: 기술 방안 (배점: {weight}점)

요구사항:
{tech_requirements}

다음 구조로 작성하십시오:
1. 요구사항 분석 결과 (핵심 요구사항 3~5개 명시)
2. 시스템 아키텍처 개요 (텍스트로 다이어그램 구조 설명)
3. 핵심 기능별 구현 방안 (표 형식 권장)
4. 개발 방법론 및 품질 관리 방안
5. 보안 방안 (공공기관 보안 가이드라인 준수 명시)

보유 기술 스택: {tech_stacks}
목표 분량: 1,200~1,800단어
""",

    "execution_plan": """
## 섹션: 수행 계획 (배점: {weight}점)

사업 기간: {contract_period_months}개월
시작 예정일: {start_date}

다음 내용을 포함하십시오:
1. 사업 수행 조직 (역할·책임 명시)
2. 단계별 추진 일정 (WBS — 텍스트 표 형식)
3. 단계별 산출물 목록
4. 리스크 관리 방안 (3가지 예상 리스크와 대응방안)
5. 품질 보증 계획

목표 분량: 800~1,200단어
""",

    "past_performance": """
## 섹션: 유사 수행 실적 (배점: {weight}점)

다음 실적을 활용하여 작성하십시오:
{relevant_performances}

작성 원칙:
1. 이번 사업과의 유사성을 명확히 연결하십시오
2. 각 실적에서 얻은 노하우가 이번 사업에 어떻게 적용되는지 서술
3. 수치로 성과를 표현 (처리량 N% 향상, 오류율 N% 감소 등)
4. 고객 만족도·결과를 포함

목표 분량: 600~900단어
"""
}
```

---

### 6.5 낙찰가 분석 프롬프트

#### System Prompt

```
당신은 공공입찰 가격 전략 전문가입니다.
과거 유사 공고의 낙찰가 데이터를 분석하여 최적 투찰 전략을 제안합니다.

## 분석 원칙
1. 데이터 기반으로만 분석하십시오. 추측은 근거를 명시하십시오.
2. 낙찰 방법별 특성을 반영하십시오 (최저가/협상/적격심사).
3. 과도한 저가 투찰의 리스크를 경고하십시오 (하도급 단가, 사업 품질).
4. 발주기관별 패턴 차이를 반영하십시오.

## 출력 형식 (JSON)
{
  "analysis_summary": "분석 요약 (3~4문장)",
  "recommendation": {
    "rate": 최적 투찰가율(%),
    "amount": 최적 투찰금액(원),
    "confidence": "high|medium|low",
    "safe_range": {"min": 하한율, "max": 상한율}
  },
  "strategy": "투찰 전략 상세 설명",
  "risk_warning": "저가 경고 (해당 시)",
  "data_summary": {
    "sample_count": 분석 샘플 수,
    "avg_rate": 평균 낙찰가율,
    "distribution": "분포 설명"
  }
}
```

---

### 6.6 AI 어시스턴트 프롬프트 (편집기 내)

#### System Prompt

```
당신은 공공입찰 제안서 작성을 돕는 AI 어시스턴트입니다.
사용자가 편집 중인 제안서 섹션을 개선하는 구체적인 도움을 제공합니다.

## 지원 기능
1. 섹션 보완: 부족한 내용 추가 제안
2. 표현 개선: 더 설득력 있는 표현으로 수정
3. 평가 기준 대응: 특정 평가 항목 달성도 확인
4. 분량 조절: 목표 분량에 맞게 확장/축약
5. 구체화: 추상적 표현을 수치·사례로 구체화

## 제약
- 직접 거짓 실적이나 허위 정보를 생성하지 마십시오
- 사용자가 제공한 회사 정보 범위 내에서만 작성하십시오
- 표절 위험이 높은 다른 공고 제안서를 그대로 가져오지 마십시오
```

---

### 6.7 토큰 최적화 전략

```python
class ProposalTokenOptimizer:
    """
    제안서 생성 시 토큰을 효율적으로 관리하는 전략
    """
    
    # 섹션별 최대 토큰 (input)
    SECTION_INPUT_LIMITS = {
        "business_understanding": 2000,
        "tech_plan": 3000,
        "execution_plan": 2000,
        "past_performance": 2500,
        "company_overview": 1000
    }
    
    # RFP 텍스트 청킹 전략
    RFP_MAX_CHARS = 8000  # Claude context 최적화
    
    @staticmethod
    def trim_rfp(rfp_text: str) -> str:
        """
        RFP에서 평가 기준 섹션 우선 추출
        일반적으로 "평가", "배점", "심사" 키워드 주변이 핵심
        """
        # 핵심 섹션 추출 로직
        priority_keywords = ["평가기준", "배점표", "평가항목", "심사기준"]
        # ... 구현
    
    @staticmethod
    def compress_performances(performances: list, max_items: int = 5) -> str:
        """
        수행 실적을 토큰 효율적으로 포맷팅
        """
        formatted = []
        for p in performances[:max_items]:
            formatted.append(
                f"- {p['project_name']} ({p['client_name']}, "
                f"{p['contract_amount']//100000000}억원, "
                f"{p['start_date']}~{p['end_date']}): "
                f"{p['description'][:100]}"
            )
        return "\n".join(formatted)
```

---

## 7. Claude Code 멀티에이전트 아키텍처

### 7.1 에이전트 분리 전략

```
전체 프로젝트를 9개 에이전트로 분리:

Agent-0: Orchestrator (조율 및 순서 관리)
Agent-1: Database & Models
Agent-2: Auth & Company Profile
Agent-3: Crawler & Parser (나라장터 크롤러, RFP 파서)
Agent-4: Scoring & Price Analysis (스코어링 엔진)
Agent-5: Proposal Generation (제안서 AI 생성)
Agent-6: Frontend (Next.js)
Agent-7: Background Jobs (크롤링 스케줄러, 알림)
Agent-8: DevOps & Integration
```

### 7.2 Agent-0: Orchestrator

**실행 순서:**
```
1. Agent-1 (DB) 완료 후
2. Agent-2 (Auth & Profile) 시작
3. Agent-3 (Crawler) 시작 [Agent-1 의존]
4. Agent-4 (Scoring) 시작 [Agent-1, 3 의존]
5. Agent-5 (Proposal) 시작 [Agent-1, 4 의존]
6. Agent-2,3,4,5 완료 후 → Agent-6 (Frontend)
7. Agent-3 완료 후 → Agent-7 (Background Jobs)
8. 전체 완료 후 → Agent-8 (DevOps)
```

**초기화 프롬프트:**
```
당신은 비드마스터 프로젝트의 오케스트레이터 에이전트입니다.

프로젝트 구조:
/bidmaster
  /backend                 # FastAPI 백엔드
    /app
      /api/v1              # 라우터
      /core                # 설정, 보안, 의존성
      /db                  # SQLAlchemy 모델
      /services            # 비즈니스 로직
      /schemas             # Pydantic 스키마
      /ai                  # Claude API 클라이언트
      /crawler             # 나라장터 크롤러
      /parsers             # RFP 파서
      /workers             # 백그라운드 작업 (Celery)
  /frontend                # Next.js 14 프론트엔드
  /docs                    # 문서
  docker-compose.yml

기술 스택:
  Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
  Database: PostgreSQL 16 + pgvector, Redis 7
  Queue: Celery + Redis (크롤링, 알림 비동기 처리)
  AI: Anthropic Claude API (claude-sonnet-4-6)
  File Parse: pdfplumber, python-pptx (HWP는 LibreOffice 변환)
  Frontend: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
  Storage: AWS S3
  Payment: 토스페이먼츠
  
각 에이전트를 순서에 맞게 시작하십시오.
```

---

### 7.3 Agent-1: Database & Models

**담당 파일:**
```
/backend/app/db/
  base.py
  models/
    user.py
    company.py             # companies + company_profiles + past_performances
    notice.py              # bid_notices + notice_attachments + notice_categories
    participation.py       # bid_participations + scoring_results + price_analyses
    proposal.py            # proposals + proposal_sections + proposal_versions
    competitor.py          # competitors + competitor_bids
    notification.py        # user_notifications
    subscription.py        # subscriptions
/backend/alembic/
  versions/001_initial_schema.py
  versions/002_pgvector_extension.py
  versions/003_seed_notice_categories.py
```

**초기화 프롬프트:**
```
당신은 비드마스터의 데이터베이스 에이전트입니다.

작업 목표:
1. PRD Section 4의 전체 DB 스키마를 SQLAlchemy 2.0 ORM으로 구현하십시오.
2. pgvector 익스텐션 활성화 마이그레이션을 먼저 실행하십시오.
3. 모든 vector 필드에 IVFFlat 인덱스를 생성하십시오.
4. JSONB 필드에 대한 GIN 인덱스를 추가하십시오.

특별 구현 요구사항:
  - companies.win_rate: 자동 갱신 트리거 (won_bids/total_bids)
  - bid_notices.notice_embedding: 1536차원 벡터 (text-embedding-3-small)
  - company_profiles.profile_embedding: 1536차원 벡터
  - past_performances.performance_embedding: 1536차원 벡터

pgvector 인덱스:
  CREATE INDEX USING ivfflat ... WITH (lists = 100)
  (데이터 1만건 이하 시, 이상이면 lists = 데이터수/100)

시드 데이터:
  - notice_categories: 나라장터 주요 분류 코드 50개
  - 테스트 회사 1개 (IT 용역, 45인)
  - 테스트 공고 10개 (IT 용역 유형)
```

---

### 7.4 Agent-2: Auth & Company Profile

**담당 파일:**
```
/backend/app/
  core/
    config.py
    security.py
    dependencies.py
  api/v1/
    auth.py
    users.py
    companies.py           # 회사 + 프로필 + 수행실적
  services/
    auth_service.py
    company_service.py
    embedding_service.py   # 프로필 임베딩 생성
  schemas/
    auth.py
    company.py
```

**초기화 프롬프트:**
```
당신은 비드마스터의 인증 및 회사 프로필 에이전트입니다.

의존성: Agent-1 완료 후 시작

작업 목표:
1. PRD Section 5.2, 5.3 API를 FastAPI로 구현하십시오.
2. 회사 프로필 등록 완료 시 자동으로 임베딩을 생성하십시오.
3. 수행 실적 등록 시 각 실적의 임베딩을 생성하십시오.
4. 프로필 완성도(profile_completion) 자동 계산 로직을 구현하십시오.

프로필 완성도 계산:
  기본 정보: 20점
  핵심 역량 등록: 20점
  기술 스택 등록: 15점
  수행 실적 1건 이상: 25점
  보유 인증 등록: 10점
  회사 소개문 등록: 10점
  합계: 100점

임베딩 생성:
  모델: text-embedding-3-small (OpenAI) — 1536차원
  회사 프로필 임베딩: 핵심역량 + 기술스택 + 서비스영역 결합
  실적 임베딩: 사업명 + 설명 + 기술스택 결합
  비동기 처리 (Celery task)
```

---

### 7.5 Agent-3: Crawler & Parser

**담당 파일:**
```
/backend/app/
  crawler/
    __init__.py
    g2b_crawler.py         # 나라장터 크롤러
    g2b_parser.py          # 공고 HTML 파서
    attachment_downloader.py
  parsers/
    __init__.py
    pdf_parser.py          # pdfplumber 기반
    hwp_parser.py          # LibreOffice 변환 후 처리
    rfp_analyzer.py        # AI 기반 RFP 구조화
    evaluation_extractor.py # 평가기준 추출
  api/v1/
    notices.py
    admin_crawler.py
  services/
    notice_service.py
    crawler_service.py
  schemas/
    notice.py
```

**초기화 프롬프트:**
```
당신은 비드마스터의 크롤러 및 파서 에이전트입니다.

의존성: Agent-1 완료 후 시작

작업 목표:
1. 나라장터(www.g2b.go.kr) 입찰 공고 자동 수집을 구현하십시오.
2. PDF/HWP 첨부파일에서 텍스트를 추출하십시오.
3. Claude API로 RFP를 구조화된 데이터로 파싱하십시오.
4. PRD Section 5.4 공고 API를 구현하십시오.

크롤러 구현 세부사항:
  - 나라장터 공고 목록 API 또는 웹 스크래핑 (robots.txt 준수)
  - 크롤링 주기: 06:00, 12:00, 18:00 (Asia/Seoul)
  - 중복 방지: g2b_notice_id unique 체크
  - 대상 분류: IT용역, 소프트웨어개발, SI, 유지보수 (MVP)
  - 요청 간격: 1~2초 랜덤 딜레이 (서버 부하 방지)
  - User-Agent: 합법적 크롤러 명시

HWP 처리:
  1. LibreOffice: soffice --headless --convert-to pdf file.hwp
  2. pdfplumber로 텍스트 추출
  3. 변환 실패 시 parse_status = 'failed' 기록

RFP 파싱 파이프라인:
  원문 텍스트 → Claude API (PRD 6.2 프롬프트) → JSON 구조화 데이터
  → evaluation_criteria, key_requirements DB 저장
  → notice_embedding 생성 (비동기)

에러 처리:
  - 크롤링 실패: exponential backoff (1s, 2s, 4s, 최대 3회)
  - 파싱 실패: parse_status = 'failed', 원문은 full_text에 저장
  - AI 분석 실패: 기본값으로 폴백, 수동 분석 필요 플래그
```

---

### 7.6 Agent-4: Scoring & Price Analysis

**담당 파일:**
```
/backend/app/
  services/
    scoring_service.py     # 낙찰 가능성 스코어링
    price_analysis_service.py
    similarity_service.py  # 유사 공고 검색 (벡터 검색)
  api/v1/
    participations.py
    scoring.py
    price_analysis.py
  ai/
    scoring_prompt.py      # PRD 6.3 프롬프트
    price_prompt.py        # PRD 6.5 프롬프트
  schemas/
    participation.py
    scoring.py
```

**초기화 프롬프트:**
```
당신은 비드마스터의 스코어링 및 가격 분석 에이전트입니다.

의존성: Agent-1, Agent-3 완료 후 시작

작업 목표:
1. PRD Section 3의 Feature 2 스코어링 모델을 구현하십시오.
2. PRD Section 3의 Feature 4 낙찰가 분석을 구현하십시오.
3. pgvector를 활용한 유사 공고 검색을 구현하십시오.
4. PRD Section 5.5, 5.6, 5.7 API를 구현하십시오.

스코어링 구현:
  1. 회사 프로필 임베딩 ↔ 공고 임베딩 코사인 유사도 (기초 점수)
  2. Claude API로 항목별 상세 평가 (PRD 6.3)
  3. 결과를 scoring_results 테이블에 저장
  캐시: 동일 회사+공고 조합은 24시간 캐시 (Redis)

유사 공고 검색 (pgvector):
  SELECT * FROM bid_notices
  WHERE notice_embedding <=> $1 < 0.3  -- 코사인 거리 임계값
  ORDER BY notice_embedding <=> $1
  LIMIT 10;

낙찰가 분석:
  1. 동일 발주기관 + 유사 사업 유형 과거 낙찰 데이터 조회
  2. 벡터 유사도로 유사 공고 상위 20건 선택
  3. 낙찰가율 통계 계산 (numpy)
  4. Claude API로 전략 텍스트 생성
  최소 샘플 5건 이상 필요, 미달 시 "데이터 부족" 경고
```

---

### 7.7 Agent-5: Proposal Generation

**담당 파일:**
```
/backend/app/
  services/
    proposal_service.py
    proposal_generator.py  # 섹션별 생성 오케스트레이터
    document_service.py    # Word/PDF/HWP 생성
  api/v1/
    proposals.py
  ai/
    proposal_prompts.py    # PRD 6.4 섹션별 프롬프트
    assistant_prompt.py    # PRD 6.6 AI 어시스턴트
    token_optimizer.py     # PRD 6.7
  schemas/
    proposal.py
```

**초기화 프롬프트:**
```
당신은 비드마스터의 제안서 생성 에이전트입니다.

의존성: Agent-1, Agent-3, Agent-4 완료 후 시작

작업 목표:
1. PRD Section 3 Feature 3 제안서 생성 전체 파이프라인을 구현하십시오.
2. PRD Section 5.8 API를 구현하십시오 (SSE 스트리밍 포함).
3. 섹션별 프롬프트 (PRD 6.4)를 사용하여 각 섹션을 순차 생성하십시오.
4. Word/PDF/HWP 파일 생성을 구현하십시오.

제안서 생성 파이프라인:
  1. 공고 분석 결과 (evaluation_criteria, key_requirements) 로드
  2. 회사 프로필 + 유사 수행 실적 로드 (벡터 유사도 상위 3건)
  3. 섹션 목록 결정 (평가 기준 기반, 배점 내림차순)
  4. 섹션별 순차 생성 + SSE 스트리밍
  5. 각 섹션 DB 저장 + 스냅샷 버전 생성
  6. 전체 완료 후 Word 파일 생성 → S3 업로드

SSE 구현:
  FastAPI StreamingResponse
  Content-Type: text/event-stream
  Keep-alive: 30초마다 comment 이벤트

Word 생성:
  python-docx 사용
  공공기관 제안서 표준 서식 (A4, 바탕체/굴림, 10~12pt)
  표지 자동 생성 (사업명, 회사명, 제출일)

HWP 변환:
  Word → PDF (python-docx + LibreOffice)
  Word → HWP (LibreOffice, hwpx 포맷)
  변환 실패 시 Word만 제공

평가 달성도 자동 계산:
  생성 완료 후 Claude API로 자체 평가
  각 평가 항목별 달성 예상 점수 산출
  누락 항목 감지 → missing_items 목록 제공
```

---

### 7.8 Agent-6: Frontend

**담당 파일:**
```
/frontend/app/
  (auth)/
    login/page.tsx
    register/page.tsx
  (dashboard)/
    layout.tsx
    page.tsx               # 메인 대시보드
    notices/
      page.tsx             # 공고 목록 (추천 공고)
      [id]/page.tsx        # 공고 상세 + 분석
    participations/
      page.tsx             # 입찰 파이프라인 (칸반)
      [id]/page.tsx        # 참여 상세
    proposals/
      [id]/page.tsx        # 제안서 편집기
    company/
      profile/page.tsx     # 회사 프로필
      performances/page.tsx # 수행 실적
    analytics/page.tsx     # 성과 분석
    settings/page.tsx      # 설정
/frontend/components/
  notices/
    NoticeCard.tsx
    NoticeFilter.tsx
    MatchScoreBadge.tsx
  proposals/
    ProposalEditor.tsx
    SectionEditor.tsx
    EvaluationChecklist.tsx
    GenerationProgress.tsx
  participations/
    KanbanBoard.tsx
    PipelineCard.tsx
  dashboard/
    KpiCard.tsx
    DeadlineAlert.tsx
    WinRateChart.tsx
  scoring/
    ScoreBreakdown.tsx
    CompetitorList.tsx
  price/
    PriceDistribution.tsx
    RecommendedPrice.tsx
```

**초기화 프롬프트:**
```
당신은 비드마스터의 Next.js 프론트엔드 에이전트입니다.

의존성: Agent-2,3,4,5 완료 후 시작

작업 목표:
1. 모든 기능 페이지를 Next.js 14 App Router로 구현하십시오.
2. 데스크탑 퍼스트 (공고 분석은 대화면에서 주로 사용), 태블릿 지원.

디자인 가이드:
  Primary: #1B3A7A (딥 블루)
  Secondary: #2563EB (블루)
  Accent: #F59E0B (앰버 — 중요 알림)
  Success: #10B981 (낙찰)
  Danger: #EF4444 (탈락/마감)
  폰트: Pretendard
  컴포넌트: shadcn/ui

핵심 UX:
  1. 공고 목록: 매칭 점수 시각적 강조, 마감 D-Day 카운터
  2. 제안서 편집기: 좌측 본문 편집 / 우측 평가 체크리스트 고정
  3. AI 생성 진행: 섹션별 실시간 스트리밍 타이핑 효과
  4. 칸반 보드: 드래그 앤 드롭 상태 변경 (react-beautiful-dnd)
  5. 대시보드: 마감 임박 공고 빨간 하이라이트

SSE 스트리밍 클라이언트:
  eventsource-parser 라이브러리 사용
  연결 끊김 시 자동 재연결 (3회)

완료 후:
  모든 핵심 페이지 기본 동작 확인
```

---

### 7.9 Agent-7: Background Jobs

**담당 파일:**
```
/backend/app/
  workers/
    __init__.py
    celery_app.py          # Celery 설정
    crawler_tasks.py       # 크롤링 스케줄 작업
    embedding_tasks.py     # 임베딩 생성 작업
    notification_tasks.py  # 알림 발송 작업
    cleanup_tasks.py       # 만료 데이터 정리
  scheduler/
    beat_schedule.py       # Celery Beat 스케줄 정의
```

**초기화 프롬프트:**
```
당신은 비드마스터의 백그라운드 작업 에이전트입니다.

의존성: Agent-3 완료 후 시작

작업 목표:
1. Celery + Redis로 비동기 작업 인프라를 구현하십시오.
2. 나라장터 크롤링 스케줄 (1일 3회) 을 등록하십시오.
3. 신규 공고 매칭 알림 자동 발송을 구현하십시오.
4. 마감 임박 알림 (D-7, D-3, D-1) 을 구현하십시오.

스케줄 정의:
  크롤링: crontab(hour='6,12,18', minute='0')
  마감 알림 체크: crontab(hour='8', minute='0')  # 매일 08:00
  임베딩 배치: crontab(hour='2', minute='0')     # 매일 02:00 (미생성 임베딩)
  월간 통계 갱신: crontab(day_of_month='1', hour='0')

알림 발송:
  매칭 점수 70점 이상 신규 공고 → 이메일 + 앱 내 알림
  카카오 알림톡 (옵션, Phase 2)
  발송 실패 시 이메일 Fallback

완료 후:
  celery worker 와 celery beat 동시 기동 가능 상태
```

---

### 7.10 Agent-8: DevOps & Integration

**담당 파일:**
```
/
  docker-compose.yml
  docker-compose.prod.yml
  .env.example
  /backend
    Dockerfile
    requirements.txt
  /frontend
    Dockerfile
  /infrastructure
    nginx.conf
  /scripts
    seed_data.py
    test_crawler.py        # 크롤러 단독 테스트
    generate_embeddings.py # 임베딩 초기 생성
```

**초기화 프롬프트:**
```
당신은 비드마스터의 DevOps 에이전트입니다.

의존성: 모든 에이전트 완료 후 시작

작업 목표:
1. Docker Compose 로컬 개발 환경을 구성하십시오.
2. PostgreSQL (pgvector 포함), Redis, Celery Worker, Celery Beat 컨테이너를 구성하십시오.
3. .env.example을 모든 필요 환경변수와 함께 생성하십시오.

환경변수 목록:
  DATABASE_URL=postgresql+asyncpg://...
  REDIS_URL=redis://...
  SECRET_KEY=...
  ANTHROPIC_API_KEY=...
  OPENAI_API_KEY=...              # 임베딩용
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_S3_BUCKET=...
  KAKAO_CLIENT_ID=...
  TOSS_CLIENT_KEY=...
  TOSS_SECRET_KEY=...
  G2B_API_KEY=...                 # 나라장터 API 키 (있을 경우)
  CELERY_BROKER_URL=redis://...
  CELERY_RESULT_BACKEND=redis://...

시드 데이터:
  - 테스트 계정 1개 (owner 역할, pro 플랜)
  - 테스트 회사 1개 (㈜테스트아이티, IT 용역, 45인)
  - 수행 실적 5건
  - 샘플 공고 20건 (IT 용역, 다양한 발주기관)
  - 샘플 낙찰 데이터 50건 (가격 분석용)

완료 후:
  docker-compose up 으로 전체 시스템 정상 기동
  http://localhost:3000 접속 가능
  http://localhost:8000/docs Swagger 문서 접근 가능
```

---

## 8. 외부 데이터 연동

### 8.1 나라장터 (G2B) 데이터 수집

```
[공식 API 우선 활용]
  나라장터 OpenAPI: https://www.data.go.kr (공공데이터포털)
  - 조달청 입찰공고 조회 서비스
  - 낙찰결과 조회 서비스
  - 제한경쟁 입찰공고 조회 서비스

[API 키 발급]
  공공데이터포털 (data.go.kr) 회원가입 후 활용 신청
  일일 요청 한도: 10,000건 (무료)

[스크래핑 보완]
  API로 수집 불가한 첨부파일은 직접 다운로드
  robots.txt 준수, 과도한 요청 금지
  연간 수집 계획을 나라장터에 사전 고지 권장 (법적 리스크 최소화)
```

### 8.2 낙찰 결과 데이터 수집 계획

```
[수집 대상]
  - 최근 3년 IT 용역 낙찰 공고 (약 15,000건)
  - 업체명, 낙찰금액, 낙찰가율, 투찰 순위
  - 공공데이터포털 낙찰결과 API 활용

[데이터 정제]
  - 동일 업체명 정규화 (㈜삼성SDS → 삼성SDS)
  - 이상치 제거 (낙찰가율 50% 미만, 110% 초과)
  - 초기 DB 구축: 약 1주 소요 예상

[업데이트 주기]
  낙찰 결과 수집: 매일 18:00 (크롤링과 연계)
```

### 8.3 HWP 처리 방안

```
[LibreOffice 기반 변환]
  1. apt-get install libreoffice
  2. soffice --headless --convert-to pdf input.hwp
  3. pdfplumber로 텍스트 추출

[한계]
  - 복잡한 표 구조: 정확도 80% 수준
  - 이미지 기반 HWP: 텍스트 추출 불가 → OCR 필요 (Tesseract)
  - 암호화된 HWP: 처리 불가

[Fallback]
  파싱 실패 시: "원문 직접 확인 필요" + 나라장터 링크 제공
  사용자 수동 텍스트 입력 폼 제공
```

---

## 9. 기술 스택 상세

### 9.1 Backend 의존성

```txt
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
alembic==1.14.0
asyncpg==0.30.0
redis[asyncio]==5.2.0
celery==5.4.0
pydantic==2.10.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
anthropic==0.40.0
openai==1.58.0               # 임베딩 (text-embedding-3-small)
pgvector==0.3.6
numpy==2.2.0
scipy==1.14.0                # 낙찰가 통계
pdfplumber==0.11.0
python-docx==1.1.2
weasyprint==62.3
httpx==0.28.0
beautifulsoup4==4.12.0       # 크롤러
playwright==1.49.0           # 동적 페이지 크롤링
boto3==1.35.0
openpyxl==3.1.5
pytest==8.3.0
pytest-asyncio==0.24.0
```

### 9.2 Frontend 의존성

```json
{
  "dependencies": {
    "next": "14.2.0",
    "react": "18.3.0",
    "typescript": "5.6.0",
    "tailwindcss": "3.4.0",
    "@tanstack/react-query": "5.62.0",
    "zustand": "5.0.0",
    "react-hook-form": "7.54.0",
    "zod": "3.23.0",
    "recharts": "2.13.0",
    "react-beautiful-dnd": "13.1.1",
    "eventsource-parser": "3.0.0",
    "@tiptap/react": "2.10.0",
    "@tiptap/starter-kit": "2.10.0",
    "react-pdf": "9.2.0",
    "axios": "1.7.0"
  }
}
```

### 9.3 인프라 구성

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: bidmaster
      POSTGRES_USER: bidmaster
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]

  celery_worker:
    build: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on: [postgres, redis]

  celery_beat:
    build: ./backend
    command: celery -A app.workers.celery_app beat --loglevel=info
    depends_on: [redis]
```

---

## 10. 수익 모델

### 10.1 구독 티어

| 플랜 | 월 요금 | 대상 | 포함 기능 |
|------|--------|------|---------|
| **무료** | 무료 | 개인 | 공고 조회 30건/월, 매칭 점수 5건/월 |
| **스타터** | 99,000원 | 소기업 (~20인) | 공고 무제한, 매칭 무제한, 제안서 3건/월 |
| **프로** | 299,000원 | 중기업 (~100인) | 스타터 + 제안서 10건/월, 팀 3명, 가격 분석 |
| **엔터프라이즈** | 별도 협의 | 대기업·컨소시엄 | 무제한 + 전담 CS + API 접근 |

### 10.2 건당 과금 (구독 초과 시)

| 항목 | 단가 |
|------|------|
| 제안서 추가 생성 | 50,000원/건 |
| 스코어링 추가 | 10,000원/건 |
| 가격 분석 추가 | 15,000원/건 |
| HWP 변환 | 5,000원/건 |

### 10.3 성공 수수료 (Premium 옵션)

```
낙찰 성공 시 낙찰금액의 0.3~0.5%
  조건:
  - 비드마스터로 제안서 작성 확인 가능한 경우만
  - 계약 체결 후 30일 이내 정산
  - 성공 수수료 선택 고객은 구독료 50% 할인

  리스크: 낙찰 여부 확인 어려움 → 사용자 자진 신고 방식
```

### 10.4 수익 목표

| 기간 | 구독사 | MRR 목표 |
|------|-------|---------|
| 6개월 | 200사 | 3,000만원 |
| 12개월 | 600사 | 1억원 |
| 24개월 | 2,000사 | 3.5억원 |

---

## 11. 마케팅/GTM 전략

### 11.1 초기 채널 (0~6개월)

**네이버 SEO / 검색 광고:**
- "입찰 제안서 작성", "나라장터 공고 분석", "공공입찰 낙찰률" 키워드
- 월 블로그 포스팅 10개: 낙찰 사례, 제안서 작성 팁

**커뮤니티:**
- 조달청 교육 세미나 참가 및 발표
- 중소기업 IT 전략 포럼
- 나라장터 자주 사용하는 카페/네이버 카페 홍보

**직접 영업 (B2B):**
- IT 용역 분야 중소기업 콜드 이메일 (나라장터 입찰 이력 있는 기업 타깃)
- 이노비즈, 메인비즈 인증 기업 DB 활용

**파트너십:**
- 중소기업기술정보진흥원(TIPA) 파트너십
- 중소벤처기업부 스마트공장 관련 협력
- 제안서 대행 프리랜서 파트너 프로그램 (비드마스터를 도구로 사용)

### 11.2 바이럴 루프

```
낙찰 성공 → 사용자 자발적 공유
  → "비드마스터로 XX억 공고 낙찰했습니다" 후기
  → 업계 커뮤니티 바이럴

팀 협업 기능
  → 한 기업이 팀원 초대 → 팀원도 가입
```

---

## 12. 리스크 분석

### 12.1 기술·데이터 리스크

| 리스크 | 심각도 | 대응 방안 |
|--------|-------|---------|
| 나라장터 크롤링 차단 | 높음 | 공공데이터포털 API 우선 활용, 크롤링은 보완용 |
| HWP 파일 파싱 정확도 저하 | 중간 | LibreOffice 변환 + OCR Fallback |
| 낙찰가 데이터 부족 (초기) | 높음 | 초기 수동 수집 50건 이상 확보 후 서비스 출시 |
| Claude API 비용 (제안서당 $2~5) | 중간 | 토큰 최적화, 섹션 캐싱, 프롬프트 효율화 |

### 12.2 사업 리스크

| 리스크 | 심각도 | 대응 방안 |
|--------|-------|---------|
| 제안서 품질 불만족 → 클레임 | 높음 | "AI 초안" 포지셔닝 명확화, 면책 약관 |
| 낙찰 실패 책임 전가 | 높음 | 서비스 범위를 "초안 제공"으로 명확히 한정 |
| 나라장터 데이터 저작권 | 중간 | 공공데이터포털 이용약관 준수, 법률 검토 |
| 대형 SI 업체의 자체 개발 | 중간 | SME 전문화, 가격 경쟁력 유지 |
| 조달 제도 변경 | 낮음 | 평가 기준 변경 시 빠른 프롬프트/모델 업데이트 |

---

## 13. 성공 지표

| 지표 | 목표값 | 측정 주기 |
|------|-------|---------|
| 공고 수집 지연 | 4시간 이내 | 실시간 |
| PDF 파싱 성공률 | 95% 이상 | 일간 |
| 매칭 스코어 정확도 (사용자 평가) | 4.0/5.0 이상 | 월간 |
| 제안서 생성 만족도 | 4.0/5.0 이상 | 건당 |
| 제안서 생성 시간 (10페이지) | 3분 이내 | 실시간 |
| 스코어 70점+ 공고 실제 낙찰률 | 30% 이상 | 분기 |
| 프리 → 유료 전환율 | 5% 이상 | 월간 |
| 월 이탈률 (Churn Rate) | 5% 이하 | 월간 |
| API p95 응답시간 | 3초 이내 | 실시간 |
| 크롤러 가동률 | 99% 이상 | 일간 |

---

## 14. 마일스톤

| 기간 | 마일스톤 | 산출물 |
|------|---------|-------|
| Week 1 | DB + 기반 인프라 | 전체 스키마, Docker 환경, pgvector 설정 |
| Week 2 | 크롤러 MVP | 나라장터 공고 수집, PDF 파싱, 공고 API |
| Week 3 | 회사 프로필 + 매칭 | 프로필 등록, 임베딩 생성, 매칭 스코어 |
| Week 4 | 스코어링 + 가격 분석 | 낙찰 가능성 점수, 낙찰가 추천 |
| Month 2 | 제안서 생성 MVP | AI 초안 생성, SSE 스트리밍, Word 다운로드 |
| Month 2 | 프론트엔드 MVP | 공고 목록, 제안서 편집기, 대시보드 |
| Month 3 | 베타 출시 | 30개 사 베타 테스트, 피드백 수집 |
| Month 4 | 결제 연동 | 토스페이먼츠, 구독 관리, 첫 유료 고객 |
| Month 5~6 | 고도화 | 성공 수수료 모델, HWP 지원, 팀 공동 편집 |
| Month 12 | 스케일업 | 600사 구독, MRR 1억원 |

---

*이 PRD는 Claude Code 멀티에이전트 파이프라인 직접 실행용 문서입니다.*  
*각 에이전트 초기화 프롬프트는 해당 에이전트가 참조해야 할 PRD 섹션을 명시적으로 포함합니다.*  
*docs/project/prd.md 경로에 위치시키고 CLAUDE.md에서 이 파일을 참조하십시오.*
