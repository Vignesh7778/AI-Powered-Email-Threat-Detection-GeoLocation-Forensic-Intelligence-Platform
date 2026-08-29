import dns.resolver
import json
import urllib.request
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class DomainIntelProvider:
    """
    Strict Zero-Hallucination Domain Intelligence Engine.
    Queries real live DNS records (MX, TXT/SPF, DMARC, A, NS) and real RDAP registration records.
    Never fabricates missing values or guesses domain ages.
    """

    def analyze(self, domain: Optional[str]) -> Dict[str, Any]:
        queried_at = datetime.now(timezone.utc).isoformat()

        if not domain or not isinstance(domain, str) or not domain.strip() or "." not in domain:
            return {
                "domain": domain or "unknown",
                "domain_age_days": None,
                "registrar": "Invalid Domain",
                "mx_records": [],
                "dns_records": {"a": [], "txt": [], "ns": [], "dmarc": []},
                "status": "invalid_domain",
                "provenance": {
                    "provider": "live_dns_rdap",
                    "queried_at": queried_at,
                    "response_status": "invalid"
                }
            }

        domain = domain.lower().strip()

        resolver = dns.resolver.Resolver()
        resolver.timeout = 2.5
        resolver.lifetime = 2.5

        mx_records: List[str] = []
        a_records: List[str] = []
        txt_records: List[str] = []
        ns_records: List[str] = []
        dmarc_records: List[str] = []
        dns_status = "resolved"

        # 1. Live MX lookup
        try:
            mx_answers = resolver.resolve(domain, 'MX')
            for r in mx_answers:
                mx_records.append(str(r.exchange).rstrip('.'))
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except Exception:
            dns_status = "error_or_timeout"

        # 2. Live A records
        try:
            a_answers = resolver.resolve(domain, 'A')
            for r in a_answers:
                a_records.append(str(r.address))
        except Exception:
            pass

        # 3. Live NS records
        try:
            ns_answers = resolver.resolve(domain, 'NS')
            for r in ns_answers:
                ns_records.append(str(r.target).rstrip('.'))
        except Exception:
            pass

        # 4. Live TXT records (SPF)
        try:
            txt_answers = resolver.resolve(domain, 'TXT')
            for r in txt_answers:
                for string in r.strings:
                    txt_records.append(string.decode('utf-8', errors='ignore'))
        except Exception:
            pass

        # 5. Live DMARC TXT records (_dmarc.<domain>)
        try:
            dmarc_answers = resolver.resolve(f"_dmarc.{domain}", 'TXT')
            for r in dmarc_answers:
                for string in r.strings:
                    dmarc_records.append(string.decode('utf-8', errors='ignore'))
        except Exception:
            pass

        # 6. Real RDAP lookup for registration date and registrar
        domain_age_days: Optional[int] = None
        registrar: str = "Unavailable (RDAP not queried or unlisted)"
        rdap_status = "unavailable"

        try:
            rdap_url = f"https://rdap.org/domain/{domain}"
            req = urllib.request.Request(
                rdap_url,
                headers={"User-Agent": "TraceX-Forensic-Intelligence-Platform/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    rdap_status = "verified"
                    
                    # Extract registrar
                    for ent in data.get("entities", []):
                        if "registrar" in ent.get("roles", []):
                            vcard = ent.get("vcardArray", [])
                            if len(vcard) > 1:
                                for item in vcard[1]:
                                    if item[0] == "fn":
                                        registrar = str(item[3])
                                        break

                    # Extract creation / registration event
                    for ev in data.get("events", []):
                        if ev.get("eventAction") in ["registration", "created"]:
                            ev_date_str = ev.get("eventDate")
                            if ev_date_str:
                                clean_date = ev_date_str.replace("Z", "+00:00")
                                created_dt = datetime.fromisoformat(clean_date)
                                now_dt = datetime.now(timezone.utc)
                                age_delta = now_dt - created_dt
                                domain_age_days = max(0, age_delta.days)
                                break
        except Exception:
            # Strictly do NOT invent or guess age!
            rdap_status = "unavailable"
            registrar = "Unknown / Unverified"
            domain_age_days = None

        return {
            "domain": domain,
            "domain_age_days": domain_age_days,
            "registrar": registrar,
            "mx_records": mx_records,
            "dns_records": {
                "a": a_records,
                "txt": txt_records,
                "ns": ns_records,
                "dmarc": dmarc_records
            },
            "status": "verified" if (mx_records or a_records) else "no_dns_records",
            "provenance": {
                "provider": "live_dns_and_rdap",
                "queried_at": queried_at,
                "dns_status": dns_status,
                "rdap_status": rdap_status,
                "response_status": "verified" if (mx_records or a_records) else "unavailable"
            }
        }

domain_intel_provider = DomainIntelProvider()
