"""FastAPI 애플리케이션 메인"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.deps import close_redis
from src.config import get_settings
from src.api.v1.router import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시 실행
    yield
    # 종료 시 실행
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
