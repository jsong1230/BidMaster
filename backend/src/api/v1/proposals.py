"""제안서 API"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_proposals():
    """제안서 목록 조회"""
    return {"success": True, "data": {"items": []}, "message": "제안서 목록 조회 기능 구현 예정"}


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: int):
    """제안서 상세 조회"""
    return {"success": True, "data": {"id": proposal_id}, "message": "제안서 상세 조회 기능 구현 예정"}


@router.post("/")
async def create_proposal():
    """제안서 생성"""
    return {"success": True, "message": "제안서 생성 기능 구현 예정"}
