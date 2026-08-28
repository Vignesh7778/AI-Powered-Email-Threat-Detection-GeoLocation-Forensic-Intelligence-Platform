import pytest
import os
import sys

# Ensure backend root is on path
PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from backend.analysis.headers.header_analyzer import header_analyzer
from backend.analysis.authentication.auth_validator import auth_validator
from backend.analysis.origin.origin_tracer import origin_tracer
from backend.analysis.geolocation.geo_service import geo_service
from backend.analysis.domain.domain_intel import domain_intel_provider
from backend.analysis.domain.lookalike import lookalike_detector
from backend.analysis.threat_intel.infra_flags import threat_intel
from backend.ml.inference.nlp_engine import nlp_engine
from backend.ml.inference.link_engine import link_engine
from backend.ml.inference.attachment_engine import attachment_scanner
from backend.ml.models.classifier import fraud_classifier
from backend.ml.inference.aggregator import score_aggregator
from backend.graph.graph_engine import graph_engine
from backend.reports.report_generator import report_generator
from backend.app.schemas.schemas import (
    EmailSubmission, RawBody, SourceContext, MLFeatures,
    AuthResults, AttachmentScanRequest
)
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator

SAMPLE_RAW_HEADERS = '''Received: from unknown-host.net (unknown-host.net [185.220.101.5])
    by gateway.company.org with SMTP id PHISH999;
    Fri, 28 Aug 2026 09:15:00 +0000
Authentication-Results: gateway.company.org; spf=fail smtp.mailfrom=secure-paypal-login.xyz; dkim=none; dmarc=fail
From: "PayPal Account Security" <service@secure-paypal-login.xyz>
Reply-To: security-alert@secure-paypal-login.xyz
To: victim@company.org
Subject: URGENT: Your PayPal Account Has Been Suspended!
Message-ID: <phish-9912@attacker.net>
Return-Path: <bounce@secure-paypal-login.xyz>
Date: Fri, 28 Aug 2026 09:15:00 +0000
'''

def test_header_analyzer():
    res = header_analyzer.parse_headers(SAMPLE_RAW_HEADERS)
    assert res.from_address == "service@secure-paypal-login.xyz"
    assert res.return_path == "bounce@secure-paypal-login.xyz"
    assert len(res.received_chain) >= 1
    assert res.received_chain[0].ip == "185.220.101.5"

def test_auth_validator():
    res = auth_validator.validate(SAMPLE_RAW_HEADERS, "secure-paypal-login.xyz")
    assert res.spf.result in ["fail", "softfail", "none"]
    assert res.dmarc.result in ["fail", "none"]

def test_origin_tracer():
    headers_res = header_analyzer.parse_headers(SAMPLE_RAW_HEADERS)
    res = origin_tracer.trace_origin(headers_res.received_chain)
    assert res.originating_ip == "185.220.101.5"
    assert res.confidence > 0.5

def test_geo_service():
    res = geo_service.lookup("185.220.101.5")
    assert res.country is not None
    assert res.lat is not None
    assert res.lon is not None

def test_threat_intel():
    res = threat_intel.get_flags("185.220.101.5")
    assert isinstance(res.flags, list)
    assert len(res.source_lists) >= 1

def test_domain_lookalike():
    res = lookalike_detector.check("paypa1.com")
    assert res.lookalike_of == "paypal.com"
    assert res.score >= 0.8

def test_nlp_engine():
    subject = "URGENT: Final Notice - Immediate Action Required"
    body = "Your account will be suspended within 24 hours. Please update your credentials immediately."
    res = nlp_engine.analyze(subject, body)
    assert res["urgency_score"] > 0.5
    assert len(res["detected_patterns"]) > 0

def test_link_engine():
    html = '<p>Click <a href="http://198.51.100.24/login.php">here to verify</a> or visit http://bit.ly/fake-update</p>'
    links = link_engine.extract_and_score(html)
    assert len(links) >= 1
    assert any(l.obfuscated for l in links)

def test_attachment_scanner():
    req = AttachmentScanRequest(
        storage_ref="/data/invoice_update.xlsm",
        sha256="44d88612fea8a8f36de82e1278abb02f",
        content_type="application/vnd.ms-excel.sheet.macroEnabled.12"
    )
    res = attachment_scanner.scan(req)
    assert res.malware_score >= 0.8

def test_classifier():
    features = MLFeatures(
        auth_results=AuthResults(spf="fail", dkim="none", dmarc="fail", alignment_ok=False),
        domain_age_days=3,
        lookalike_score=0.92,
        infra_flags=["vpn", "tor"],
        header_anomalies_count=2,
        urgency_score=0.85,
        impersonation_language_score=0.78,
        link_risk_scores=[0.90]
    )
    res = fraud_classifier.classify("test-sub-01", features)
    assert res.fraud_score >= 0.70
    assert res.classification in ["phishing", "bec_fraud", "impersonation", "suspicious"]
    assert len(res.feature_importance) > 0

def test_graph_correlate():
    res = graph_engine.correlate(
        submission_id="test-sub-01",
        sender_domain="paypa1.com",
        originating_ip="203.0.113.42",
        reply_to="executive.desk2026@gmail.com",
        link_domains=["wire-remittance.net"]
    )
    assert res.linked_campaign_id is not None
    assert res.cluster_confidence > 0.5

def test_campaign_graph():
    res = graph_engine.get_campaign_graph("camp-bec-finance-2026")
    assert len(res.nodes) > 0
    assert len(res.edges) > 0

def test_end_to_end_pipeline():
    sub = EmailSubmission(
        submission_id="test-e2e-001",
        received_at="2026-08-28T10:00:00Z",
        raw_headers=SAMPLE_RAW_HEADERS,
        raw_body=RawBody(
            text_plain="Your account will be suspended within 24 hours. Click here to verify credentials.",
            text_html="<p>Your account will be suspended. <a href='http://198.51.100.24/login'>Click here</a></p>"
        ),
        attachments=[],
        source_context=SourceContext(ingested_via="upload", tenant_id="tenant-test")
    )
    assessment = pipeline_orchestrator.analyze_submission(sub, db=None, actor="test_runner")
    assert assessment.fraud_score >= 0.5
    assert assessment.risk_level in ["high", "critical"]
    assert assessment.origin.originating_ip == "185.220.101.5"

def test_report_generation():
    sub = EmailSubmission(
        submission_id="test-rep-001",
        received_at="2026-08-28T10:00:00Z",
        raw_headers=SAMPLE_RAW_HEADERS,
        raw_body=RawBody(text_plain="Test text", text_html="<p>Test</p>"),
        attachments=[],
        source_context=SourceContext(ingested_via="upload", tenant_id="tenant-test")
    )
    assessment = pipeline_orchestrator.analyze_submission(sub, db=None, actor="test_runner")
    sub_meta = {
        "submission_id": "test-rep-001",
        "sender": "service@secure-paypal-login.xyz",
        "subject": "URGENT: Suspended",
        "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "received_at": "2026-08-28T10:00:00Z",
        "source": "upload"
    }
    json_rep = report_generator.generate_json_report(assessment, sub_meta, [])
    assert json_rep["fraud_assessment"]["fraud_score"] == assessment.fraud_score
    
    pdf_rep = report_generator.generate_pdf_report(assessment, sub_meta, [])
    assert len(pdf_rep) > 1000
    assert pdf_rep.startswith(b"%PDF")
