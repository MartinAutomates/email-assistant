from fastapi import FastAPI
from pydantic import BaseModel, Field


class EmailInput(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=10, max_length=50000, description="The full email body text")


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