"""인증 API"""
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.post("/login")
async def login():
    """로그인"""
    return {"success": True, "message": "로그인 기능 구현 예정"}


@router.post("/register")
async def register():
    """회원가입"""
    return {"success": True, "message": "회원가입 기능 구현 예정"}


@router.post("/logout")
async def logout():
    """로그아웃"""
    return {"success": True, "message": "로그아웃 기능 구현 예정"}
