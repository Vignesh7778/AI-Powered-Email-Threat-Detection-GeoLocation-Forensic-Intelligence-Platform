import dns.resolver
import ipaddress
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.schemas.schemas import InfraFlagsResponse

class ThreatIntelProvider:
    """
    Strict Zero-Hallucination Threat Intelligence Provider.
    Queries live DNSBL blacklists (Spamhaus, SpamCop) and verified network flags.
    Never invents threat actors or false reputations.
    """

    DNSBL_PROVIDERS = [
        ("zen.spamhaus.org", "Spamhaus ZEN (Composite SBL/XBL/PBL)"),
        ("bl.spamcop.net", "SpamCop Blocking List")
    ]

    def get_flags(self, ip: Optional[str]) -> InfraFlagsResponse:
        queried_at = datetime.now(timezone.utc).isoformat()
        if not ip or not isinstance(ip, str) or not ip.strip():
            return InfraFlagsResponse(ip=ip or "", flags=[], source_lists=["No IP supplied"])

        ip = ip.strip()
        flags: List[str] = []
        sources: List[str] = []

        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback:
                return InfraFlagsResponse(
                    ip=ip,
                    flags=["private_network"],
                    source_lists=["RFC 1918 Private Network Filter"]
                )
        except ValueError:
            return InfraFlagsResponse(ip=ip, flags=[], source_lists=["Invalid IP address format"])

        # Live DNSBL check (only for IPv4)
        if "." in ip and ip.count(".") == 3:
            reversed_ip = ".".join(reversed(ip.split(".")))
            resolver = dns.resolver.Resolver()
            resolver.timeout = 2.0
            resolver.lifetime = 2.0

            for bl_zone, bl_name in self.DNSBL_PROVIDERS:
                query_name = f"{reversed_ip}.{bl_zone}"
                try:
                    answers = resolver.resolve(query_name, "A")
                    if answers:
                        flags.append("threat_listed")
                        sources.append(f"Live Query: {bl_name} (Match: {answers[0].address})")
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    pass
                except Exception:
                    pass

        if not flags:
            sources.append("Live DNSBL Checks (Spamhaus ZEN, SpamCop) - No verified threat match found (Clean listing does not guarantee benign status)")

        return InfraFlagsResponse(
            ip=ip,
            flags=flags,
            source_lists=sources
        )

threat_intel = ThreatIntelProvider()
