import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow

from auth import get_current_user
from models.db import User


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# In-memory store: maps state -> code_verifier
# Allows login and callback to share PKCE data across requests.
# Local dev only — production would use a database or signed cookie.
_pkce_store: dict[str, str] = {}


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
    """Redirect the user to Google's consent page."""
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # Save the PKCE verifier keyed by state, so the callback can retrieve it
    _pkce_store[state] = flow.code_verifier
    return RedirectResponse(authorization_url)


@router.get("/auth/google/callback", summary="OAuth callback — Google redirects here after consent")
async def google_callback(request: Request):
    """Receive the authorization code from Google, exchange for tokens."""
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code from Google")
    
    if not state or state not in _pkce_store:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    
    code_verifier = _pkce_store.pop(state)  # one-time use
    
    flow = _build_flow()
    flow.code_verifier = code_verifier
    
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        print(f"[Google OAuth] Token exchange failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
    
    credentials = flow.credentials
    
    print("=" * 60)
    print("[Google OAuth] Token exchange successful!")
    print(f"  Access token: {credentials.token[:40]}...")
    print(f"  Refresh token: {credentials.refresh_token[:40] if credentials.refresh_token else 'None'}...")
    print(f"  Expires at: {credentials.expiry}")
    print(f"  Scopes granted: {credentials.scopes}")
    print("=" * 60)
    
    return {
        "status": "success",
        "message": "Gmail connected. Tokens received and printed to server log.",
    }