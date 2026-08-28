from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()
_observations: list[dict] = []


class CorrelateRequest(BaseModel):
    submission_id: str
    sender_domain: str
    originating_ip: str
    reply_to: Optional[str] = None
    link_domains: list[str] = Field(default_factory=list)


@router.post("/graph/correlate", status_code=status.HTTP_200_OK)
async def correlate(payload: CorrelateRequest):
    related = [item["submission_id"] for item in _observations if item["sender_domain"] == payload.sender_domain or item["originating_ip"] == payload.originating_ip or (payload.reply_to and item.get("reply_to") == payload.reply_to)]
    _observations.append(payload.model_dump())
    campaign_id = f"campaign-{payload.sender_domain.replace('.', '-')[:36]}" if related else None
    shared = []
    if related:
        shared.append({"type": "domain", "value": payload.sender_domain, "seen_in_count": len(related) + 1})
    return {"linked_campaign_id": campaign_id, "related_submission_ids": related, "cluster_confidence": 0.82 if related else 0.15, "shared_indicators": shared}


@router.get("/graph/campaign/{campaign_id}", status_code=status.HTTP_200_OK)
async def campaign_graph(campaign_id: str):
    domain = campaign_id.removeprefix("campaign-").replace("-", ".")
    records = [item for item in _observations if item["sender_domain"] == domain]
    nodes = [{"id": domain, "type": "domain", "label": domain}]
    edges = []
    for item in records:
        nodes.append({"id": item["submission_id"], "type": "submission", "label": item["submission_id"]})
        edges.append({"source": domain, "target": item["submission_id"], "relation": "sender_domain", "weight": 1.0})
    return {"campaign_id": campaign_id, "nodes": nodes, "edges": edges}
