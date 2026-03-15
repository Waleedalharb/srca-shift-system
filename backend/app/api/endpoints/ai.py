# backend/app/api/endpoints/ai.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.ai_scheduler import AIScheduler
from app.api import deps
from app.models.user import User

router = APIRouter()
ai_scheduler = AIScheduler()

class AIRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_schedule(
    request: AIRequest,
    current_user: User = Depends(deps.get_current_active_user)
):
    """توليد اقتراح جدول مناوبات"""
    try:
        result = ai_scheduler.generate_schedule(request.prompt)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))