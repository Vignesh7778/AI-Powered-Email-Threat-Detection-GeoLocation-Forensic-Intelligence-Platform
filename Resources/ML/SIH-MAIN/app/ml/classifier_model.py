import math
from typing import Dict, Any, List, Tuple
from app.schemas.classify import Features, ClassifyResponse, FeatureImportance, ClassificationType

class FraudClassifier:
    """
    ML Fraud Classifier predicting classification category (legitimate, suspicious,
    impersonation, phishing, bec_fraud), overall fraud_score, confidence,
    and feature importance contributions.
    """

    CLASSES: List[ClassificationType] = [
        "legitimate",
        "suspicious",
        "impersonation",
        "phishing",
        "bec_fraud"
    ]

    def __init__(self, model_version: str = "v4.1.0"):
        self.model_version = model_version

    def _extract_feature_vector(self, features: Features) -> Dict[str, float]:
        spf_map = {"pass": 0.0, "neutral": 0.3, "softfail": 0.7, "fail": 1.0, "none": 0.5}
        dkim_map = {"pass": 0.0, "fail": 1.0, "none": 0.5}
        dmarc_map = {"pass": 0.0, "fail": 1.0, "none": 0.5}

        spf_val = (features.auth_results.spf or "none").lower()
        dkim_val = (features.auth_results.dkim or "none").lower()
        dmarc_val = (features.auth_results.dmarc or "none").lower()

        spf_risk = spf_map.get(spf_val, 0.5)
        dkim_risk = dkim_map.get(dkim_val, 0.5)
        dmarc_risk = dmarc_map.get(dmarc_val, 0.5)

        # Domain age risk (new domains < 30 days are high risk)
        domain_age_risk = 1.0 - min(features.domain_age_days / 180.0, 1.0)
        lookalike_score = features.lookalike_score

        infra_weight = 0.0
        for flag in features.infra_flags:
            f = flag.lower()
            if "tor" in f:
                infra_weight = max(infra_weight, 0.9)
            elif "vpn" in f:
                infra_weight = max(infra_weight, 0.5)
            elif "proxy" in f or "hosting" in f:
                infra_weight = max(infra_weight, 0.4)
            elif "dynamic" in f:
                infra_weight = max(infra_weight, 0.3)
        infra_risk = infra_weight

        header_anomalies_risk = min(features.header_anomalies_count * 0.3, 1.0)
        urgency_score = features.urgency_score
        impersonation_language_score = features.impersonation_language_score

        if features.link_risk_scores:
            max_link_risk = max(features.link_risk_scores)
            avg_link_risk = sum(features.link_risk_scores) / len(features.link_risk_scores)
        else:
            max_link_risk = 0.0
            avg_link_risk = 0.0

        return {
            "spf_risk": spf_risk,
            "dkim_risk": dkim_risk,
            "dmarc_risk": dmarc_risk,
            "domain_age_risk": domain_age_risk,
            "lookalike_score": lookalike_score,
            "infra_risk": infra_risk,
            "header_anomalies_risk": header_anomalies_risk,
            "urgency_score": urgency_score,
            "impersonation_language_score": impersonation_language_score,
            "max_link_risk": max_link_risk,
            "avg_link_risk": avg_link_risk
        }

    def classify(self, submission_id: str, features: Features) -> ClassifyResponse:
        f = self._extract_feature_vector(features)

        # Multi-class scoring models calibrated for email threat taxonomy
        # 1. BEC Fraud score
        bec_score = (
            f["impersonation_language_score"] * 0.35 +
            f["urgency_score"] * 0.25 +
            f["lookalike_score"] * 0.25 +
            f["dmarc_risk"] * 0.15
        )

        # 2. Phishing score
        phishing_score = (
            f["max_link_risk"] * 0.40 +
            f["urgency_score"] * 0.20 +
            f["domain_age_risk"] * 0.20 +
            f["spf_risk"] * 0.20
        )

        # 3. Impersonation score
        impersonation_score = (
            f["lookalike_score"] * 0.45 +
            f["impersonation_language_score"] * 0.35 +
            f["header_anomalies_risk"] * 0.20
        )

        # 4. Suspicious score
        suspicious_score = (
            f["infra_risk"] * 0.30 +
            f["header_anomalies_risk"] * 0.30 +
            f["domain_age_risk"] * 0.25 +
            f["spf_risk"] * 0.15
        )

        # 5. Legitimate score (inverse of composite risk)
        composite_risk = (
            f["spf_risk"] * 0.10 +
            f["dkim_risk"] * 0.08 +
            f["dmarc_risk"] * 0.12 +
            f["domain_age_risk"] * 0.10 +
            f["lookalike_score"] * 0.18 +
            f["infra_risk"] * 0.08 +
            f["header_anomalies_risk"] * 0.06 +
            f["urgency_score"] * 0.12 +
            f["impersonation_language_score"] * 0.14 +
            f["max_link_risk"] * 0.15
        )
        legit_score = max(0.0, 1.0 - composite_risk)

        # Class determination
        class_scores = {
            "bec_fraud": bec_score,
            "phishing": phishing_score,
            "impersonation": impersonation_score,
            "suspicious": suspicious_score,
            "legitimate": legit_score
        }

        # If all threats are low, classify as legitimate
        max_threat_val = max(bec_score, phishing_score, impersonation_score, suspicious_score)
        if max_threat_val < 0.35:
            pred_class: ClassificationType = "legitimate"
            fraud_score = round(max(0.02, min(composite_risk * 0.5, 0.30)), 2)
            confidence = round(min(0.95, max(0.70, legit_score)), 2)
        else:
            # Pick highest threat
            threat_items = [
                ("bec_fraud", bec_score),
                ("phishing", phishing_score),
                ("impersonation", impersonation_score),
                ("suspicious", suspicious_score)
            ]
            threat_items.sort(key=lambda x: x[1], reverse=True)
            pred_class = threat_items[0][0]
            fraud_score = round(min(0.99, max(0.40, threat_items[0][1] * 0.85 + composite_risk * 0.15)), 2)
            confidence = round(min(0.98, max(0.65, threat_items[0][1])), 2)

        # Compute feature importance contributions
        feature_importance = self._compute_feature_importance(f)

        return ClassifyResponse(
            classification=pred_class,
            fraud_score=fraud_score,
            confidence=confidence,
            model_version=self.model_version,
            feature_importance=feature_importance
        )

    def _compute_feature_importance(self, f: Dict[str, float]) -> List[FeatureImportance]:
        weights = {
            "lookalike_score": 0.30,
            "impersonation_language_score": 0.26,
            "urgency_score": 0.22,
            "link_risk_scores": 0.25,
            "dmarc_policy": 0.14,
            "spf_authentication": 0.12,
            "domain_age_risk": 0.15,
            "infra_flags": 0.12,
            "header_anomalies_count": 0.10
        }

        val_map = {
            "lookalike_score": f["lookalike_score"],
            "impersonation_language_score": f["impersonation_language_score"],
            "urgency_score": f["urgency_score"],
            "link_risk_scores": f["max_link_risk"],
            "dmarc_policy": f["dmarc_risk"],
            "spf_authentication": f["spf_risk"],
            "domain_age_risk": f["domain_age_risk"],
            "infra_flags": f["infra_risk"],
            "header_anomalies_count": f["header_anomalies_risk"]
        }

        contributions = []
        for name, weight in weights.items():
            val = val_map.get(name, 0.0)
            if val > 0.05:
                contrib = round(val * weight, 3)
                contributions.append((name, contrib))

        contributions.sort(key=lambda x: x[1], reverse=True)
        top_contribs = contributions[:5] if contributions else [("baseline_risk", 0.05)]

        total = sum(c[1] for c in top_contribs)
        results = []
        for name, contrib in top_contribs:
            normalized = round(contrib / total if total > 0 else 0.2, 2)
            results.append(FeatureImportance(feature=name, contribution=normalized))

        return results

classifier_model = FraudClassifier()
