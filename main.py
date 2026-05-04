from fastapi import FastAPI
from pydantic import BaseModel


class EmailInput(BaseModel):
    subject: str
    body: str


app = FastAPI()


@app.get("/")
def read_root():
    return{"message": "Hello World"}

@app.get("/email/{email_id}")
def read_email(email_id: int):
    return{"email_id": email_id, "subject": "Test email"}

@app.post("/classify")
def classify_email(email: EmailInput):
    return{
        "subject": email.subject,
        "category": "urgent",
        "confidence": 0.95
    }