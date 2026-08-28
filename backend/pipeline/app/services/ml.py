import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.schemas import Attachment, AuthResults, DomainIntel, Indicator, Origin


URL_PATTERN = re.compile(r"https?://[^\s\"'<>()]+", re.IGNORECASE)
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "rb.gy", "is.gd"}


@dataclass
class LinkScore:
    url: str
    risk_score: float
    reasons: list[str]


class MLAdapter:
    model_version = "v4.1.0"

    def nlp(self, subject: str, body: str) -> tuple[float, float, list[Indicator]]:
        text = f"{subject} {body}".lower()
        urgency_terms = ("urgent", "immediately", "today", "24 hours", "action required", "asap")
        identity_terms = ("ceo", "finance", "invoice", "wire transfer", "banking details", "password", "verify your account")
        urgency_count = sum(term in text for term in urgency_terms)
        identity_count = sum(term in text for term in identity_terms)
        urgency = min(1.0, urgency_count / 3)
        impersonation = min(1.0, identity_count / 3)
        indicators: list[Indicator] = []
        if urgency:
            indicators.append(Indicator(type="urgency_language", detail="Urgent or time-bound language was detected.", weight=round(0.15 + urgency * 0.15, 2)))
        if impersonation:
            indicators.append(Indicator(type="impersonation_language", detail="Language suggests financial, executive, or account impersonation.", weight=round(0.15 + impersonation * 0.15, 2)))
        return urgency, impersonation, indicators

    def links(self, html: str) -> list[LinkScore]:
        links: list[LinkScore] = []
        for raw_url in URL_PATTERN.findall(html or ""):
            parsed = urlparse(raw_url.rstrip(".,"))
            host = (parsed.hostname or "").lower()
            reasons: list[str] = []
            if host in SHORTENERS:
                reasons.append("url_shortener")
            if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
                reasons.append("ip_literal_host")
            if any(token in host for token in ("login", "verify", "secure", "account")):
                reasons.append("credential_lure_host")
            score = min(0.95, 0.15 + len(reasons) * 0.25)
            links.append(LinkScore(url=raw_url, risk_score=round(score, 2), reasons=reasons))
        return links

    def scan_attachment(self, attachment: Attachment) -> tuple[bool, float, str]:
        lowered = f"{attachment.filename} {attachment.content_type}".lower()
        sandboxing = any(token in lowered for token in (".xlsm", ".docm", ".exe", ".js", "macro"))
        score = 0.84 if sandboxing else 0.08
        detected = "macro_dropper" if sandboxing else "none"
        return sandboxing, score, detected

    def classify(self, auth: AuthResults, domain: DomainIntel, origin: Origin, urgency: float, impersonation: float, links: list[LinkScore], header_anomalies: int) -> tuple[str, float, float, list[Indicator]]:
        auth_risk = 1.0 if "fail" in (auth.spf, auth.dkim, auth.dmarc) else 0.35 if "none" in (auth.spf, auth.dkim, auth.dmarc) else 0.0
        link_risk = max((link.risk_score for link in links), default=0.0)
        domain_risk = max(domain.lookalike_score, 1 - min(domain.domain_age_days / 180, 1))
        infra_risk = 0.55 if origin.infra_flags else 0.0
        anomaly_risk = min(header_anomalies * 0.25, 0.75)
        fraud = min(0.99, round(auth_risk * .20 + domain_risk * .25 + urgency * .12 + impersonation * .18 + link_risk * .17 + infra_risk * .04 + anomaly_risk * .04, 2))
        if impersonation > .55 and domain.lookalike_score > .65:
            classification = "bec_fraud"
        elif link_risk >= .65:
            classification = "phishing"
        elif domain.lookalike_score >= .65:
            classification = "impersonation"
        elif fraud >= .35:
            classification = "suspicious"
        else:
            classification = "legitimate"
        confidence = min(.98, max(.65, round(.62 + fraud * .36, 2)))
        indicators: list[Indicator] = []
        if auth_risk >= .5:
            indicators.append(Indicator(type="authentication_failure", detail="Sender authentication did not validate cleanly.", weight=.25))
        if domain.lookalike_score >= .65:
            indicators.append(Indicator(type="lookalike_domain", detail=f"Sender domain resembles {domain.lookalike_of}.", weight=.30))
        for link in links:
            if link.risk_score >= .6:
                indicators.append(Indicator(type="malicious_link", detail=f"Suspicious link indicators: {', '.join(link.reasons)}.", weight=.22))
        return classification, fraud, confidence, indicators


ml = MLAdapter()
