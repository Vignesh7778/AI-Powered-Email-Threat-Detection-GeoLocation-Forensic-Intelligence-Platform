from typing import Dict, Any, List
from backend.app.schemas.schemas import MLFeatures, ClassifyResponse, FeatureImportance

class FraudClassifier:
    """
    ML Threat Classification Engine.
    Produces deterministic, explainable multi-class threat categories:
    legitimate, suspicious, impersonation, phishing, bec_fraud.
    """

    def __init__(self, model_version: str = "v4.1.0"):
        self.model_version = model_version

    def _extract_vector(self, f: MLFeatures) -> Dict[str, float]:
        spf_map = {"pass": 0.0, "neutral": 0.3, "softfail": 0.7, "fail": 1.0, "none": 0.5}
        dkim_map = {"pass": 0.0, "fail": 1.0, "none": 0.5}
        dmarc_map = {"pass": 0.0, "fail": 1.0, "none": 0.5}

        spf_risk = spf_map.get((f.auth_results.spf or "none").lower(), 0.5)
        dkim_risk = dkim_map.get((f.auth_results.dkim or "none").lower(), 0.5)
        dmarc_risk = dmarc_map.get((f.auth_results.dmarc or "none").lower(), 0.5)

        domain_age_risk = (1.0 - min(f.domain_age_days / 180.0, 1.0)) if f.domain_age_days is not None else 0.5
        lookalike_score = f.lookalike_score

        infra_weight = 0.0
        for flag in f.infra_flags:
            fl = flag.lower()
            if "tor" in fl:
                infra_weight = max(infra_weight, 0.9)
            elif "vpn" in fl:
                infra_weight = max(infra_weight, 0.5)
            elif "botnet" in fl:
                infra_weight = max(infra_weight, 0.85)
            elif "cloud" in fl or "relay" in fl:
                infra_weight = max(infra_weight, 0.35)

        header_anomalies_risk = min(f.header_anomalies_count * 0.3, 1.0)
        urgency_score = f.urgency_score
        impersonation_score = f.impersonation_language_score

        max_link_risk = max(f.link_risk_scores) if f.link_risk_scores else 0.0

        return {
            "spf_risk": spf_risk,
            "dkim_risk": dkim_risk,
            "dmarc_risk": dmarc_risk,
            "domain_age_risk": domain_age_risk,
            "lookalike_score": lookalike_score,
            "infra_risk": infra_weight,
            "header_anomalies_risk": header_anomalies_risk,
            "urgency_score": urgency_score,
            "impersonation_score": impersonation_score,
            "max_link_risk": max_link_risk
        }

    def classify(self, submission_id: str, features: MLFeatures) -> ClassifyResponse:
        v = self._extract_vector(features)

        # 1. BEC Fraud Score
        bec_score = (
            v["impersonation_score"] * 0.35 +
            v["urgency_score"] * 0.25 +
            v["lookalike_score"] * 0.25 +
            v["dmarc_risk"] * 0.15
        )

        # 2. Phishing Score
        phishing_score = (
            v["max_link_risk"] * 0.40 +
            v["urgency_score"] * 0.20 +
            v["domain_age_risk"] * 0.20 +
            v["spf_risk"] * 0.20
        )

        # 3. Impersonation Score
        impersonation_score = (
            v["lookalike_score"] * 0.45 +
            v["impersonation_score"] * 0.35 +
            v["header_anomalies_risk"] * 0.20
        )

        # 4. Suspicious Score
        suspicious_score = (
            v["infra_risk"] * 0.30 +
            v["header_anomalies_risk"] * 0.30 +
            v["domain_age_risk"] * 0.25 +
            v["spf_risk"] * 0.15
        )

        # Composite overall risk
        composite_risk = (
            v["spf_risk"] * 0.10 +
            v["dkim_risk"] * 0.08 +
            v["dmarc_risk"] * 0.12 +
            v["domain_age_risk"] * 0.10 +
            v["lookalike_score"] * 0.18 +
            v["infra_risk"] * 0.08 +
            v["header_anomalies_risk"] * 0.06 +
            v["urgency_score"] * 0.12 +
            v["impersonation_score"] * 0.14 +
            v["max_link_risk"] * 0.15
        )

        max_threat = max(bec_score, phishing_score, impersonation_score, suspicious_score)

        if max_threat < 0.32:
            pred_class = "legitimate"
            fraud_score = round(max(0.02, min(composite_risk * 0.4, 0.25)), 2)
            confidence = round(min(0.96, max(0.75, 1.0 - composite_risk)), 2)
        else:
            threats = [
                ("bec_fraud", bec_score),
                ("phishing", phishing_score),
                ("impersonation", impersonation_score),
                ("suspicious", suspicious_score)
            ]
            threats.sort(key=lambda x: x[1], reverse=True)
            pred_class = threats[0][0]
            fraud_score = round(min(0.99, max(0.40, threats[0][1] * 0.85 + composite_risk * 0.15)), 2)
            confidence = round(min(0.98, max(0.65, threats[0][1])), 2)

        # Feature importance calculation
        feature_importance = self._compute_feature_importance(v)

        return ClassifyResponse(
            classification=pred_class,
            fraud_score=fraud_score,
            confidence=confidence,
            model_version=self.model_version,
            feature_importance=feature_importance
        )

    def _compute_feature_importance(self, v: Dict[str, float]) -> List[FeatureImportance]:
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
            "lookalike_score": v["lookalike_score"],
            "impersonation_language_score": v["impersonation_score"],
            "urgency_score": v["urgency_score"],
            "link_risk_scores": v["max_link_risk"],
            "dmarc_policy": v["dmarc_risk"],
            "spf_authentication": v["spf_risk"],
            "domain_age_risk": v["domain_age_risk"],
            "infra_flags": v["infra_risk"],
            "header_anomalies_count": v["header_anomalies_risk"]
        }

        contributions = []
        for name, weight in weights.items():
            val = val_map.get(name, 0.0)
            if val > 0.05:
                contrib = round(val * weight, 3)
                contributions.append((name, contrib))

        contributions.sort(key=lambda x: x[1], reverse=True)
        top_contribs = contributions[:5] if contributions else [("baseline_signals", 0.05)]

        total = sum(c[1] for c in top_contribs)
        results = []
        for name, contrib in top_contribs:
            normalized = round(contrib / total if total > 0 else 0.2, 2)
            results.append(FeatureImportance(feature=name, contribution=normalized))

        return results

fraud_classifier = FraudClassifier()
