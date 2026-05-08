from fastapi import FastAPI
from routers import root, emails, classify, summarize


app = FastAPI()


app.include_router(root.router)
app.include_router(emails.router)
app.include_router(classify.router)
app.include_router(summarize.router)