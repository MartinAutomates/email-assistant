import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

from auth import get_current_user
from database import get_db
from models.db import User, OAuthToken
from crypto import encrypt_str


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Per-state PKCE store + which user initiated the flow
# Maps: state -> {"code_verifier": str, "user_id": int}
_pkce_store: dict[str, dict] = {}


router = APIRouter(tags=["Gmail OAuth"])


def _build_flow() -> Flow:
    """Construct the Google OAuth Flow object from our client config."""
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


@router.get("/auth/google/login", summary="Start the Gmail OAuth flow")
async def google_login(current_user: User = Depends(get_current_user)):
    """Redirect the user to Google's consent page. AUTH TEMPORARILY DISABLED FOR TESTING."""
    user_id = current_user.id  # TEMP: hardcoded — restore Depends(get_current_user) after this test
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    _pkce_store[state] = {
        "code_verifier": flow.code_verifier,
        "user_id": user_id,
    }
    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback", summary="OAuth callback — exchange code, store encrypted tokens")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive Google's redirect, exchange code, save encrypted tokens to DB."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from Google")
    
    if not state or state not in _pkce_store:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    
    state_data = _pkce_store.pop(state)
    code_verifier = state_data["code_verifier"]
    user_id = state_data["user_id"]
    
    flow = _build_flow()
    flow.code_verifier = code_verifier
    
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        print(f"[Google OAuth] Token exchange failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
    
    credentials = flow.credentials
    
    # Check if user already has a token row → update it. Otherwise insert.
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user_id))
    existing = result.scalar_one_or_none()
    
    encrypted_access = encrypt_str(credentials.token)
    encrypted_refresh = encrypt_str(credentials.refresh_token) if credentials.refresh_token else None
    scopes_str = ",".join(credentials.scopes) if credentials.scopes else None
    
    if existing:
        existing.access_token = encrypted_access
        if encrypted_refresh:  # Don't overwrite refresh_token if Google didn't send one
            existing.refresh_token = encrypted_refresh
        existing.token_expires_at = credentials.expiry
        existing.scopes = scopes_str
        existing.updated_at = datetime.utcnow()
    else:
        new_token = OAuthToken(
            user_id=user_id,
            provider="google",
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_expires_at=credentials.expiry,
            scopes=scopes_str,
        )
        db.add(new_token)
    
    await db.commit()
    
    print(f"[Google OAuth] Tokens stored for user_id={user_id}, expires_at={credentials.expiry}")
    
    return {
        "status": "success",
        "message": "Gmail connected. Tokens stored securely.",
        "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
        "scopes": credentials.scopes,
    }


@router.get("/auth/google/status", summary="Check if Gmail is connected for current user")
async def google_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return whether the current user has stored Gmail tokens."""
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == current_user.id))
    token = result.scalar_one_or_none()
    
    if token is None:
        return {"connected": False}
    
    return {
        "connected": True,
        "provider": token.provider,
        "expires_at": token.token_expires_at.isoformat() if token.token_expires_at else None,
        "scopes": token.scopes.split(",") if token.scopes else [],
    }