from fastapi import APIRouter, HTTPException
from models.email import EmailToSummarize
from ai import summarize_email_with_ai, AIServiceError

router = APIRouter()


@router.post("/summarize")
async def summarize_email(email: EmailToSummarize):
    try:
        summary = await summarize_email_with_ai(
            email.subject,
            email.body,
            email.max_sentences,
        )
    except AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI summarization service is temporarily unavailable. Please try again later."
        )
    
    return {
        "original_subject": email.subject,
        "summary": summary,
        "sentence_count": email.max_sentences,
    }