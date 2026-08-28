from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings
from app.schemas import AnalysisRecord, AnalyzeAccepted, Attribution, EmailSubmission, FraudAssessment, Indicator
from app.services.clients import ForensicsHttpClient, MlHttpClient
from app.services.evidence import evidence_ledger
from app.services.forensics import forensics
from app.services.ml import ml


class PipelineRepository:
    def __init__(self) -> None:
        self.records: dict[str, AnalysisRecord] = {}
        self.history: list[FraudAssessment] = []

    def save(self, record: AnalysisRecord) -> None:
        self.records[record.submission_id] = record

    def get(self, submission_id: str) -> Optional[AnalysisRecord]:
        return self.records.get(submission_id)


class Orchestrator:
    def __init__(self, repository: PipelineRepository, forensic_client=None, ml_client=None) -> None:
        self.repository = repository
        self.forensics = forensic_client or ForensicsHttpClient(settings.forensic_api)
        self.ml = ml_client or MlHttpClient(settings.ml_api)

    def analyze(self, submission: EmailSubmission) -> FraudAssessment | AnalyzeAccepted:
        assessment = self._run(submission, processing_mode="sync")
        if assessment.processing_mode == "async":
            return AnalyzeAccepted(submission_id=submission.submission_id)
        return assessment

    def _run(self, submission: EmailSubmission, processing_mode: str) -> FraudAssessment:
        self._record(submission.submission_id, "parsed_headers")
        fields, relay_path, anomalies = self.forensics.parse_headers(submission.raw_headers)
        auth = self.forensics.validate_authentication(submission.raw_headers)
        self._record(submission.submission_id, "validated_authentication")
        origin = self.forensics.build_origin(relay_path)
        self._record(submission.submission_id, "traced_origin", originating_ip=origin.originating_ip)
        self._record(submission.submission_id, "geo_lookup", country=origin.geolocation.country)
        sender_domain = self.forensics.sender_domain(fields["from_address"])
        domain = self.forensics.domain_intelligence(sender_domain, settings.protected_domains)
        self._record(submission.submission_id, "domain_lookup", sender_domain=sender_domain)

        urgency, impersonation, nlp_indicators = self.ml.nlp(fields.get("subject", ""), submission.raw_body.text_plain or "")
        link_scores = self.ml.links(submission.raw_body.text_html or submission.raw_body.text_plain or "")
        attachment_indicators: list[Indicator] = []
        for attachment in submission.attachments:
            sandboxing, malware_score, detected = self.ml.scan_attachment(attachment)
            processing_mode = "async" if sandboxing else processing_mode
            self._record(submission.submission_id, "scanned_attachment", filename=attachment.filename)
            if malware_score >= .7:
                attachment_indicators.append(Indicator(type="malicious_attachment", detail=f"{attachment.filename} flagged as {detected}.", weight=.25))

        classification, fraud_score, confidence, classifier_indicators = self.ml.classify(
            auth, domain, origin, urgency, impersonation, link_scores, len(anomalies)
        )
        if attachment_indicators:
            fraud_score = min(.99, round(fraud_score + .08, 2))
        attribution = self._correlate(submission.submission_id, sender_domain, origin.originating_ip, fields.get("reply_to", ""), link_scores, fraud_score)
        indicators = sorted(nlp_indicators + classifier_indicators + attachment_indicators, key=lambda item: item.weight, reverse=True)
        risk_level = "critical" if fraud_score >= .80 else "high" if fraud_score >= .60 else "medium" if fraud_score >= .35 else "low"
        narrative = self._narrative(sender_domain, origin.geolocation.country, auth, domain, risk_level)
        assessment = FraudAssessment(
            submission_id=submission.submission_id,
            analyzed_at=datetime.now(timezone.utc),
            fraud_score=fraud_score,
            risk_level=risk_level,
            classification=classification,
            confidence=confidence,
            model_version=self.ml.model_version,
            auth_results=auth,
            origin=origin,
            relay_path=relay_path,
            domain_intel=domain,
            indicators=indicators,
            attribution=attribution,
            narrative_summary=narrative,
            processing_mode=processing_mode,
            webhook_status="pending" if processing_mode == "async" else "not_applicable",
        )
        self.repository.save(AnalysisRecord(submission_id=submission.submission_id, status="complete", assessment=assessment))
        self.repository.history.append(assessment)
        self._record(submission.submission_id, "aggregated_assessment", risk_level=risk_level)
        return assessment

    def _record(self, submission_id: str, action: str, **metadata: str) -> None:
        evidence_ledger.record(submission_id, action, **metadata)
        if hasattr(self.forensics, "log_evidence"):
            self.forensics.log_evidence(submission_id, action)

    def _correlate(self, submission_id: str, domain: str, ip: str, reply_to: str, links: list, fraud_score: float) -> Attribution:
        if hasattr(self.ml, "correlate"):
            return self.ml.correlate(submission_id, domain, ip, reply_to, links)
        related = [item.submission_id for item in self.repository.history if item.domain_intel.sender_domain == domain or item.origin.originating_ip == ip]
        indicators: list[dict[str, object]] = []
        if related:
            indicators.append({"type": "sender_domain", "value": domain, "seen_in_count": len(related) + 1})
        if links:
            indicators.append({"type": "link_target", "value": links[0].url, "seen_in_count": 1})
        campaign_id = f"campaign-{domain.replace('.', '-')[:36]}" if related or fraud_score >= .8 else None
        confidence = .82 if related else (.55 if campaign_id else .15)
        return Attribution(linked_campaign_id=campaign_id, related_submission_ids=related, cluster_confidence=confidence, shared_indicators=indicators)

    @staticmethod
    def _narrative(domain: str, country: str, auth, domain_intel, risk_level: str) -> str:
        reasons: list[str] = []
        if "fail" in (auth.spf, auth.dkim, auth.dmarc):
            reasons.append("sender authentication failed")
        if domain_intel.lookalike_of:
            reasons.append(f"the domain resembles {domain_intel.lookalike_of}")
        if not reasons:
            reasons.append("the available indicators require routine review")
        return f"This email was sent from infrastructure located in {country}. It is rated {risk_level} risk because {' and '.join(reasons)}."


repository = PipelineRepository()
orchestrator = Orchestrator(repository)
