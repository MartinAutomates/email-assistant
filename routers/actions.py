from fastapi import APIRouter, HTTPException
from models.email import EmailInput
from ai import extract_actions_with_ai, AIServiceError

router = APIRouter(tags=["AI"])


@router.post("/extract-actions", summary="Extract action items from an email using AI")
async def extract_actions(email: EmailInput):
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