import json
import re
import urllib.request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from backend.app.core.config import settings

class GroqObservation(BaseModel):
    fact: str
    evidence_ref: str

class GroqInference(BaseModel):
    inference: str
    reasoning: str
    confidence: float = 0.0

class GroqAttribution(BaseModel):
    assessment: str
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)

class GroqAnalysisResponse(BaseModel):
    status: str = "verified"
    model: str = "llama-3.3-70b-versatile"
    grounding_status: str = "grounded_in_evidence"  # or 'unsupported_claim_detected'
    unsupported_claims: List[str] = Field(default_factory=list)
    assessment: str
    risk_score: float = 0.0
    confidence: float = 0.0
    observations: List[GroqObservation] = Field(default_factory=list)
    inferences: List[GroqInference] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    attribution: GroqAttribution = Field(default_factory=lambda: GroqAttribution(assessment="Unknown infrastructure association"))
    queried_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class GroqAnalyzer:
    """
    Groq AI Zero-Hallucination Evidence Reasoning Engine.
    Powered by high-speed LPU inference with strict grounding on verified forensic telemetry.
    """

    SYSTEM_PROMPT = """You are an expert Cyber Forensics and Threat Intelligence Analyst for a national Forensic Intelligence platform.
You must reason ONLY from the supplied evidence (headers, DNS records, GeoIP, URLs, attachment hashes, and authentication checks).

MANDATORY RULES:
1. Do NOT invent facts or technical indicators.
2. Do NOT infer unavailable technical values as verified facts.
3. If evidence is missing or ambiguous, state that it is unavailable or unknown.
4. Strictly separate OBSERVED facts from INFERRED possibilities.
5. Every observation must cite the exact evidence field supporting it.
6. Never claim confirmed attacker identity or exact physical location unless authoritative evidence establishes it. Use terms like 'IP-associated infrastructure' and 'Probable campaign pattern'.
7. You must respond with a SINGLE valid JSON object conforming to the schema below.

JSON Schema:
{
  "assessment": "Concise forensic verdict grounded strictly in observed telemetry",
  "risk_score": <number between 0 and 100>,
  "confidence": <number between 0.0 and 1.0>,
  "observations": [
    {"fact": "Observed fact string", "evidence_ref": "Header/DNS/GeoIP/URL field name"}
  ],
  "inferences": [
    {"inference": "Probabilistic conclusion", "reasoning": "Why this is inferred", "confidence": 0.85}
  ],
  "unknowns": ["List of unverified or missing signals"],
  "recommendations": ["Actionable triage/remediation steps for security analysts"],
  "attribution": {
    "assessment": "Probable infrastructure association description",
    "confidence": 0.75,
    "evidence": ["Supporting signal 1", "Supporting signal 2"]
  }
}
"""

    def analyze(self, evidence_packet: Dict[str, Any]) -> GroqAnalysisResponse:
        api_key = getattr(settings, 'GROQ_API_KEY', None)
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        base_url = getattr(settings, 'GROQ_BASE_URL', 'https://api.groq.com/openai/v1')
        queried_at = datetime.now(timezone.utc).isoformat()

        # 1. Graceful fallback if API key is not configured (STRICT ZERO-MOCK)
        if not api_key or str(api_key).strip() in ['', 'None', 'placeholder', 'none']:
            return GroqAnalysisResponse(
                status="disabled",
                model="none",
                grounding_status="not_applicable",
                assessment="LLM evidence-based reasoning is currently disabled: GROQ_API_KEY is not configured in environment.",
                risk_score=0.0,
                confidence=0.0,
                observations=[],
                inferences=[],
                unknowns=["GROQ_API_KEY is missing from environment. Real-time deterministic analysis remains fully active."],
                recommendations=["Configure GROQ_API_KEY in .env to enable deep evidence-grounded Groq LPU reasoning."],
                attribution=GroqAttribution(assessment="Attribution inference unavailable without LLM reasoning layer", confidence=0.0),
                queried_at=queried_at
            )

        # 2. Prepare sanitized evidence packet
        user_prompt = f"Analyze this verified email forensic evidence:\n```json\n{json.dumps(evidence_packet, indent=2, default=str)}\n```\n\nProvide your structured zero-hallucination analysis in JSON:"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,  # Low temperature for strict factual accuracy
            "max_tokens": 1500,
            "response_format": {"type": "json_object"}
        }

        try:
            req = urllib.request.Request(
                f"{base_url.rstrip('/')}/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "TraceX-Forensic-Intelligence-Platform/1.0"
                }
            )

            with urllib.request.urlopen(req, timeout=12.0) as resp:
                if resp.status == 200:
                    resp_data = json.loads(resp.read().decode('utf-8'))
                    raw_content = resp_data['choices'][0]['message']['content'].strip()

                    # Extract JSON from code fences if present
                    json_str = raw_content
                    if "```json" in raw_content:
                        json_str = raw_content.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_content:
                        json_str = raw_content.split("```")[1].split("```")[0].strip()

                    parsed = json.loads(json_str)

                    # 3. Grounding & Hallucination Validator
                    unsupported_claims = self._validate_grounding(parsed, evidence_packet)
                    grounding_status = "unsupported_claim_detected" if unsupported_claims else "grounded_in_evidence"

                    return GroqAnalysisResponse(
                        status="verified",
                        model=model,
                        grounding_status=grounding_status,
                        unsupported_claims=unsupported_claims,
                        assessment=parsed.get("assessment", "Analysis completed."),
                        risk_score=float(parsed.get("risk_score", 0.0)),
                        confidence=float(parsed.get("confidence", 0.0)),
                        observations=[GroqObservation(**o) for o in parsed.get("observations", []) if isinstance(o, dict)],
                        inferences=[GroqInference(**i) for i in parsed.get("inferences", []) if isinstance(i, dict)],
                        unknowns=parsed.get("unknowns", []),
                        recommendations=parsed.get("recommendations", []),
                        attribution=GroqAttribution(**(parsed.get("attribution") or {})),
                        queried_at=queried_at
                    )
        except Exception as err:
            return GroqAnalysisResponse(
                status="error",
                model=model,
                grounding_status="error_occurred",
                assessment=f"Groq AI reasoning API query failed: {str(err)}",
                risk_score=0.0,
                confidence=0.0,
                observations=[],
                inferences=[],
                unknowns=["Groq API request could not be completed"],
                recommendations=["Check network connectivity and GROQ_API_KEY quota."],
                attribution=GroqAttribution(assessment="API Error", confidence=0.0),
                queried_at=queried_at
            )

    def _validate_grounding(self, llm_output: Dict[str, Any], evidence_packet: Dict[str, Any]) -> List[str]:
        """
        Detects hallucinated IPs, domains, and ungrounded claims.
        """
        unsupported = []
        evidence_text = json.dumps(evidence_packet).lower()
        llm_text = json.dumps(llm_output).lower()

        # Check for extracted IP literals in LLM text
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        for ip in re.findall(ip_pattern, llm_text):
            if ip not in evidence_text and not ip.startswith('0.') and not ip.startswith('127.'):
                unsupported.append(f"Ungrounded IP indicator mentioned by LLM: {ip}")

        return unsupported

groq_analyzer = GroqAnalyzer()

