"""제안서 AI 생성 서비스 (F-03) - GLM API 사용"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import get_settings
from src.core.exceptions import AppException
from src.models.bid import Bid
from src.models.company import Company
from src.models.proposal import Proposal
from src.models.proposal_section import ProposalSection, SECTION_DEFINITIONS
from src.services.proposal_service import ProposalService

logger = logging.getLogger(__name__)

# GLM API 클라이언트
try:
    from zhipuai import ZhipuAI

    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False
    logger.warning("[GLM] zhipuai 라이브러리가 설치되지 않음")


class ProposalGeneratorService:
    """제안서 AI 생성 서비스"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()
        self.proposal_service = ProposalService(db)

        # Jinja2 환경 설정
        template_dir = Path(__file__).parent.parent / "templates" / "prompts"
        template_dir.mkdir(parents=True, exist_ok=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(),
        )

        # GLM 클라이언트 초기화
        self.glm_client = None
        if GLM_AVAILABLE and self.settings.glm_api_key:
            self.glm_client = ZhipuAI(api_key=self.settings.glm_api_key)

    # ============================================================
    # 제안서 생성 메인 플로우
    # ============================================================

    async def generate_proposal(
        self,
        proposal_id: UUID,
        user_id: UUID,
        section_keys: list[str] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        제안서 전체 생성 (SSE 스트리밍)

        Yield: 진행 상황 이벤트
        """
        # 제안서 조회
        proposal = await self.proposal_service.get_proposal(
            proposal_id, user_id, include_sections=True
        )

        # 상태를 generating으로 변경
        await self.proposal_service.update_status(proposal_id, user_id, "generating")

        # 공고 및 회사 정보 조회
        bid = await self._get_bid(proposal.bid_id)
        company = None
        if proposal.company_id:
            company = await self._get_company(proposal.company_id)

        # 생성할 섹션 결정
        if section_keys:
            target_sections = [
                k for k in section_keys if k in SECTION_DEFINITIONS
            ]
        else:
            target_sections = list(SECTION_DEFINITIONS.keys())

        total_sections = len(target_sections)
        completed_sections = 0

        yield {
            "event": "start",
            "data": {
                "proposalId": str(proposal_id),
                "totalSections": total_sections,
                "message": "제안서 생성을 시작합니다.",
            },
        }

        # 섹션별 생성
        for section_key in target_sections:
            try:
                yield {
                    "event": "section_start",
                    "data": {
                        "sectionKey": section_key,
                        "title": SECTION_DEFINITIONS[section_key]["title"],
                        "message": f"{SECTION_DEFINITIONS[section_key]['title']} 섹션 생성 중...",
                    },
                }

                # 섹션 생성
                content = await self._generate_section(
                    proposal=proposal,
                    section_key=section_key,
                    bid=bid,
                    company=company,
                )

                # 섹션 업데이트
                await self.proposal_service.update_section(
                    proposal_id=proposal_id,
                    section_key=section_key,
                    user_id=user_id,
                    content=content,
                )

                completed_sections += 1

                yield {
                    "event": "section_complete",
                    "data": {
                        "sectionKey": section_key,
                        "title": SECTION_DEFINITIONS[section_key]["title"],
                        "wordCount": len(content),
                        "completedSections": completed_sections,
                        "totalSections": total_sections,
                    },
                }

            except Exception as e:
                logger.error(f"[제안서] 섹션 생성 실패: {section_key} - {e}")
                yield {
                    "event": "section_error",
                    "data": {
                        "sectionKey": section_key,
                        "error": str(e),
                    },
                }

        # 완료 처리
        await self.proposal_service.update_status(proposal_id, user_id, "ready")

        # 버전 생성
        await self.proposal_service.create_version(proposal_id, user_id)

        yield {
            "event": "complete",
            "data": {
                "proposalId": str(proposal_id),
                "status": "ready",
                "message": "제안서 생성이 완료되었습니다.",
            },
        }

    async def generate_single_section(
        self,
        proposal_id: UUID,
        section_key: str,
        user_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """개별 섹션 재생성"""
        if section_key not in SECTION_DEFINITIONS:
            raise AppException(
                code="SECTION_002",
                message="유효하지 않은 섹션 키입니다.",
            )

        proposal = await self.proposal_service.get_proposal(
            proposal_id, user_id, include_sections=True
        )

        bid = await self._get_bid(proposal.bid_id)
        company = None
        if proposal.company_id:
            company = await self._get_company(proposal.company_id)

        # 컨텍스트 병합
        extra_context = context or {}

        content = await self._generate_section(
            proposal=proposal,
            section_key=section_key,
            bid=bid,
            company=company,
            extra_context=extra_context,
        )

        # 섹션 업데이트
        section = await self.proposal_service.update_section(
            proposal_id=proposal_id,
            section_key=section_key,
            user_id=user_id,
            content=content,
        )

        return {
            "sectionKey": section_key,
            "title": section.title,
            "content": content,
            "wordCount": len(content),
        }

    # ============================================================
    # 섹션별 생성 로직
    # ============================================================

    async def _generate_section(
        self,
        proposal: Proposal,
        section_key: str,
        bid: Bid,
        company: Company | None,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """개별 섹션 생성"""
        section_def = SECTION_DEFINITIONS[section_key]

        # 프롬프트 템플릿 렌더링
        prompt = await self._render_prompt(
            section_key=section_key,
            proposal=proposal,
            bid=bid,
            company=company,
            extra_context=extra_context,
        )

        # GLM API 호출
        content = await self._call_glm_api(prompt)

        return content

    async def _render_prompt(
        self,
        section_key: str,
        proposal: Proposal,
        bid: Bid,
        company: Company | None,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """프롬프트 템플릿 렌더링"""
        # 기본 컨텍스트
        context = {
            "proposal_title": proposal.title,
            "bid_title": bid.title,
            "bid_organization": bid.organization,
            "bid_deadline": bid.deadline.isoformat() if bid.deadline else "",
            "bid_budget": bid.budget or "미공개",
            "bid_description": bid.description or "",
            "bid_requirements": bid.requirements or [],
            "company_name": company.name if company else "",
            "company_description": company.description if company else "",
            "company_business_areas": company.business_areas if company else [],
            "company_certifications": company.certifications if company else [],
        }

        # 추가 컨텍스트 병합
        if extra_context:
            context.update(extra_context)

        # 템플릿 로드 (파일이 없으면 기본 템플릿 사용)
        template_file = f"{section_key}.jinja2"
        try:
            template = self.jinja_env.get_template(template_file)
            return template.render(**context)
        except Exception:
            # 기본 템플릿 사용
            return self._get_default_prompt(section_key, context)

    def _get_default_prompt(
        self, section_key: str, context: dict[str, Any]
    ) -> str:
        """섹션별 기본 프롬프트"""
        prompts = {
            "overview": f"""다음 공고에 대한 사업 개요를 작성하세요.

공고명: {context['bid_title']}
발주기관: {context['bid_organization']}
사업 예산: {context['bid_budget']}
공고 내용: {context['bid_description']}

요구사항:
- 사업의 목적과 필요성을 명확히 기술
- 사업 범위와 대상 정의
- 기대 효과 제시

한글로 1000자 내외로 작성하세요.""",

            "technical": f"""다음 공고에 대한 기술 제안서를 작성하세요.

공고명: {context['bid_title']}
발주기관: {context['bid_organization']}
요구사항: {context['bid_requirements']}
회사 정보: {context['company_name']} - {context['company_description']}

요구사항:
- 기술적 접근 방법 상세 기술
- 핵심 기술 요소 및 솔루션 설명
- 기술적 우수성 및 차별점 제시

한글로 2000자 내외로 작성하세요.""",

            "methodology": f"""다음 공고에 대한 수행 방법론을 작성하세요.

공고명: {context['bid_title']}
발주기관: {context['bid_organization']}
사업 내용: {context['bid_description']}

요구사항:
- 단계별 수행 방법론 기술
- 각 단계별 주요 산출물 정의
- 품질 관리 방안 포함

한글로 1500자 내외로 작성하세요.""",

            "schedule": f"""다음 공고에 대한 추진 일정을 작성하세요.

공고명: {context['bid_title']}
마감일: {context['bid_deadline']}

요구사항:
- 전체 사업 기간 중 주요 단계 구분
- 각 단계별 상세 일정 (월/주 단위)
- 주요 마일스톤 및 산출물 제시

한글로 800자 내외로 작성하세요.""",

            "organization": f"""다음 공고에 대한 조직 구성안을 작성하세요.

공고명: {context['bid_title']}
발주기관: {context['bid_organization']}
회사명: {context['company_name']}

요구사항:
- 프로젝트 조직도 구성
- 주요 인력별 역할 및 책임
- 인력 투입 계획

한글로 1000자 내외로 작성하세요.""",

            "budget": f"""다음 공고에 대한 예산 내역을 작성하세요.

공고명: {context['bid_title']}
사업 예산: {context['bid_budget']}

요구사항:
- 항목별 예산 내역 (인건비, 제경비, 기타)
- 예산 산출 근거
- 비용 절감 방안

한글로 800자 내외로 작성하세요.""",
        }

        return prompts.get(section_key, f"{section_key} 섹션 내용을 작성하세요.")

    # ============================================================
    # GLM API 연동
    # ============================================================

    async def _call_glm_api(self, prompt: str) -> str:
        """GLM API 호출"""
        if not self.glm_client:
            # API 키가 없으면 목업 응답 반환
            logger.warning("[GLM] API 키 없음, 목업 응답 반환")
            return self._get_mock_response(prompt)

        try:
            # 비동기로 실행 (동기 클라이언트를 별도 스레드에서 실행)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._call_glm_sync,
                prompt,
            )

            return response

        except Exception as e:
            logger.error(f"[GLM] API 호출 실패: {e}")
            raise AppException(
                code="AI_001",
                message=f"AI 생성 중 오류가 발생했습니다: {str(e)}",
            )

    def _call_glm_sync(self, prompt: str) -> str:
        """GLM API 동기 호출"""
        response = self.glm_client.chat.completions.create(
            model=self.settings.glm_model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 공공 입찰 제안서 작성 전문가입니다. "
                    "명확하고 전문적인 제안서 내용을 작성합니다.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.settings.glm_max_tokens,
            temperature=self.settings.glm_temperature,
        )

        return response.choices[0].message.content

    def _get_mock_response(self, prompt: str) -> str:
        """API 키 없을 때 목업 응답"""
        # 프롬프트에서 섹션 유형 추론
        if "사업 개요" in prompt:
            return """## 1. 사업 개요

### 1.1 사업의 목적

본 사업은 발주기관의 디지털 전환을 위한 핵심 인프라 구축을 목적으로 합니다. 급변하는 디지털 환경에 대응하고, 업무 효율성을 극대화하기 위한 통합 시스템 구축이 시급한 실정입니다.

### 1.2 사업의 필요성

최근 공공기관의 디지털 전환 요구가 급증함에 따라, 기존 시스템의 한계를 극복하고 새로운 디지털 서비스를 제공할 수 있는 플랫폼이 필요합니다.

### 1.3 사업 범위

- 시스템 설계 및 구축
- 데이터 마이그레이션
- 사용자 교육 및 기술 지원
- 유지보수 및 운영 지원

### 1.4 기대 효과

본 사업 완료 시 다음과 같은 효과가 기대됩니다:
- 업무 처리 시간 50% 단축
- 연간 운영 비용 30% 절감
- 사용자 만족도 90% 이상 달성"""

        elif "기술 제안" in prompt:
            return """## 2. 기술 제안

### 2.1 기술적 접근 방법

본 프로젝트에서는 클라우드 네이티브 아키텍처를 기반으로 한 MSA(Microservices Architecture)를 적용하여 확장성과 유연성을 확보합니다.

### 2.2 핵심 기술 요소

1. **프론트엔드**: React 기반 SPA, 반응형 웹 디자인
2. **백엔드**: FastAPI 기반 RESTful API, 비동기 처리
3. **데이터베이스**: PostgreSQL 주 DB, Redis 캐시
4. **인프라**: AWS 클라우드, Docker 컨테이너

### 2.3 기술적 우수성

- 고가용성 아키텍처 설계 (99.9% SLA)
- 보안 인증(K-ISMS) 대응 설계
- 자동화된 CI/CD 파이프라인"""

        elif "수행 방법론" in prompt:
            return """## 3. 수행 방법론

### 3.1 단계별 수행 방법

본 프로젝트는 다음과 같이 5단계로 수행합니다:

**1단계: 요구사항 분석 (4주)**
- 현황 분석 및 요구사항 도출
- 시스템 아키텍처 설계

**2단계: 설계 (6주)**
- 상세 설계 및 화면 설계
- DB 설계 및 API 명세 작성

**3단계: 개발 (12주)**
- 프론트엔드/백엔드 개발
- 단위 테스트 및 통합 테스트

**4단계: 테스트 및 안정화 (4주)**
- 시스템 테스트
- 사용자 교육

**5단계: 이관 및 운영 (2주)**
- 데이터 마이그레이션
- 시스템 이관 및 기술 지원"""

        return "본 섹션의 내용이 생성되었습니다. 실제 서비스에서는 AI가 생성한 전문적인 내용이 표시됩니다."

    # ============================================================
    # 내부 메서드
    # ============================================================

    async def _get_bid(self, bid_id: UUID) -> Bid:
        """공고 조회"""
        from sqlalchemy import select

        stmt = select(Bid).where(Bid.id == bid_id)
        result = await self.db.execute(stmt)
        bid = result.scalar_one_or_none()

        if not bid:
            raise AppException(
                code="BID_001",
                message="입찰 공고를 찾을 수 없습니다.",
            )
        return bid

    async def _get_company(self, company_id: UUID) -> Company | None:
        """회사 조회"""
        from sqlalchemy import select

        stmt = select(Company).where(Company.id == company_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
