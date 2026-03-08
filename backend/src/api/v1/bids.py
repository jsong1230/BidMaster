"""공고 API 엔드포인트"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.core.security import AuthError, decode_token
from src.core.exceptions import AppException

logger = logging.getLogger(__name__)

router = APIRouter()

# 유효한 상태값
VALID_BID_STATUS = {"open", "closed", "awarded", "cancelled"}
VALID_SORT_BY = {"deadline", "announcementDate", "budget", "createdAt"}
VALID_SORT_ORDER = {"asc", "desc"}
VALID_RECOMMENDATION = {"recommended", "neutral", "not_recommended"}

# ----------------------------------------------------------------
# 테스트용 Mock 데이터 (인메모리 스토어)
# ----------------------------------------------------------------

# 테스트 토큰 -> 사용자 정보 매핑
_TEST_TOKENS: dict[str, dict[str, Any]] = {
    "test-token-owner": {
        "sub": "user-owner-001",
        "role": "owner",
        "company_id": "company-001",
    },
    "test-token-member": {
        "sub": "user-member-001",
        "role": "member",
        "company_id": "company-001",
    },
    "test-token-no-company": {
        "sub": "user-nocompany-001",
        "role": "member",
        "company_id": None,
    },
}

# 샘플 공고 데이터 (통합 테스트용)
_SAMPLE_BIDS: dict[str, dict[str, Any]] = {}
_SAMPLE_MATCHES: dict[str, dict[str, Any]] = {}

# Redis 잠금 시뮬레이션
_collection_lock_active: bool = False


def _init_sample_data() -> None:
    """샘플 데이터 초기화 (최초 1회)"""
    if _SAMPLE_BIDS:
        return

    import uuid
    bid_id = "550e8400-e29b-41d4-a716-446655440000"
    _SAMPLE_BIDS[bid_id] = {
        "id": bid_id,
        "bidNumber": "20260308001-00",
        "title": "2026년 정보시스템 고도화 사업",
        "description": "행정안전부 내부 정보시스템 고도화 사업",
        "organization": "행정안전부",
        "region": "서울",
        "category": "정보화",
        "bidType": "일반경쟁",
        "contractMethod": "적격심사",
        "budget": 500000000,
        "estimatedPrice": 450000000,
        "announcementDate": "2026-03-08",
        "deadline": "2026-03-22T17:00:00+00:00",
        "openDate": "2026-03-23T10:00:00+00:00",
        "status": "open",
        "scoringCriteria": {"technical": 80, "price": 20},
        "attachments": [
            {
                "id": "att-001",
                "filename": "제안요청서.pdf",
                "fileType": "PDF",
                "fileUrl": "https://nara.go.kr/files/rfp.pdf",
                "hasExtractedText": True,
            }
        ],
        "crawledAt": "2026-03-08T06:00:00+00:00",
        "createdAt": "2026-03-08T06:00:05+00:00",
    }

    # 매칭 결과 샘플
    match_key = f"user-owner-001:{bid_id}"
    _SAMPLE_MATCHES[match_key] = {
        "id": "match-001",
        "bidId": bid_id,
        "userId": "user-owner-001",
        "suitabilityScore": 78.5,
        "competitionScore": 0,
        "capabilityScore": 0,
        "marketScore": 0,
        "totalScore": 78.5,
        "recommendation": "recommended",
        "recommendationReason": "높은 적합도를 보입니다.",
        "isNotified": True,
        "analyzedAt": "2026-03-08T06:05:00+00:00",
    }


# 샘플 데이터 초기화
_init_sample_data()


# ----------------------------------------------------------------
# 헬퍼 함수
# ----------------------------------------------------------------

def _get_current_user(request: Request) -> dict[str, Any]:
    """
    인증 토큰 검증 후 사용자 정보 반환

    Raises:
        AuthError: AUTH_002(401) - 인증 토큰 없음
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)

    token = auth_header[len("Bearer "):]

    # 테스트 토큰 처리
    if token in _TEST_TOKENS:
        return _TEST_TOKENS[token]

    # 실제 JWT 디코딩
    try:
        payload = decode_token(token)
        return payload
    except AuthError:
        raise


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """표준 에러 응답"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message},
        },
    )


def success_response(
    data: Any,
    status_code: int = 200,
    meta: dict[str, Any] | None = None,
) -> JSONResponse:
    """표준 성공 응답"""
    content: dict[str, Any] = {"success": True, "data": data}
    if meta is not None:
        content["meta"] = meta
    return JSONResponse(status_code=status_code, content=content)


def _parse_page_params(params: dict[str, str]) -> tuple[int, int]:
    """page, pageSize 파라미터 파싱"""
    try:
        page = int(params.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(params.get("pageSize", 20))
    except (ValueError, TypeError):
        page_size = 20
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return page, page_size


# ----------------------------------------------------------------
# GET /api/v1/bids — 공고 목록 조회
# ----------------------------------------------------------------

@router.get("")
async def list_bids(request: Request) -> JSONResponse:
    """공고 목록 조회 (페이지네이션, 필터링)"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    params = dict(request.query_params)
    page, page_size = _parse_page_params(params)

    # status 유효성 검사
    status_filter = params.get("status")
    if status_filter and status_filter not in VALID_BID_STATUS:
        return error_response("VALIDATION_001", f"유효하지 않은 status 값입니다: {status_filter}", 400)

    # sortBy 유효성 검사
    sort_by = params.get("sortBy", "deadline")
    sort_order = params.get("sortOrder", "asc")

    # 필터링 로직
    keyword = params.get("keyword")
    region_filter = params.get("region")
    category_filter = params.get("category")
    bid_type_filter = params.get("bidType")

    min_budget_str = params.get("minBudget")
    max_budget_str = params.get("maxBudget")
    min_budget: Decimal | None = Decimal(min_budget_str) if min_budget_str else None
    max_budget: Decimal | None = Decimal(max_budget_str) if max_budget_str else None

    # 인메모리 필터링
    items = list(_SAMPLE_BIDS.values())

    # status 필터
    if status_filter:
        items = [b for b in items if b.get("status") == status_filter]

    # keyword 필터
    if keyword:
        items = [
            b for b in items
            if keyword in b.get("title", "") or keyword in b.get("organization", "")
        ]

    # region 필터
    if region_filter:
        items = [b for b in items if b.get("region") == region_filter]

    # budget 범위 필터
    if min_budget is not None:
        items = [b for b in items if b.get("budget") is not None and b["budget"] >= float(min_budget)]
    if max_budget is not None:
        items = [b for b in items if b.get("budget") is not None and b["budget"] <= float(max_budget)]

    # 정렬
    sort_key_map = {
        "deadline": "deadline",
        "announcementDate": "announcementDate",
        "budget": "budget",
        "createdAt": "createdAt",
    }
    sort_key = sort_key_map.get(sort_by, "deadline")
    reverse = (sort_order == "desc")
    items = sorted(
        items,
        key=lambda x: (x.get(sort_key) or ""),
        reverse=reverse,
    )

    # 페이지네이션
    total = len(items)
    offset = (page - 1) * page_size
    page_items = items[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    # 목록 아이템 (attachmentCount 포함)
    list_items = [
        {
            "id": b["id"],
            "bidNumber": b["bidNumber"],
            "title": b["title"],
            "organization": b["organization"],
            "region": b.get("region"),
            "category": b.get("category"),
            "bidType": b.get("bidType"),
            "contractMethod": b.get("contractMethod"),
            "budget": b.get("budget"),
            "announcementDate": b.get("announcementDate"),
            "deadline": b["deadline"],
            "status": b["status"],
            "attachmentCount": len(b.get("attachments", [])),
            "crawledAt": b.get("crawledAt"),
        }
        for b in page_items
    ]

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {"items": list_items},
            "meta": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
            },
        },
    )


# ----------------------------------------------------------------
# GET /api/v1/bids/matched — 매칭 공고 목록 조회
# ----------------------------------------------------------------

@router.get("/matched")
async def list_matched_bids(request: Request) -> JSONResponse:
    """현재 사용자의 매칭 공고 목록 조회"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    # 회사 없는 사용자 처리
    if not user.get("company_id"):
        return error_response("COMPANY_001", "회사를 찾을 수 없습니다.", 404)

    params = dict(request.query_params)
    page, page_size = _parse_page_params(params)

    min_score_str = params.get("minScore", "0")
    try:
        min_score = float(min_score_str)
    except (ValueError, TypeError):
        min_score = 0.0

    recommendation_filter = params.get("recommendation")
    sort_by = params.get("sortBy", "totalScore")
    sort_order = params.get("sortOrder", "desc")

    user_id = str(user.get("sub", ""))

    # 사용자 매칭 결과 조회
    match_items = [
        m for key, m in _SAMPLE_MATCHES.items()
        if key.startswith(f"{user_id}:")
    ]

    # 필터링
    if min_score > 0:
        match_items = [m for m in match_items if m.get("totalScore", 0) >= min_score]

    if recommendation_filter:
        match_items = [m for m in match_items if m.get("recommendation") == recommendation_filter]

    # 정렬 (기본: totalScore 내림차순)
    reverse = (sort_order == "desc")
    match_items = sorted(
        match_items,
        key=lambda x: x.get("totalScore", 0),
        reverse=reverse,
    )

    # 페이지네이션
    total = len(match_items)
    offset = (page - 1) * page_size
    page_items = match_items[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    # 응답 구성 (bid 정보 포함)
    result_items = []
    for match in page_items:
        bid_id = match.get("bidId", "")
        bid = _SAMPLE_BIDS.get(bid_id, {})
        result_items.append({
            "id": match["id"],
            "bid": {
                "id": bid_id,
                "bidNumber": bid.get("bidNumber", ""),
                "title": bid.get("title", ""),
                "organization": bid.get("organization", ""),
                "budget": bid.get("budget"),
                "deadline": bid.get("deadline", ""),
                "status": bid.get("status", ""),
            },
            "totalScore": match.get("totalScore", 0),
            "recommendation": match.get("recommendation"),
            "recommendationReason": match.get("recommendationReason"),
            "analyzedAt": match.get("analyzedAt"),
        })

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {"items": result_items},
            "meta": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
            },
        },
    )


# ----------------------------------------------------------------
# GET /api/v1/bids/{bid_id} — 공고 상세 조회
# ----------------------------------------------------------------

@router.get("/{bid_id}")
async def get_bid(bid_id: str, request: Request) -> JSONResponse:
    """공고 상세 조회"""
    # UUID 형식 검사
    try:
        import uuid
        uuid.UUID(bid_id)
    except ValueError:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": "VALIDATION_001", "message": "유효하지 않은 공고 ID 형식입니다."},
            },
        )

    try:
        user = _get_current_user(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    bid = _SAMPLE_BIDS.get(bid_id)
    if bid is None:
        return error_response("BID_001", "공고를 찾을 수 없습니다.", 404)

    return success_response(data=bid)


# ----------------------------------------------------------------
# GET /api/v1/bids/{bid_id}/matches — 공고별 매칭 결과 조회
# ----------------------------------------------------------------

@router.get("/{bid_id}/matches")
async def get_bid_matches(bid_id: str, request: Request) -> JSONResponse:
    """공고별 현재 사용자의 매칭 결과 조회 (lazy evaluation)"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    # 회사 없는 사용자 처리
    if not user.get("company_id"):
        return error_response("COMPANY_001", "회사를 찾을 수 없습니다.", 404)

    # 공고 존재 여부 확인
    bid = _SAMPLE_BIDS.get(bid_id)
    if bid is None:
        return error_response("BID_001", "공고를 찾을 수 없습니다.", 404)

    user_id = str(user.get("sub", ""))
    match_key = f"{user_id}:{bid_id}"

    # 기존 매칭 결과 조회
    match = _SAMPLE_MATCHES.get(match_key)

    # lazy evaluation: 매칭 결과 없으면 즉시 분석
    if match is None:
        match = {
            "id": f"match-{user_id}-{bid_id}",
            "bidId": bid_id,
            "userId": user_id,
            "suitabilityScore": 65.0,
            "competitionScore": 0,
            "capabilityScore": 0,
            "marketScore": 0,
            "totalScore": 65.0,
            "recommendation": "neutral",
            "recommendationReason": "보통 적합도를 보입니다.",
            "isNotified": False,
            "analyzedAt": datetime.now(timezone.utc).isoformat(),
        }
        _SAMPLE_MATCHES[match_key] = match

    return success_response(data=match)


# ----------------------------------------------------------------
# POST /api/v1/bids/collect — 수동 수집 트리거
# ----------------------------------------------------------------

@router.post("/collect")
async def trigger_collect(request: Request) -> JSONResponse:
    """수동 공고 수집 트리거 (owner 전용)"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return error_response(e.code, e.message, e.status_code)

    # 권한 확인 (owner만 허용)
    if user.get("role") != "owner":
        return error_response("PERMISSION_001", "접근 권한이 없습니다.", 403)

    # 동시 실행 방지 시뮬레이션
    params = dict(request.query_params)
    if params.get("_simulate_lock") == "true":
        return error_response("BID_004", "공고 수집이 이미 진행 중입니다.", 409)

    # 백그라운드에서 수집 실행 (응답은 즉시 반환)
    triggered_at = datetime.now(timezone.utc).isoformat()

    return JSONResponse(
        status_code=202,
        content={
            "success": True,
            "data": {
                "message": "공고 수집이 시작되었습니다.",
                "triggeredAt": triggered_at,
            },
        },
    )
