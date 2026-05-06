from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class EmailInput(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=10, max_length=50000, description="The full email body text")


class EmailToSummarize(BaseModel):
    subject: str = Field(min_length=1, max_length=200, description="The email subject line")
    body: str = Field(min_length=50, max_length=50000, description="The full email body text")
    max_sentences: int = Field(ge=1, le=10, default=3, description="The number of sentences")


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/email/{email_id}")
def read_email(email_id: int):
    fake_emails = {
        1: {"subject": "Welcome to our service"},
        2: {"subject": "Your invoice is ready"},
        3: {"subject": "Password reset request"},
    }
    
    if email_id not in fake_emails:
        raise HTTPException(
            status_code=404,
            detail=f"Email with id {email_id} not found"
        )
    
    return {"email_id": email_id, **fake_emails[email_id]}


@app.post("/classify")
def classify_email(email: EmailInput):
    if not email.subject.strip():
        raise HTTPException(
            status_code=400,
            detail="Subject cannot be empty or whitespace only"
        )
    
    if not email.body.strip():
        raise HTTPException(
            stattus_code=400,
            detail="Body cannot be empty or whitespace only"
        )
    
    exclamation_count = email.subject.count("!")
    uppercase_ratio = sum(1 for c in email.subject if c.isupper()) / len(email.subject)

    if exclamation_count >= 3 and uppercase_ratio > 0.5:
        raise HTTPException(
            status_code=400,
            detail="Subject looks like spam (too many exclamations and uppercase letters)"
        )

    return {
        "subject": email.subject,
        "category": "urgent",
        "confidence": 0.95
    }


@app.post("/summarize")
def summarize_email(email: EmailToSummarize):
    return {
        "original_subject": email.subject,
        "summary": "This is a placeholder summary",
        "sentence_count": email.max_sentences
    }