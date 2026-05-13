import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Tests for GET /
async def test_read_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# Tests for GET /email/{email_id}
async def test_read_email_existing(client):
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


# Tests for POST /classify
async def test_classify_valid(client):
    response = await client.post("/classify", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. Please review by Friday."
    })
    assert response.status_code == 200
    assert response.json()["category"] == "urgent"


async def test_classify_missing_body(client):
    response = await client.post("/classify", json={
        "subject": "Hello"
    })
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


# Tests for POST /summarize
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


# Tests for POST /emails (new!)
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
    response = await client.get("/emails")
    assert response.status_code == 200
    data = response.json()
    assert "emails" in data
    assert "count" in data
    assert data["skip"] == 0
    assert data["limit"] == 10
    assert isinstance(data["emails"], list)


async def test_list_emails_with_limit(client):
    response = await client.get("/emails?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 2
    assert len(data["emails"]) <= 2


async def test_list_emails_with_category_filter(client):
    response = await client.get("/emails?category=urgent")
    assert response.status_code == 200
    data = response.json()
    assert data["category_filter"] == "urgent"
    # Every returned email should have category 'urgent'
    for email in data["emails"]:
        assert email["category"] == "urgent"