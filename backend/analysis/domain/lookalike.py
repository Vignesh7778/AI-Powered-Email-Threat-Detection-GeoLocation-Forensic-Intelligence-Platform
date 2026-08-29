from typing import List, Optional, Tuple
from backend.app.schemas.schemas import LookalikeCheckResponse

class LookalikeDetector:
    """
    Lookalike & Typosquatting Domain Detector.
    Detects character substitutions (e.g., '1' for 'l', '0' for 'o'),
    homoglyphs, combosquatting (e.g., 'paypal-security.com'), and TLD swaps.
    """

    HOMOGLYPH_MAP = {
        '1': 'l', 'l': '1', 'i': '1', '|': 'l',
        '0': 'o', 'o': '0',
        '3': 'e', 'e': '3',
        '4': 'a', '@': 'a',
        '5': 's', '$': 's',
        '8': 'b',
        'vv': 'w', 'rn': 'm'
    }

    PROTECTED_BRANDS = [
        "paypal.com",
        "microsoft.com",
        "google.com",
        "apple.com",
        "amazon.com",
        "netflix.com",
        "chase.com",
        "bankofamerica.com",
        "wellsfargo.com",
        "irs.gov",
        "aicte-india.org"
    ]

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return LookalikeDetector._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def check(self, domain: Optional[str], compare_against: Optional[List[str]] = None) -> LookalikeCheckResponse:
        if not domain or not isinstance(domain, str) or not domain.strip():
            return LookalikeCheckResponse(
                domain=domain or "unknown",
                lookalike_of=None,
                technique=None,
                score=0.0
            )

        domain = domain.lower().strip()
        brand_list = compare_against or self.PROTECTED_BRANDS

        # Exact match is legitimate
        if domain in brand_list:
            return LookalikeCheckResponse(
                domain=domain,
                lookalike_of=None,
                technique=None,
                score=0.0
            )

        domain_stem = domain.split('.')[0]
        domain_tld = "." + ".".join(domain.split('.')[1:]) if '.' in domain else ""

        best_brand: Optional[str] = None
        best_technique: Optional[str] = None
        highest_score = 0.0

        for brand in brand_list:
            brand_stem = brand.split('.')[0]
            brand_tld = "." + ".".join(brand.split('.')[1:])

            # 1. Combosquatting (e.g. paypal-verification.com, login-microsoft.net)
            if brand_stem in domain_stem and domain_stem != brand_stem:
                score = 0.88
                technique = "combosquatting"
                if score > highest_score:
                    highest_score = score
                    best_brand = brand
                    best_technique = technique

            # 2. TLD Swap (e.g. paypal.xyz instead of paypal.com)
            if domain_stem == brand_stem and domain_tld != brand_tld:
                score = 0.92
                technique = "tld_swap"
                if score > highest_score:
                    highest_score = score
                    best_brand = brand
                    best_technique = technique

            # 3. Homoglyph / Character Substitution
            normalized_domain = domain_stem
            for char, repl in self.HOMOGLYPH_MAP.items():
                normalized_domain = normalized_domain.replace(char, repl)

            if normalized_domain == brand_stem and domain_stem != brand_stem:
                score = 0.95
                technique = "character_substitution"
                if score > highest_score:
                    highest_score = score
                    best_brand = brand
                    best_technique = technique

            # 4. Levenshtein edit distance (1 or 2 edits away)
            dist = self._levenshtein_distance(domain_stem, brand_stem)
            if dist == 1 and len(brand_stem) >= 4:
                score = 0.90
                technique = "homoglyph"
                if score > highest_score:
                    highest_score = score
                    best_brand = brand
                    best_technique = technique
            elif dist == 2 and len(brand_stem) >= 6:
                score = 0.70
                technique = "character_substitution"
                if score > highest_score:
                    highest_score = score
                    best_brand = brand
                    best_technique = technique

        return LookalikeCheckResponse(
            domain=domain,
            lookalike_of=best_brand if highest_score >= 0.6 else None,
            technique=best_technique if highest_score >= 0.6 else None,
            score=round(highest_score, 2)
        )

lookalike_detector = LookalikeDetector()
