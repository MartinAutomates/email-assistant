from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from auth import get_current_user
from models.db import Email, User
from models.email import EmailInput

router = APIRouter(tags=["Emails"])


@router.get("/email/{email_id}", summary="Get a single email by ID")
async def read_email(
    email_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user.id)
    )
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
        "is_read": email.is_read,
        "created_at": email.created_at,
    }


@router.post("/emails", summary="Create a new email")
async def create_email(
    email: EmailInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_email = Email(
        subject=email.subject,
        body=email.body,
        user_id=current_user.id,
    )
    
    db.add(new_email)
    await db.commit()
    await db.refresh(new_email)
    
    return {
        "email_id": new_email.id,
        "subject": new_email.subject,
        "body": new_email.body,
        "category": new_email.category,
        "is_read": new_email.is_read,
        "created_at": new_email.created_at,
    }


@router.get("/emails", summary="List emails (paginated, filterable by category)")
async def list_emails(
    skip: int = 0,
    limit: int = 10,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Email).where(Email.user_id == current_user.id).order_by(Email.id)
    
    if category:
        query = query.where(Email.category == category)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    emails = result.scalars().all()
    
    return {
        "skip": skip,
        "limit": limit,
        "category_filter": category,
        "count": len(emails),
        "emails": [
            {
                "email_id": email.id,
                "subject": email.subject,
                "body": email.body,
                "category": email.category,
                "is_read": email.is_read,
                "created_at": email.created_at,
            }
            for email in emails
        ],
    }


@router.delete("/emails/{email_id}", status_code=204, summary="Delete an email")
async def delete_email(
    email_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user.id)
    )
    email = result.scalar_one_or_none()
    
    if email is None:
        raise HTTPException(
            status_code=404,
            detail=f"Email with id {email_id} not found"
        )
    
    await db.delete(email)
    await db.commit()