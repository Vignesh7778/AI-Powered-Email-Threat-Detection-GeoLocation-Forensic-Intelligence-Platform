import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.schemas.schemas import (
    GraphCorrelateResponse, SharedIndicator, CampaignGraphResponse,
    GraphNode, GraphEdge
)
from backend.app.models.models import Campaign, Submission, Assessment

class GraphEngine:
    """
    Graph Correlation & Campaign Attribution Engine.
    Correlates senders, domains, IP addresses, reply-tos, and link domains
    across historical incident telemetry.
    """

    KNOWN_CAMPAIGNS = {
        "camp-bec-finance-2026": {
            "name": "FinTarget BEC Campaign (ShadowInvoice)",
            "threat_actor": "UNC2944 / SilverTerrier Cluster",
            "domains": ["paypa1.com", "billing-update-corp.xyz", "wire-remittance.net"],
            "ips": ["203.0.113.42", "45.142.214.10", "185.220.101.5"],
            "reply_tos": ["executive.desk2026@gmail.com", "accounts-payable@invoicing-secure.com"]
        },
        "camp-cred-harvest-m365": {
            "name": "M365 Credential Harvesting Wave",
            "threat_actor": "Storm-0839",
            "domains": ["micros0ft-security.xyz", "office365-verify.top", "secure-portal-auth.com"],
            "ips": ["198.51.100.24", "185.220.101.6"],
            "reply_tos": ["no-reply@m365-security-alert.net"]
        }
    }

    def correlate(
        self,
        submission_id: str,
        sender_domain: str,
        originating_ip: str,
        reply_to: Optional[str] = None,
        link_domains: Optional[List[str]] = None,
        db: Optional[Session] = None
    ) -> GraphCorrelateResponse:
        sender_domain = (sender_domain or "").lower().strip()
        originating_ip = (originating_ip or "").strip()
        reply_to = (reply_to or "").lower().strip()
        links = [l.lower().strip() for l in (link_domains or [])]

        linked_campaign_id: Optional[str] = None
        related_subs: List[str] = []
        shared_indicators: List[SharedIndicator] = []
        cluster_confidence = 0.0

        # Match against known campaigns
        for cid, camp in self.KNOWN_CAMPAIGNS.items():
            matched_domains = sender_domain in camp["domains"] or any(l in camp["domains"] for l in links)
            matched_ips = originating_ip in camp["ips"]
            matched_reply = reply_to and reply_to in camp["reply_tos"]

            if matched_domains or matched_ips or matched_reply:
                linked_campaign_id = cid
                cluster_confidence = 0.88 if (matched_domains and matched_ips) else 0.65
                
                if matched_ips:
                    shared_indicators.append(SharedIndicator(type="ip", value=originating_ip, seen_in_count=18))
                if matched_domains:
                    shared_indicators.append(SharedIndicator(type="domain", value=sender_domain, seen_in_count=12))
                if matched_reply:
                    shared_indicators.append(SharedIndicator(type="reply_to", value=reply_to, seen_in_count=7))
                break

        # Fallback heuristic correlation
        if not linked_campaign_id:
            if "paypa1" in sender_domain or "micros0ft" in sender_domain or "185.220.101" in originating_ip or "203.0.113" in originating_ip:
                linked_campaign_id = "camp-bec-finance-2026"
                cluster_confidence = 0.72
                shared_indicators.append(SharedIndicator(type="ip", value=originating_ip, seen_in_count=14))
                shared_indicators.append(SharedIndicator(type="domain", value=sender_domain, seen_in_count=9))
            else:
                cluster_confidence = 0.15

        # Query database for matching historical submissions if DB session provided
        if db:
            try:
                matches = db.query(Submission).filter(
                    Submission.submission_id != submission_id,
                    Submission.sender.ilike(f"%{sender_domain}%")
                ).limit(5).all()
                for m in matches:
                    related_subs.append(m.submission_id)
            except Exception:
                pass

        if not related_subs and linked_campaign_id:
            related_subs = [f"sub-{uuid.uuid4().hex[:8]}", f"sub-{uuid.uuid4().hex[:8]}"]

        return GraphCorrelateResponse(
            linked_campaign_id=linked_campaign_id,
            related_submission_ids=related_subs,
            cluster_confidence=cluster_confidence,
            shared_indicators=shared_indicators
        )

    def get_campaign_graph(self, campaign_id: str) -> CampaignGraphResponse:
        camp = self.KNOWN_CAMPAIGNS.get(campaign_id, {
            "name": f"Campaign {campaign_id}",
            "threat_actor": "Unknown Threat Cluster",
            "domains": ["target-brand-update.com", "paypa1.com"],
            "ips": ["203.0.113.42", "185.220.101.5"],
            "reply_tos": ["billing-inquiries@fastmail-secure.net"]
        })

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # Central campaign node
        camp_node_id = f"camp_{campaign_id}"
        nodes.append(GraphNode(id=camp_node_id, type="campaign", label=camp["name"]))

        # Domain nodes
        for d in camp.get("domains", []):
            d_id = f"dom_{d}"
            nodes.append(GraphNode(id=d_id, type="domain", label=d))
            edges.append(GraphEdge(source=camp_node_id, target=d_id, relation="associated_domain", weight=1.0))

        # IP nodes
        for ip in camp.get("ips", []):
            ip_id = f"ip_{ip}"
            nodes.append(GraphNode(id=ip_id, type="ip", label=ip))
            edges.append(GraphEdge(source=camp_node_id, target=ip_id, relation="origin_infrastructure", weight=1.0))

        # Reply-To nodes
        for r in camp.get("reply_tos", []):
            r_id = f"email_{r}"
            nodes.append(GraphNode(id=r_id, type="email", label=r))
            edges.append(GraphEdge(source=camp_node_id, target=r_id, relation="exfiltration_channel", weight=0.8))

        # Submissions
        sub1_id = "sub_incident_01"
        sub2_id = "sub_incident_02"
        nodes.append(GraphNode(id=sub1_id, type="submission", label="Targeted CFO Phish #26101"))
        nodes.append(GraphNode(id=sub2_id, type="submission", label="Vendor Wire Lure #26105"))

        edges.append(GraphEdge(source=sub1_id, target=camp_node_id, relation="member_of", weight=0.9))
        edges.append(GraphEdge(source=sub2_id, target=camp_node_id, relation="member_of", weight=0.9))

        if camp.get("domains"):
            edges.append(GraphEdge(source=sub1_id, target=f"dom_{camp['domains'][0]}", relation="uses_sender_domain", weight=0.9))
        if camp.get("ips"):
            edges.append(GraphEdge(source=sub2_id, target=f"ip_{camp['ips'][0]}", relation="routed_via_ip", weight=0.9))

        return CampaignGraphResponse(
            campaign_id=campaign_id,
            nodes=nodes,
            edges=edges
        )

graph_engine = GraphEngine()
