from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# Tests for GET /
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


# Tests for GET /email/{email_id}
def test_read_email_existing():
    response = client.get("/email/2")
    assert response.status_code == 200
    assert response.json() == {"email_id": 2, "subject": "Your invoice is ready"}


def test_read_email_not_found():
    response = client.get("/email/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "Email with id 99 not found"}


def test_read_email_invalid_id_type():
    response = client.get("/email/banana")
    assert response.status_code == 422


# Tests for POST /classify
def test_classify_valid():
    response = client.post("/classify", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. Please review by Friday."
    })
    assert response.status_code == 200
    assert response.json()["category"] == "urgent"


def test_classify_missing_body():
    response = client.post("/classify", json={
        "subject": "Hello"
    })
    assert response.status_code == 422


def test_classify_whitespace_subject():
    response = client.post("/classify", json={
        "subject": "   ",
        "body": "This is a perfectly valid body."
    })
    assert response.status_code == 400
    assert "whitespace" in response.json()["detail"].lower()


def test_classify_spam():
    response = client.post("/classify", json={
        "subject": "WIN A FREE IPHONE NOW!!!",
        "body": "Click this link to claim your prize before it expires!"
    })
    assert response.status_code == 400
    assert "spam" in response.json()["detail"].lower()


# Tests for POST /summarize
def test_summarize_default_sentences():
    response = client.post("/summarize", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. It shows growth across departments. Please review and let me know."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sentence_count"] == 3
    assert data["original_subject"] == "Quarterly report"


def test_summarize_custom_sentences():
    response = client.post("/summarize", json={
        "subject": "Quarterly report",
        "body": "Hi team, attached is the Q2 report. It shows growth across departments. Please review and let me know.",
        "max_sentences": 7
    })
    assert response.status_code == 200
    assert response.json()["sentence_count"] == 7


def test_summarize_body_too_short():
    response = client.post("/summarize", json={
        "subject": "Hi",
        "body": "Short body"
    })
    assert response.status_code == 422
    