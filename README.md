# Email Assistant 

AI-powered email classifier and assistant. Built as a portfolio project to learn full-stack development with Python.

## Status

🚧 In development. Started May 2026.

## What it does

- Connects to your Gmail inbox via OAuth
- Classifies incomming emails by category (urgent, personal, newsletter, spam)
- Summarizes long emails into 2-3 sentences
- Suggests drafts replies using AI
- Provides a clean web UI to manage eveything

## Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic
- **Database:** PostgreSQL, SQLAlchemy
- **AI:** Claude API (Anthropic)
- **Frontend:** React, Tailwind CSS
- **Auth:** JWT, Gmail OAuth 2.0
- **Deployment:** Docker, deployed on Railway/Render

## Roadmap

- [x] Project setup, FastAPI scaffold
- [ ] Database models and migrations
- [ ] User authentication (JWT)
- [ ] AI classification endpoint
- [ ] Gmail OAuth integration
- [ ] Email summarization and reply suggestion
- [ ] Frontend (React)
- [ ] Docker + deployment
- [ ] Live demo

## Author

Martin Stoyanov — [GitHub](https://github.com/MartinAutomates)


## Setup

```bash
# Clone the repo
git clone https://github.com/MartinAutomates/email-assistant.git
cd email-assistant

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs at `/docs`.