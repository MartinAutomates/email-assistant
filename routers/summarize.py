from fastapi import APIRouter, HTTPException, Request
from models.email import EmailToSummarize
from ai import summarize_email_with_ai, AIServiceError
from limiter import limiter

router = APIRouter(tags=["AI"])


@router.post("/summarize", summary="Generate an AI summary of an email in N sentences")
@limiter.limit("10/minute")
async def summarize_email(request: Request, email: EmailToSummarize):
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