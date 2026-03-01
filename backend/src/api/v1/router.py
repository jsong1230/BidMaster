"""API v1 라우터"""
from fastapi import APIRouter

from src.api.v1 import auth, proposals

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["제안서"])
