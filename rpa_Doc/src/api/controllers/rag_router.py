# src/api/controllers/rag_router.py
from fastapi import APIRouter, HTTPException
from src.api.models.schemas import QuestionRequest, QuestionResponse
from src.api.services.rag_service import RAGService
from src.repository.log_repository import LogRepository

router = APIRouter(prefix="/rag", tags=["RAG"])
rag_service = RAGService()
log_repo = LogRepository()

@router.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    try:
        answer = rag_service.ask_question(request.question)
        last_log = log_repo.get_last_log()
        
        # คืนค่าผลลัพธ์พร้อมอ้างอิง
        return QuestionResponse(
            answer=answer,
            refs=last_log.get("refs", []),
            domain=last_log.get("domain", "ทั่วไป"),
            status=last_log.get("status", "success")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_history():
    return log_repo.get_all_logs()
