import re
from typing import List, Tuple, Dict, Any
from app.schemas.nlp import DetectedPattern, PatternType

class NLPEngine:
    """
    NLP Analysis Engine for detecting social engineering, urgency cues,
    credential harvesting, invoice fraud, and executive impersonation patterns.
    Extracts exact character offset spans [start, end] into the original body text.
    """

    PATTERNS: Dict[PatternType, List[Dict[str, Any]]] = {
        "urgency_cue": [
            {"regex": r"(?i)\b(urgent|immediately|action required|within 24 hours|account will be suspended|immediate response|expires today|act now|critical security alert|final notice)\b", "weight": 0.85},
            {"regex": r"(?i)\b(as soon as possible|prompt action|time sensitive|limited time|respond immediately|terminate your account)\b", "weight": 0.75}
        ],
        "executive_impersonation": [
            {"regex": r"(?i)\b(ceo|cfo|chief executive|president|managing director|board of directors|executive office|sent from my (?:iphone|mobile))\b", "weight": 0.70},
            {"regex": r"(?i)\b(are you at your desk|quick favor|are you available|confidential request|handle this discreetly|in a meeting right now)\b", "weight": 0.88},
            {"regex": r"(?i)\b(keep this strictly confidential|do not discuss this with anyone|wire instructions from ceo)\b", "weight": 0.95}
        ],
        "payment_diversion": [
            {"regex": r"(?i)\b(wire transfer|bank account details|new routing number|updated bank details|change of banking|swift code|ach payment|direct deposit change|transfer funds)\b", "weight": 0.90},
            {"regex": r"(?i)\b(remit payment to|send payment to|gift card|itunes card|google play card|steam card|crypto wallet|bitcoin address)\b", "weight": 0.92},
            {"regex": r"(?i)\b(vendor payment|remittance advice|overdue invoice|remittance info|payment pending)\b", "weight": 0.78}
        ],
        "fake_invoice": [
            {"regex": r"(?i)\b(invoice\s*#?\s*\d+|invoice attached|billing statement|past due invoice|payment receipt|po\s*#?\s*\d+|purchase order)\b", "weight": 0.80},
            {"regex": r"(?i)\b(find the attached invoice|unpaid balance|outstanding balance|service renewal fee|automatic subscription)\b", "weight": 0.85}
        ],
        "credential_harvesting": [
            {"regex": r"(?i)\b(verify your account|login to your account|click here to verify|reset your password|update your credentials|sign in to review|re-authenticate|session expired)\b", "weight": 0.92},
            {"regex": r"(?i)\b(mailbox quota exceeded|validate email|security verification|two-factor authentication update|portal login)\b", "weight": 0.88}
        ]
    }

    def __init__(self, model_version: str = "v2.3.1"):
        self.model_version = model_version

    def analyze(self, subject: str, body_text: str) -> Dict[str, Any]:
        detected_patterns: List[DetectedPattern] = []
        urgency_signals: List[float] = []
        impersonation_signals: List[float] = []
        
        full_text = f"{subject}\n{body_text}"
        
        # Scan body_text specifically for excerpt_span indices
        for p_type, rule_list in self.PATTERNS.items():
            for rule in rule_list:
                pattern = rule["regex"]
                base_weight = rule["weight"]
                
                # Check in body text for spans
                for match in re.finditer(pattern, body_text):
                    start, end = match.span()
                    confidence = round(min(base_weight + (0.05 if len(match.group()) > 15 else 0.0), 0.98), 2)
                    detected_patterns.append(
                        DetectedPattern(
                            type=p_type,
                            excerpt_span=(start, end),
                            confidence=confidence
                        )
                    )
                    
                    if p_type == "urgency_cue":
                        urgency_signals.append(confidence)
                    elif p_type in ["executive_impersonation", "payment_diversion"]:
                        impersonation_signals.append(confidence)

                # Check in subject as well for overall scoring
                for match in re.finditer(pattern, subject):
                    confidence = round(min(base_weight + 0.05, 0.99), 2)
                    if p_type == "urgency_cue":
                        urgency_signals.append(confidence * 1.1)
                    elif p_type in ["executive_impersonation", "payment_diversion"]:
                        impersonation_signals.append(confidence * 1.1)

        # Deduplicate patterns with identical spans and types
        unique_patterns = []
        seen = set()
        for p in detected_patterns:
            key = (p.type, p.excerpt_span[0], p.excerpt_span[1])
            if key not in seen:
                seen.add(key)
                unique_patterns.append(p)

        # Compute aggregate urgency score
        if urgency_signals:
            # Non-linear saturated aggregation
            combined = 1.0 - 1.0
            for s in urgency_signals:
                combined = combined + s * (1.0 - combined) * 0.7
            urgency_score = round(min(max(combined, 0.0), 1.0), 2)
        else:
            urgency_score = 0.05

        # Compute aggregate impersonation score
        if impersonation_signals:
            combined = 1.0 - 1.0
            for s in impersonation_signals:
                combined = combined + s * (1.0 - combined) * 0.75
            impersonation_score = round(min(max(combined, 0.0), 1.0), 2)
        else:
            impersonation_score = 0.05

        return {
            "urgency_score": urgency_score,
            "impersonation_language_score": impersonation_score,
            "detected_patterns": unique_patterns,
            "language_model_version": self.model_version
        }

nlp_engine = NLPEngine()

