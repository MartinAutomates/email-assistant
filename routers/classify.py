from fastapi import APIRouter, HTTPException
from models.email import EmailInput
from ai import classify_email_with_ai

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
    
    # Real AI classification
    category = await classify_email_with_ai(email.subject, email.body)
    
    return {
        "subject": email.subject,
        "category": category,
        "confidence": None,  # No confidence score from this approach
    }