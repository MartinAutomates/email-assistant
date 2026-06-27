from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models.db import User
from gmail_service import fetch_message_ids, fetch_message, GmailNotConnectedError


router = APIRouter(tags=["Gmail"])


@router.get("/gmail/fetch-ids", summary="Fetch recent message IDs from connected Gmail")
async def gmail_fetch_ids(
    max_results: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the IDs of the user's most recent emails. Useful for debugging."""
    try:
        ids = await fetch_message_ids(current_user.id, db, max_results=max_results)
    except GmailNotConnectedError:
        raise HTTPException(
            status_code=400,
            detail="Gmail not connected. Visit /auth/google/login first."
        )
    
    return {
        "count": len(ids),
        "message_ids": ids,
    }


@router.get("/gmail/fetch-message/{message_id}", summary="Fetch one full Gmail message")
async def gmail_fetch_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the raw Gmail message for a given ID. Useful for debugging payload structure."""
    try:
        message = await fetch_message(current_user.id, db, message_id)
    except GmailNotConnectedError:
        raise HTTPException(
            status_code=400,
            detail="Gmail not connected. Visit /auth/google/login first."
        )
    
    return message