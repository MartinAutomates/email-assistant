import os
import base64
import html as html_lib
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from email.mime.text import MIMEText

from models.db import OAuthToken
from crypto import encrypt_str, decrypt_str


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]


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


def _get_header(headers: list[dict], name: str) -> str:
    """Find a header value by name from Gmail's headers list."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def _decode_body(data: str) -> str:
    """Decode a base64url-encoded Gmail body string."""
    # Gmail sometimes strips padding — add it back before decoding
    padded = data + "=="
    decoded_bytes = base64.urlsafe_b64decode(padded)
    return decoded_bytes.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    """Very basic HTML tag stripper. Not perfect but good enough for email bodies."""
    import re
    # Remove style and script blocks entirely
    html = re.sub(r'<(style|script)[^>]*>.*?</(style|script)>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block-level tags with newlines
    html = re.sub(r'<(br|p|div|tr|li)[^>]*>', '\n', html, flags=re.IGNORECASE)
    # Remove all remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # Collapse whitespace
    html = re.sub(r'[ \t]*\n[ \t]*', '\n', html)  # strip spaces around newlines
    html = re.sub(r'\n{3,}', '\n\n', html)          # collapse 3+ newlines to 2
    html = re.sub(r'[ \t]+', ' ', html)
    html = html_lib.unescape(html)
    return html.strip()


def _extract_plain_text(payload: dict) -> str:
    """Recursively extract readable text from a Gmail message payload.
    
    Prefers text/plain. Falls back to text/html (stripped of tags).
    Handles simple, multipart, and nested multipart structures.
    """
    mime_type = payload.get("mimeType", "")
    
    # Case 1: Simple text/plain — best case
    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return _decode_body(data) if data else ""
    
    # Case 2 & 3: Multipart — recurse, prefer plain text
    if mime_type.startswith("multipart/"):
        plain_result = ""
        html_result = ""
        for part in payload.get("parts", []):
            result = _extract_plain_text(part)
            if result:
                part_mime = part.get("mimeType", "")
                if part_mime == "text/plain" or plain_result:
                    plain_result = plain_result or result
                else:
                    html_result = html_result or result
        return plain_result or html_result
    
    # Case 4: HTML only — strip tags
    if mime_type == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            raw_html = _decode_body(data)
            return _strip_html(raw_html)
    
    return ""


def parse_gmail_message(raw_message: dict, user_id: int) -> dict:
    """Parse a raw Gmail API message into a clean dict ready for Email model insertion.
    
    Returns a dict with keys: subject, body, gmail_message_id, user_id.
    Does NOT create a DB row — caller handles that.
    """
    payload = raw_message.get("payload", {})
    headers = payload.get("headers", [])
    
    subject = _get_header(headers, "Subject") or "(no subject)"
    body = _extract_plain_text(payload)
    
    # Fallback: if no plain text found, use the snippet (short preview)
    if not body.strip():
        body = raw_message.get("snippet", "(no body)")
    
    return {
        "subject": subject[:200],  # Email.subject is String(200)
        "body": body or "(no body)",
        "gmail_message_id": raw_message["id"],
        "user_id": user_id,
    }


async def sync_gmail_emails(
    user_id: int,
    db: AsyncSession,
    max_emails: int = 10,
) -> dict:
    """Fetch recent Gmail emails, classify each, store new ones in DB.
    
    Returns a summary dict with counts of synced and skipped emails.
    Skips emails already in DB (by gmail_message_id).
    """
    from sqlalchemy import select
    from models.db import Email
    from ai import classify_email_with_ai, AIServiceError
    
    # Step 1: Get recent message IDs
    message_ids = await fetch_message_ids(user_id, db, max_results=max_emails)
    
    synced = 0
    skipped = 0
    errors = 0
    
    for msg_id in message_ids:
        # Step 2: Check if already in DB (avoid duplicate API call)
        existing = await db.execute(
            select(Email).where(Email.gmail_message_id == msg_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        
        # Step 3: Fetch + parse the full message
        try:
            raw = await fetch_message(user_id, db, msg_id)
            parsed = parse_gmail_message(raw, user_id)
        except Exception as e:
            print(f"[sync_gmail] Failed to fetch/parse {msg_id}: {e}")
            errors += 1
            continue
        
        # Step 4: Classify with AI
        try:
            category = await classify_email_with_ai(parsed["subject"], parsed["body"])
        except AIServiceError:
            category = None  # Store without category rather than skip entirely
        
        # Step 5: Store in DB
        new_email = Email(
            subject=parsed["subject"],
            body=parsed["body"],
            category=category,
            user_id=user_id,
            gmail_message_id=parsed["gmail_message_id"],
        )
        db.add(new_email)
        
        try:
            await db.commit()
            synced += 1
            print(f"[sync_gmail] Stored: '{parsed['subject'][:50]}' → {category}")
        except Exception as e:
            await db.rollback()
            print(f"[sync_gmail] DB error for {msg_id}: {e}")
            errors += 1
    
    return {
        "synced": synced,
        "skipped": skipped,
        "errors": errors,
        "total_checked": len(message_ids),
    }


def _build_reply_mime(to_email: str, subject: str, body: str, thread_id: str, original_message_id_header: str) -> str:
    """Build a base64url-encoded MIME message formatted as a reply, threaded to the original."""
    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    
    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = reply_subject
    message["In-Reply-To"] = original_message_id_header
    message["References"] = original_message_id_header
    
    raw_bytes = message.as_bytes()
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")


async def send_reply(
    user_id: int,
    db: AsyncSession,
    gmail_message_id: str,
    reply_body: str,
) -> dict:
    """Send a reply to a specific Gmail message, properly threaded."""
    creds, _ = await _load_credentials(user_id, db)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    # Fetch the original message to get headers needed for threading + recipient
    original = service.users().messages().get(
        userId="me",
        id=gmail_message_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"],
    ).execute()
    
    headers = original.get("payload", {}).get("headers", [])
    from_header = _get_header(headers, "From")
    subject_header = _get_header(headers, "Subject")
    message_id_header = _get_header(headers, "Message-ID")
    thread_id = original.get("threadId")
    
    if not from_header:
        raise ValueError("Could not determine recipient from original email")
    
    raw_message = _build_reply_mime(
        to_email=from_header,
        subject=subject_header,
        body=reply_body,
        thread_id=thread_id,
        original_message_id_header=message_id_header,
    )
    
    sent = service.users().messages().send(
        userId="me",
        body={"raw": raw_message, "threadId": thread_id},
    ).execute()
    
    return {
        "sent_message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "to": from_header,
    }