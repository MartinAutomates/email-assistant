from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.email import EmailForReply
from ai import suggest_reply_with_ai, suggest_reply_stream, AIServiceError

router = APIRouter(tags=["AI"])


@router.post("/suggest-reply", summary="Draft an AI reply to an email (JSON response)")
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


@router.post("/suggest-reply-stream", summary="Draft an AI reply with streaming token-by-token output")
async def suggest_reply_streaming(email: EmailForReply):
    """Stream the AI reply token-by-token. Returns text/plain chunks."""
    generator = suggest_reply_stream(email.subject, email.body, email.tone)
    return StreamingResponse(generator, media_type="text/plain")