"""HTTP clients for the Forensics and AI/ML contracts in docs/.

The pipeline owns orchestration; the specialist services own signal generation.
"""
from datetime import datetime
import re
from typing import Any

import httpx

from app.schemas import Attribution, AuthResults, DomainIntel, Geolocation, Indicator, Origin, RelayHop
from app.services.ml import LinkScore


class ServiceClientError(RuntimeError):
    pass


class _HttpClient:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(base_url=self.base_url, timeout=12.0)

    def post(self, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            response = self.client.post(path if self.client.base_url else f"{self.base_url}{path}", json=payload)
            response.raise_for_status()
            return response.status_code, response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ServiceClientError(f"Service request to {path} failed: {exc}") from exc


class ForensicsHttpClient(_HttpClient):
    def parse_headers(self, raw_headers: str):
        _, data = self.post("/forensics/headers/parse", {"raw_headers": raw_headers})
        fields = {key: data.get(key, "") for key in ("from_address", "return_path", "reply_to", "message_id")}
        relays = [RelayHop.model_validate({"hop": item["hop"], "ip": item.get("ip"), "hostname": item.get("from_host") or item.get("hostname"), "timestamp": item.get("timestamp")}) for item in data.get("received_chain", [])]
        return fields, relays, data.get("anomalies", [])

    @staticmethod
    def sender_domain(header_value: str) -> str:
        match = re.search(r"@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", header_value)
        return match.group(1).lower() if match else "unknown.invalid"

    def validate_authentication(self, raw_headers: str) -> AuthResults:
        _, data = self.post("/forensics/auth/validate", {"raw_headers": raw_headers, "sender_domain": self.sender_domain(raw_headers)})
        return AuthResults(
            spf=data.get("spf", {}).get("result", "none"),
            dkim=data.get("dkim", {}).get("result", "none"),
            dmarc=data.get("dmarc", {}).get("result", "none"),
            alignment_ok=data.get("alignment_ok", False),
        )

    def build_origin(self, relays: list[RelayHop]) -> Origin:
        chain = [{"hop": item.hop, "ip": item.ip, "hostname": item.hostname} for item in relays if item.ip]
        _, trace = self.post("/forensics/origin/trace", {"received_chain": chain, "trusted_relay_ranges": []})
        ip = trace["originating_ip"]
        _, geo = self.post("/forensics/geo/lookup", {"ip": ip})
        _, flags = self.post("/forensics/infra/flags", {"ip": ip})
        return Origin(
            originating_ip=ip,
            confidence=trace.get("confidence", .5),
            reasoning=trace.get("reasoning", "Origin obtained from forensics service."),
            geolocation=Geolocation.model_validate(geo),
            infra_flags=flags.get("flags", []),
        )

    def domain_intelligence(self, domain: str, protected_domains: list[str]) -> DomainIntel:
        _, intel = self.post("/forensics/domain/intel", {"domain": domain})
        _, lookalike = self.post("/forensics/domain/lookalike-check", {"domain": domain, "compare_against": protected_domains})
        return DomainIntel(
            sender_domain=domain,
            registrar=intel.get("registrar", "unknown"),
            created_date=intel["created_date"],
            domain_age_days=intel.get("age_days", 0),
            mx_records=intel.get("mx_records", []),
            lookalike_of=lookalike.get("lookalike_of"),
            lookalike_score=lookalike.get("score", 0.0),
        )

    def log_evidence(self, submission_id: str, action: str) -> None:
        self.post("/forensics/evidence/log", {"submission_id": submission_id, "actor": "system:pipeline", "action": action, "timestamp": datetime.utcnow().isoformat() + "Z"})


class MlHttpClient(_HttpClient):
    model_version = "v4.1.0"

    def nlp(self, subject: str, body: str):
        _, data = self.post("/ml/nlp/analyze-content", {"subject": subject, "body_text": body})
        indicators = [Indicator(type=item["type"], detail="Detected by NLP analysis.", weight=item.get("confidence", .1)) for item in data.get("detected_patterns", [])]
        return data.get("urgency_score", 0.0), data.get("impersonation_language_score", 0.0), indicators

    def links(self, html: str) -> list[LinkScore]:
        _, data = self.post("/ml/links/extract-and-score", {"body_html": html})
        return [LinkScore(url=item["actual_url"], risk_score=item["risk_score"], reasons=item.get("reasons", [])) for item in data.get("links", [])]

    def scan_attachment(self, attachment):
        _, data = self.post("/ml/attachments/scan", {"storage_ref": attachment.storage_ref, "sha256": attachment.sha256, "content_type": attachment.content_type})
        return data.get("status") == "sandboxing", data.get("malware_score", 0.0), data.get("detected_type", "none")

    def classify(self, auth, domain, origin, urgency, impersonation, links, header_anomalies):
        _, data = self.post("/ml/classify", {"submission_id": "pipeline", "features": {"auth_results": auth.model_dump(exclude={"alignment_ok"}), "domain_age_days": domain.domain_age_days, "lookalike_score": domain.lookalike_score, "infra_flags": origin.infra_flags, "header_anomalies_count": header_anomalies, "urgency_score": urgency, "impersonation_language_score": impersonation, "link_risk_scores": [item.risk_score for item in links]}})
        self.model_version = data.get("model_version", self.model_version)
        indicators = [Indicator(type=item["feature"], detail="Classifier feature contribution.", weight=item["contribution"]) for item in data.get("feature_importance", [])]
        return data["classification"], data["fraud_score"], data["confidence"], indicators

    def correlate(self, submission_id: str, domain: str, ip: str, reply_to: str, links: list[LinkScore]) -> Attribution:
        _, data = self.post("/ml/graph/correlate", {"submission_id": submission_id, "sender_domain": domain, "originating_ip": ip, "reply_to": reply_to or None, "link_domains": [item.url for item in links]})
        return Attribution.model_validate(data)

    def aggregate(self, submission_id: str, forensics_results: dict[str, Any], classify_result: dict[str, Any], nlp_result: dict[str, Any], links_result: dict[str, Any], attachment_results: list[dict[str, Any]]) -> None:
        self.post("/ml/aggregate", {"submission_id": submission_id, "forensics_results": forensics_results, "classify_result": classify_result, "nlp_result": nlp_result, "links_result": links_result, "attachment_results": attachment_results})
