from fastapi import APIRouter
from .schemas import GenerateRequest, GenerateResponse
from .service import AIService

router = APIRouter(prefix="/api/ai", tags=["AI Generation"])

@router.post("/generate", response_model=GenerateResponse)
async def generate_workflow(request: GenerateRequest):
    return await AIService.generate_workflow(request)