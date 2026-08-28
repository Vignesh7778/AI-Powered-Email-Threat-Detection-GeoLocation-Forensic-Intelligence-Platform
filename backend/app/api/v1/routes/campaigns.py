from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.core.database import get_db
from backend.app.models.models import Campaign
from backend.graph.graph_engine import graph_engine

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
def list_campaigns_endpoint(db: Session = Depends(get_db)):
    try:
        db_campaigns = db.query(Campaign).all()
        if db_campaigns and len(db_campaigns) > 0:
            return [
                {
                    "campaign_id": c.campaign_id,
                    "name": c.name,
                    "threat_actor": c.threat_actor or "UNC-Threat-Cluster",
                    "description": c.description or "Correlated infrastructure campaign.",
                    "status": c.status or "active",
                    "created_at": c.first_seen.isoformat() if c.first_seen else "2026-08-20T00:00:00Z"
                }
                for c in db_campaigns
            ]
    except Exception:
        pass
    
    # Return known clusters from graph engine
    res = []
    for cid, c in graph_engine.KNOWN_CAMPAIGNS.items():
        res.append({
            "campaign_id": cid,
            "name": c["name"],
            "threat_actor": c.get("threat_actor", "UNC-Threat-Cluster"),
            "description": f"Identified threat campaign correlating {len(c.get('domains', []))} domains, {len(c.get('ips', []))} infrastructure IPs, and shared return paths.",
            "status": "active",
            "created_at": "2026-08-20T00:00:00Z"
        })
    return res

@router.get("/{campaign_id}/graph")
def get_campaign_graph_endpoint(campaign_id: str, db: Session = Depends(get_db)):
    try:
        camp = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
        if camp:
            return graph_engine.get_campaign_graph(campaign_id)
    except Exception:
        pass
    return graph_engine.get_campaign_graph(campaign_id)
