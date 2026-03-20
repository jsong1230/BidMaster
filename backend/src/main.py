"""FastAPI 애플리케이션 메인"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.deps import close_redis
from src.config import get_settings
from src.api.v1.router import api_router
from src.core.exceptions import AppException

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 스케줄러 시작 (설정에서 활성화된 경우)
    scheduler = None
    if settings.scheduler_enabled:
        try:
            from src.scheduler import create_scheduler
            scheduler = create_scheduler()
            scheduler.start()
            app.state.scheduler = scheduler
            logger.info("[APScheduler] 공고 수집 스케줄러 시작됨")
        except ImportError as e:
            logger.warning(f"[APScheduler] 스케줄러 초기화 실패 (apscheduler 미설치): {e}")
        except Exception as e:
            logger.warning(f"[APScheduler] 스케줄러 시작 오류: {e}")

    yield

    # 종료 시 정리
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
            logger.info("[APScheduler] 스케줄러 종료됨")
        except Exception as e:
            logger.warning(f"[APScheduler] 스케줄러 종료 오류: {e}")

    await close_redis()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ============================================================
# 글로벌 예외 핸들러
# ============================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """애플리케이션 예외 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "ok", "service": settings.app_name}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "BidMaster API",
        "version": "0.1.0",
        "docs": "/docs",
    }
