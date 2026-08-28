import ipaddress
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from backend.app.schemas.schemas import RelayHop, OriginTraceResponse

class OriginTracer:
    """
    Forensic Origin Tracer.
    Traverses the Received chain backwards to determine the earliest reliable
    sending infrastructure node, filtering out internal, loopback, and trusted relays.
    Never fabricates a fallback IP if none is observed.
    """

    DEFAULT_TRUSTED = [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "fc00::/7",
        "::1/128"
    ]

    def trace_origin(self, received_chain: List[RelayHop], trusted_relay_ranges: Optional[List[str]] = None) -> OriginTraceResponse:
        queried_at = datetime.now(timezone.utc).isoformat()
        trusted_networks = []
        ranges = trusted_relay_ranges or self.DEFAULT_TRUSTED
        for r in ranges:
            try:
                trusted_networks.append(ipaddress.ip_network(r))
            except Exception:
                pass

        # Traversal: Earliest observed hop (Hop 0 or first in reverse)
        for hop in received_chain:
            if hop.ip:
                try:
                    ip_obj = ipaddress.ip_address(hop.ip)
                    # Check if IP is private/loopback/trusted
                    is_trusted = any(ip_obj in net for net in trusted_networks) or ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved
                    
                    if not is_trusted:
                        return OriginTraceResponse(
                            originating_ip=hop.ip,
                            confidence=0.91,
                            reasoning=f"Earliest reliable public relay infrastructure observed outside trusted CIDR boundaries at hop {hop.hop} ({hop.hostname or 'unknown host'}).",
                            provenance={
                                "provider": "received_header_traversal",
                                "queried_at": queried_at,
                                "hop_index": hop.hop,
                                "hostname": hop.hostname,
                                "status": "verified"
                            }
                        )
                except Exception:
                    continue

        # If only internal / private hops exist
        if len(received_chain) > 0 and received_chain[0].ip:
            first_ip = received_chain[0].ip
            return OriginTraceResponse(
                originating_ip=first_ip,
                confidence=0.50,
                reasoning=f"Only private/internal relay IP ({first_ip}) observed at hop 0. Originating public sending infrastructure was not recorded in headers.",
                provenance={
                    "provider": "received_header_traversal",
                    "queried_at": queried_at,
                    "status": "internal_only"
                }
            )

        # Strictly ZERO-HALLUCINATION: Return None when no origin exists
        return OriginTraceResponse(
            originating_ip=None,
            confidence=0.0,
            reasoning="Origin could not be reliably determined. No valid Received headers containing IP addresses were present in the email.",
            provenance={
                "provider": "received_header_traversal",
                "queried_at": queried_at,
                "status": "unavailable"
            }
        )

origin_tracer = OriginTracer()
