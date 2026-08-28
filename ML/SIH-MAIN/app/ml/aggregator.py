from datetime import datetime, timezone
from typing import Dict, Any, List
from app.schemas.aggregate import AggregateRequest, FraudAssessment, ScoreBreakdown

class AggregatorEngine:
    """
    Combines Forensics results, ML Classifier output, NLP cues,
    Link risk assessments, and Attachment scan results into a comprehensive FraudAssessment.
    """

    def aggregate(self, req: AggregateRequest) -> FraudAssessment:
        sub_id = req.submission_id
        classify_res = req.classify_result or {}
        forensics_res = req.forensics_results or {}
        nlp_res = req.nlp_result or {}
        links_res = req.links_result or {}
        attachments = req.attachment_results or []

        # 1. Extract sub-scores
        classifier_score = float(classify_res.get("fraud_score", 0.1))
        classification = classify_res.get("classification", "suspicious")
        classifier_conf = float(classify_res.get("confidence", 0.8))

        # Forensic risk heuristic
        forensics_risk = 0.1
        if forensics_res:
            auth = forensics_res.get("auth_results", {})
            if auth.get("dmarc") == "fail" or auth.get("spf") == "fail":
                forensics_risk += 0.4
            if forensics_res.get("domain_age_days", 365) < 30:
                forensics_risk += 0.3
            if forensics_res.get("lookalike_score", 0.0) > 0.6:
                forensics_risk += 0.3
        forensics_risk = round(min(forensics_risk, 1.0), 2)

        # NLP risk
        nlp_urgency = float(nlp_res.get("urgency_score", 0.0))
        nlp_impersonation = float(nlp_res.get("impersonation_language_score", 0.0))
        nlp_risk = round(min(max(nlp_urgency * 0.5 + nlp_impersonation * 0.5, 0.0), 1.0), 2)

        # Link risk
        links_list = links_res.get("links", [])
        if links_list:
            link_scores = [float(l.get("risk_score", 0.0)) for l in links_list]
            link_risk = round(max(link_scores), 2)
        else:
            link_risk = 0.0

        # Attachment risk
        if attachments:
            att_scores = [float(a.get("malware_score", 0.0)) for a in attachments]
            attachment_risk = round(max(att_scores), 2)
        else:
            attachment_risk = 0.0

        # 2. Weighted overall fraud score calculation
        # ML Classifier represents the central unified multi-feature decision (50%),
        # weighted with forensics (20%), NLP (10%), link risk (10%), attachment risk (10%)
        composite_fraud_score = round(
            0.50 * classifier_score +
            0.20 * forensics_risk +
            0.10 * nlp_risk +
            0.10 * link_risk +
            0.10 * attachment_risk,
            2
        )
        composite_fraud_score = min(max(composite_fraud_score, 0.01), 0.99)

        # 3. Determine Risk Level and Verdict
        if composite_fraud_score >= 0.80 or classifier_score >= 0.85 or attachment_risk >= 0.85:
            risk_level = "CRITICAL"
            verdict = "BLOCKED"
        elif composite_fraud_score >= 0.60 or classifier_score >= 0.65:
            risk_level = "HIGH"
            verdict = "REVIEW_REQUIRED"
        elif composite_fraud_score >= 0.35:
            risk_level = "MEDIUM"
            verdict = "SUSPICIOUS"
        else:
            risk_level = "LOW"
            verdict = "PASS"

        # 4. Generate Key Findings & Recommended Actions
        key_findings: List[str] = []
        recommended_actions: List[str] = []

        if classification == "bec_fraud":
            key_findings.append("Identified Business Email Compromise (BEC) patterns targeting financial transactions.")
            recommended_actions.append("Halt any wire transfers or credential changes requested in this thread.")
        elif classification == "phishing":
            key_findings.append("Detected credential harvesting and high-risk URL structures.")
            recommended_actions.append("Block destination domains at network perimeter and purge email from inboxes.")
        elif classification == "impersonation":
            key_findings.append("High lookalike domain similarity and executive impersonation tone.")
            recommended_actions.append("Verify sender identity via out-of-band communication channel.")

        if link_risk >= 0.7:
            key_findings.append(f"Contains high-risk obfuscated links (risk score: {link_risk}).")
            recommended_actions.append("Submit extracted URLs to web filtering and proxy blocklists.")

        if attachment_risk >= 0.7:
            key_findings.append(f"Attachment flagged with elevated malware probability ({attachment_risk}).")
            recommended_actions.append("Quarantine attachment and initiate deeper dynamic sandbox analysis.")

        if not key_findings:
            key_findings.append("No critical indicators of malicious intent or fraudulent identity detected.")
            recommended_actions.append("Deliver email to recipient mailbox normally.")

        return FraudAssessment(
            submission_id=sub_id,
            verdict=verdict,
            fraud_score=composite_fraud_score,
            risk_level=risk_level,
            primary_threat=classification,
            confidence=classifier_conf,
            score_breakdown=ScoreBreakdown(
                forensics_risk=forensics_risk,
                nlp_risk=nlp_risk,
                link_risk=link_risk,
                attachment_risk=attachment_risk,
                classifier_score=classifier_score
            ),
            key_findings=key_findings,
            recommended_actions=recommended_actions,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            pipeline_version="v4.1.0"
        )

aggregator_engine = AggregatorEngine()

