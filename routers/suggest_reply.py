from fastapi import APIRouter, HTTPException
from models.email import EmailForReply
from ai import suggest_reply_with_ai, AIServiceError

router = APIRouter()


@router.post("/suggest-reply")
async def suggest_reply(email: EmailForReply):
    try:
        reply = await suggest_reply_with_ai(email.subject, email.body, email.tone)
    except AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI reply suggestion service is temporarily unavailable. Please try again later."
        )
    
    return {
        "original_subject": email.subject,
        "tone": email.tone,
        "suggested_reply": reply,
    }