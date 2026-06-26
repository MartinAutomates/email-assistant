import time
import logging
from fastapi import FastAPI
from routers import root, emails, classify, summarize, auth, actions, suggest_reply, google_auth


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