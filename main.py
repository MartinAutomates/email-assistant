from fastapi import FastAPI
from routers import root, emails, classify, summarize, auth


app = FastAPI()


app.include_router(root.router)
app.include_router(emails.router)
app.include_router(classify.router)
app.include_router(summarize.router)
app.include_router(auth.router)