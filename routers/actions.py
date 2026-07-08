from fastapi import APIRouter, HTTPException, Request
from models.email import EmailInput
from ai import extract_actions_with_ai, AIServiceError
from limiter import limiter

router = APIRouter(tags=["AI"])


@router.post("/extract-actions", summary="Extract action items from an email using AI")
@limiter.limit("10/minute")
async def extract_actions(request: Request, email: EmailInput):
    try:
        actions = await extract_actions_with_ai(email.subject, email.body)
    except AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI action extraction service is temporarily unavailable. Please try again later."
        )
    
    return {
        "subject": email.subject,
        "action_count": len(actions),
        "actions": actions,
    }