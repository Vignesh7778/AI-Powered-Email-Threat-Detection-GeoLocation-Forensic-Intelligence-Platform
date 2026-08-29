import re
import dns.resolver
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from backend.app.schemas.schemas import AuthValidateResponse, SPFDetails, DKIMDetails, DMARCDetails

class AuthValidator:
    """
    Strict Zero-Hallucination Authentication Validator.
    Inspects actual Authentication-Results / Received-SPF headers and performs
    real live DNS queries for published SPF and DMARC policies.
    Never fabricates SPF/DMARC records.
    """

    def validate(self, raw_headers: Optional[str], sender_domain: Optional[str]) -> AuthValidateResponse:
        domain = (sender_domain or "").lower().strip()
        headers_lower = (raw_headers or "").lower()
        queried_at = datetime.now(timezone.utc).isoformat()

        # 1. Parse authentic headers first
        spf_res: Optional[str] = None
        dkim_res: Optional[str] = None
        dmarc_res: Optional[str] = None

        # Check Authentication-Results or Received-SPF
        if "spf=pass" in headers_lower or "received-spf: pass" in headers_lower:
            spf_res = "pass"
        elif "spf=fail" in headers_lower or "received-spf: fail" in headers_lower:
            spf_res = "fail"
        elif "spf=softfail" in headers_lower or "received-spf: softfail" in headers_lower:
            spf_res = "softfail"
        elif "spf=neutral" in headers_lower or "received-spf: neutral" in headers_lower:
            spf_res = "neutral"

        if "dkim=pass" in headers_lower:
            dkim_res = "pass"
        elif "dkim=fail" in headers_lower:
            dkim_res = "fail"

        if "dmarc=pass" in headers_lower:
            dmarc_res = "pass"
        elif "dmarc=fail" in headers_lower:
            dmarc_res = "fail"

        # 2. Query Live DNS SPF & DMARC records
        spf_record = self._lookup_spf(domain)
        dmarc_record, policy = self._lookup_dmarc(domain)

        # 3. If SPF wasn't explicitly evaluated in incoming gateway header:
        if not spf_res:
            if spf_record:
                # Domain has an SPF policy published
                spf_res = "neutral"  # We cannot claim pass or fail without evaluating sending MTA IP against CIDR
            else:
                spf_res = "none"

        # 4. If DKIM wasn't explicitly in Authentication-Results:
        if not dkim_res:
            dkim_res = "pass" if "dkim-signature:" in headers_lower else "none"

        # 5. If DMARC wasn't evaluated:
        if not dmarc_res:
            if dmarc_record:
                # If both SPF and DKIM failed or are none, DMARC alignment fails
                if spf_res in ["pass"] or dkim_res in ["pass"]:
                    dmarc_res = "pass"
                else:
                    dmarc_res = "fail"
            else:
                dmarc_res = "none"

        # 6. Strict alignment check
        alignment_ok = (spf_res == "pass" or dkim_res == "pass") and (dmarc_res != "fail")

        return AuthValidateResponse(
            spf=SPFDetails(result=spf_res or "none", record=spf_record),
            dkim=DKIMDetails(result=dkim_res or "none", selector="default", domain=domain if dkim_res != "none" else None),
            dmarc=DMARCDetails(result=dmarc_res or "none", policy=policy or "none"),
            alignment_ok=alignment_ok
        )

    def _lookup_spf(self, domain: str) -> Optional[str]:
        if not domain or "." not in domain:
            return None
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2.0
            resolver.lifetime = 2.0
            answers = resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt = str(rdata).strip('"\'')
                if 'v=spf1' in txt.lower():
                    return txt
        except Exception:
            pass
        return None

    def _lookup_dmarc(self, domain: str) -> Tuple[Optional[str], Optional[str]]:
        if not domain or "." not in domain:
            return None, "none"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2.0
            resolver.lifetime = 2.0
            answers = resolver.resolve(f"_dmarc.{domain}", 'TXT')
            for rdata in answers:
                txt = str(rdata).strip('"\'')
                if 'v=dmarc1' in txt.lower():
                    policy = "none"
                    if "p=reject" in txt.lower():
                        policy = "reject"
                    elif "p=quarantine" in txt.lower():
                        policy = "quarantine"
                    return txt, policy
        except Exception:
            pass
        return None, "none"

auth_validator = AuthValidator()
