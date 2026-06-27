import os
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from models.db import OAuthToken
from crypto import encrypt_str, decrypt_str


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailNotConnectedError(Exception):
    """Raised when the user has no stored OAuth tokens."""
    pass


async def _load_credentials(user_id: int, db: AsyncSession) -> tuple[Credentials, OAuthToken]:
    """Load OAuth tokens from DB, build a Credentials object, refresh if needed.
    
    Returns the live Credentials object AND the DB row, so callers can persist refresh updates.
    Raises GmailNotConnectedError if the user has no tokens stored.
    """
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user_id))
    token_row = result.scalar_one_or_none()
    
    if token_row is None:
        raise GmailNotConnectedError(f"User {user_id} has no stored Gmail credentials")
    
    creds = Credentials(
        token=decrypt_str(token_row.access_token),
        refresh_token=decrypt_str(token_row.refresh_token) if token_row.refresh_token else None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=token_row.scopes.split(",") if token_row.scopes else GMAIL_SCOPES,
    )
    
    # Refresh if expired (and we have a refresh token to do so)
    if creds.expired and creds.refresh_token:
        print(f"[Gmail] Access token expired for user_id={user_id}, refreshing...")
        creds.refresh(Request())
        # Persist the new access token back to DB
        token_row.access_token = encrypt_str(creds.token)
        token_row.token_expires_at = creds.expiry
        token_row.updated_at = datetime.utcnow()
        await db.commit()
        print(f"[Gmail] Token refreshed, new expiry: {creds.expiry}")
    
    return creds, token_row


async def fetch_message_ids(user_id: int, db: AsyncSession, max_results: int = 20) -> list[str]:
    """Fetch the most recent N message IDs from the user's Gmail inbox."""
    creds, _ = await _load_credentials(user_id, db)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    response = service.users().messages().list(
        userId="me",
        maxResults=max_results,
    ).execute()
    
    messages = response.get("messages", [])
    return [m["id"] for m in messages]


async def fetch_message(user_id: int, db: AsyncSession, message_id: str) -> dict:
    """Fetch a single full Gmail message by ID. Returns the raw Gmail message dict."""
    creds, _ = await _load_credentials(user_id, db)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    return service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()