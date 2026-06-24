import asyncio
import httpx


async def test_stream():
    url = "http://127.0.0.1:8000/suggest-reply-stream"
    payload = {
        "subject": "Can we move the meeting?",
        "body": "Hi, I have a conflict at 2pm tomorrow. Can we reschedule to 4pm or Friday?",
        "tone": "professional",
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream("POST", url, json=payload) as response:
            print(f"Status: {response.status_code}\n")
            print("Stream (watch words appear):")
            print("-" * 50)
            async for chunk in response.aiter_text():
                print(chunk, end="", flush=True)
            print("\n" + "-" * 50)
            print("Done.")


asyncio.run(test_stream())