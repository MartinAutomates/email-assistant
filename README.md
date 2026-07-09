![CI](https://github.com/MartinAutomates/email-assistant/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![License](https://img.shields.io/badge/license-MIT-green)

# Email Assistant

AI-powered full-stack email assistant. FastAPI + PostgreSQL + Groq AI backend, with a React frontend, JWT auth, and Gmail OAuth integration.

Started May 2026 as a self-taught learning project.

**🔗 Live app:** [email-assistant-kappa-wine.vercel.app](https://email-assistant-kappa-wine.vercel.app)
**📝 Blog post:** [How I built this](https://martinstoyanovhashnodedev.hashnode.dev/my-ai-read-my-email-decided-how-to-reply-and-sent-it-here-s-how-i-built-that)

## Table of Contents

- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [What it does](#what-it-does)
- [Tech stack](#tech-stack)
- [Project status](#project-status)
- [API endpoints](#api-endpoints)
- [Setup](#setup)
- [Testing](#testing)
- [Project structure](#project-structure)
- [Notes](#notes)
- [Author](#author)

## Screenshots

**Login**
![Login screen](screenshots/login.png)

**Email list with AI categorization**
![Email list](screenshots/email-list.png)

**AI summary + suggested reply**
![Email detail view](screenshots/email-detail.png)

## Architecture

**React Frontend** (Vite + JSX) → JWT auth → **FastAPI Backend** (async Python)

The backend talks to three services:
- **PostgreSQL** (SQLAlchemy + Alembic) — user data, emails, encrypted OAuth tokens
- **Groq API** (Llama 3.1) — classify / summarize / extract actions / suggest reply
- **Gmail API** (OAuth 2.0) — fetch and sync emails

Tokens never touch the database in plaintext — OAuth tokens are encrypted at rest with Fernet before storage.

## What it does

- **JWT authentication** — register, login, protected endpoints
- **Per-user data isolation** — every email belongs to one user, enforced by foreign key + WHERE filter
- **AI classification** — categorize emails as urgent, work, newsletter, spam, or other (via Groq + Llama 3.1)
- **AI summarization** — condense emails into N-sentence summaries
- **AI action extraction** — pull action items as structured JSON
- **AI reply drafting** — generate professional / friendly / brief replies, with an accept/decline stance, optional token-by-token streaming, and one-click sending via Gmail
- **Gmail OAuth** — users connect their Gmail account; tokens stored encrypted at rest (Fernet)
- **Gmail sync** — fetch recent emails, parse MIME/base64 content, auto-classify, store with deduplication
- **Gmail send** — send AI-drafted replies directly, properly threaded to the original conversation
- **React frontend** — login, email list with live category filtering, one-click AI reclassification, expandable email detail view with summary/reply generation, accept/decline drafting, and send/copy actions
- **Smart safeguards** — response caching, graceful degradation on AI service failure, request logging middleware, rate limiting (10 req/min on AI endpoints)
- **Production monitoring** — Sentry error tracking, GitHub Actions CI on every push

## Tech stack

- **Backend:** Python 3.12, FastAPI, async SQLAlchemy
- **Frontend:** React 19 (Vite), vanilla CSS
- **Database:** PostgreSQL 18, Alembic migrations
- **Auth:** JWT (python-jose), bcrypt password hashing
- **AI:** Groq API (Llama 3.1 8B Instant)
- **OAuth:** Google OAuth 2.0 with PKCE
- **Encryption:** Fernet (cryptography library) for OAuth tokens at rest
- **Testing:** pytest with pytest-asyncio, isolated test database, 71% coverage
- **DevOps:** Docker, GitHub Actions CI, Sentry monitoring, slowapi rate limiting
- **Deployment:** Railway (backend + PostgreSQL), Vercel (frontend)
- **Other:** Pydantic v2, python-dotenv

## Project status

| Phase | Status |
|---|---|
| FastAPI scaffold + project structure | ✅ Done |
| Pydantic input validation + error handling | ✅ Done |
| PostgreSQL + SQLAlchemy + Alembic | ✅ Done |
| JWT authentication (register, login, protected routes) | ✅ Done |
| Per-user data isolation (foreign keys, scoped queries) | ✅ Done |
| AI classification, summarization, action extraction, reply drafting | ✅ Done |
| Response caching + AI service error handling | ✅ Done |
| Streaming responses for AI replies | ✅ Done |
| Request logging middleware + API documentation polish | ✅ Done |
| Gmail OAuth flow with encrypted token storage | ✅ Done |
| Gmail fetch + sync (read inbox, classify, store) | ✅ Done |
| Gmail send (accept/decline drafting, threaded replies) | ✅ Done |
| React frontend (login, list, filter, detail view, AI actions) | ✅ Done |
| Docker + deployment (Railway + Vercel) | ✅ Done |
| Live demo | ✅ Done |
| CI/CD (GitHub Actions) | ✅ Done |
| Error monitoring (Sentry) + rate limiting | ✅ Done |

## API endpoints

Interactive documentation at `/docs` after running the server. Highlights:

**Auth**
- `POST /register` — create a new user
- `POST /login` — exchange credentials for a JWT
- `GET /auth/google/login` — start Gmail OAuth flow
- `GET /auth/google/callback` — handle Google's callback, store encrypted tokens
- `GET /auth/google/status` — check whether Gmail is connected

**Emails (all per-user, all require JWT)**
- `POST /emails` — create an email
- `GET /email/{id}` — fetch one email
- `GET /emails` — list emails (paginated, filterable by category)
- `DELETE /emails/{id}` — delete an email

**Gmail**
- `GET /gmail/fetch-ids` — list recent Gmail message IDs
- `GET /gmail/fetch-message/{id}` — fetch one raw Gmail message
- `GET /gmail/parse-message/{id}` — fetch + parse a message into clean fields
- `POST /sync-gmail` — fetch, classify, and store recent Gmail emails (deduplicated)
- `POST /gmail/send-reply/{gmail_message_id}` — send a reply, threaded to the original message

**AI**
- `POST /classify` — categorize an email
- `POST /summarize` — summarize an email in N sentences
- `POST /extract-actions` — extract action items as a list
- `POST /suggest-reply` — draft a reply (tone: professional / friendly / brief; optional decision: accept / decline)
- `POST /suggest-reply-stream` — streaming version of the above

## Setup

### Prerequisites
- Python 3.12+
- Node.js 20+ (for the frontend)
- PostgreSQL 18+ running locally on port 5432 (or Docker — see below)
- A Groq API key ([get one free](https://console.groq.com))
- Optional: Google Cloud project with OAuth credentials for Gmail features
- Optional: Docker + Docker Compose for containerized setup

### Backend

```bash
# Clone
git clone https://github.com/MartinAutomates/email-assistant.git
cd email-assistant

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/email_assistant_dev
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/email_assistant_test

SECRET_KEY=generate-a-long-random-string-for-jwt-signing
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GROQ_API_KEY=gsk_your_groq_key_here

TOKEN_ENCRYPTION_KEY=generate-with-Fernet.generate_key

# Optional — only needed for Gmail OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Optional — error monitoring
SENTRY_DSN=your_sentry_dsn_here
```

Generate the encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create both databases:
```bash
psql -U postgres -c "CREATE DATABASE email_assistant_dev;"
psql -U postgres -c "CREATE DATABASE email_assistant_test;"
```

Run migrations:
```bash
alembic upgrade head
```

Start the backend:
```bash
uvicorn main:app --reload
```

API available at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd email-assistant-frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`. Requires the backend running at `http://127.0.0.1:8000`.

### Docker (alternative)

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Backend available at `http://127.0.0.1:8000`, PostgreSQL runs in its own container.

## Testing

```bash
pytest
```

37 tests run against an isolated test database (71% coverage), with auto-created schema and a clean state before every test. Tests run automatically via GitHub Actions on every push.

## Project structure

Backend (`/`):
- `main.py` — FastAPI app + middleware + router includes
- `database.py` — Async engine + session factory
- `auth.py` — Password hashing, JWT, get_current_user dependency
- `crypto.py` — Fernet encrypt/decrypt for OAuth tokens
- `ai.py` — Groq calls: classify, summarize, extract_actions, suggest_reply
- `gmail_service.py` — Gmail API: fetch, parse MIME/base64, sync, send
- `limiter.py` — Rate limiting configuration

`models/`:
- `db.py` — SQLAlchemy models: User, Email, OAuthToken
- `email.py` — Pydantic schemas for email endpoints
- `user.py` — Pydantic schemas for auth

`routers/`:
- `root.py` — `/`
- `auth.py` — `/register`, `/login`
- `google_auth.py` — Gmail OAuth flow
- `emails.py` — CRUD endpoints
- `gmail.py` — Gmail fetch/sync/send endpoints
- `classify.py`, `summarize.py`, `actions.py`, `suggest_reply.py` — AI endpoints

`tests/`:
- `test_main.py` — 37 async tests with isolated DB + auth helpers

Other top-level:
- `alembic/` — Migration scripts
- `email-assistant-frontend/` — React app (Vite), main logic in `src/App.jsx`
- `screenshots/` — README images
- `.github/workflows/` — CI pipeline
- `Dockerfile`, `docker-compose.yml` — containerization
- `conftest.py`, `pytest.ini`, `requirements.txt`

## Notes

- All AI calls are async and gracefully degrade to HTTP 503 on Groq failures. Frontend surfaces these error messages directly to the user instead of failing silently.
- Classification and summarization results are cached in-memory (MD5 keyed by input). Reply drafts are intentionally not cached.
- The OAuth flow uses PKCE; verifier persistence between login and callback is handled via the `state` parameter, keyed alongside the initiating user's ID.
- OAuth tokens are encrypted with Fernet before storage; decryption only happens in application code when calling Gmail API. Access tokens are refreshed automatically when expired.
- Gmail messages (MIME/base64, HTML or plain text) are parsed into clean subject/body pairs before classification.
- Sending replies builds proper MIME messages with `In-Reply-To`/`References` headers so they thread correctly in Gmail.
- The frontend authenticates via JWT stored in `localStorage`; a 401 response triggers automatic logout rather than a silent failure.
- All AI endpoints are rate-limited to 10 requests/minute per IP.

## Author

Martin Stoyanov — [GitHub](https://github.com/MartinAutomates)