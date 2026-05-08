from fastapi import APIRouter
from models.email import EmailToSummarize

router = APIRouter()


@router.post("/summarize")
def summarize_email(email: EmailToSummarize):
    return {
        "original_subject": email.subject,
        "summary": "This is a placeholder summary",
        "sentence_count": email.max_sentences
    }