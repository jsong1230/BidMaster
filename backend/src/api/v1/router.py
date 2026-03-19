"""API v1 라우터"""
from fastapi import APIRouter

from src.api.v1 import auth, proposals, bids, notifications, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["제안서"])
api_router.include_router(bids.router, prefix="/bids", tags=["공고"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["알림"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["대시보드"])
