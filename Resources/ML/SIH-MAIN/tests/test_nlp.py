from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_nlp_analyze_bec_urgent():
    payload = {
        "subject": "URGENT: Executive Wire Transfer Required Immediately",
        "body_text": "Hello, this is CEO. Are you at your desk? Please initiate an urgent wire transfer to the new vendor account within 24 hours. Keep this strictly confidential."
    }
    response = client.post("/ml/nlp/analyze-content", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "urgency_score" in data
    assert "impersonation_language_score" in data
    assert "detected_patterns" in data
    assert data["urgency_score"] > 0.5
    assert data["impersonation_language_score"] > 0.5
    assert len(data["detected_patterns"]) > 0

    # Verify excerpt_span points to valid slices of original body_text
    for pattern in data["detected_patterns"]:
        start, end = pattern["excerpt_span"]
        assert 0 <= start < end <= len(payload["body_text"])
        assert pattern["confidence"] >= 0.0

def test_nlp_analyze_benign():
    payload = {
        "subject": "Team Lunch on Friday",
        "body_text": "Hey team, just checking if anyone wants to grab lunch together at the cafeteria on Friday noon."
    }
    response = client.post("/ml/nlp/analyze-content", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["urgency_score"] <= 0.3
    assert data["impersonation_language_score"] <= 0.3

