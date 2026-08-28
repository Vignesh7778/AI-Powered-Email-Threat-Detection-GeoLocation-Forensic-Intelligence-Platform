from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_attachment_scan_macro():
    payload = {
        "storage_ref": "s3://inbox-attachments/invoice_macro.xlsm",
        "sha256": "8a329d91f2c282f185f140e90c9b05d5f35b9c02ff436d4b47e2b7a9bf9a4c8a",
        "content_type": "application/vnd.ms-excel.sheet.macroEnabled.12"
    }
    response = client.post("/ml/attachments/scan", json=payload)
    assert response.status_code in [200, 202]
    data = response.json()
    assert data["malware_score"] > 0.6
    assert "macro" in data["detected_type"]

def test_attachment_scan_benign_pdf():
    payload = {
        "storage_ref": "s3://inbox-attachments/annual_report.pdf",
        "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "content_type": "application/pdf"
    }
    response = client.post("/ml/attachments/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["malware_score"] <= 0.2
    assert data["detected_type"] == "none"

