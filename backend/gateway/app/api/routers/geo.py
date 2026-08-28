"""Geo heatmap route — aggregates origin geolocation from assessment JSON."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Assessment, Submission
from app.schemas.schemas import HeatmapPoint

router = APIRouter()


@router.get("/api/v1/geo/heatmap", response_model=list[HeatmapPoint])
def geo_heatmap(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Aggregate origin geo blocks across assessments into a heatmap.
    Returns one point per (country, region) with count and avg_confidence.
    """
    q = db.query(Assessment).join(
        Submission, Assessment.submission_id == Submission.submission_id
    )

    if from_date:
        try:
            q = q.filter(Submission.ingested_at >= datetime.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            q = q.filter(Submission.ingested_at <= datetime.fromisoformat(to_date))
        except ValueError:
            pass
    if classification:
        q = q.filter(Assessment.classification == classification)
    if min_confidence is not None:
        q = q.filter(Assessment.confidence >= min_confidence)

    # Bucket by (country, region)
    buckets: dict[tuple, dict] = defaultdict(lambda: {"count": 0, "confidence_sum": 0.0, "lat": None, "lon": None})

    for a in q.limit(5000).all():
        try:
            data = json.loads(a.assessment_json)
            geo = data.get("origin", {}).get("geolocation", {})
            country = geo.get("country", "Unknown")
            region = geo.get("region")
            lat = geo.get("lat")
            lon = geo.get("lon")
            confidence = data.get("confidence", 0.0)

            key = (country, region)
            buckets[key]["count"] += 1
            buckets[key]["confidence_sum"] += confidence
            if lat is not None:
                buckets[key]["lat"] = lat
            if lon is not None:
                buckets[key]["lon"] = lon
        except Exception:
            continue

    return [
        HeatmapPoint(
            country=k[0],
            region=k[1],
            lat=v["lat"],
            lon=v["lon"],
            count=v["count"],
            avg_confidence=round(v["confidence_sum"] / v["count"], 4) if v["count"] else 0.0,
        )
        for k, v in sorted(buckets.items(), key=lambda x: -x[1]["count"])
    ]
