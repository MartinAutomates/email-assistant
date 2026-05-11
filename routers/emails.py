from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.db import Email

router = APIRouter()


@router.get("/email/{email_id}")
async def read_email(email_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    
    if email is None:
        raise HTTPException(
            status_code=404,
            detail=f"Email with id {email_id} not found"
        )
    
    return {
        "email_id": email.id,
        "subject": email.subject,
        "body": email.body,
        "category": email.category,
        "created_at": email.created_at,
    }