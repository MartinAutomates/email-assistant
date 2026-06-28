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


@router.get("/gmail/parse-message/{message_id}", summary="Parse one Gmail message into clean fields (debug)")
async def gmail_parse_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch and parse a Gmail message — shows subject, body preview, gmail_message_id."""
    try:
        raw = await fetch_message(current_user.id, db, message_id)
    except GmailNotConnectedError:
        raise HTTPException(
            status_code=400,
            detail="Gmail not connected. Visit /auth/google/login first."
        )
    
    from gmail_service import parse_gmail_message
    parsed = parse_gmail_message(raw, current_user.id)
    
    return {
        "gmail_message_id": parsed["gmail_message_id"],
        "subject": parsed["subject"],
        "body_preview": parsed["body"][:300] + "..." if len(parsed["body"]) > 300 else parsed["body"],
        "body_length": len(parsed["body"]),
        "user_id": parsed["user_id"],
    }


@router.post("/sync-gmail", summary="Fetch, classify, and store recent Gmail emails")
async def sync_gmail(
    max_emails: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync recent Gmail emails: fetch → parse → AI classify → store in DB.
    
    Skips emails already stored. Returns a summary of what was synced.
    Warning: slow for large max_emails values (one API call per email).
    """
    try:
        from gmail_service import sync_gmail_emails
        result = await sync_gmail_emails(current_user.id, db, max_emails=max_emails)
    except GmailNotConnectedError:
        raise HTTPException(
            status_code=400,
            detail="Gmail not connected. Visit /auth/google/login first."
        )
    
    return result