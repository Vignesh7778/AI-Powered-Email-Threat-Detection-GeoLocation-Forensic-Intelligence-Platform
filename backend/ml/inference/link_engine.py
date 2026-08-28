import re
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser
from typing import List, Tuple
from backend.app.schemas.schemas import LinkScore

class SimpleLinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: List[Tuple[str, str]] = []
        self._current_href = None
        self._current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self._current_href = v
                    self._current_text = []

    def handle_data(self, data):
        if self._current_href is not None:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._current_href is not None:
            text = "".join(self._current_text).strip()
            self.links.append((text or self._current_href, self._current_href))
            self._current_href = None
            self._current_text = []

class LinkEngine:
    """
    Analyzes links extracted from HTML body for obfuscation, phishing indicators,
    IP literals, URL shorteners, and text-href discrepancies.
    """

    SHORTENER_DOMAINS = {
        "bit.ly", "tinyurl.com", "t.co", "is.gd", "ow.ly", "buff.ly",
        "cutt.ly", "goo.gl", "rebrand.ly", "tiny.cc", "rb.gy", "shorte.st"
    }

    SUSPICIOUS_TLDS = {
        ".xyz", ".top", ".work", ".loan", ".click", ".gq", ".tk", ".ml",
        ".cf", ".ga", ".buzz", ".cam", ".rest", ".fit", ".monster", ".bar"
    }

    IP_PATTERN = re.compile(
        r"^(?:http[s]?://)?(?:www\.)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/.*)?$",
        re.IGNORECASE
    )

    def extract_and_score(self, body_html: str) -> List[LinkScore]:
        parser = SimpleLinkExtractor()
        try:
            parser.feed(body_html)
            raw_parsed_links = parser.links
        except Exception:
            raw_parsed_links = []

        links: List[LinkScore] = []
        seen_links = set()

        for text, href in raw_parsed_links:
            href_clean = href.strip()
            if not href_clean or href_clean.startswith("mailto:") or href_clean.startswith("tel:"):
                continue

            link_score = self._evaluate_link(displayed_text=text, actual_url=href_clean)
            key = (link_score.displayed_text, link_score.actual_url)
            if key not in seen_links:
                seen_links.add(key)
                links.append(link_score)

        # Raw URLs in plain text
        raw_urls = re.findall(r"(?:https?://|www\.)[a-zA-Z0-9\-._~:/?#\[\]@!$&()*+,;=%]+", body_html)
        for raw_url in raw_urls:
            cleaned = raw_url.strip(".,;)>]\"'")
            key = (cleaned, cleaned)
            if key not in seen_links:
                seen_links.add(key)
                links.append(self._evaluate_link(displayed_text=cleaned, actual_url=cleaned))

        return links

    def _evaluate_link(self, displayed_text: str, actual_url: str) -> LinkScore:
        reasons: List[str] = []
        risk_score: float = 0.05
        obfuscated: bool = False

        parsed_url = urlparse(actual_url if "://" in actual_url else f"http://{actual_url}")
        netloc = parsed_url.netloc.lower()
        domain = netloc.split(":")[0]

        # Check 1: IP literal host
        if self.IP_PATTERN.match(actual_url) or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", domain):
            reasons.append("ip_literal_host")
            risk_score += 0.45
            obfuscated = True

        # Check 2: URL Shortener
        if any(short in domain for short in self.SHORTENER_DOMAINS):
            reasons.append("url_shortener")
            risk_score += 0.35
            obfuscated = True

        # Check 3: Mismatched display text
        disp_parsed = urlparse(displayed_text if "://" in displayed_text else f"http://{displayed_text}")
        disp_domain = disp_parsed.netloc.lower().split(":")[0]
        if "." in displayed_text and " " not in displayed_text:
            if disp_domain and domain and disp_domain != domain and not domain.endswith(f".{disp_domain}"):
                reasons.append("mismatched_display_text")
                risk_score += 0.50
                obfuscated = True

        # Check 4: Punycode homograph
        if "xn--" in netloc:
            reasons.append("punycode_homograph")
            risk_score += 0.40
            obfuscated = True

        # Check 5: Suspicious TLD
        if any(domain.endswith(tld) for tld in self.SUSPICIOUS_TLDS):
            reasons.append("suspicious_tld")
            risk_score += 0.25

        # Check 6: Encoded credentials / Redirects
        unquoted = unquote(actual_url)
        if unquoted != actual_url and ("%" in actual_url or "@" in actual_url):
            reasons.append("encoded_redirect")
            risk_score += 0.30
            obfuscated = True

        final_risk = round(min(max(risk_score, 0.05), 0.99), 2)
        if final_risk > 0.3:
            obfuscated = True

        return LinkScore(
            displayed_text=displayed_text,
            actual_url=actual_url,
            obfuscated=obfuscated,
            risk_score=final_risk,
            reasons=reasons
        )

link_engine = LinkEngine()
