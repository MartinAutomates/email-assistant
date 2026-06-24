from fastapi import FastAPI
from routers import root, emails, classify, summarize, auth, actions, suggest_reply


app = FastAPI()


app.include_router(root.router)
app.include_router(emails.router)
app.include_router(classify.router)
app.include_router(summarize.router)
app.include_router(auth.router)
app.include_router(actions.router)
app.include_router(suggest_reply.router)