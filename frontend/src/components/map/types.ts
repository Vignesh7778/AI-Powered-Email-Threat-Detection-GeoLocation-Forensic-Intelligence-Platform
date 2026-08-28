export type MapTheme = 'standard' | 'dark' | 'satellite';

export interface InfrastructureNode {
  id: string;
  hop: number;
  ip: string;
  hostname?: string;
  lat?: number | null;
  lon?: number | null;
  asn?: string | null;
  isp?: string | null;
  country?: string | null;
  city?: string | null;
  confidence?: string | number;
  source?: string;
  timestamp?: string;
  risk?: 'critical' | 'high' | 'medium' | 'low' | 'verified' | 'unknown';
  isEarliestPublic?: boolean;
  isPrivate?: boolean;
}

export interface MapThemeConfig {
  name: string;
  url: string;
  attribution: string;
  maxZoom: number;
}
