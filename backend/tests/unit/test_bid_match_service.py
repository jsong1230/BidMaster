"""
BidMatchService 단위 테스트

test-spec.md 기준:
- 매칭 점수 계산 (0~100)
- 70점 이상 공고 필터링
- 빈 텍스트 처리
- 여러 회사 동시 매칭
- _score_to_recommendation 경계값 테스트

RED 상태: 구현 전이므로 import 시 ImportError 발생
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# 구현 전이므로 import 시 ImportError 발생 - RED 상태
from src.services.bid_match_service import BidMatchService
from src.core.exceptions import AppException


def _make_mock_bid(title="정보시스템 구축 사업", organization="행정안전부", category="정보화", description="공공기관 정보시스템 고도화"):
    """테스트용 Bid Mock 생성 헬퍼"""
    bid = MagicMock()
    bid.id = str(uuid4())
    bid.title = title
    bid.organization = organization
    bid.category = category
    bid.description = description
    bid.status = "open"
    return bid


def _make_mock_company(industry="소프트웨어", description="공공기관 SI 전문 기업"):
    """테스트용 Company Mock 생성 헬퍼"""
    company = MagicMock()
    company.id = str(uuid4())
    company.industry = industry
    company.description = description
    company.deleted_at = None
    return company


def _make_mock_user(company_id=None):
    """테스트용 User Mock 생성 헬퍼"""
    user = MagicMock()
    user.id = str(uuid4())
    user.company_id = company_id
    return user


class TestAnalyzeMatch:
    """analyze_match 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_높은_적합도_매칭_70점_이상(self):
        """
        Given: 업종 일치 회사 + 유사한 공고
        When: analyze_match() 호출
        Then: total_score >= 70, recommendation="recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        company = _make_mock_company(
            industry="소프트웨어 개발업",
            description="공공기관 정보시스템 구축 전문. 행정 시스템, 전자정부 솔루션 개발."
        )
        bid = _make_mock_bid(
            title="2026년 정보시스템 고도화 사업",
            organization="행정안전부",
            category="정보화",
            description="행정안전부 전자정부 시스템 구축 및 유지보수. 소프트웨어 개발."
        )

        performances = [
            MagicMock(project_name="전자정부 시스템 구축", client_name="한국정보화진흥원", contract_amount=500000000),
            MagicMock(project_name="행정 DB 구축", client_name="행정안전부", contract_amount=300000000),
        ]
        certifications = [
            MagicMock(name="GS인증 1등급", issuer="한국정보통신기술협회"),
        ]

        service._get_user_company = AsyncMock(return_value=company)
        service._get_bid = AsyncMock(return_value=bid)
        service._get_company_performances = AsyncMock(return_value=performances)
        service._get_company_certifications = AsyncMock(return_value=certifications)
        service._get_bid_attachments = AsyncMock(return_value=[])
        service._upsert_match = AsyncMock(side_effect=lambda match: match)

        # Act
        result = await service.analyze_match(user_id=user_id, bid_id=bid_id)

        # Assert
        assert result is not None
        assert result.total_score >= 70
        assert result.recommendation == "recommended"

    @pytest.mark.asyncio
    async def test_낮은_적합도_매칭_40점_미만(self):
        """
        Given: 업종 불일치 회사 + 관련 없는 공고
        When: analyze_match() 호출
        Then: total_score < 40, recommendation="not_recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        company = _make_mock_company(
            industry="음식료 제조업",
            description="식품 가공 및 유통 전문 기업. 식자재 공급 서비스."
        )
        bid = _make_mock_bid(
            title="2026년 정보시스템 고도화 사업",
            organization="행정안전부",
            category="정보화",
            description="공공기관 IT 인프라 구축 및 소프트웨어 개발."
        )

        service._get_user_company = AsyncMock(return_value=company)
        service._get_bid = AsyncMock(return_value=bid)
        service._get_company_performances = AsyncMock(return_value=[])
        service._get_company_certifications = AsyncMock(return_value=[])
        service._get_bid_attachments = AsyncMock(return_value=[])
        service._upsert_match = AsyncMock(side_effect=lambda match: match)

        # Act
        result = await service.analyze_match(user_id=user_id, bid_id=bid_id)

        # Assert
        assert result is not None
        assert result.total_score < 40
        assert result.recommendation == "not_recommended"

    @pytest.mark.asyncio
    async def test_보통_적합도_40점_이상_70점_미만(self):
        """
        Given: 부분 일치 회사 + 공고
        When: analyze_match() 호출
        Then: 40 <= total_score < 70, recommendation="neutral"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        company = _make_mock_company(
            industry="데이터 처리업",
            description="데이터 분석 및 통계 처리 서비스."
        )
        bid = _make_mock_bid(
            title="공공데이터 처리 시스템 구축",
            organization="통계청",
            category="통계",
            description="국가 통계 데이터 관리 시스템. 데이터 수집, 가공."
        )

        service._get_user_company = AsyncMock(return_value=company)
        service._get_bid = AsyncMock(return_value=bid)
        service._get_company_performances = AsyncMock(return_value=[])
        service._get_company_certifications = AsyncMock(return_value=[])
        service._get_bid_attachments = AsyncMock(return_value=[])
        service._upsert_match = AsyncMock(side_effect=lambda match: match)

        # Act
        result = await service.analyze_match(user_id=user_id, bid_id=bid_id)

        # Assert
        assert result is not None
        assert 40 <= result.total_score < 70
        assert result.recommendation == "neutral"

    @pytest.mark.asyncio
    async def test_회사_프로필_없음_AppException_COMPANY_001(self):
        """
        Given: company_id=None인 사용자 (회사 미소속)
        When: analyze_match() 호출
        Then: AppException(COMPANY_001) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        # 회사 없음
        service._get_user_company = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.analyze_match(user_id=user_id, bid_id=bid_id)

        assert exc_info.value.code == "COMPANY_001"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_공고_없음_AppException_BID_001(self):
        """
        Given: 존재하지 않는 bid_id
        When: analyze_match() 호출
        Then: AppException(BID_001) 발생
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        company = _make_mock_company()
        service._get_user_company = AsyncMock(return_value=company)
        service._get_bid = AsyncMock(return_value=None)

        # Act & Assert
        with pytest.raises(AppException) as exc_info:
            await service.analyze_match(user_id=user_id, bid_id=bid_id)

        assert exc_info.value.code == "BID_001"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_기존_매칭_결과_upsert(self):
        """
        Given: 이미 같은 user+bid 매칭 결과가 존재
        When: analyze_match() 호출
        Then: 기존 결과 갱신 (upsert), 중복 생성 아님
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        user_id = uuid4()
        bid_id = uuid4()

        company = _make_mock_company()
        bid = _make_mock_bid()

        service._get_user_company = AsyncMock(return_value=company)
        service._get_bid = AsyncMock(return_value=bid)
        service._get_company_performances = AsyncMock(return_value=[])
        service._get_company_certifications = AsyncMock(return_value=[])
        service._get_bid_attachments = AsyncMock(return_value=[])

        upsert_call_count = {"n": 0}
        async def mock_upsert(match):
            upsert_call_count["n"] += 1
            return match
        service._upsert_match = mock_upsert

        # Act
        result1 = await service.analyze_match(user_id=user_id, bid_id=bid_id)
        result2 = await service.analyze_match(user_id=user_id, bid_id=bid_id)

        # Assert — upsert가 2회 호출 (중복 생성 아님)
        assert upsert_call_count["n"] == 2


class TestBuildCompanyText:
    """_build_company_text 메서드 테스트"""

    def test_풀_프로필_텍스트_생성(self):
        """
        Given: 회사 + 실적 3건 + 인증 2건
        When: _build_company_text() 호출
        Then: 업종, 설명, 실적, 인증이 모두 포함된 텍스트 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        company = _make_mock_company(industry="소프트웨어 개발업", description="공공 IT 전문 기업")
        performances = [
            MagicMock(project_name="행정시스템 구축", client_name="행정안전부", contract_amount=500000000),
            MagicMock(project_name="전자정부 포털", client_name="국민권익위원회", contract_amount=300000000),
            MagicMock(project_name="통계 데이터 플랫폼", client_name="통계청", contract_amount=200000000),
        ]
        certifications = [
            MagicMock(name="GS인증 1등급", issuer="한국정보통신기술협회"),
            MagicMock(name="ISO 27001", issuer="BSI"),
        ]

        # Act
        result = service._build_company_text(company, performances, certifications)

        # Assert
        assert "소프트웨어 개발업" in result
        assert "공공 IT 전문 기업" in result
        assert "행정시스템 구축" in result
        assert "전자정부 포털" in result
        assert "통계 데이터 플랫폼" in result
        assert "GS인증 1등급" in result
        assert "ISO 27001" in result

    def test_최소_프로필_텍스트_생성(self):
        """
        Given: 회사 기본 정보만 (실적/인증 없음)
        When: _build_company_text() 호출
        Then: 업종 + 설명만 포함된 텍스트 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        company = _make_mock_company(industry="IT서비스", description="IT 서비스 전문 기업")

        # Act
        result = service._build_company_text(company, [], [])

        # Assert
        assert "IT서비스" in result
        assert "IT 서비스 전문 기업" in result
        assert len(result) > 0


class TestBuildBidText:
    """_build_bid_text 메서드 테스트"""

    def test_첨부파일_포함_공고_텍스트(self):
        """
        Given: 공고 + 첨부파일 2건 (1건 파싱됨)
        When: _build_bid_text() 호출
        Then: 공고 텍스트 + 파싱 텍스트 결합 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        bid = _make_mock_bid(
            title="정보시스템 고도화",
            organization="행정안전부",
            category="정보화",
            description="시스템 고도화 사업"
        )

        attachments = [
            MagicMock(extracted_text="첨부파일 1 추출 텍스트: 상세 요건..."),
            MagicMock(extracted_text=None),  # 파싱 실패
        ]

        # Act
        result = service._build_bid_text(bid, attachments)

        # Assert
        assert "정보시스템 고도화" in result
        assert "행정안전부" in result
        assert "첨부파일 1 추출 텍스트" in result

    def test_첨부파일_없는_공고_텍스트(self):
        """
        Given: 공고만 (첨부파일 없음)
        When: _build_bid_text() 호출
        Then: 공고 제목 + 설명만 포함된 텍스트 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        bid = _make_mock_bid(
            title="정보시스템 구축",
            organization="국세청",
            description="세무 시스템 구축 사업"
        )

        # Act
        result = service._build_bid_text(bid, [])

        # Assert
        assert "정보시스템 구축" in result
        assert "국세청" in result
        assert len(result) > 0


class TestCalculateTfidfSimilarity:
    """_calculate_tfidf_similarity 메서드 테스트"""

    def test_동일_텍스트_유사도_1에_근접(self):
        """
        Given: 동일한 텍스트 2개
        When: _calculate_tfidf_similarity() 호출
        Then: 유사도 1.0 (또는 근사값)
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        text = "소프트웨어 개발업 공공기관 정보시스템 구축 전문 전자정부 행정 시스템"

        # Act
        result = service._calculate_tfidf_similarity(text, text)

        # Assert
        assert result >= 0.9  # 동일 텍스트는 1.0에 근접

    def test_완전히_다른_텍스트_유사도_0에_근접(self):
        """
        Given: 관련 없는 텍스트 2개
        When: _calculate_tfidf_similarity() 호출
        Then: 유사도 0.0에 가까운 값
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        text_a = "소프트웨어 개발업 정보시스템 전자정부 행정"
        text_b = "농업 식품 유통 농산물 축산업 수산업"

        # Act
        result = service._calculate_tfidf_similarity(text_a, text_b)

        # Assert
        assert result < 0.3  # 관련 없는 텍스트는 유사도 낮음

    def test_빈_텍스트_유사도_0(self):
        """
        Given: 빈 문자열 + 일반 텍스트
        When: _calculate_tfidf_similarity() 호출
        Then: 유사도 0.0
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        result = service._calculate_tfidf_similarity("", "소프트웨어 개발 정보시스템")

        # Assert
        assert result == 0.0

    def test_두_텍스트_모두_빈_문자열_유사도_0(self):
        """
        Given: 두 텍스트 모두 빈 문자열
        When: _calculate_tfidf_similarity() 호출
        Then: 유사도 0.0 (ZeroDivision 예외 없음)
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        result = service._calculate_tfidf_similarity("", "")

        # Assert
        assert result == 0.0


class TestScoreToRecommendation:
    """_score_to_recommendation 메서드 테스트"""

    def test_점수_85_recommended(self):
        """
        Given: total_score=85
        When: _score_to_recommendation() 호출
        Then: ("recommended", "높은 적합도...") 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, reason = service._score_to_recommendation(85)

        # Assert
        assert recommendation == "recommended"
        assert "높은 적합도" in reason

    def test_점수_55_neutral(self):
        """
        Given: total_score=55
        When: _score_to_recommendation() 호출
        Then: ("neutral", "보통 적합도...") 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, reason = service._score_to_recommendation(55)

        # Assert
        assert recommendation == "neutral"
        assert "보통 적합도" in reason

    def test_점수_25_not_recommended(self):
        """
        Given: total_score=25
        When: _score_to_recommendation() 호출
        Then: ("not_recommended", "낮은 적합도...") 반환
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, reason = service._score_to_recommendation(25)

        # Assert
        assert recommendation == "not_recommended"
        assert "낮은 적합도" in reason

    def test_경계값_70점_recommended(self):
        """
        Given: total_score=70 (경계값)
        When: _score_to_recommendation() 호출
        Then: "recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(70)

        # Assert
        assert recommendation == "recommended"

    def test_경계값_69점_neutral(self):
        """
        Given: total_score=69 (70 미만 경계값)
        When: _score_to_recommendation() 호출
        Then: "neutral"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(69)

        # Assert
        assert recommendation == "neutral"

    def test_경계값_40점_neutral(self):
        """
        Given: total_score=40 (경계값)
        When: _score_to_recommendation() 호출
        Then: "neutral"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(40)

        # Assert
        assert recommendation == "neutral"

    def test_경계값_39점_not_recommended(self):
        """
        Given: total_score=39 (40 미만 경계값)
        When: _score_to_recommendation() 호출
        Then: "not_recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(39)

        # Assert
        assert recommendation == "not_recommended"

    def test_점수_0_not_recommended(self):
        """
        Given: total_score=0 (최솟값)
        When: _score_to_recommendation() 호출
        Then: "not_recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(0)

        # Assert
        assert recommendation == "not_recommended"

    def test_점수_100_recommended(self):
        """
        Given: total_score=100 (최댓값)
        When: _score_to_recommendation() 호출
        Then: "recommended"
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        # Act
        recommendation, _ = service._score_to_recommendation(100)

        # Assert
        assert recommendation == "recommended"


class TestAnalyzeNewBidsForAllUsers:
    """analyze_new_bids_for_all_users 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_신규_공고_2건_사용자_3명_매칭_6건_생성(self):
        """
        Given: bid_ids 2개, 회사 보유 사용자 3명
        When: analyze_new_bids_for_all_users() 호출
        Then: 6개 매칭 결과 생성 (2 * 3)
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        bid_ids = [uuid4(), uuid4()]
        users = [_make_mock_user(company_id=str(uuid4())) for _ in range(3)]

        # 회사 보유 사용자 3명 반환
        service._get_users_with_company = AsyncMock(return_value=users)
        service.analyze_match = AsyncMock(return_value=MagicMock(total_score=75, is_notified=False))

        # Act
        count = await service.analyze_new_bids_for_all_users(bid_ids=bid_ids)

        # Assert
        assert count == 6
        assert service.analyze_match.call_count == 6

    @pytest.mark.asyncio
    async def test_회사_없는_사용자_제외(self):
        """
        Given: 사용자 5명 중 3명만 회사 있음
        When: analyze_new_bids_for_all_users() 호출
        Then: 3명 * 공고 수만 매칭 (회사 없는 2명 제외)
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        bid_ids = [uuid4()]
        users_with_company = [_make_mock_user(company_id=str(uuid4())) for _ in range(3)]

        # 회사 보유 사용자만 3명 반환 (서비스 내부에서 필터링)
        service._get_users_with_company = AsyncMock(return_value=users_with_company)
        service.analyze_match = AsyncMock(return_value=MagicMock(total_score=50, is_notified=False))

        # Act
        count = await service.analyze_new_bids_for_all_users(bid_ids=bid_ids)

        # Assert
        assert count == 3  # 3명 * 1건
        assert service.analyze_match.call_count == 3


class TestNotifyHighScoreMatches:
    """_notify_high_score_matches 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_70점_이상_매칭_2건_알림_발송(self):
        """
        Given: 매칭 결과 리스트 (70점 이상 2건)
        When: _notify_high_score_matches() 호출
        Then: NotificationService.send 2회 호출, is_notified=True
        """
        # Arrange
        mock_db = AsyncMock()
        service = BidMatchService(db=mock_db)

        matches = [
            MagicMock(user_id=str(uuid4()), bid_id=str(uuid4()), total_score=85, is_notified=False),
            MagicMock(user_id=str(uuid4()), bid_id=str(uuid4()), total_score=72, is_notified=False),
            MagicMock(user_id=str(uuid4()), bid_id=str(uuid4()), total_score=65, is_notified=False),  # 70점 미만
        ]

        mock_notification_service = AsyncMock()
        mock_notification_service.send_bid_match_notification = AsyncMock()
        service.notification_service = mock_notification_service

        # Act
        await service._notify_high_score_matches(matches)

        # Assert
        assert mock_notification_service.send_bid_match_notification.call_count == 2
        # 알림 발송된 매칭의 is_notified = True
        assert matches[0].is_notified is True
        assert matches[1].is_notified is True
        assert matches[2].is_notified is False  # 65점은 발송 안 됨
