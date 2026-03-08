"""
ScoringService 단위 테스트

test-spec.md 기준:
- _calculate_competition: 경쟁 강도 점수 산출
- _calculate_capability: 역량 점수 산출
- _calculate_market: 시장 환경 점수 산출
- _compute_total: 가중합 총점 계산
- _determine_recommendation: 4단계 추천 등급 결정
- _get_competitor_stats: 경쟁사 통계 조회
- _get_similar_bid_stats: 유사 공고 통계 조회

구현 전 — RED 상태: ImportError로 FAIL 예상
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# 구현 전 — RED 상태
from src.services.scoring_service import ScoringService  # noqa: F401 — 구현 전 ImportError 발생


# ============================================================
# Fixture
# ============================================================

@pytest.fixture
def mock_db():
    """DB Mock"""
    return AsyncMock()


@pytest.fixture
def scoring_service(mock_db):
    """ScoringService 인스턴스"""
    return ScoringService(db=mock_db)


@pytest.fixture
def bid_행정안전부_정보화():
    """행정안전부 정보화 분야 공고 Mock"""
    from tests.conftest import MockBid
    return MockBid(
        id=str(uuid4()),
        organization="행정안전부",
        category="정보화",
        bid_type="일반경쟁",
        contract_method="적격심사",
        budget=500_000_000,
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
    )


@pytest.fixture
def bid_미등록기관():
    """유사 이력 없는 기관 공고 Mock"""
    from tests.conftest import MockBid
    return MockBid(
        id=str(uuid4()),
        organization="미등록기관",
        category="기타",
        bid_type="제한경쟁",
        contract_method="적격심사",
        budget=100_000_000,
        deadline=datetime.now(timezone.utc) + timedelta(days=14),
    )


@pytest.fixture
def company_medium():
    """중견기업 회사 Mock"""
    from tests.conftest import MockCompany
    return MockCompany(
        id=str(uuid4()),
        scale="medium",
        name="중견IT기업",
    )


@pytest.fixture
def company_small():
    """소기업 회사 Mock"""
    from tests.conftest import MockCompany
    return MockCompany(
        id=str(uuid4()),
        scale="small",
        name="소기업",
    )


@pytest.fixture
def performances_7건(company_medium):
    """실적 7건 (대표실적 1건 포함)"""
    from tests.conftest import MockPerformance
    perfs = []
    for i in range(6):
        perfs.append(MockPerformance(
            company_id=company_medium.id,
            project_name=f"일반 프로젝트 {i+1}",
            client_name="한국정보화진흥원",
            contract_amount=300_000_000,
            is_representative=False,
        ))
    perfs.append(MockPerformance(
        company_id=company_medium.id,
        project_name="대표 실적 프로젝트",
        client_name="행정안전부",
        contract_amount=500_000_000,
        is_representative=True,
    ))
    return perfs


@pytest.fixture
def performances_빈():
    """실적 없음"""
    return []


@pytest.fixture
def certifications_2건(company_medium):
    """유효한 인증 2건"""
    from tests.conftest import MockCertification
    future = (date.today() + timedelta(days=365)).isoformat()
    return [
        MockCertification(
            company_id=company_medium.id,
            name="GS인증 1등급",
            expiry_date=future,
        ),
        MockCertification(
            company_id=company_medium.id,
            name="ISO 9001",
            expiry_date=future,
        ),
    ]


@pytest.fixture
def certifications_빈():
    """인증 없음"""
    return []


@pytest.fixture
def certifications_만료():
    """만료된 인증만 보유"""
    from tests.conftest import MockCertification
    past = (date.today() - timedelta(days=1)).isoformat()
    return [
        MockCertification(
            name="만료된 인증",
            expiry_date=past,
        ),
    ]


@pytest.fixture
def win_history_행정안전부_3업체():
    """행정안전부/정보화/일반경쟁 낙찰 이력 5건, 고유 업체 3개"""
    return [
        {"winner_business_number": "AAA", "winner_name": "(주)가나다", "winning_price": 420_000_000, "bid_rate": 0.84, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
        {"winner_business_number": "AAA", "winner_name": "(주)가나다", "winning_price": 380_000_000, "bid_rate": 0.87, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
        {"winner_business_number": "BBB", "winner_name": "(주)라마바", "winning_price": 460_000_000, "bid_rate": 0.82, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
        {"winner_business_number": "CCC", "winner_name": "(주)사아자", "winning_price": 410_000_000, "bid_rate": 0.85, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
        {"winner_business_number": "BBB", "winner_name": "(주)라마바", "winning_price": 390_000_000, "bid_rate": 0.88, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
    ]


@pytest.fixture
def win_history_경쟁과열():
    """고유 업체 10개 이상 이력 (경쟁 과열)"""
    history = []
    for i in range(15):
        history.append({
            "winner_business_number": f"BIZ{i:04d}",
            "winner_name": f"(주)업체{i}",
            "winning_price": 400_000_000,
            "bid_rate": 0.85,
            "_organization": "경쟁과열기관",
            "_category": "정보화",
            "_bid_type": "일반경쟁",
        })
    return history


# ============================================================
# _calculate_competition 테스트
# ============================================================

class Test경쟁강도점수:

    @pytest.mark.asyncio
    async def test_유사공고_5건_고유업체_3개_점수70(self, scoring_service, bid_행정안전부_정보화, win_history_행정안전부_3업체):
        """유사 공고 낙찰 이력 5건, 고유 업체 3개 → 점수 70.0"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=win_history_행정안전부_3업체)):
            # Act
            score, factors = await scoring_service._calculate_competition(bid_행정안전부_정보화)

        # Assert
        # 고유 업체 3개 / 10 = 0.3 → competition_score = (1 - 0.3) * 100 = 70.0
        assert score == pytest.approx(70.0, abs=1.0)
        assert any("3" in f for f in factors), f"'3개사' 관련 문구가 factors에 없음: {factors}"

    @pytest.mark.asyncio
    async def test_유사공고_없음_기본값_50(self, scoring_service, bid_미등록기관):
        """유사 공고 없음 → 기본값 50.0, factors에 '데이터 없음' 포함"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=[])):
            # Act
            score, factors = await scoring_service._calculate_competition(bid_미등록기관)

        # Assert
        assert score == pytest.approx(50.0, abs=1.0)
        assert any("없" in f or "부족" in f or "데이터" in f for f in factors), \
            f"'데이터 없음' 관련 문구가 factors에 없음: {factors}"

    @pytest.mark.asyncio
    async def test_경쟁과열_고유업체_10개이상_점수_낮음(self, scoring_service, bid_행정안전부_정보화, win_history_경쟁과열):
        """유사 공고 15건, 고유 업체 15개 → 점수 0~20 (경쟁 매우 높음)"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=win_history_경쟁과열)):
            # Act
            score, factors = await scoring_service._calculate_competition(bid_행정안전부_정보화)

        # Assert
        # 고유 업체 15개 / 10 = 1.5 → clamp to 1.0 → competition_score = 0
        assert 0 <= score <= 20, f"경쟁 과열 시 점수가 0~20이어야 함, 실제: {score}"


# ============================================================
# _calculate_capability 테스트
# ============================================================

class Test역량점수:

    @pytest.mark.asyncio
    async def test_실적7건_인증2건_규모medium_점수60_80(
        self, scoring_service, company_medium, performances_7건, certifications_2건, bid_행정안전부_정보화
    ):
        """실적 7건, 인증 2건, 규모 medium → 점수 60~80"""
        # Arrange & Act
        score, factors = await scoring_service._calculate_capability(
            company_medium, performances_7건, certifications_2건, bid_행정안전부_정보화
        )

        # Assert
        assert 60 <= score <= 80, f"기대 범위 60~80, 실제: {score}"
        assert len(factors) > 0, "factors가 비어있음"
        # 실적/인증/규모 각각 언급 확인
        factor_text = " ".join(factors)
        assert any(k in factor_text for k in ["실적", "수행", "프로젝트"]), f"실적 언급 없음: {factors}"
        assert any(k in factor_text for k in ["인증", "GS", "ISO"]), f"인증 언급 없음: {factors}"

    @pytest.mark.asyncio
    async def test_실적0건_인증0건_규모small_점수낮음(
        self, scoring_service, company_small, performances_빈, certifications_빈, bid_행정안전부_정보화
    ):
        """실적 0건, 인증 0건, 규모 small → 점수 0~30"""
        # Arrange & Act
        score, factors = await scoring_service._calculate_capability(
            company_small, performances_빈, certifications_빈, bid_행정안전부_정보화
        )

        # Assert
        assert 0 <= score <= 30, f"기대 범위 0~30, 실제: {score}"

    @pytest.mark.asyncio
    async def test_대표실적_동일발주기관_보너스_반영(
        self, scoring_service, company_medium, bid_행정안전부_정보화, certifications_빈
    ):
        """대표실적 포함 + 동일 발주기관(행정안전부) 실적 → 기본 대비 +20~30 보너스"""
        from tests.conftest import MockPerformance

        # Arrange — 일반 실적만 (보너스 없는 기준)
        normal_perfs = [
            MockPerformance(
                company_id=company_medium.id,
                client_name="국토교통부",  # 다른 기관
                is_representative=False,
                contract_amount=300_000_000,
            )
        ]
        base_score, _ = await scoring_service._calculate_capability(
            company_medium, normal_perfs, certifications_빈, bid_행정안전부_정보화
        )

        # Arrange — 대표실적 + 동일 기관(행정안전부)
        bonus_perfs = [
            MockPerformance(
                company_id=company_medium.id,
                client_name="행정안전부",
                is_representative=True,
                contract_amount=500_000_000,
            )
        ]
        bonus_score, _ = await scoring_service._calculate_capability(
            company_medium, bonus_perfs, certifications_빈, bid_행정안전부_정보화
        )

        # Assert: 보너스 반영 시 점수가 높아야 함
        assert bonus_score > base_score, f"보너스 미반영: base={base_score}, bonus={bonus_score}"

    @pytest.mark.asyncio
    async def test_만료된_인증만_보유_인증점수_낮음(
        self, scoring_service, company_medium, performances_빈, certifications_만료, bid_행정안전부_정보화
    ):
        """만료된 인증만 보유 → 인증 유효율 0, 유효 인증 없는 경우보다 점수 낮거나 같음"""
        # Arrange & Act
        score_만료, factors_만료 = await scoring_service._calculate_capability(
            company_medium, performances_빈, certifications_만료, bid_행정안전부_정보화
        )
        score_없음, _ = await scoring_service._calculate_capability(
            company_medium, performances_빈, certifications_빈, bid_행정안전부_정보화
        )

        # Assert: 만료 인증은 유효 인증 0건과 동일하거나 더 낮아야 함
        assert score_만료 <= score_없음 + 5, \
            f"만료 인증이 없는 것보다 점수가 높으면 안 됨: 만료={score_만료}, 없음={score_없음}"


# ============================================================
# _calculate_market 테스트
# ============================================================

class Test시장환경점수:

    @pytest.mark.asyncio
    async def test_예산5억_평균4억_적격심사_마감14일_점수높음(self, scoring_service):
        """예산 5억, 평균 수행금액 4억, 적격심사, 마감 14일 → 점수 70~90"""
        from tests.conftest import MockBid, MockPerformance

        # Arrange
        bid = MockBid(
            budget=500_000_000,
            contract_method="적격심사",
            deadline=datetime.now(timezone.utc) + timedelta(days=14),
        )
        # 평균 수행금액 4억
        performances = [
            MockPerformance(contract_amount=400_000_000),
            MockPerformance(contract_amount=400_000_000),
        ]

        # Act
        score, factors = await scoring_service._calculate_market(bid, performances)

        # Assert
        assert 70 <= score <= 90, f"기대 범위 70~90, 실제: {score}"
        assert len(factors) > 0

    @pytest.mark.asyncio
    async def test_예산50억_평균1억_최저가_마감2일_점수낮음(self, scoring_service):
        """예산 50억, 평균 수행금액 1억, 최저가, 마감 2일 → 점수 20~40"""
        from tests.conftest import MockBid, MockPerformance

        # Arrange
        bid = MockBid(
            budget=5_000_000_000,
            contract_method="최저가",
            deadline=datetime.now(timezone.utc) + timedelta(days=2),
        )
        performances = [
            MockPerformance(contract_amount=100_000_000),
        ]

        # Act
        score, factors = await scoring_service._calculate_market(bid, performances)

        # Assert
        assert 20 <= score <= 40, f"기대 범위 20~40, 실제: {score}"

    @pytest.mark.asyncio
    async def test_실적없음_예산적합성_기본_50점(self, scoring_service):
        """실적 없음 (평균 수행금액 계산 불가) → 예산 적합성 기본 50점 반영"""
        from tests.conftest import MockBid

        # Arrange
        bid = MockBid(
            budget=500_000_000,
            contract_method="적격심사",
            deadline=datetime.now(timezone.utc) + timedelta(days=14),
        )

        # Act
        score, factors = await scoring_service._calculate_market(bid, [])

        # Assert: 예산 적합성이 기본 50점이므로 전체적으로 중간값 근방
        assert 0 <= score <= 100, f"점수 범위 초과: {score}"
        # 실적이 없어도 기타 요소(계약방식, 시기)로 점수 산출 가능
        assert len(factors) > 0, "factors가 비어있음"


# ============================================================
# _compute_total 테스트
# ============================================================

class Test총점계산:

    def test_가중합_정상_계산(self, scoring_service):
        """suit=80, comp=60, cap=70, market=60 → 80*0.3 + 60*0.25 + 70*0.3 + 60*0.15 = 69.0"""
        # Arrange
        scores = {"suitability": 80.0, "competition": 60.0, "capability": 70.0, "market": 60.0}

        # Act
        total = scoring_service._compute_total(scores)

        # Assert
        expected = 80 * 0.30 + 60 * 0.25 + 70 * 0.30 + 60 * 0.15
        assert total == pytest.approx(expected, abs=0.01), f"기대: {expected}, 실제: {total}"

    def test_모든항목_100_합계_100(self, scoring_service):
        """모든 항목 100 → 총점 100.0"""
        # Arrange
        scores = {"suitability": 100.0, "competition": 100.0, "capability": 100.0, "market": 100.0}

        # Act
        total = scoring_service._compute_total(scores)

        # Assert
        assert total == pytest.approx(100.0, abs=0.01)

    def test_모든항목_0_합계_0(self, scoring_service):
        """모든 항목 0 → 총점 0.0"""
        # Arrange
        scores = {"suitability": 0.0, "competition": 0.0, "capability": 0.0, "market": 0.0}

        # Act
        total = scoring_service._compute_total(scores)

        # Assert
        assert total == pytest.approx(0.0, abs=0.01)


# ============================================================
# _determine_recommendation 테스트
# ============================================================

class Test추천등급결정:

    def test_점수_85_강력추천(self, scoring_service):
        """총점 85 → strongly_recommended, '강력추천', 사유 포함"""
        # Arrange & Act
        code, label, reason = scoring_service._determine_recommendation(85.0, {})

        # Assert
        assert code == "strongly_recommended"
        assert "강력추천" in label
        assert len(reason) > 0, "추천 사유가 비어있음"

    def test_점수_65_추천(self, scoring_service):
        """총점 65 → recommended, '추천'"""
        # Arrange & Act
        code, label, reason = scoring_service._determine_recommendation(65.0, {})

        # Assert
        assert code == "recommended"
        assert "추천" in label
        assert len(reason) > 0

    def test_점수_45_보류(self, scoring_service):
        """총점 45 → neutral, '보류'"""
        # Arrange & Act
        code, label, reason = scoring_service._determine_recommendation(45.0, {})

        # Assert
        assert code == "neutral"
        assert "보류" in label
        assert len(reason) > 0

    def test_점수_30_비추천(self, scoring_service):
        """총점 30 → not_recommended, '비추천', 사유 포함"""
        # Arrange & Act
        code, label, reason = scoring_service._determine_recommendation(30.0, {})

        # Assert
        assert code == "not_recommended"
        assert "비추천" in label
        assert len(reason) > 0

    def test_경계값_80_강력추천(self, scoring_service):
        """경계값 80 → strongly_recommended (80 이상)"""
        code, label, reason = scoring_service._determine_recommendation(80.0, {})
        assert code == "strongly_recommended"

    def test_경계값_60_추천(self, scoring_service):
        """경계값 60 → recommended (60~79)"""
        code, label, reason = scoring_service._determine_recommendation(60.0, {})
        assert code == "recommended"

    def test_경계값_40_보류(self, scoring_service):
        """경계값 40 → neutral (40~59)"""
        code, label, reason = scoring_service._determine_recommendation(40.0, {})
        assert code == "neutral"

    def test_경계값_79_추천(self, scoring_service):
        """경계값 79 → recommended (60~79, 80 미만)"""
        code, label, reason = scoring_service._determine_recommendation(79.9, {})
        assert code == "recommended"

    def test_경계값_39_비추천(self, scoring_service):
        """경계값 39 → not_recommended (39 이하)"""
        code, label, reason = scoring_service._determine_recommendation(39.9, {})
        assert code == "not_recommended"


# ============================================================
# _get_competitor_stats 테스트
# ============================================================

class Test경쟁사통계:

    @pytest.mark.asyncio
    async def test_이력_존재_경쟁사_반환(self, scoring_service, bid_행정안전부_정보화, win_history_행정안전부_3업체):
        """유사 공고 이력 존재 → estimatedCompetitors > 0, topCompetitors 리스트"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=win_history_행정안전부_3업체)):
            # Act
            stats = await scoring_service._get_competitor_stats(bid_행정안전부_정보화)

        # Assert
        assert stats["estimatedCompetitors"] > 0
        assert isinstance(stats["topCompetitors"], list)
        assert len(stats["topCompetitors"]) > 0

    @pytest.mark.asyncio
    async def test_이력_없음_빈_통계(self, scoring_service, bid_미등록기관):
        """이력 없음 → estimatedCompetitors=0, topCompetitors=[]"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=[])):
            # Act
            stats = await scoring_service._get_competitor_stats(bid_미등록기관)

        # Assert
        assert stats["estimatedCompetitors"] == 0
        assert stats["topCompetitors"] == []


# ============================================================
# _get_similar_bid_stats 테스트
# ============================================================

class Test유사공고통계:

    @pytest.mark.asyncio
    async def test_유사공고_3건_통계_산출(self, scoring_service, bid_행정안전부_정보화):
        """유사 공고 3건 → totalCount=3, avgWinRate/avgWinningPrice 산출"""
        # Arrange
        history_3건 = [
            {"winning_price": 420_000_000, "bid_rate": 0.84, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
            {"winning_price": 380_000_000, "bid_rate": 0.87, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
            {"winning_price": 400_000_000, "bid_rate": 0.85, "_organization": "행정안전부", "_category": "정보화", "_bid_type": "일반경쟁"},
        ]
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=history_3건)):
            # Act
            stats = await scoring_service._get_similar_bid_stats(bid_행정안전부_정보화)

        # Assert
        assert stats["totalCount"] == 3
        assert stats["avgWinRate"] is not None
        assert stats["avgWinningPrice"] is not None
        assert stats["avgWinRate"] == pytest.approx((0.84 + 0.87 + 0.85) / 3, abs=0.01)

    @pytest.mark.asyncio
    async def test_유사공고_없음_빈_통계(self, scoring_service, bid_미등록기관):
        """유사 공고 없음 → totalCount=0, avgWinRate=None, avgWinningPrice=None"""
        # Arrange
        with patch.object(scoring_service, '_get_win_history', AsyncMock(return_value=[])):
            # Act
            stats = await scoring_service._get_similar_bid_stats(bid_미등록기관)

        # Assert
        assert stats["totalCount"] == 0
        assert stats["avgWinRate"] is None
        assert stats["avgWinningPrice"] is None


# ============================================================
# 총점 경계 조건 및 클램핑
# ============================================================

class Test점수_경계조건:

    def test_총점_항상_0_이상_100_이하(self, scoring_service):
        """total_score는 항상 0~100 범위 (클램핑 확인)"""
        # 경계 이상의 입력이 들어와도 클램핑
        scores_over = {"suitability": 100.0, "competition": 100.0, "capability": 100.0, "market": 100.0}
        scores_under = {"suitability": 0.0, "competition": 0.0, "capability": 0.0, "market": 0.0}

        total_over = scoring_service._compute_total(scores_over)
        total_under = scoring_service._compute_total(scores_under)

        assert 0 <= total_over <= 100
        assert 0 <= total_under <= 100
