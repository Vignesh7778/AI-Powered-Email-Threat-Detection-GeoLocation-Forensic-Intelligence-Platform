from fastapi.testclient import TestClient
from app.main import app
from app.services.forensics import forensics
from app.services.ml import ml
from app.services.orchestrator import Orchestrator, PipelineRepository


app.state.orchestrator = Orchestrator(PipelineRepository(), forensic_client=forensics, ml_client=ml)
client = TestClient(app)


def submission(submission_id: str, attachment: bool = False) -> dict:
    attachments = []
    if attachment:
        attachments.append({"filename": "invoice.xlsm", "content_type": "application/vnd.ms-excel.sheet.macroEnabled.12", "sha256": "a" * 64, "size_bytes": 1234, "storage_ref": "store://invoice.xlsm"})
    return {
        "submission_id": submission_id,
        "received_at": "2026-08-28T10:15:00Z",
        "raw_headers": """From: Finance Desk <accounts@aicte-finance.co>\nReturn-Path: <reply@relay-mail.co>\nAuthentication-Results: mx.example; spf=fail; dkim=none; dmarc=fail\nReceived: from vpn-relay.example (vpn-relay.example [45.83.64.12]) by mx.example with ESMTP;\n""",
        "raw_body": {"text_plain": "Urgent: please update the vendor banking details today. CEO approval is required.", "text_html": "<a href='https://bit.ly/verify-account'>Verify your account</a>"},
        "attachments": attachments,
        "source_context": {"ingested_via": "upload", "tenant_id": "tenant-1", "mailbox": "finance@aicte.org"},
    }


def test_sync_analysis_returns_assessment_and_evidence():
    response = client.post("/internal/analyze", json=submission("submission-sync"))
    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] in {"high", "critical"}
    assert body["classification"] in {"bec_fraud", "phishing", "impersonation", "suspicious"}
    assert body["auth_results"]["dmarc"] == "fail"
    assert body["domain_intel"]["lookalike_of"] == "aicte.org"
    assert body["processing_mode"] == "sync"
    evidence = client.get("/internal/evidence/submission-sync")
    assert evidence.status_code == 200
    assert {item["action"] for item in evidence.json()} >= {"parsed_headers", "traced_origin", "aggregated_assessment"}


def test_sandboxable_attachment_uses_async_contract_and_persists_result():
    response = client.post("/internal/analyze", json=submission("submission-async", attachment=True))
    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    status_response = client.get("/internal/analysis/submission-async")
    assert status_response.status_code == 200
    record = status_response.json()
    assert record["status"] == "complete"
    assert record["assessment"]["processing_mode"] == "async"


def test_unknown_analysis_returns_404():
    response = client.get("/internal/analysis/missing")
    assert response.status_code == 404
