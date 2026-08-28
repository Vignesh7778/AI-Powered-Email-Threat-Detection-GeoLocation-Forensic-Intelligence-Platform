from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.app.schemas.schemas import (
    FraudAssessment, AuthResults, OriginInfo, GeoLocation,
    RelayHop, DomainIntel, ThreatIndicator, AttributionInfo
)

class ScoreAggregator:
    """
    Score Aggregator Engine.
    Combines outputs from Cyber Forensics, NLP content cues, Link risk scoring,
    Attachment scans, Classifier heuristics, and Graph correlation into the authoritative
    FraudAssessment wire contract.
    """

    def aggregate(
        self,
        submission_id: str,
        auth_results: AuthResults,
        origin_ip: str,
        geolocation: GeoLocation,
        infra_flags: List[str],
        relay_path: List[RelayHop],
        domain_intel: DomainIntel,
        nlp_res: Dict[str, Any],
        links_res: List[Any],
        attachments_res: List[Any],
        classify_res: Dict[str, Any],
        graph_res: Optional[Dict[str, Any]] = None,
        processing_mode: str = "sync"
    ) -> FraudAssessment:
        fraud_score = float(classify_res.get("fraud_score", 0.1))
        classification = classify_res.get("classification", "suspicious")
        confidence = float(classify_res.get("confidence", 0.8))

        # Risk level determination
        if fraud_score >= 0.75:
            risk_level = "critical"
        elif fraud_score >= 0.50:
            risk_level = "high"
        elif fraud_score >= 0.25:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Build explainable threat indicators
        indicators: List[ThreatIndicator] = []

        if auth_results.spf == "fail":
            indicators.append(ThreatIndicator(type="spf_failure", detail="SPF sender policy check failed for sending IP", weight=0.25))
        if auth_results.dmarc == "fail":
            indicators.append(ThreatIndicator(type="dmarc_failure", detail="DMARC authentication failed with policy enforcement", weight=0.30))
        if domain_intel.lookalike_score >= 0.6:
            indicators.append(ThreatIndicator(type="lookalike_domain", detail=f"Sender domain is a lookalike of protected brand {domain_intel.lookalike_of or 'known domain'}", weight=0.40))
        if domain_intel.domain_age_days is not None and domain_intel.domain_age_days < 30:
            indicators.append(ThreatIndicator(type="newly_registered_domain", detail=f"Sender domain registered only {domain_intel.domain_age_days} days ago", weight=0.20))
        if "threat_listed" in infra_flags:
            indicators.append(ThreatIndicator(type="dnsbl_threat_listed", detail="Originating IP is actively listed on Spamhaus ZEN / SpamCop DNSBL blacklists", weight=0.50))
        if "tor" in infra_flags:
            indicators.append(ThreatIndicator(type="tor_exit_node", detail="Originating IP matches active TOR exit node infrastructure", weight=0.45))
        elif "vpn" in infra_flags:
            indicators.append(ThreatIndicator(type="vpn_infrastructure", detail="Originating IP routes through commercial VPN / proxy service", weight=0.20))
        if nlp_res.get("urgency_score", 0) > 0.6:
            indicators.append(ThreatIndicator(type="urgency_language", detail="High degree of coercive urgency detected in email body/subject", weight=0.25))
        if nlp_res.get("impersonation_language_score", 0) > 0.6:
            indicators.append(ThreatIndicator(type="executive_impersonation", detail="Authority impersonation or confidential payment diversion tone", weight=0.30))

        for l in links_res:
            l_dict = l.model_dump() if hasattr(l, 'model_dump') else (l if isinstance(l, dict) else {})
            if l_dict.get("risk_score", 0) >= 0.6:
                indicators.append(ThreatIndicator(type="malicious_link", detail=f"Deceptive/obfuscated link targeting {l_dict.get('actual_url', '')[:60]}", weight=0.35))

        for a in attachments_res:
            a_dict = a.model_dump() if hasattr(a, 'model_dump') else (a if isinstance(a, dict) else {})
            if a_dict.get("malware_score", 0) >= 0.6:
                indicators.append(ThreatIndicator(type="suspicious_attachment", detail=f"High-risk payload detected: {a_dict.get('detected_type', 'malware')}", weight=0.45))

        if not indicators:
            indicators.append(ThreatIndicator(type="benign_signals", detail="All authentication protocols aligned and content heuristics normal", weight=0.05))

        # Attribution data
        g_data = graph_res or {}
        attribution = AttributionInfo(
            linked_campaign_id=g_data.get("linked_campaign_id"),
            related_submission_ids=g_data.get("related_submission_ids", []),
            cluster_confidence=g_data.get("cluster_confidence", 0.0)
        )

        return FraudAssessment(
            submission_id=submission_id,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            fraud_score=fraud_score,
            risk_level=risk_level,
            classification=classification,
            confidence=confidence,
            auth_results=auth_results,
            origin=OriginInfo(
                originating_ip=origin_ip,
                geolocation=geolocation,
                infra_flags=infra_flags
            ),
            relay_path=relay_path,
            domain_intel=domain_intel,
            indicators=indicators,
            attribution=attribution,
            groq_analysis=classify_res.get("groq_analysis"),
            signal_breakdown=classify_res.get("signal_breakdown"),
            processing_mode=processing_mode,
            webhook_status="not_applicable"
        )

score_aggregator = ScoreAggregator()
