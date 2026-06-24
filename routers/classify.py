from fastapi import APIRouter, HTTPException
from models.email import EmailInput
from ai import classify_email_with_ai, AIServiceError

router = APIRouter()


@router.post("/classify")
async def classify_email(email: EmailInput):
    if not email.subject.strip():
        raise HTTPException(
            status_code=400,
            detail="Subject cannot be empty or whitespace only"
        )
    
    if not email.body.strip():
        raise HTTPException(
            status_code=400,
            detail="Body cannot be empty or whitespace only"
        )
    
    exclamation_count = email.subject.count("!")
    uppercase_ratio = sum(1 for c in email.subject if c.isupper()) / len(email.subject)
    
    if exclamation_count >= 3 and uppercase_ratio > 0.5:
        raise HTTPException(
            status_code=400,
            detail="Subject looks like spam (too many exclamations and uppercase letters)"
        )
    
    try:
        category = await classify_email_with_ai(email.subject, email.body)
    except AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI classification service is temporarily unavailable. Please try again later."
        )
    
    return {
        "subject": email.subject,
        "category": category,
        "confidence": None,
    }