"""HTTP clients for Forensics API and ML API (URLs from md/.env)."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from app.core.config import settings


class _BaseClient:
    """Shared sync httpx wrapper with sensible defaults."""

    def __init__(self, base_url: str, timeout: float = 20.0) -> None:
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: Optional[dict] = None) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base}{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base}{path}", json=payload)
            resp.raise_for_status()
            return resp.json()

    def _delete(self, path: str) -> int:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.delete(f"{self.base}{path}")
            resp.raise_for_status()
            return resp.status_code


class ForensicsClient(_BaseClient):
    """Client for the Forensics API deployed at FORENSIC_API."""

    def __init__(self) -> None:
        super().__init__(settings.forensic_api)

    # --- Evidence / Chain of Custody -----------------------------------------

    def evidence_chain(self, submission_id: str) -> list[dict]:
        """GET /forensics/evidence/{submission_id}/chain"""
        try:
            data = self._get(f"/forensics/evidence/{submission_id}/chain")
            return data if isinstance(data, list) else data.get("chain", [])
        except httpx.HTTPError:
            return []

    def log_evidence(self, submission_id: str, actor: str, action: str) -> None:
        """POST /forensics/evidence/log — non-blocking, swallows errors."""
        try:
            self._post(
                "/forensics/evidence/log",
                {"submission_id": submission_id, "actor": actor, "action": action},
            )
        except Exception:  # noqa: BLE001
            pass

    # --- Header / Auth -------------------------------------------------------

    def parse_headers(self, raw_headers: str) -> dict:
        """POST /forensics/headers/parse"""
        return self._post("/forensics/headers/parse", {"raw_headers": raw_headers})

    def validate_auth(self, raw_headers: str, sender_domain: str) -> dict:
        """POST /forensics/auth/validate"""
        return self._post(
            "/forensics/auth/validate",
            {"raw_headers": raw_headers, "sender_domain": sender_domain},
        )

    # --- Origin / Geo --------------------------------------------------------

    def trace_origin(self, received_chain: list, trusted_relay_ranges: list = None) -> dict:
        """POST /forensics/origin/trace"""
        return self._post(
            "/forensics/origin/trace",
            {"received_chain": received_chain, "trusted_relay_ranges": trusted_relay_ranges or []},
        )

    def geo_lookup(self, ip: str) -> dict:
        """POST /forensics/geo/lookup"""
        return self._post("/forensics/geo/lookup", {"ip": ip})

    def infra_flags(self, ip: str) -> dict:
        """POST /forensics/infra/flags"""
        return self._post("/forensics/infra/flags", {"ip": ip})

    # --- Domain Intel --------------------------------------------------------

    def domain_intel(self, domain: str) -> dict:
        """POST /forensics/domain/intel"""
        return self._post("/forensics/domain/intel", {"domain": domain})

    def lookalike_check(self, domain: str, compare_against: list[str]) -> dict:
        """POST /forensics/domain/lookalike-check"""
        return self._post(
            "/forensics/domain/lookalike-check",
            {"domain": domain, "compare_against": compare_against},
        )


class MlClient(_BaseClient):
    """Client for the ML API deployed at ML_API."""

    def __init__(self) -> None:
        super().__init__(settings.ml_api)

    # --- NLP / Classify ------------------------------------------------------

    def analyze_content(self, subject: str, body_text: str) -> dict:
        """POST /ml/nlp/analyze-content"""
        return self._post("/ml/nlp/analyze-content", {"subject": subject, "body_text": body_text})

    def extract_and_score_links(self, body_html: str) -> dict:
        """POST /ml/links/extract-and-score"""
        return self._post("/ml/links/extract-and-score", {"body_html": body_html})

    def scan_attachment(self, storage_ref: str, sha256: str, content_type: str) -> dict:
        """POST /ml/attachments/scan"""
        return self._post(
            "/ml/attachments/scan",
            {"storage_ref": storage_ref, "sha256": sha256, "content_type": content_type},
        )

    def classify(self, submission_id: str, features: dict) -> dict:
        """POST /ml/classify"""
        return self._post("/ml/classify", {"submission_id": submission_id, "features": features})

    # --- Graph / Campaign ----------------------------------------------------

    def correlate(self, submission_id: str, sender_domain: str, originating_ip: str,
                  reply_to: Optional[str], link_domains: list[str]) -> dict:
        """POST /ml/graph/correlate"""
        return self._post(
            "/ml/graph/correlate",
            {
                "submission_id": submission_id,
                "sender_domain": sender_domain,
                "originating_ip": originating_ip,
                "reply_to": reply_to,
                "link_domains": link_domains,
            },
        )

    def get_campaign_graph(self, campaign_id: str) -> dict:
        """GET /ml/graph/campaign/{campaign_id}"""
        return self._get(f"/ml/graph/campaign/{campaign_id}")

    # --- Feedback ------------------------------------------------------------

    def submit_feedback(self, submission_id: str, analyst_verdict: str, analyst_id: str) -> dict:
        """POST /ml/models/feedback"""
        return self._post(
            "/ml/models/feedback",
            {
                "submission_id": submission_id,
                "analyst_verdict": analyst_verdict,
                "analyst_id": analyst_id,
            },
        )

    def model_health(self) -> dict:
        """GET /ml/models/health"""
        return self._get("/ml/models/health")


# Singletons used across the app
forensics_client = ForensicsClient()
ml_client = MlClient()
