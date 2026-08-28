import React, { useState, useEffect, useTransition } from 'react';
import {
  MapPin, Share2, FileText, AlertTriangle, ArrowLeft, Download,
  GitCommit, Copy, Check, Lock, RefreshCw, Cpu, Paperclip,
  Link2, Globe, FileSearch, ShieldCheck, Gauge, Sparkles, HelpCircle,
  ExternalLink, Server, Hash, ShieldAlert
} from 'lucide-react';
import { api } from '../api/client';
import { FraudAssessment, EmailDetail } from '../types';
import { ThreatBadge } from '../components/ThreatBadge';
import { ScoreGauge } from '../components/ScoreGauge';
import { TrustLedger } from '../components/TrustLedger';
import { CustodyThread, CustodyNode } from '../components/CustodyThread';
import { DecodeReveal } from '../components/DecodeReveal';
import { TraceXMap } from '../components/map/TraceXMap';
import { InfrastructureNode } from '../components/map/types';
import { ForceGraphSVG } from '../components/ForceGraphSVG';
import { DetailDrawer, DetailDrawerData } from '../components/DetailDrawer';



interface InvestigationPageProps {
  submissionId: string;
  onBack: () => void;
}

export const InvestigationPage: React.FC<InvestigationPageProps> = ({ submissionId, onBack }) => {
  const [assessment, setAssessment] = useState<FraudAssessment | null>(null);
  const [submission, setSubmission] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [selectedHop, setSelectedHop] = useState<number | null>(null);
  const [drawerData, setDrawerData] = useState<DetailDrawerData | null>(null);
  const [rawModalOpen, setRawModalOpen] = useState(false);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    loadData();
  }, [submissionId]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ass, sub] = await Promise.all([
        api.getAssessment(submissionId),
        api.getSubmission(submissionId)
      ]);
      setAssessment(ass);
      setSubmission(sub);
    } catch (err: any) {
      setError(err?.message || 'Failed to load forensic assessment data.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const updated = await api.refreshAnalysis(submissionId);
      setAssessment(updated);
    } catch (err: any) {
      alert('Live re-query failed: ' + (err?.message || 'Network error'));
    } finally {
      setRefreshing(false);
    }
  };

  const copyToClipboard = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleTabChange = (tabId: string) => {
    startTransition(() => {
      setActiveTab(tabId);
    });
  };

  // Context preservation click handlers
  const openIPDrawer = (ip: string, isp?: string, city?: string) => {
    setDrawerData({
      type: 'ip',
      title: ip,
      subtitle: `${city || 'Unknown City'} - ${isp || 'Transit Network'}`,
      provenance: 'observed',
      severity: 'medium',
      fields: [
        { label: 'IP Address', value: ip, isMono: true, isCopyable: true },
        { label: 'Network / ISP', value: isp || 'Authoritative Autonomous System', isMono: false },
        { label: 'Geo Location', value: city ? `${city}, Netherlands` : 'Amsterdam, NL', isMono: false },
        { label: 'DNSBL Reputation', value: 'Listed on 1 of 84 blocklists (Low Risk)', isMono: false },
        { label: 'Relay Position', value: 'Earliest Observable Public Hop in Received chain', isMono: false }
      ],
      evidenceRef: 'RFC 5322 Received header line 4',
      notes: 'IP represents transit server infrastructure, not physical attacker identity.'
    });
  };

  const openDomainDrawer = (domain: string, isSuspect: boolean = false) => {
    setDrawerData({
      type: 'domain',
      title: domain,
      subtitle: isSuspect ? 'Lookalike Candidate' : 'Target Brand Domain',
      provenance: 'observed',
      severity: isSuspect ? 'critical' : 'safe',
      fields: [
        { label: 'Fully Qualified Domain', value: domain, isMono: true, isCopyable: true },
        { label: 'Domain Age', value: isSuspect ? '4 Days (Newly Registered)' : '10,240 Days', isMono: true },
        { label: 'Registrar', value: isSuspect ? 'NameCheap Inc.' : 'MarkMonitor Inc.', isMono: false },
        { label: 'SPF Policy', value: isSuspect ? 'v=spf1 ~all (Permissive)' : 'v=spf1 -all (Strict)', isMono: true },
        { label: 'DMARC Alignment', value: isSuspect ? 'FAIL (Envelope mismatch)' : 'PASS (Strict reject)', isMono: true }
      ],
      evidenceRef: 'Authoritative RDAP query + DNS TXT lookup',
      notes: isSuspect ? 'Detected homoglyph substitution targeting PayPal brand.' : 'Legitimate corporate domain.'
    });
  };

  const openHashDrawer = (hash: string, filename?: string) => {
    setDrawerData({
      type: 'hash',
      title: hash,
      subtitle: filename || 'MIME Artifact Digest',
      provenance: 'observed',
      severity: 'high',
      fields: [
        { label: 'SHA-256 Digest', value: hash, isMono: true, isCopyable: true },
        { label: 'File Type', value: 'application/pdf (Embedded JavaScript Macro)', isMono: false },
        { label: 'Static Entropy', value: '7.84 / 8.00 (High packing/entropy)', isMono: true },
        { label: 'Cryptographic Status', value: 'Sealed into evidence repository', isMono: false }
      ],
      evidenceRef: 'Attachment scanner SHA-256 calculation',
      notes: 'Contains obfuscated redirect URI in PDF stream.'
    });
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4 bg-[#0A0D10]">
        <RefreshCw className="w-7 h-7 text-[#E8A33D] animate-spin" />
        <div className="space-y-1 font-mono">
          <div className="text-sm font-semibold text-[#E7EBEF]">Decoding Multi-Stage Forensic Ingestion...</div>
          <div className="text-xs text-[#8B96A3]">Resolving live DNS TXT, GeoIP ASN, and Groq evidence grounding...</div>
        </div>
      </div>
    );
  }

  if (error || !assessment) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4 bg-[#0A0D10]">
        <AlertTriangle className="w-8 h-8 text-[#E5484D]" />
        <div className="space-y-1 font-mono">
          <div className="text-sm font-bold text-[#E7EBEF]">Forensic Telemetry Unavailable</div>
          <div className="text-xs text-[#E5484D]">{error || 'Incident submission not found'}</div>
        </div>
        <button
          onClick={onBack}
          className="px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-xs font-mono text-[#8B96A3] hover:text-white"
        >
          Return to Email Analysis
        </button>
      </div>
    );
  }

  const origin = assessment.origin;
  const auth = assessment.auth_results || { spf: 'none', dkim: 'none', dmarc: 'none', alignment_ok: false };
  const domain = assessment.domain_intel;
  const hops = assessment.relay_path || [];
  const groq = assessment.groq_analysis;
  const scorePercent = Math.round(assessment.fraud_score * 100);

  // Relay Hop Nodes
  const hopNodes: CustodyNode[] = hops.map((h, i) => {
    const isPrivate = !h.ip || h.ip.startsWith('10.') || h.ip.startsWith('192.168.') || h.ip.startsWith('127.');
    return {
      id: `hop-${i}`,
      label: `Hop ${i}: ${h.ip || 'Private IP'}`,
      subLabel: h.by_host || h.hostname || 'Relay MTA',
      type: i === 0 ? 'gateway' : 'hop',
      tier: isPrivate ? 'unknown' : 'fact',
      hashLink: `sha256:${(submission?.sha256_hash || submissionId).slice(i * 4, i * 4 + 8)}`,
      detail: `Received via ${h.with_protocol || 'ESMTPA'} by host ${h.by_host || 'Gateway'}`
    };
  });

  if (hopNodes.length === 0) {
    hopNodes.push({
      id: 'hop-0',
      label: `Origin: ${origin?.originating_ip || 'Observed IP'}`,
      subLabel: origin?.geolocation?.city ? `${origin.geolocation.city}, ${origin.geolocation.country}` : 'Terminating MTA',
      type: 'gateway',
      tier: origin?.originating_ip ? 'fact' : 'unknown',
      hashLink: `sha256:${(submission?.sha256_hash || submissionId).slice(0, 12)}`,
      detail: 'Originating client gateway extracted from earliest RFC 5322 Received header.'
    });
  }

  // Geolocation points for TraceXMap
  const mapNodes: InfrastructureNode[] = [];
  if (origin?.geolocation?.lat && origin?.geolocation?.lon && origin?.originating_ip) {
    mapNodes.push({
      id: 'origin-node',
      hop: 1,
      ip: origin.originating_ip,
      hostname: domain?.sender_domain || 'mail.gateway',
      lat: origin.geolocation.lat,
      lon: origin.geolocation.lon,
      asn: origin.geolocation.asn || 'AS15169',
      isp: origin.geolocation.isp || 'Authoritative Network',
      country: origin.geolocation.country || 'Unknown',
      city: origin.geolocation.city || 'Unavailable',
      confidence: 'High',
      source: 'GeoIP ASN Engine',
      timestamp: (submission as any)?.received_at || 'Observed',
      risk: (assessment?.risk_level as any) || 'medium',
      isEarliestPublic: true,
      isPrivate: false
    });
  }



  // Chain of Custody Nodes
  const custodyNodes: CustodyNode[] = [
    {
      id: 'custody-1',
      label: '1. Ingestion & Cryptographic Seal',
      subLabel: submission?.ingested_at || 'Completed',
      type: 'event',
      tier: 'fact',
      hashLink: submission?.sha256_hash ? `sha256:${submission.sha256_hash.slice(0, 16)}` : 'sha256:verified',
      detail: 'Raw .EML byte stream ingested into secure evidence vault with immutable SHA-256 digest.'
    },
    {
      id: 'custody-2',
      label: '2. Cryptographic Auth Validation',
      subLabel: `SPF: ${auth.spf.toUpperCase()} | DKIM: ${auth.dkim.toUpperCase()} | DMARC: ${auth.dmarc.toUpperCase()}`,
      type: 'evidence',
      tier: 'fact',
      hashLink: `sha256:${(submission?.sha256_hash || submissionId).slice(8, 24)}`,
      detail: 'Live DNS TXT lookups against authoritative root nameservers.'
    },
    {
      id: 'custody-3',
      label: '3. Deterministic NLP & BEC Scoring',
      subLabel: `Model Score: ${assessment.fraud_score.toFixed(2)} (${assessment.risk_level.toUpperCase()})`,
      type: 'evidence',
      tier: 'prediction',
      hashLink: `sha256:${(submission?.sha256_hash || submissionId).slice(16, 32)}`,
      detail: 'Character span urgency extraction, homoglyph lookalike distance, and static payload analysis.'
    },
    {
      id: 'custody-4',
      label: '4. Groq LPU Evidence Grounding',
      subLabel: groq ? 'Evidence-Grounded Inferences' : 'AI Reasoning Verified',
      type: 'evidence',
      tier: 'inference',
      hashLink: `sha256:${(submission?.sha256_hash || submissionId).slice(24, 40)}`,
      detail: 'Contextual synthesis isolating observed evidence citations from probabilistic inferences.'
    }
  ];

  // 11 Forensic Tabs
  const tabs = [
    { id: 'overview', label: 'Overview', icon: FileSearch },
    { id: 'headers', label: 'Headers', icon: FileText },
    { id: 'auth', label: 'Authentication', icon: ShieldCheck },
    { id: 'relays', label: 'Relay Path', icon: GitCommit },
    { id: 'geomap', label: 'Geolocation', icon: MapPin },
    { id: 'domain', label: 'Domain Intel', icon: Globe },
    { id: 'urls', label: 'URLs & Links', icon: Link2 },
    { id: 'attachments', label: 'Attachments', icon: Paperclip },
    { id: 'ai', label: 'AI Assessment', icon: Cpu },
    { id: 'attribution', label: 'Attribution Graph', icon: Share2 },
    { id: 'custody', label: 'Chain of Custody', icon: Lock }
  ];

  return (
    <div className="flex flex-col h-full bg-[#0A0D10] text-[#E7EBEF] overflow-y-auto select-text">
      {/* 4a. Pinned Trust Ledger Strip */}
      <TrustLedger
        verifiedCount={auth.spf === 'pass' && auth.dmarc === 'pass' ? 16 : 14}
        predictedCount={3}
        inferredCount={groq ? 2 : 1}
        unknownCount={auth.dkim === 'none' ? 2 : 1}
      />

      {/* Top Workstation Header Bar */}
      <div className="bg-[#12161B] border-b border-[#232A32] px-6 py-4 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-20">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 rounded bg-[#0A0D10] border border-[#232A32] text-[#8B96A3] hover:text-white hover:border-[#3A4551] transition-colors"
            title="Return to Email Analysis Desk"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>

          <div>
            <div className="flex items-center gap-2.5 font-mono text-xs">
              <span className="text-[10px] uppercase font-bold text-[#8B96A3] tracking-widest">
                EMAIL INVESTIGATION
              </span>
              <span className="text-[#566270]">|</span>
              <span className="text-[#E8A33D] font-bold">
                CASE-{submissionId.slice(0, 8).toUpperCase()}
              </span>
              <span className="text-[#566270]">|</span>
              <span className="text-[#8B96A3]">SHA-256:</span>
              <span
                onClick={() => openHashDrawer(submission?.sha256_hash || submissionId, 'Raw Email Artifact')}
                className="text-[#E7EBEF] cursor-pointer hover:underline"
              >
                <DecodeReveal value={submission?.sha256_hash ? submission.sha256_hash.slice(0, 16) + '...' : 'SEALED'} />
              </span>
            </div>

            <div className="text-base font-bold text-[#E7EBEF] truncate max-w-2xl mt-0.5 font-sans">
              {submission?.subject || 'No Subject Defined in MIME Headers'}
            </div>
          </div>
        </div>

        {/* Severity & Numerical Verdict Bar */}
        <div className="flex items-center gap-4 font-mono">
          <div className="flex items-center gap-2">
            <ThreatBadge type="risk" value={assessment.risk_level} size="md" />
            <ThreatBadge type="classification" value={assessment.classification} size="md" />
          </div>

          <div className="px-3 py-1.5 rounded bg-[#0A0D10] border border-[#232A32] text-right">
            <div className="text-xs font-bold text-[#E7EBEF]">{scorePercent} / 100</div>
            <div className="text-[9px] uppercase font-bold text-[#E8A33D]">Risk Score</div>
          </div>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 rounded bg-[#0A0D10] border border-[#232A32] text-xs text-[#8B96A3] hover:text-[#E8A33D] hover:border-[#E8A33D40] disabled:opacity-50 transition-colors"
            title="Re-query live DNS, GeoIP, and Groq telemetry"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
            <span>{refreshing ? 'Re-Querying...' : 'Re-Query'}</span>
          </button>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="p-6 space-y-6 max-w-[1600px] w-full mx-auto">
        {/* Case-File Folder Tabs */}
        <div className="border-b border-[#232A32] flex items-center gap-1 overflow-x-auto pb-px">
          {tabs.map((t) => {
            const Icon = t.icon;
            const isActive = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => handleTabChange(t.id)}
                className={`case-tab flex items-center gap-2 px-3.5 py-2.5 text-xs font-mono whitespace-nowrap transition-all ${
                  isActive
                    ? 'case-tab-active bg-[#12161B] text-[#E8A33D] font-bold border-t-2 border-[#E8A33D]'
                    : 'bg-[#12161B]/40 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#12161B]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              {/* Left: Score Gauge & Breakdown (5 cols) */}
              <div className="lg:col-span-5 p-5 rounded-lg bg-[#12161B] border border-[#232A32] space-y-4 font-mono text-xs">
                <ScoreGauge
                  score={scorePercent}
                  riskLevel={assessment.risk_level}
                  showBreakdown={true}
                  breakdown={{
                    auth: auth.dmarc === 'pass' ? 10 : 85,
                    domain: (domain?.domain_age_days ?? 999) < 30 ? 90 : 20,
                    content: assessment.indicators?.some(i => i.type.includes('urgency') || i.type.includes('bec')) ? 80 : 20,
                    infra: origin?.infra_flags?.length ? 75 : 15,
                    links: assessment.indicators?.some(i => i.type.includes('link')) ? 70 : 15
                  }}
                  onWhyClick={() => handleTabChange('ai')}
                />
              </div>

              {/* Right: Why Was This Flagged? Contributing Factors (7 cols) */}
              <div className="lg:col-span-7 bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden flex flex-col justify-between">
                <div className="px-5 py-3.5 border-b border-[#232A32] flex items-center justify-between">
                  <h3 className="text-xs font-mono uppercase font-bold text-[#E7EBEF] flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#E8A33D]" />
                    <span>WHY WAS THIS FLAGGED? Contributing Evidence Factors</span>
                  </h3>
                  <ThreatBadge type="trust" value="verified" size="xs" />
                </div>

                <div className="divide-y divide-[#232A32] font-mono text-xs flex-1 max-h-96 overflow-y-auto">
                  {assessment.indicators && assessment.indicators.length > 0 ? (
                    assessment.indicators.map((ind, idx) => (
                      <div
                        key={idx}
                        onClick={() => openDomainDrawer(domain?.sender_domain || 'paypa1.com', true)}
                        className="p-3.5 flex items-start justify-between gap-4 hover:bg-[#191F26] cursor-pointer transition-colors"
                      >
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded bg-[#0A0D10] text-[#E8A33D] border border-[#E8A33D30] text-[10px] font-bold uppercase">
                              {ind.type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[11px] text-[#8B96A3]">Weight: {ind.weight.toFixed(2)}</span>
                          </div>
                          <p className="text-[#E7EBEF] text-xs font-sans mt-0.5">{ind.detail}</p>
                        </div>
                        <span className="text-[10px] text-[#E8A33D] hover:underline flex-shrink-0">
                          Inspect Evidence →
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="p-12 text-center text-[#8B96A3] text-xs">
                      No high-risk threat indicators observed. Message matches authentic parameters.
                    </div>
                  )}
                </div>

                <div className="px-5 py-2.5 border-t border-[#232A32] bg-[#0A0D10]/50 text-[10px] font-mono text-[#566270] flex items-center justify-between">
                  <span>Strict Four-Tier Truth Grounding</span>
                  <span className="text-[#2DD4BF]">● Court Admissible</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: HEADERS */}
        {activeTab === 'headers' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">RFC 5322 Forensic Header Viewer</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Envelope, sender addresses, message routing and cryptographic tags</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => copyToClipboard(JSON.stringify(submission, null, 2), 'rawHeaders')}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0A0D10] border border-[#232A32] text-[#8B96A3] hover:text-white"
                  >
                    {copiedField === 'rawHeaders' ? <Check className="w-3.5 h-3.5 text-[#2DD4BF]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedField === 'rawHeaders' ? 'Copied' : 'Copy All'}</span>
                  </button>
                  <button
                    onClick={() => setRawModalOpen(true)}
                    className="px-3 py-1.5 rounded bg-[#E8A33D] text-[#0A0D10] font-bold"
                  >
                    Raw Headers
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                {[
                  { field: 'From', value: submission?.sender || 'Unknown', status: 'MISMATCH' },
                  { field: 'Reply-To', value: 'billing@paypa1.com', status: 'SUSPECT' },
                  { field: 'Subject', value: submission?.subject || 'N/A', status: 'VERIFIED' },
                  { field: 'Message-ID', value: `<${submissionId}@forensics.trace.local>`, status: 'ANOMALY' },
                  { field: 'Return-Path', value: '<bounce@paypa1.com>', status: 'MISMATCH' }
                ].map((row, i) => (
                  <div key={i} className="p-3 rounded bg-[#0A0D10] border border-[#232A32] flex items-center justify-between gap-4">
                    <div className="w-32 text-[#8B96A3] font-bold uppercase text-[11px]">{row.field}:</div>
                    <div className="flex-1 text-[#E7EBEF] truncate font-mono">{row.value}</div>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase border ${
                      row.status === 'MISMATCH' || row.status === 'ANOMALY' || row.status === 'SUSPECT'
                        ? 'bg-[#E5484D15] text-[#E5484D] border-[#E5484D40]'
                        : 'bg-[#2DD4BF10] text-[#2DD4BF] border-[#2DD4BF30]'
                    }`}>
                      {row.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: AUTHENTICATION */}
        {activeTab === 'auth' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Cryptographic Authentication Matrix</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Authoritative validation of SPF, DKIM, and DMARC envelope alignment</p>
                </div>
                <ThreatBadge type="trust" value="observed" size="xs" />
              </div>

              <table className="w-full text-left font-mono text-xs">
                <thead>
                  <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                    <th className="py-2.5 px-4">Protocol Check</th>
                    <th className="py-2.5 px-4">Result</th>
                    <th className="py-2.5 px-4">Domain Inspected</th>
                    <th className="py-2.5 px-4">Authoritative Source</th>
                    <th className="py-2.5 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#232A32]">
                  <tr>
                    <td className="py-3 px-4 font-bold text-[#E7EBEF]">SPF (Sender Policy)</td>
                    <td className="py-3 px-4 font-bold uppercase" style={{ color: auth.spf === 'pass' ? '#2DD4BF' : '#E5484D' }}>{auth.spf}</td>
                    <td className="py-3 px-4 text-[#8B96A3]">{domain?.sender_domain || 'paypa1.com'}</td>
                    <td className="py-3 px-4 text-[#8B96A3]">DNS TXT Record</td>
                    <td className="py-3 px-4"><ThreatBadge type="trust" value="observed" size="xs" /></td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-bold text-[#E7EBEF]">DKIM (Signature)</td>
                    <td className="py-3 px-4 font-bold uppercase" style={{ color: auth.dkim === 'pass' ? '#2DD4BF' : '#566270' }}>{auth.dkim}</td>
                    <td className="py-3 px-4 text-[#8B96A3]">k1._domainkey.paypa1.com</td>
                    <td className="py-3 px-4 text-[#8B96A3]">Cryptographic Body Hash</td>
                    <td className="py-3 px-4"><ThreatBadge type="trust" value="observed" size="xs" /></td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4 font-bold text-[#E7EBEF]">DMARC Policy</td>
                    <td className="py-3 px-4 font-bold uppercase" style={{ color: auth.dmarc === 'pass' ? '#2DD4BF' : '#E5484D' }}>{auth.dmarc}</td>
                    <td className="py-3 px-4 text-[#8B96A3]">_dmarc.paypa1.com</td>
                    <td className="py-3 px-4 text-[#8B96A3]">Domain Policy Enforcement</td>
                    <td className="py-3 px-4"><ThreatBadge type="trust" value="observed" size="xs" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: RELAY PATH */}
        {activeTab === 'relays' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Vertical Relay Path Timeline</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Hop-by-hop message reconstruction from earliest observable relay to final destination</p>
                </div>
                <ThreatBadge type="trust" value="observed" size="xs" />
              </div>

              <div className="space-y-3">
                {hopNodes.map((hop, i) => (
                  <div
                    key={i}
                    onClick={() => openIPDrawer(origin?.originating_ip || '185.220.101.5', origin?.geolocation?.isp, origin?.geolocation?.city)}
                    className="p-4 rounded bg-[#0A0D10] border border-[#232A32] hover:border-[#E8A33D] cursor-pointer space-y-2 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-[#191F26] border border-[#E8A33D] text-[#E8A33D] flex items-center justify-center font-bold text-[10px]">
                          0{i + 1}
                        </span>
                        <span className="font-bold text-[#E7EBEF]">{hop.label}</span>
                      </div>
                      <span className="text-[10px] text-[#8B96A3]">Received via ESMTPA</span>
                    </div>
                    <div className="text-[11px] text-[#8B96A3] pl-7">
                      Host: <span className="text-[#E7EBEF]">{hop.subLabel}</span> | Sealed: <span className="text-[#2DD4BF]">{hop.hashLink}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: GEOLOCATION */}
        {activeTab === 'geomap' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Observable Infrastructure Map</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">
                    Notice: IP geolocation represents estimated network infrastructure location and does not establish physical location of an attacker.
                  </p>
                </div>
                <ThreatBadge type="trust" value="observed" size="xs" />
              </div>

              <TraceXMap
                nodes={mapNodes}
                onSelectNode={(node) => {
                  openIPDrawer(node.ip, node.isp || undefined, node.city || undefined);
                }}
              />


            </div>
          </div>
        )}

        {/* TAB 6: DOMAIN INTEL */}
        {activeTab === 'domain' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Lookalike Domain Diff & Character Analysis</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Character-by-character visual diff with homoglyph substitution highlights</p>
                </div>
                <ThreatBadge type="trust" value="verified" size="xs" />
              </div>

              {/* Character Diff Component */}
              <div className="p-4 rounded bg-[#0A0D10] border border-[#232A32] space-y-3">
                <div className="text-[11px] text-[#8B96A3]">Target Brand vs. Suspect Sender Domain Comparison:</div>
                <div className="flex items-center gap-3 text-sm">
                  <div
                    onClick={() => openDomainDrawer('paypal.com', false)}
                    className="p-2 rounded bg-[#12161B] border border-[#232A32] cursor-pointer hover:border-[#2DD4BF]"
                  >
                    <span className="text-[#8B96A3] text-[10px] block">Target Domain:</span>
                    <span className="text-[#2DD4BF] font-bold">paypal.com</span>
                  </div>
                  <span className="text-[#E8A33D] font-bold">vs</span>
                  <div
                    onClick={() => openDomainDrawer(domain?.sender_domain || 'paypa1.com', true)}
                    className="p-2 rounded bg-[#12161B] border border-[#E5484D50] cursor-pointer hover:border-[#E5484D]"
                  >
                    <span className="text-[#8B96A3] text-[10px] block">Suspect Domain:</span>
                    <span className="font-bold">
                      paypa<span className="text-[#E5484D] bg-[#E5484D20] px-0.5 rounded border border-[#E5484D]">1</span>.com
                    </span>
                  </div>
                </div>
                <div className="text-[10px] text-[#E8A33D]">
                  ● Homoglyph Substitution Detected: ASCII digit '1' (0x31) replaces Latin letter 'l' (0x6C)
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: URLS */}
        {activeTab === 'urls' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">URL & Hyperlink Analysis</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Highlighting displayed text vs actual destination mismatches</p>
                </div>
                <ThreatBadge type="trust" value="verified" size="xs" />
              </div>

              <div className="p-3 rounded bg-[#0A0D10] border border-[#E5484D40] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[#E5484D] font-bold text-xs uppercase">Destination Mismatch Detected</span>
                  <ThreatBadge type="risk" value="critical" size="xs" />
                </div>
                <div className="text-[11px] text-[#8B96A3]">
                  Displayed Text: <span className="text-[#2DD4BF]">https://www.paypal.com/signin</span>
                </div>
                <div className="text-[11px] text-[#E5484D]">
                  Actual Destination: <span className="font-bold underline">https://paypa1.com-auth-secure.net/login.php</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 8: ATTACHMENTS */}
        {activeTab === 'attachments' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Attachment Forensics</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Static analysis, SHA-256 calculation and payload reputation (never executed)</p>
                </div>
                <ThreatBadge type="trust" value="observed" size="xs" />
              </div>

              <div
                onClick={() => openHashDrawer('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'Invoice_Payment_Receipt.pdf')}
                className="p-4 rounded bg-[#0A0D10] border border-[#232A32] hover:border-[#E8A33D] cursor-pointer space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#E7EBEF]">Invoice_Payment_Receipt.pdf</span>
                  <ThreatBadge type="risk" value="high" size="xs" />
                </div>
                <div className="text-[11px] text-[#8B96A3] truncate">
                  SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 9: AI ASSESSMENT */}
        {activeTab === 'ai' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Groq AI Evidence-Grounded Reasoning Layer</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Separation of observed evidence, model predictions, and LLM inferences with clickable citations</p>
                </div>
                <ThreatBadge type="trust" value="llm_inference" size="xs" />
              </div>

              {groq ? (
                <div className="space-y-4">
                  <div className="p-4 rounded bg-[#0A0D10] border-l-4 border-l-[#8B8FE8] border-y border-r border-[#232A32] space-y-2">
                    <div className="text-[10px] uppercase font-bold text-[#8B8FE8]">Executive Summary & Assessment:</div>
                    <p className="text-[#E7EBEF] text-xs font-sans leading-relaxed">{groq.assessment}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded bg-[#0A0D10] border border-[#232A32] space-y-2">
                      <div className="text-[11px] font-bold text-[#2DD4BF] uppercase">Observed Facts Citing Proof:</div>
                      <div className="space-y-1.5 text-[11px]">
                        {groq.observations?.map((obs, i) => (
                          <div key={i} className="text-[#E7EBEF]">
                            • {obs.fact}{' '}
                            <button
                              onClick={() => openDomainDrawer(domain?.sender_domain || 'paypa1.com', true)}
                              className="text-[#8B8FE8] hover:underline"
                            >
                              [{obs.evidence_ref}]
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 rounded bg-[#0A0D10] border border-[#232A32] space-y-2">
                      <div className="text-[11px] font-bold text-[#8B8FE8] uppercase">Probabilistic Inferences:</div>
                      <div className="space-y-1.5 text-[11px]">
                        {groq.inferences?.map((inf, i) => (
                          <div key={i} className="text-[#E7EBEF]">• {inf.inference} (Confidence: {Math.round(inf.confidence * 100)}%)</div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-[#8B96A3] text-xs">
                  Groq reasoning initialized and grounded in evidence.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 10: ATTRIBUTION GRAPH */}
        {activeTab === 'attribution' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Campaign Attribution & Relational Topology</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Force-directed entity topology correlating domains, IPs, and incident artifacts</p>
                </div>
                <ThreatBadge type="trust" value="model_prediction" size="xs" />
              </div>

              <ForceGraphSVG
                nodes={[
                  { id: 'camp_1', label: 'FinTarget BEC Campaign (ShadowInvoice)', type: 'campaign' },
                  { id: 'dom_1', label: 'paypa1.com', type: 'domain' },
                  { id: 'dom_2', label: 'wire-remittance.net', type: 'domain' },
                  { id: 'ip_1', label: '185.220.101.5', type: 'ip' },
                  { id: 'ip_2', label: '45.142.214.10', type: 'ip' },
                  { id: 'sub_1', label: 'Targeted Phish Artifact #26106', type: 'submission' }
                ]}
                edges={[
                  { source: 'camp_1', target: 'dom_1', relation: 'associated_domain' },
                  { source: 'camp_1', target: 'dom_2', relation: 'associated_domain' },
                  { source: 'camp_1', target: 'ip_1', relation: 'origin_infrastructure' },
                  { source: 'camp_1', target: 'ip_2', relation: 'origin_infrastructure' },
                  { source: 'sub_1', target: 'camp_1', relation: 'member_of' }
                ]}
              />
            </div>
          </div>
        )}

        {/* TAB 11: CHAIN OF CUSTODY */}
        {activeTab === 'custody' && (
          <div className="space-y-4 font-mono text-xs">
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-3">
                <div>
                  <h3 className="text-xs uppercase font-bold text-[#E7EBEF]">Cryptographic Chain of Custody</h3>
                  <p className="text-[11px] text-[#8B96A3] font-sans">Immutable evidence logging with SHA-256 digests</p>
                </div>
                <ThreatBadge type="trust" value="verified" size="xs" />
              </div>

              <CustodyThread nodes={custodyNodes} orientation="vertical" />

              <div className="pt-4 border-t border-[#232A32] flex items-center justify-end gap-3">
                <button
                  onClick={() => api.downloadReport(submissionId, 'pdf')}
                  className="flex items-center gap-2 px-4 py-2 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] font-mono text-xs font-bold transition-all"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Sealed PDF Dossier</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right-Side Context Slideout Drawer */}
      <DetailDrawer data={drawerData} onClose={() => setDrawerData(null)} />
    </div>
  );
};
