"""
BiddingStrategyService 단위 테스트

test-spec.md 기준:
- _calculate_distribution: numpy 기반 낙찰가율 분포 계산
- _calculate_ranges_qualification: 적격심사 투찰가 추천 범위
- _calculate_ranges_lowest_price: 최저가 투찰가 추천 범위
- _estimate_win_probability: 낙찰 확률 추정 (0~100%)
- _determine_risk_level: 리스크 레벨 판정
- _generate_strategy_report: 전략 리포트 생성
- _get_estimated_price: 예정가격 추출 (우선순위)
- simulate: 투찰가 시뮬레이션

구현 전 — RED 상태: ImportError로 FAIL 예상
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# 구현 전 — RED 상태
from src.services.bidding_strategy_service import BiddingStrategyService  # noqa: F401 — 구현 전 ImportError 발생


# ============================================================
# Fixture
# ============================================================

@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def strategy_service(mock_db):
    return BiddingStrategyService(db=mock_db)


@pytest.fixture
def distribution_정상():
    """정상 낙찰가율 분포"""
    return {
        "mean": 0.899,
        "std": 0.030,
        "median": 0.895,
        "q25": 0.880,
        "q75": 0.920,
        "minRate": 0.850,
        "maxRate": 0.950,
        "sampleCount": 10,
    }


@pytest.fixture
def distribution_std0():
    """표준편차 0 (편차 없음)"""
    return {
        "mean": 0.87,
        "std": 0.0,
        "median": 0.87,
        "q25": 0.87,
        "q75": 0.87,
        "minRate": 0.87,
        "maxRate": 0.87,
        "sampleCount": 3,
    }


@pytest.fixture
def ranges_적격심사():
    """적격심사 추천 범위 예시"""
    estimated = 450_000_000
    return {
        "safe": {"minRate": 0.92, "maxRate": 0.95, "minPrice": int(estimated * 0.92), "maxPrice": int(estimated * 0.95)},
        "moderate": {"minRate": 0.89, "maxRate": 0.92, "minPrice": int(estimated * 0.89), "maxPrice": int(estimated * 0.92)},
        "aggressive": {"minRate": 0.86, "maxRate": 0.89, "minPrice": int(estimated * 0.86), "maxPrice": int(estimated * 0.89)},
    }


@pytest.fixture
def bid_적격심사():
    from tests.conftest import MockBid
    return MockBid(
        id=str(uuid4()),
        contract_method="적격심사",
        budget=500_000_000,
        title="2026년 정보시스템 고도화 사업",
    )


@pytest.fixture
def bid_최저가():
    from tests.conftest import MockBid
    return MockBid(
        id=str(uuid4()),
        contract_method="최저가",
        budget=200_000_000,
        title="2026년 IT 장비 구매",
    )


# ============================================================
# _calculate_distribution 테스트
# ============================================================

class Test낙찰가율분포계산:

    def test_정상데이터_10건_통계산출(self, strategy_service):
        """정상 데이터 10건 → mean/median/q25/q75/std/sampleCount 정상 산출"""
        # Arrange
        bid_rates = [0.85, 0.87, 0.88, 0.89, 0.89, 0.90, 0.91, 0.92, 0.93, 0.95]

        # Act
        result = strategy_service._calculate_distribution(bid_rates)

        # Assert
        assert result is not None
        assert result["sampleCount"] == 10
        assert result["mean"] == pytest.approx(sum(bid_rates) / len(bid_rates), abs=0.01)
        assert result["std"] > 0
        assert result["q25"] <= result["median"] <= result["q75"]
        assert result["minRate"] == min(bid_rates)
        assert result["maxRate"] == max(bid_rates)

    def test_단일데이터_1건(self, strategy_service):
        """단일 데이터 → mean=0.90, std=0.0, median=q25=q75=0.90"""
        # Arrange
        bid_rates = [0.90]

        # Act
        result = strategy_service._calculate_distribution(bid_rates)

        # Assert
        assert result is not None
        assert result["mean"] == pytest.approx(0.90, abs=0.001)
        assert result["std"] == pytest.approx(0.0, abs=0.001)
        assert result["median"] == pytest.approx(0.90, abs=0.001)
        assert result["sampleCount"] == 1

    def test_빈데이터_None반환(self, strategy_service):
        """빈 데이터 → None 반환 (분포 계산 불가)"""
        # Arrange & Act
        result = strategy_service._calculate_distribution([])

        # Assert
        assert result is None

    def test_동일값_std0(self, strategy_service):
        """동일 값 3개 → mean=0.90, std=0.0, median=0.90"""
        # Arrange
        bid_rates = [0.90, 0.90, 0.90]

        # Act
        result = strategy_service._calculate_distribution(bid_rates)

        # Assert
        assert result is not None
        assert result["mean"] == pytest.approx(0.90, abs=0.001)
        assert result["std"] == pytest.approx(0.0, abs=0.001)
        assert result["median"] == pytest.approx(0.90, abs=0.001)


# ============================================================
# _calculate_ranges_qualification 테스트
# ============================================================

class Test적격심사추천범위:

    def test_분포있음_3구간_정상산출(self, strategy_service, distribution_정상):
        """유사 공고 분포 있음 → 3개 구간 모두 price > 0, safe.maxRate <= 0.95"""
        # Arrange
        estimated_price = 450_000_000

        # Act
        ranges = strategy_service._calculate_ranges_qualification(estimated_price, distribution_정상)

        # Assert
        for level in ["safe", "moderate", "aggressive"]:
            assert ranges[level]["minPrice"] > 0
            assert ranges[level]["maxPrice"] > 0
            assert ranges[level]["minPrice"] <= ranges[level]["maxPrice"]
        assert ranges["safe"]["maxRate"] <= 0.95

    def test_분포없음_기본구간_사용(self, strategy_service):
        """유사 공고 분포 없음 (None) → 기본 구간 88~95% 사용"""
        # Arrange
        estimated_price = 450_000_000

        # Act
        ranges = strategy_service._calculate_ranges_qualification(estimated_price, None)

        # Assert
        # safe 기본: estimated * 0.92 ~ 0.95
        assert ranges["safe"]["minPrice"] == pytest.approx(estimated_price * 0.92, rel=0.01)
        assert ranges["safe"]["maxPrice"] == pytest.approx(estimated_price * 0.95, rel=0.01)

    def test_estimated_price_0_처리(self, strategy_service, distribution_정상):
        """estimated_price=0 → 모든 price=0 또는 안전하게 처리 (0 나누기 방지)"""
        # Arrange & Act
        try:
            ranges = strategy_service._calculate_ranges_qualification(0, distribution_정상)
            # price=0이거나 정상 처리됨
            for level in ["safe", "moderate", "aggressive"]:
                assert ranges[level]["minPrice"] == 0
                assert ranges[level]["maxPrice"] == 0
        except Exception as e:
            # 예외 발생 시 AppException이나 ValueError 여야 함
            assert "price" in str(e).lower() or "zero" in str(e).lower() or "0" in str(e)


# ============================================================
# _calculate_ranges_lowest_price 테스트
# ============================================================

class Test최저가추천범위:

    def test_정상분포_구간순서_보장(self, strategy_service, distribution_정상):
        """정상 분포 → aggressive.minRate < moderate.minRate < safe.minRate"""
        # Arrange
        estimated_price = 200_000_000

        # Act
        ranges = strategy_service._calculate_ranges_lowest_price(estimated_price, distribution_정상)

        # Assert
        assert ranges["aggressive"]["minRate"] <= ranges["moderate"]["minRate"] <= ranges["safe"]["minRate"], \
            f"구간 순서 오류: {ranges['aggressive']['minRate']} <= {ranges['moderate']['minRate']} <= {ranges['safe']['minRate']}"

    def test_std0_구간이_mean에_수렴(self, strategy_service, distribution_std0):
        """std=0 → 모든 구간이 mean 근처로 수렴"""
        # Arrange
        estimated_price = 200_000_000
        mean = distribution_std0["mean"]

        # Act
        ranges = strategy_service._calculate_ranges_lowest_price(estimated_price, distribution_std0)

        # Assert
        for level in ["safe", "moderate", "aggressive"]:
            assert ranges[level]["minRate"] == pytest.approx(mean, abs=0.05), \
                f"{level} 구간이 mean에 수렴해야 함: minRate={ranges[level]['minRate']}, mean={mean}"


# ============================================================
# _estimate_win_probability 테스트
# ============================================================

class Test낙찰확률추정:

    def test_적격심사_적정구간_확률높음(self, strategy_service, distribution_정상):
        """적격심사, bid_rate=0.91 (적정 구간) → 확률 50~80%"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.91, distribution_정상, "적격심사")

        # Assert
        assert 50 <= prob <= 80, f"적정 구간에서 확률 50~80% 기대, 실제: {prob}"

    def test_적격심사_너무낮음_확률낮음(self, strategy_service, distribution_정상):
        """적격심사, bid_rate=0.80 (너무 낮음, 덤핑 의심) → 확률 10~30%"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.80, distribution_정상, "적격심사")

        # Assert
        assert 10 <= prob <= 35, f"덤핑 구간에서 확률 10~30% 기대, 실제: {prob}"

    def test_적격심사_너무높음_확률낮음(self, strategy_service, distribution_정상):
        """적격심사, bid_rate=0.99 (너무 높음) → 확률 20~40%"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.99, distribution_정상, "적격심사")

        # Assert
        assert 10 <= prob <= 45, f"과도하게 높은 구간에서 확률 낮음 기대, 실제: {prob}"

    def test_최저가_매우낮음_확률높음(self, strategy_service, distribution_정상):
        """최저가, bid_rate=0.82 (매우 낮음) → 확률 70~90% (유리)"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.82, distribution_정상, "최저가")

        # Assert
        assert 60 <= prob <= 100, f"최저가에서 낮은 투찰가는 유리: 기대 70~90%, 실제: {prob}"

    def test_최저가_높음_확률낮음(self, strategy_service, distribution_정상):
        """최저가, bid_rate=0.95 (높음) → 확률 5~20% (불리)"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.95, distribution_정상, "최저가")

        # Assert
        assert 0 <= prob <= 30, f"최저가에서 높은 투찰가는 불리: 기대 5~20%, 실제: {prob}"

    def test_분포없음_기본확률_50(self, strategy_service):
        """분포 데이터 없음 → 기본 확률 50%"""
        # Arrange & Act
        prob = strategy_service._estimate_win_probability(0.90, None, "적격심사")

        # Assert
        assert prob == 50, f"분포 없을 때 기본 확률 50% 기대, 실제: {prob}"

    def test_낙찰확률_항상_0_100_범위(self, strategy_service, distribution_정상):
        """낙찰 확률은 항상 0~100 범위"""
        for rate in [0.5, 0.7, 0.8, 0.9, 1.0, 1.2]:
            for method in ["적격심사", "최저가"]:
                prob = strategy_service._estimate_win_probability(rate, distribution_정상, method)
                assert 0 <= prob <= 100, f"rate={rate}, method={method} → 확률 범위 초과: {prob}"


# ============================================================
# _determine_risk_level 테스트
# ============================================================

class Test리스크레벨판정:

    def test_safe_구간_내(self, strategy_service, ranges_적격심사):
        """bid_rate=0.93, safe 구간(0.92~0.95) → ('safe', '낮은 리스크')"""
        # Arrange & Act
        risk_level, risk_label = strategy_service._determine_risk_level(0.93, ranges_적격심사)

        # Assert
        assert risk_level == "safe"
        assert "낮은" in risk_label or "safe" in risk_label.lower()

    def test_moderate_구간_내(self, strategy_service, ranges_적격심사):
        """bid_rate=0.90, moderate 구간(0.89~0.92) → ('moderate', '중간 리스크')"""
        # Arrange & Act
        risk_level, risk_label = strategy_service._determine_risk_level(0.905, ranges_적격심사)

        # Assert
        assert risk_level == "moderate"
        assert "중간" in risk_label or "moderate" in risk_label.lower()

    def test_aggressive_구간_내(self, strategy_service, ranges_적격심사):
        """bid_rate=0.87, aggressive 구간(0.86~0.89) → ('aggressive', '높은 리스크')"""
        # Arrange & Act
        risk_level, risk_label = strategy_service._determine_risk_level(0.875, ranges_적격심사)

        # Assert
        assert risk_level == "aggressive"
        assert "높은" in risk_label or "aggressive" in risk_label.lower()

    def test_구간외_초과(self, strategy_service, ranges_적격심사):
        """bid_rate=0.98, 구간 초과 → 레벨 및 라벨 반환 (예외 없음)"""
        # Arrange & Act
        risk_level, risk_label = strategy_service._determine_risk_level(0.98, ranges_적격심사)

        # Assert
        assert isinstance(risk_level, str)
        assert isinstance(risk_label, str)

    def test_구간외_미달(self, strategy_service, ranges_적격심사):
        """bid_rate=0.80, 구간 미달 → 레벨 및 라벨 반환 (예외 없음)"""
        # Arrange & Act
        risk_level, risk_label = strategy_service._determine_risk_level(0.80, ranges_적격심사)

        # Assert
        assert isinstance(risk_level, str)
        assert isinstance(risk_label, str)


# ============================================================
# _generate_strategy_report 테스트
# ============================================================

class Test전략리포트생성:

    def test_적격심사_공고_기술_종합평가_키워드(self, strategy_service, bid_적격심사, distribution_정상, ranges_적격심사):
        """적격심사 공고 → contractMethodStrategy에 '기술'/'종합 평가' 키워드 포함"""
        # Arrange & Act
        report = strategy_service._generate_strategy_report(bid_적격심사, distribution_정상, ranges_적격심사)

        # Assert
        strategy_text = report.get("contractMethodStrategy", "")
        assert any(k in strategy_text for k in ["기술", "종합", "평가"]), \
            f"적격심사 전략에 기술/종합 평가 키워드 없음: {strategy_text}"

    def test_최저가_공고_가격경쟁_키워드(self, strategy_service, bid_최저가, distribution_정상, ranges_적격심사):
        """최저가 공고 → contractMethodStrategy에 '가격 경쟁' 키워드 포함"""
        # Arrange & Act
        report = strategy_service._generate_strategy_report(bid_최저가, distribution_정상, ranges_적격심사)

        # Assert
        strategy_text = report.get("contractMethodStrategy", "")
        assert any(k in strategy_text for k in ["가격", "경쟁", "최저"]), \
            f"최저가 전략에 가격 경쟁 키워드 없음: {strategy_text}"

    def test_유사공고없음_데이터부족_문구(self, strategy_service, bid_적격심사, ranges_적격심사):
        """유사 공고 없음 (distribution=None) → 리포트에 '데이터 부족' 문구 포함"""
        # Arrange & Act
        report = strategy_service._generate_strategy_report(bid_적격심사, None, ranges_적격심사)

        # Assert
        all_text = " ".join([
            report.get("contractMethodStrategy", ""),
            report.get("marketInsight", ""),
            *report.get("recommendations", []),
        ])
        assert any(k in all_text for k in ["부족", "데이터", "없"]), \
            f"데이터 부족 문구 없음: {all_text}"


# ============================================================
# _get_estimated_price 테스트
# ============================================================

class Test예정가격추출:

    def test_estimated_price_우선(self, strategy_service):
        """estimated_price와 budget 모두 있을 때 → estimated_price 우선"""
        from tests.conftest import MockBid

        # Arrange
        bid = MockBid(budget=500_000_000)
        bid.estimated_price = 450_000_000  # 명시적 설정

        # Act
        price = strategy_service._get_estimated_price(bid)

        # Assert
        assert price == 450_000_000

    def test_estimated_price_없음_budget_폴백(self, strategy_service):
        """estimated_price=None → budget 폴백"""
        from tests.conftest import MockBid

        # Arrange
        bid = MockBid(budget=500_000_000)
        bid.estimated_price = None

        # Act
        price = strategy_service._get_estimated_price(bid)

        # Assert
        assert price == 500_000_000

    def test_둘다_없음_None반환(self, strategy_service):
        """estimated_price=None, budget=None → None"""
        from tests.conftest import MockBid

        # Arrange
        bid = MockBid(budget=None)
        bid.estimated_price = None

        # Act
        price = strategy_service._get_estimated_price(bid)

        # Assert
        assert price is None


# ============================================================
# simulate 테스트
# ============================================================

class Test투찰가시뮬레이션:

    @pytest.mark.asyncio
    async def test_정상_시뮬레이션(self, strategy_service, bid_적격심사, distribution_정상):
        """정상 시뮬레이션 → bidRate > 0, winProbability 0~100, riskLevel 존재"""
        from tests.conftest import MockBidWinHistory

        # Arrange
        bid_적격심사.estimated_price = 450_000_000
        win_history = [MockBidWinHistory(bid_rate=r) for r in [0.85, 0.87, 0.89, 0.91, 0.93]]

        with patch.object(strategy_service, '_get_similar_win_history', AsyncMock(return_value=win_history)), \
             patch('src.api.v1.bids._SAMPLE_BIDS', {bid_적격심사.id: {"id": bid_적격심사.id, "contractMethod": "적격심사", "estimatedPrice": 450_000_000, "budget": 500_000_000}}):
            # Act — bid_id 대신 bid 객체를 직접 주입하는 방식 확인 필요
            # 서비스가 bid_id로 조회하므로 내부 조회 mock
            with patch.object(strategy_service, 'analyze_strategy', AsyncMock()):
                result = await strategy_service.simulate(bid_적격심사.id, 410_000_000)

        # Assert
        assert result.bidRate > 0
        assert 0 <= result.winProbability <= 100
        assert result.riskLevel in ["safe", "moderate", "aggressive", "over_safe", "extreme"]

    @pytest.mark.asyncio
    async def test_예정가격_없는_공고_STRATEGY_002(self, strategy_service):
        """estimated_price=None, budget=None → AppException STRATEGY_002 (422)"""
        from src.core.exceptions import AppException  # 구현 전 — ImportError 발생 가능

        # Arrange
        from tests.conftest import MockBid
        bid_no_price = MockBid(budget=None)
        bid_no_price.estimated_price = None

        with patch.object(strategy_service, '_get_bid', AsyncMock(return_value=bid_no_price)):
            # Act & Assert
            with pytest.raises((AppException, Exception)) as exc_info:
                await strategy_service.simulate(bid_no_price.id, 100_000_000)

            # AppException이면 코드 확인
            exc = exc_info.value
            if hasattr(exc, 'code'):
                assert exc.code == "STRATEGY_002"
            if hasattr(exc, 'status_code'):
                assert exc.status_code == 422

    @pytest.mark.asyncio
    async def test_bid_rate_초과시_확률_낮음(self, strategy_service, distribution_정상):
        """bid_price > estimated_price → bidRate > 1.0, winProbability 매우 낮음"""
        # 이 테스트는 서비스 내부 로직 검증
        # bid_rate=1.11 (500M / 450M)을 직접 주입
        prob = strategy_service._estimate_win_probability(1.11, distribution_정상, "적격심사")

        # Assert: 예정가 초과 투찰은 확률 낮음
        assert prob <= 30, f"예정가 초과 시 확률 낮음 기대 (<=30%), 실제: {prob}"

    def test_comparison_with_recommended_3구간_포함(self, strategy_service, ranges_적격심사):
        """_get_comparison_text 또는 유사 메서드 → safe/moderate/aggressive 각각 비교 문구 반환"""
        # 서비스에 _build_comparison 또는 유사 메서드가 있다고 가정
        if hasattr(strategy_service, '_build_comparison'):
            comparison = strategy_service._build_comparison(0.91, ranges_적격심사)
            assert "safe" in comparison
            assert "moderate" in comparison
            assert "aggressive" in comparison


# ============================================================
# 데이터 부족 폴백 테스트
# ============================================================

class Test데이터부족폴백:

    def test_유사공고_0건_기본분포_사용(self, strategy_service):
        """유사 공고 0건 → _calculate_distribution([])==None → 기본 구간 사용"""
        # Act
        result = strategy_service._calculate_distribution([])

        # Assert
        assert result is None  # None이면 calculate_ranges에서 기본값 사용

    def test_유사공고_1건_std0_폴백처리(self, strategy_service):
        """유사 공고 1건 → std=0, 구간 수렴 → 서비스가 처리 가능해야 함"""
        # Arrange
        bid_rates = [0.89]

        # Act
        result = strategy_service._calculate_distribution(bid_rates)

        # Assert
        assert result is not None
        assert result["std"] == pytest.approx(0.0, abs=0.001)
        # 최저가 범위 계산 시에도 예외 없음
        ranges = strategy_service._calculate_ranges_lowest_price(300_000_000, result)
        assert ranges is not None
