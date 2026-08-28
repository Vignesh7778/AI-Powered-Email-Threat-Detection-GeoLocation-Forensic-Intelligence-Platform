"""Dashboard routes: summary, trend, top-domains."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Alert, Assessment, Case, Submission
from app.schemas.schemas import DashboardSummary, TrendPoint, TrendResponse

router = APIRouter()


@router.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Aggregate stats for the last 24 hours."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    since_naive = since.replace(tzinfo=None)

    total_24h = db.query(Submission).filter(Submission.ingested_at >= since_naive).count()

    high_risk_24h = (
        db.query(Assessment)
        .join(Submission, Assessment.submission_id == Submission.submission_id)
        .filter(
            Submission.ingested_at >= since_naive,
            Assessment.risk_level.in_(["high", "critical"]),
        )
        .count()
    )

    active_campaigns = db.query(Case).filter(Case.status == "investigating").count()

    high_confidence_fraud_open = (
        db.query(Assessment)
        .join(Submission, Assessment.submission_id == Submission.submission_id)
        .filter(
            Assessment.confidence >= 0.8,
            Assessment.classification.in_(["phishing", "bec_fraud", "impersonation"]),
            Submission.status.notin_(["dismissed", "reviewing"]),
        )
        .count()
    )

    # Top origin countries from assessment JSON
    country_counts: dict[str, int] = defaultdict(int)
    assessments = db.query(Assessment).filter(Assessment.assessment_json != None).limit(500).all()
    for a in assessments:
        try:
            data = json.loads(a.assessment_json)
            country = data.get("origin", {}).get("geolocation", {}).get("country")
            if country:
                country_counts[country] += 1
        except Exception:
            pass
    top_countries = [
        {"country": c, "count": n}
        for c, n in sorted(country_counts.items(), key=lambda x: -x[1])[:10]
    ]

    # avg_time_to_triage: mean of (updated_at - ingested_at) for completed submissions
    completed = db.query(Submission).filter(Submission.status == "reviewing").limit(200).all()
    if completed:
        deltas = [
            (s.updated_at - s.ingested_at).total_seconds()
            for s in completed
            if s.updated_at and s.ingested_at
        ]
        avg_triage = sum(deltas) / len(deltas) if deltas else None
    else:
        avg_triage = None

    return DashboardSummary(
        total_analyzed_24h=total_24h,
        high_risk_24h=high_risk_24h,
        active_campaigns=active_campaigns,
        top_origin_countries=top_countries,
        avg_time_to_triage_seconds=avg_triage,
        high_confidence_fraud_open=high_confidence_fraud_open,
    )


@router.get("/api/v1/dashboard/trend", response_model=TrendResponse)
def dashboard_trend(
    days: int = Query(30, ge=1, le=365),
    granularity: str = Query("day", pattern="^(day|week)$"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Daily/weekly submission + classification breakdown for the trend chart."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_naive = since.replace(tzinfo=None)

    submissions = (
        db.query(Submission)
        .filter(Submission.ingested_at >= since_naive)
        .all()
    )

    buckets: dict[str, dict] = defaultdict(lambda: {"total": 0, "by_classification": defaultdict(int)})
    for sub in submissions:
        dt = sub.ingested_at
        if granularity == "day":
            key = dt.strftime("%Y-%m-%d")
        else:
            # ISO week
            key = f"{dt.isocalendar()[0]}-W{dt.isocalendar()[1]:02d}"

        buckets[key]["total"] += 1
        if sub.assessment and sub.assessment.classification:
            buckets[key]["by_classification"][sub.assessment.classification] += 1

    points = [
        TrendPoint(
            date=date,
            total=data["total"],
            by_classification=dict(data["by_classification"]),
        )
        for date, data in sorted(buckets.items())
    ]
    return TrendResponse(points=points)


@router.get("/api/v1/dashboard/top-domains")
def top_domains(
    window: str = Query("7d"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Top offending sender domains in the given time window."""
    days = 7
    if window.endswith("d"):
        try:
            days = int(window[:-1])
        except ValueError:
            pass

    since = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None)
    submissions = (
        db.query(Submission)
        .filter(Submission.ingested_at >= since)
        .all()
    )

    domain_counts: dict[str, int] = defaultdict(int)
    for sub in submissions:
        if sub.assessment:
            try:
                data = json.loads(sub.assessment.assessment_json)
                domain = data.get("domain_intel", {}).get("sender_domain")
                if domain:
                    domain_counts[domain] += 1
            except Exception:
                pass
        elif sub.sender and "@" in sub.sender:
            domain_counts[sub.sender.split("@")[-1]] += 1

    top = sorted(domain_counts.items(), key=lambda x: -x[1])[:20]
    return {"window": window, "domains": [{"domain": d, "count": c} for d, c in top]}
