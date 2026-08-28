export interface UserProfile {
  user_id: string;
  username: string;
  full_name?: string;
  email: string;
  role: 'analyst' | 'admin' | 'investigator';
  tenant_id?: string;
}

export interface AuthResults {
  spf: 'pass' | 'fail' | 'softfail' | 'neutral' | 'none';
  dkim: 'pass' | 'fail' | 'none';
  dmarc: 'pass' | 'fail' | 'none';
  alignment_ok: boolean;
}

export interface GeoLocation {
  country: string;
  region?: string;
  city: string;
  isp: string;
  hosting_provider?: string | null;
  lat?: number | null;
  lon?: number | null;
  asn?: string | null;
  status?: string;
  provenance?: Record<string, any>;
}

export interface OriginInfo {
  originating_ip?: string | null;
  geolocation?: GeoLocation;
  infra_flags: string[];
  confidence?: number;
  reasoning?: string | null;
  provenance?: Record<string, any>;
}

export interface RelayHop {
  hop: number;
  ip?: string | null;
  hostname?: string | null;
  timestamp?: string | null;
  by_host?: string | null;
  with_protocol?: string | null;
}

export interface DomainIntel {
  sender_domain: string;
  domain_age_days?: number | null;
  registrar?: string | null;
  mx_records: string[];
  lookalike_of?: string | null;
  lookalike_score: number;
  dns_records?: Record<string, any>;
  provenance?: Record<string, any>;
}

export interface ThreatIndicator {
  type: string;
  detail: string;
  weight: number;
}

export interface AttributionInfo {
  linked_campaign_id?: string | null;
  related_submission_ids: string[];
  cluster_confidence: number;
}

export interface GroqObservation {
  fact: string;
  evidence_ref: string;
}

export interface GroqInference {
  inference: string;
  reasoning: string;
  confidence: number;
}

export interface GroqAttribution {
  assessment: string;
  confidence: number;
  evidence?: string[];
}

export interface GroqAnalysis {
  status: 'verified' | 'disabled' | 'error';
  model: string;
  grounding_status: 'grounded_in_evidence' | 'unsupported_claim_detected' | 'not_applicable' | 'error_occurred';
  unsupported_claims?: string[];
  assessment: string;
  risk_score: number;
  confidence: number;
  observations: GroqObservation[];
  inferences: GroqInference[];
  unknowns: string[];
  recommendations: string[];
  attribution: GroqAttribution;
  queried_at?: string;
}

export interface FraudAssessment {
  submission_id: string;
  analyzed_at: string;
  fraud_score: number;
  risk_level: string;
  classification: string;
  confidence: number;
  auth_results: AuthResults;
  origin: OriginInfo;
  relay_path: RelayHop[];
  domain_intel: DomainIntel;
  indicators: ThreatIndicator[];
  attribution: AttributionInfo;
  groq_analysis?: GroqAnalysis;
  signal_breakdown?: Record<string, any>;
  processing_mode?: string;
  webhook_status?: string;
}

export interface EmailListItem {
  submission_id: string;
  risk_level: string;
  classification: string;
  fraud_score: number;
  sender?: string;
  recipient?: string;
  subject?: string;
  origin_ip?: string;
  origin_asn?: string;
  timestamp?: string;
  received_at?: string;
  status: string;
}


export interface EmailDetail {
  submission_id: string;
  status: string;
  ingested_at: string;
  file_name?: string;
  sha256_hash?: string;
  sender?: string;
  recipient?: string;
  subject?: string;
  assessment?: FraudAssessment;
}

export interface Case {
  case_id: string;
  title: string;
  status: string;
  severity: string;
  notes?: string;
  assigned_analyst?: string;
  submission_ids: string[];
  created_at?: string;
  updated_at?: string;
}

export interface Alert {
  alert_id: string;
  submission_id: string;
  severity: string;
  fraud_score: number;
  title: string;
  reason: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  triggered_at?: string;
}

export interface DashboardStats {
  total_emails_analyzed: number;
  active_alerts_count: number;
  open_cases_count: number;
  risk_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    clean: number;
  };
  attack_trend_24h: {
    hour: string;
    threats: number;
    legitimate: number;
  }[];
  top_origin_countries: {
    country: string;
    count: number;
  }[];
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface CampaignGraph {
  campaign_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ChainEntry {
  log_id?: string;
  actor: string;
  action: string;
  timestamp: string;
  integrity_hash?: string;
  details?: Record<string, any>;
}

export interface EvidenceChain {
  submission_id: string;
  entries: ChainEntry[];
}
