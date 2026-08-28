import re
from typing import Dict, Any, List, Optional
from email import message_from_string
from backend.app.schemas.schemas import RelayHop, HeaderAnomaly, HeaderParseResponse

class HeaderAnalyzer:
    """
    Forensic Email Header & Protocol Analyzer.
    Preserves Received-chain hop ordering and detects anomalies.
    """

    IP_REGEX = re.compile(r'\[?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\]?')

    def parse_headers(self, raw_headers: str) -> HeaderParseResponse:
        msg = message_from_string(raw_headers)
        
        # Core fields
        from_raw = msg.get('from', '')
        message_id = msg.get('message-id', 'unknown-msg-id')
        return_path = msg.get('return-path', '').strip('<>')
        reply_to = msg.get('reply-to')
        subject = msg.get('subject', '')

        # Extract display name & email from 'From'
        from_display = from_raw
        from_address = from_raw
        if '<' in from_raw and '>' in from_raw:
            from_display = from_raw.split('<')[0].strip('"\' ')
            from_address = from_raw.split('<')[1].split('>')[0].strip()

        # Parse Received chain (preserve hop order: reverse list so hop 0 is earliest sending node)
        raw_received = msg.get_all('received', []) or []
        received_chain: List[RelayHop] = []
        
        # Raw received headers appear in reverse chronological order (latest hop at index 0)
        # We reverse them to make hop 0 the originating sender
        chronological_hops = list(reversed(raw_received))

        for idx, rec_header in enumerate(chronological_hops):
            cleaned = " ".join(rec_header.split())
            
            # Extract IP
            ip_match = self.IP_REGEX.search(cleaned)
            ip = ip_match.group(0).strip('[]') if ip_match else None
            
            # Extract from host
            from_match = re.search(r'from\s+([^\s;]+)', cleaned, re.IGNORECASE)
            from_host = from_match.group(1) if from_match else None

            # Extract by host
            by_match = re.search(r'by\s+([^\s;]+)', cleaned, re.IGNORECASE)
            by_host = by_match.group(1) if by_match else None

            # Extract with protocol
            with_match = re.search(r'with\s+([^\s;]+)', cleaned, re.IGNORECASE)
            with_protocol = with_match.group(1) if with_match else None

            # Extract timestamp
            timestamp = None
            if ';' in cleaned:
                timestamp = cleaned.split(';')[-1].strip()

            received_chain.append(
                RelayHop(
                    hop=idx,
                    ip=ip,
                    hostname=from_host,
                    by_host=by_host,
                    with_protocol=with_protocol,
                    timestamp=timestamp
                )
            )

        # Detect Header Anomalies
        anomalies: List[HeaderAnomaly] = []

        # 1. Forged return path (Return-Path domain does not match From domain)
        if return_path and from_address and '@' in return_path and '@' in from_address:
            rp_domain = return_path.split('@')[-1].lower()
            from_domain = from_address.split('@')[-1].lower()
            if rp_domain != from_domain:
                anomalies.append(
                    HeaderAnomaly(
                        type="forged_return_path",
                        detail=f"Return-Path domain ({rp_domain}) differs from From domain ({from_domain})",
                        severity="high"
                    )
                )

        # 2. Header injection (newlines in subject or from)
        if "\n" in subject or "\r" in subject:
            anomalies.append(
                HeaderAnomaly(
                    type="header_injection",
                    detail="Carriage return or newline detected inside subject line",
                    severity="high"
                )
            )

        # 3. Missing Message-ID or suspicious format
        if not msg.get('message-id') or '@' not in msg.get('message-id', ''):
            anomalies.append(
                HeaderAnomaly(
                    type="relay_manipulation",
                    detail="Message-ID header is missing or does not follow standard RFC FQDN structure",
                    severity="medium"
                )
            )

        # 4. Reply-To mismatch
        if reply_to and '@' in reply_to and '@' in from_address:
            reply_domain = reply_to.split('@')[-1].lower().strip('<> ')
            from_domain = from_address.split('@')[-1].lower().strip('<> ')
            if reply_domain != from_domain:
                anomalies.append(
                    HeaderAnomaly(
                        type="relay_manipulation",
                        detail=f"Reply-To address ({reply_to}) routes replies to a different domain ({reply_domain})",
                        severity="medium"
                    )
                )

        return HeaderParseResponse(
            message_id=message_id,
            return_path=return_path,
            reply_to=reply_to,
            from_display=from_display,
            from_address=from_address,
            subject=subject,
            received_chain=received_chain,
            anomalies=anomalies
        )

header_analyzer = HeaderAnalyzer()
