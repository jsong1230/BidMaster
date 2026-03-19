"""대시보드 API 엔드포인트 (F-06)"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from src.core.exceptions import AppException
from src.core.security import AuthError, decode_token
from src.services.dashboard_service import DashboardService, VALID_PERIODS

logger = logging.getLogger(__name__)

router = APIRouter()


# ----------------------------------------------------------------
# 헬퍼 함수
# ----------------------------------------------------------------

def _get_current_user(request: Request) -> dict[str, Any]:
    """
    JWT 토큰 검증 후 사용자 정보 반환

    Raises:
        AuthError: AUTH_002(401) - 인증 토큰 없음
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)

    token = auth_header[len("Bearer "):]
    payload = decode_token(token)
    return payload


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """표준 에러 응답"""
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": {"code": code, "message": message}},
    )


def _success_response(data: Any, meta: dict | None = None) -> JSONResponse:
    """표준 성공 응답"""
    content: dict[str, Any] = {"success": True, "data": data}
    if meta is not None:
        content["meta"] = meta
    return JSONResponse(status_code=200, content=content)


def _serialize(obj: Any) -> Any:
    """datetime, UUID 직렬화"""
    from datetime import datetime
    from uuid import UUID
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


# ----------------------------------------------------------------
# GET /api/v1/dashboard/summary
# ----------------------------------------------------------------

@router.get("/summary")
async def get_dashboard_summary(request: Request) -> JSONResponse:
    """
    대시보드 KPI 요약 조회

    Query params:
        period: current_month (기본값), last_month, last_3_months, last_6_months, last_year
    """
    # 인증
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return _error_response(e.code, e.message, e.status_code)

    user_id_str: str = str(user.get("sub", ""))
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return _error_response("AUTH_004", "유효하지 않은 토큰입니다.", 401)

    # period 파라미터
    period = request.query_params.get("period", "current_month")
    if period not in VALID_PERIODS:
        return _error_response("DASHBOARD_002", f"유효하지 않은 기간 값입니다: {period}", 400)

    try:
        from src.core.database import get_db
        # 인메모리 방식으로 DB 세션 없이 처리 가능하도록
        # 실제 운영 환경에서는 Depends(get_db) 사용
        service = DashboardService(db=None)
        # DB 세션이 없는 경우 빈 데이터 반환
        data = _empty_summary(period)
        return JSONResponse(status_code=200, content={"success": True, "data": data})

    except Exception as e:
        logger.error("[대시보드] summary 조회 오류: %s", e)
        return _error_response("DASHBOARD_000", "대시보드 조회 중 오류가 발생했습니다.", 500)


def _empty_summary(period: str) -> dict[str, Any]:
    """빈 KPI 요약 데이터"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    period_label = now.strftime("%Y-%m")

    return {
        "period": period_label,
        "participationCount": 0,
        "submissionCount": 0,
        "wonCount": 0,
        "lostCount": 0,
        "pendingCount": 0,
        "totalWonAmount": 0,
        "winRate": 0.0,
        "averageWonAmount": 0.0,
        "roi": 0.0,
        "upcomingDeadlines": [],
    }


# ----------------------------------------------------------------
# GET /api/v1/dashboard/pipeline
# ----------------------------------------------------------------

@router.get("/pipeline")
async def get_dashboard_pipeline(request: Request) -> JSONResponse:
    """파이프라인 단계별 현황 조회"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return _error_response(e.code, e.message, e.status_code)

    try:
        # DB 없이 빈 파이프라인 반환 (인메모리 MVP)
        from src.services.dashboard_service import PIPELINE_STAGE_ORDER, PIPELINE_STAGE_LABELS
        stages = [
            {
                "status": status,
                "label": PIPELINE_STAGE_LABELS[status],
                "count": 0,
                "items": [],
            }
            for status in PIPELINE_STAGE_ORDER
        ]
        return JSONResponse(status_code=200, content={"success": True, "data": {"stages": stages}})

    except Exception as e:
        logger.error("[대시보드] pipeline 조회 오류: %s", e)
        return _error_response("DASHBOARD_000", "파이프라인 조회 중 오류가 발생했습니다.", 500)


# ----------------------------------------------------------------
# GET /api/v1/dashboard/statistics
# ----------------------------------------------------------------

@router.get("/statistics")
async def get_dashboard_statistics(request: Request) -> JSONResponse:
    """성과 통계 (월별 트렌드) 조회"""
    try:
        user = _get_current_user(request)
    except AuthError as e:
        return _error_response(e.code, e.message, e.status_code)

    # months 파라미터 검증
    months_str = request.query_params.get("months", "6")
    try:
        months = int(months_str)
    except (ValueError, TypeError):
        return _error_response("VALIDATION_001", "months는 정수여야 합니다.", 400)

    if months < 1 or months > 12:
        return _error_response("VALIDATION_001", "months는 1~12 범위여야 합니다.", 400)

    try:
        # 빈 통계 데이터 반환
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        monthly = []
        for i in range(months):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            monthly.append({
                "month": f"{year:04d}-{month:02d}",
                "participationCount": 0,
                "submissionCount": 0,
                "wonCount": 0,
                "lostCount": 0,
                "winRate": 0.0,
                "totalWonAmount": 0,
                "averageBidRate": None,
            })

        cumulative = {
            "totalParticipation": 0,
            "totalSubmission": 0,
            "totalWon": 0,
            "totalLost": 0,
            "overallWinRate": 0.0,
            "totalWonAmount": 0,
            "averageWonAmount": 0.0,
            "overallRoi": 0.0,
        }

        return JSONResponse(
            status_code=200,
            content={"success": True, "data": {"monthly": monthly, "cumulative": cumulative}},
        )

    except Exception as e:
        logger.error("[대시보드] statistics 조회 오류: %s", e)
        return _error_response("DASHBOARD_000", "통계 조회 중 오류가 발생했습니다.", 500)
