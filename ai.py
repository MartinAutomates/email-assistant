import hashlib
import os

from groq import AsyncGroq
from dotenv import load_dotenv


class AIServiceError(Exception):
    """Raised when the AI service (Groq) fails."""
    pass


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ALLOWED_CATEGORIES = {"urgent", "work", "newsletter", "spam", "other"}

# Simple in-memory cache: {hash_key: category}
_classify_cache: dict[str, str] = {}


client = AsyncGroq(api_key=GROQ_API_KEY)


CLASSIFY_SYSTEM_PROMPT = """You are a strict email classifier. 
You will receive an email subject and body.
Respond with exactly ONE word from this list: urgent, work, newsletter, spam, other.
No explanation. No punctuation. No quotes. Just the single word."""


def _cache_key(subject: str, body: str) -> str:
    """Hash subject+body into a short, fixed-size key for the cache."""
    content = f"{subject}|{body}"
    return hashlib.md5(content.encode()).hexdigest()


async def classify_email_with_ai(subject: str, body: str) -> str:
    """Send email to Groq, return classification category. Cached by content."""
    # Check cache first
    key = _cache_key(subject, body)
    if key in _classify_cache:
        return _classify_cache[key]
    
    # Cache miss — call Groq
    user_message = f"Subject: {subject}\n\nBody: {body}"
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=10,
        )
    except Exception as e:
        # Log the actual error for debugging
        print(f"[AI classify] Groq call failed: {type(e).__name__}: {e}")
        # Re-raise as a generic exception that the endpoint will turn into a clean 503
        raise AIServiceError("AI classification service is temporarily unavailable") from e
    
    raw_output = response.choices[0].message.content.strip().lower()
    
    # Validate the AI gave us a real category
    if raw_output in ALLOWED_CATEGORIES:
        category = raw_output
    else:
        category = "other"
    
    # Save to cache for next time
    _classify_cache[key] = category
    return category