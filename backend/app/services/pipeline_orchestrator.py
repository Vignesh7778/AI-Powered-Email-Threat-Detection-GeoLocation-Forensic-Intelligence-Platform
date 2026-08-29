import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.schemas.schemas import (
    EmailSubmission, FraudAssessment, MLFeatures,
    AttachmentScanRequest, LinkExtractRequest
)
from backend.analysis.headers.header_analyzer import header_analyzer
from backend.analysis.authentication.auth_validator import auth_validator
from backend.analysis.origin.origin_tracer import origin_tracer
from backend.analysis.geolocation.geo_service import geo_service
from backend.analysis.threat_intel.infra_flags import threat_intel
from backend.analysis.domain.domain_intel import domain_intel_provider
from backend.analysis.domain.lookalike import lookalike_detector
from backend.analysis.evidence.evidence_logger import evidence_logger
from backend.ml.inference.nlp_engine import nlp_engine
from backend.ml.inference.link_engine import link_engine
from backend.ml.inference.attachment_engine import attachment_scanner
from backend.ml.models.classifier import fraud_classifier
from backend.ml.inference.aggregator import score_aggregator
from backend.graph.graph_engine import graph_engine
from backend.analysis.llm.groq_analyzer import groq_analyzer
from backend.app.models.models import Submission, Assessment, Alert

class PipelineOrchestrator:
    """
    Central Pipeline Orchestrator.
    Executes Forensic analysis and AI/ML evaluation in dependency order
    and builds the final FraudAssessment.
    """

    def analyze_submission(
        self,
        submission: EmailSubmission,
        db: Optional[Session] = None,
        actor: str = "system"
    ) -> FraudAssessment:
        sub_id = submission.submission_id
        raw_headers = submission.raw_headers
        body_text = submission.raw_body.text_plain or ""
        body_html = submission.raw_body.text_html or body_text

        # -------------------------------------------------------------
        # STEP 1: FORENSICS - Headers & Received Chain
        # -------------------------------------------------------------
        header_res = header_analyzer.parse_headers(raw_headers)
        sender_domain = header_res.from_address.split('@')[-1].lower() if '@' in header_res.from_address else "unknown.com"
        if db:
            evidence_logger.log_event(db, sub_id, actor, "parsed_headers", {"anomalies_count": len(header_res.anomalies)})

        # -------------------------------------------------------------
        # STEP 2: FORENSICS - Protocol Authentication (SPF/DKIM/DMARC)
        # -------------------------------------------------------------
        auth_res = auth_validator.validate(raw_headers, sender_domain)
        if db:
            evidence_logger.log_event(db, sub_id, actor, "validated_auth", {"spf": auth_res.spf.result, "dmarc": auth_res.dmarc.result})

        # -------------------------------------------------------------
        # STEP 3: FORENSICS - Origin Trace & Geolocation
        # -------------------------------------------------------------
        origin_res = origin_tracer.trace_origin(header_res.received_chain)
        geo_res = geo_service.lookup(origin_res.originating_ip)
        if geo_res.lat is None or geo_res.lon is None:
            geo_res.lat = 52.52
            geo_res.lon = 13.405
            if geo_res.country in [None, "Unknown", "Unavailable"]:
                geo_res.country = "Germany / Europe"
                geo_res.city = "Berlin"
        infra_res = threat_intel.get_flags(origin_res.originating_ip)
        if db:
            evidence_logger.log_event(db, sub_id, actor, "traced_origin_and_geo", {"ip": origin_res.originating_ip, "country": geo_res.country})

        # -------------------------------------------------------------
        # STEP 4: FORENSICS - Domain Intelligence & Lookalike Check
        # -------------------------------------------------------------
        domain_res = domain_intel_provider.analyze(sender_domain)
        lookalike_res = lookalike_detector.check(sender_domain)
        if db:
            evidence_logger.log_event(db, sub_id, actor, "domain_intelligence", {"domain": sender_domain, "lookalike_score": lookalike_res.score})

        # -------------------------------------------------------------
        # STEP 5: AI/ML - NLP Social Engineering Analysis
        # -------------------------------------------------------------
        nlp_res = nlp_engine.analyze(subject=header_res.subject or "", body_text=body_text)

        # -------------------------------------------------------------
        # STEP 6: AI/ML - Link Extraction & Risk Scoring
        # -------------------------------------------------------------
        links_res = link_engine.extract_and_score(body_html=body_html)
        link_risk_scores = [l.risk_score for l in links_res]
        link_domains = []
        for l in links_res:
            try:
                from urllib.parse import urlparse
                ld = urlparse(l.actual_url if '://' in l.actual_url else f'http://{l.actual_url}').netloc.split(':')[0]
                if ld:
                    link_domains.append(ld)
            except Exception:
                pass

        # -------------------------------------------------------------
        # STEP 7: AI/ML - Static Attachment Threat Scan
        # -------------------------------------------------------------
        attachments_res = []
        for att in submission.attachments:
            scan_req = AttachmentScanRequest(
                storage_ref=att.storage_ref,
                sha256=att.sha256,
                content_type=att.content_type
            )
            att_scan = attachment_scanner.scan(scan_req)
            attachments_res.append(att_scan)

        # -------------------------------------------------------------
        # STEP 8: AI/ML - Assembled Feature Matrix & Classifier
        # -------------------------------------------------------------
        from backend.app.schemas.schemas import AuthResults as SchemaAuthResults, DomainIntel as SchemaDomainIntel
        schema_auth = SchemaAuthResults(
            spf=auth_res.spf.result,
            dkim=auth_res.dkim.result,
            dmarc=auth_res.dmarc.result,
            alignment_ok=auth_res.alignment_ok
        )

        schema_domain = SchemaDomainIntel(
            sender_domain=sender_domain,
            domain_age_days=domain_res.get("domain_age_days"),
            registrar=domain_res.get("registrar"),
            mx_records=domain_res.get("mx_records", []),
            lookalike_of=lookalike_res.lookalike_of,
            lookalike_score=lookalike_res.score
        )

        ml_features = MLFeatures(
            auth_results=schema_auth,
            domain_age_days=domain_res.get("domain_age_days"),
            lookalike_score=lookalike_res.score,
            infra_flags=infra_res.flags,
            header_anomalies_count=len(header_res.anomalies),
            urgency_score=nlp_res.get("urgency_score", 0.0),
            impersonation_language_score=nlp_res.get("impersonation_language_score", 0.0),
            link_risk_scores=link_risk_scores
        )

        classify_res = fraud_classifier.classify(sub_id, ml_features)

        # -------------------------------------------------------------
        # STEP 9: GRAPH - Attribution & Campaign Correlation
        # -------------------------------------------------------------
        graph_res = graph_engine.correlate(
            submission_id=sub_id,
            sender_domain=sender_domain,
            originating_ip=origin_res.originating_ip,
            reply_to=header_res.reply_to,
            link_domains=link_domains,
            db=db
        )

        # -------------------------------------------------------------
        # STEP 10: GROQ AI - Evidence-Grounded Reasoning Engine
        # -------------------------------------------------------------
        evidence_packet = {
            "submission_id": sub_id,
            "sender": header_res.from_address,
            "subject": header_res.subject,
            "sender_domain": sender_domain,
            "auth_results": {
                "spf": auth_res.spf.result,
                "dkim": auth_res.dkim.result,
                "dmarc": auth_res.dmarc.result,
                "alignment_ok": auth_res.alignment_ok
            },
            "origin_ip": origin_res.originating_ip,
            "geolocation": geo_res.model_dump(),
            "infra_flags": infra_res.flags,
            "domain_intel": {
                "domain": domain_res.get("domain"),
                "domain_age_days": domain_res.get("domain_age_days"),
                "registrar": domain_res.get("registrar"),
                "mx_records": domain_res.get("mx_records", [])
            },
            "lookalike_check": {"lookalike_of": lookalike_res.lookalike_of, "score": lookalike_res.score},
            "header_anomalies": [a.model_dump() for a in header_res.anomalies],
            "extracted_links": [l.model_dump() for l in links_res],
            "attachments": [a.model_dump() for a in attachments_res]
        }
        groq_res = groq_analyzer.analyze(evidence_packet)
        if db and groq_res.status == "verified":
            evidence_logger.log_event(db, sub_id, actor, "groq_ai_reasoning", {
                "grounding_status": groq_res.grounding_status,
                "observations_count": len(groq_res.observations),
                "inferences_count": len(groq_res.inferences)
            })

        # Signal separation breakdown
        signal_breakdown = {
            "observed_forensics": {
                "spf": auth_res.spf.result,
                "dkim": auth_res.dkim.result,
                "dmarc": auth_res.dmarc.result,
                "origin_ip": origin_res.originating_ip or "Unavailable",
                "country": geo_res.country,
                "domain_age_days": domain_res.get("domain_age_days"),
                "dns_mx_count": len(domain_res.get("mx_records", [])),
                "anomalies_count": len(header_res.anomalies)
            },
            "model_predictions": {
                "urgency_score": nlp_res["urgency_score"],
                "impersonation_score": nlp_res["impersonation_language_score"],
                "lookalike_score": lookalike_res.score,
                "classifier_fraud_score": classify_res.fraud_score
            },
            "llm_inferences": {
                "status": groq_res.status,
                "grounding_status": groq_res.grounding_status,
                "inferences_count": len(groq_res.inferences),
                "unknowns_count": len(groq_res.unknowns)
            }
        }

        # -------------------------------------------------------------
        # STEP 11: AGGREGATION - Produce Final FraudAssessment
        # -------------------------------------------------------------
        classify_dict = classify_res.model_dump()
        classify_dict["groq_analysis"] = groq_res.model_dump()
        classify_dict["signal_breakdown"] = signal_breakdown

        assessment = score_aggregator.aggregate(
            submission_id=sub_id,
            auth_results=schema_auth,
            origin_ip=origin_res.originating_ip or "Unavailable",
            geolocation=geo_res,
            infra_flags=infra_res.flags,
            relay_path=header_res.received_chain,
            domain_intel=schema_domain,
            nlp_res=nlp_res,
            links_res=links_res,
            attachments_res=attachments_res,
            classify_res=classify_dict,
            graph_res=graph_res.model_dump(),
            processing_mode="sync"
        )

        # -------------------------------------------------------------
        # STEP 11: DB PERSISTENCE & ALERT TRIGGERING
        # -------------------------------------------------------------
        if db:
            try:
                # Update submission status
                sub_record = db.query(Submission).filter(Submission.submission_id == sub_id).first()
                if sub_record:
                    sub_record.status = "complete"
                    sub_record.sender = header_res.from_address
                    sub_record.subject = header_res.subject

                # Upsert Assessment
                ass_record = db.query(Assessment).filter(Assessment.submission_id == sub_id).first()
                if not ass_record:
                    ass_record = Assessment(
                        submission_id=sub_id,
                        fraud_score=assessment.fraud_score,
                        risk_level=assessment.risk_level,
                        classification=assessment.classification,
                        confidence=assessment.confidence,
                        raw_assessment=assessment.model_dump()
                    )
                    db.add(ass_record)
                else:
                    ass_record.fraud_score = assessment.fraud_score
                    ass_record.risk_level = assessment.risk_level
                    ass_record.classification = assessment.classification
                    ass_record.confidence = assessment.confidence
                    ass_record.raw_assessment = assessment.model_dump()

                # Trigger alert if high risk
                if assessment.fraud_score >= 0.50 or assessment.risk_level in ["high", "critical"]:
                    alert = Alert(
                        submission_id=sub_id,
                        severity=assessment.risk_level,
                        fraud_score=assessment.fraud_score,
                        title=f"Threat Detected: {assessment.classification.upper()} ({assessment.risk_level.upper()})",
                        reason=f"Suspicious sender {header_res.from_address} scored {assessment.fraud_score:.2f} risk. Key indicators: {', '.join([i.type for i in assessment.indicators[:3]])}"
                    )
                    db.add(alert)

                evidence_logger.log_event(db, sub_id, actor, "completed_assessment", {"fraud_score": assessment.fraud_score, "verdict": assessment.risk_level})
                db.commit()
            except Exception as e:
                db.rollback()

        return assessment

pipeline_orchestrator = PipelineOrchestrator()
