import hashlib
import json
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
_summarize_cache: dict[str, str] = {}
_actions_cache: dict[str, list[str]] = {}


client = AsyncGroq(api_key=GROQ_API_KEY)


CLASSIFY_SYSTEM_PROMPT = """You are a strict email classifier. 
You will receive an email subject and body.
Respond with exactly ONE word from this list: urgent, work, newsletter, spam, other.
No explanation. No punctuation. No quotes. Just the single word."""


SUMMARIZE_SYSTEM_PROMPT_TEMPLATE = """You are an email summarizer.
Given an email subject and body, produce a clear summary in exactly {n} sentences.
Respond with ONLY the summary. No preamble, no explanation, no bullet points, no headers.
Just the summary sentences."""


EXTRACT_ACTIONS_SYSTEM_PROMPT = """You are an action item extractor for emails.
Given an email subject and body, identify all action items (tasks, requests, commitments) the recipient must do.
Respond with ONLY a JSON array of strings. Each string is one action item.
No preamble, no explanation, no markdown, no code fences. Just the raw JSON array.

Example output:
["Review the Q3 report by Friday", "Book the conference room", "Update the project timeline"]

If there are no action items, respond with: []"""


SUGGEST_REPLY_SYSTEM_PROMPT_TEMPLATE = """You are an email reply drafter.
Given an email subject and body, draft a {tone} reply for the recipient to send.

Guidelines:
- Match the tone requested: professional, friendly, or brief
- Acknowledge what the sender wrote
- Address the main points or questions
- Be concise — do not pad with unnecessary content
- Sign off appropriately for the tone

Respond with ONLY the reply text. No preamble, no quotes, no markdown.
Do not include a subject line. Just the email body."""


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


async def summarize_email_with_ai(subject: str, body: str, max_sentences: int) -> str:
    """Send email to Groq, return a short summary. Cached by content + sentence count."""
    # Cache key includes max_sentences (different N = different summary)
    cache_input = f"{subject}|{body}|{max_sentences}"
    key = hashlib.md5(cache_input.encode()).hexdigest()
    
    if key in _summarize_cache:
        return _summarize_cache[key]
    
    user_message = f"Subject: {subject}\n\nBody: {body}"
    system_prompt = SUMMARIZE_SYSTEM_PROMPT_TEMPLATE.format(n=max_sentences)
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=300,
        )
    except Exception as e:
        print(f"[AI summarize] Groq call failed: {type(e).__name__}: {e}")
        raise AIServiceError("AI summarization service is temporarily unavailable") from e
    
    summary = response.choices[0].message.content.strip()
    
    # Sanity check: summary shouldn't be empty
    if not summary:
        summary = "Summary unavailable."
    
    _summarize_cache[key] = summary
    return summary


async def extract_actions_with_ai(subject: str, body: str) -> list[str]:
    """Send email to Groq, return list of action items. Cached by content."""
    key = _cache_key(subject, body)
    
    if key in _actions_cache:
        return _actions_cache[key]
    
    user_message = f"Subject: {subject}\n\nBody: {body}"
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": EXTRACT_ACTIONS_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
            max_tokens=500,
        )
    except Exception as e:
        print(f"[AI extract_actions] Groq call failed: {type(e).__name__}: {e}")
        raise AIServiceError("AI action extraction service is temporarily unavailable") from e
    
    raw_output = response.choices[0].message.content.strip()
    
    # Try to parse as JSON
    try:
        actions = json.loads(raw_output)
    except json.JSONDecodeError:
        print(f"[AI extract_actions] Failed to parse JSON: {raw_output!r}")
        actions = []
    
    # Validate: must be a list of strings
    if not isinstance(actions, list):
        actions = []
    actions = [item for item in actions if isinstance(item, str) and item.strip()]
    
    _actions_cache[key] = actions
    return actions


async def suggest_reply_with_ai(subject: str, body: str, tone: str) -> str:
    """Send email to Groq, get a draft reply back. NOT cached — replies should feel fresh."""
    user_message = f"Subject: {subject}\n\nBody: {body}"
    system_prompt = SUGGEST_REPLY_SYSTEM_PROMPT_TEMPLATE.format(tone=tone)
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=500,
        )
    except Exception as e:
        print(f"[AI suggest_reply] Groq call failed: {type(e).__name__}: {e}")
        raise AIServiceError("AI reply suggestion service is temporarily unavailable") from e
    
    reply = response.choices[0].message.content.strip()
    
    if not reply:
        reply = "Reply unavailable. Please try again."
    
    return reply