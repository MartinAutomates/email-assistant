import time
import logging
import os
import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import root, emails, classify, summarize, auth, actions, suggest_reply, google_auth, gmail
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from limiter import limiter


load_dotenv()

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,
        traces_sample_rate=0.1,
    )


app = FastAPI(
    title="AI Email Assistant",
    description="""
A FastAPI backend for an AI-powered email assistant.

## Features

* **JWT Authentication** — register, login, protected endpoints
* **Email CRUD** — create, read, list, delete with per-user isolation
* **AI Classification** — categorize emails (urgent, work, newsletter, spam)
* **AI Summarization** — condense emails into N-sentence summaries
* **AI Action Extraction** — pull action items as structured JSON
* **AI Reply Drafting** — generate professional / friendly / brief replies (with streaming)

## Tech Stack

PostgreSQL · SQLAlchemy (async) · Alembic · Pydantic · JWT · Groq (Llama 3.1) · pytest
""",
    version="0.1.0",
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only — lock this down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("email-assistant")


@app.middleware("http")
async def log_requests(request, call_next):
    """Log every HTTP request with method, path, status code, and duration."""
    start = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} in {duration_ms:.1f}ms"
    )
    
    return response


app.include_router(root.router)
app.include_router(emails.router)
app.include_router(classify.router)
app.include_router(summarize.router)
app.include_router(auth.router)
app.include_router(actions.router)
app.include_router(suggest_reply.router)
app.include_router(google_auth.router)
app.include_router(gmail.router)


