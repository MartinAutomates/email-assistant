from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/email/{email_id}")
def read_email(email_id: int):
    fake_emails = {
        1: {"subject": "Welcome to our service"},
        2: {"subject": "Your invoice is ready"},
        3: {"subject": "Password reset request"},
    }
    
    if email_id not in fake_emails:
        raise HTTPException(
            status_code=404,
            detail=f"Email with id {email_id} not found"
        )
    
    return {"email_id": email_id, **fake_emails[email_id]}