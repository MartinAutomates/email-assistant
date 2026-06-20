import os
from groq import AsyncGroq
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ALLOWED_CATEGORIES = {"urgent", "work", "newsletter", "spam", "other"}


client = AsyncGroq(api_key=GROQ_API_KEY)


CLASSIFY_SYSTEM_PROMPT = """You are a strict email classifier. 
You will receive an email subject and body.
Respond with exactly ONE word from this list: urgent, work, newsletter, spam, other.
No explanation. No punctuation. No quotes. Just the single word."""


async def classify_email_with_ai(subject: str, body: str) -> str:
    """Send email to Groq, return classification category."""
    user_message = f"Subject: {subject}\n\nBody: {body}"
    
    response = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        max_tokens=10,
    )
    
    raw_output = response.choices[0].message.content.strip().lower()
    
    # Validate the AI gave us a real category
    if raw_output in ALLOWED_CATEGORIES:
        return raw_output
    
    # Fallback if AI returned something unexpected
    return "other"