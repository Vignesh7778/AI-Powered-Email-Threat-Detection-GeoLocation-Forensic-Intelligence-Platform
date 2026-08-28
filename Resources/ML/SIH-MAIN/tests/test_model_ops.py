from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_models_health():
    response = client.get("/ml/models/health")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 3
    model_names = [m["name"] for m in data["models"]]
    assert "classifier" in model_names
    assert "nlp_analyzer" in model_names

def test_models_feedback():
    payload = {
        "submission_id": "7fae2981-b51c-43f1-b939-b9c1e7a5d120",
        "analyst_verdict": "phishing",
        "analyst_id": "analyst-sec-01"
    }
    response = client.post("/ml/models/feedback", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued_for_retraining"

