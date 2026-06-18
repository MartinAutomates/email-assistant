import os
from datetime import datetime
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

from main import app
from database import Base, get_db
from models.db import Email


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

# Create a SEPARATE engine for tests, pointing at the test DB
test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create all tables before tests, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_tables():
    """Wipe all data AND reset SERIAL sequences before each test."""
    from sqlalchemy import text
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        # Reset all SERIAL sequences (e.g., emails_id_seq) to start at 1
        await conn.execute(text("ALTER SEQUENCE emails_id_seq RESTART WITH 1"))
    yield


async def override_get_db():
    """Override the app's get_db to use the test database."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def create_sample_emails(client):
    """Helper: create 3 emails via the API. Used by tests that need pre-existing data."""
    samples = [
        {"subject": "Welcome to our service", "body": "Hi! Thanks for signing up to our wonderful service."},
        {"subject": "Your invoice is ready", "body": "Hello, your monthly invoice is now available for review."},
        {"subject": "URGENT: Server down", "body": "Production server crashed at fourteen hundred. Need help."},
    ]
    for sample in samples:
        await client.post("/emails", json=sample)


# === Tests ===

async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


async def test_read_email_existing(client):
    await create_sample_emails(client)
    response = await client.get("/email/1")
    assert response.status_code == 200
    data = response.json()
    assert data["email_id"] == 1
    assert "subject" in data
    assert "body" in data


async def test_read_email_not_found(client):
    response = await client.get("/email/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_read_email_invalid_id_type(client):
    response = await client.get("/email/banana")
    assert response.status_code == 422


async def test_classify_valid(client):
    response = await client.post("/classify", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. Please review by Friday."
    })
    assert response.status_code == 200
    assert response.json()["category"] == "urgent"


async def test_classify_missing_body(client):
    response = await client.post("/classify", json={"subject": "Hello"})
    assert response.status_code == 422


async def test_classify_whitespace_subject(client):
    response = await client.post("/classify", json={
        "subject": "   ",
        "body": "This is a perfectly valid body."
    })
    assert response.status_code == 400
    assert "whitespace" in response.json()["detail"].lower()


async def test_classify_spam(client):
    response = await client.post("/classify", json={
        "subject": "WIN A FREE IPHONE NOW!!!",
        "body": "Click this link to claim your prize before it expires!"
    })
    assert response.status_code == 400
    assert "spam" in response.json()["detail"].lower()


async def test_summarize_default_sentences(client):
    response = await client.post("/summarize", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. It shows growth across departments. Please review and let me know."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sentence_count"] == 3
    assert data["original_subject"] == "Quarterly report"


async def test_summarize_custom_sentences(client):
    response = await client.post("/summarize", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. It shows growth across departments. Please review and let me know.",
        "max_sentences": 7
    })
    assert response.status_code == 200
    assert response.json()["sentence_count"] == 7


async def test_summarize_body_too_short(client):
    response = await client.post("/summarize", json={
        "subject": "Hi",
        "body": "Short body"
    })
    assert response.status_code == 422


async def test_create_email(client):
    response = await client.post("/emails", json={
        "subject": "Test email from pytest",
        "body": "This is a test email created via pytest to verify the POST endpoint works."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "Test email from pytest"
    assert "email_id" in data
    assert isinstance(data["email_id"], int)
    assert "created_at" in data


async def test_list_emails_default(client):
    await create_sample_emails(client)
    response = await client.get("/emails")
    assert response.status_code == 200
    data = response.json()
    assert "emails" in data
    assert "count" in data
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert isinstance(data["emails"], list)


async def test_list_emails_with_limit(client):
    await create_sample_emails(client)
    response = await client.get("/emails?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert len(data["emails"]) <= 2


async def test_list_emails_with_category_filter(client):
    await create_sample_emails(client)
    response = await client.get("/emails?category=urgent")
    assert response.status_code == 200
    data = response.json()
    assert data["category_filter"] == "urgent"
    # All returned emails (if any) must have the filter applied
    for email in data["emails"]:
        assert email["category"] == "urgent"


async def test_delete_email_existing(client):
    await create_sample_emails(client)
    
    # First confirm it exists
    response = await client.get("/email/1")
    assert response.status_code == 200
    
    # Delete it
    response = await client.delete("/emails/1")
    assert response.status_code == 204
    
    # Confirm it's gone
    response = await client.get("/email/1")
    assert response.status_code == 404


async def test_delete_email_not_found(client):
    response = await client.delete("/emails/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_delete_then_list(client):
    await create_sample_emails(client)
    
    # Start with 3 emails
    response = await client.get("/emails")
    assert response.json()["count"] == 3
    
    # Delete one
    await client.delete("/emails/2")
    
    # Now should have 2
    response = await client.get("/emails")
    assert response.json()["count"] == 2


async def test_register_user(client):
    response = await client.post("/register", json={
        "email": "newuser@example.com",
        "password": "supersecret123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "created_at" in data
    # CRITICAL: password and hash must never appear in response
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client):
    # Register once
    response = await client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "supersecret123"
    })
    assert response.status_code == 201
    
    # Try to register again with same email
    response = await client.post("/register", json={
        "email": "duplicate@example.com",
        "password": "different123"
    })
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


async def test_register_invalid_email(client):
    response = await client.post("/register", json={
        "email": "not-an-email",
        "password": "supersecret123"
    })
    assert response.status_code == 422


async def test_register_short_password(client):
    response = await client.post("/register", json={
        "email": "valid@example.com",
        "password": "abc"
    })
    assert response.status_code == 422