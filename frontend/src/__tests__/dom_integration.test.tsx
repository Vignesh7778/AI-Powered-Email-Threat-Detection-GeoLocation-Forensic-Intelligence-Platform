import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { ThreatBadge } from '../components/ThreatBadge';
import { ScoreGauge } from '../components/ScoreGauge';
import { DetailDrawer } from '../components/DetailDrawer';
import { IngestModal } from '../components/IngestModal';
import { Navbar } from '../components/Navbar';
import { Sidebar } from '../components/Sidebar';
import { DashboardPage } from '../pages/DashboardPage';
import { ThreatInboxPage } from '../pages/ThreatInboxPage';
import { InvestigationPage } from '../pages/InvestigationPage';
import { MapPage } from '../pages/MapPage';
import { CampaignsPage } from '../pages/CampaignsPage';
import { AlertsPage } from '../pages/AlertsPage';
import { ReportsPage } from '../pages/ReportsPage';
import { CasesPage } from '../pages/CasesPage';
import { SettingsPage } from '../pages/SettingsPage';
import { App } from '../App';
import { api } from '../api/client';

const mockEmailDetail: any = {
  submission_id: '970a9e1e-test',
  headers: {
    'Message-ID': '<test-case-msg@bank.com>',
    From: 'attacker@evil-spoof.com',
    To: 'victim@target.org',
    Subject: 'Urgent Wire Transfer Request',
    Date: 'Thu, 28 Aug 2026 14:22:18 +0000',
    Received: ['from mail.evil-spoof.com (185.220.101.5) by mx.google.com']
  },
  auth_results: {
    spf: { result: 'fail', sender_ip: '185.220.101.5', domain: 'evil-spoof.com' },
    dkim: { result: 'fail', selector: 'default', domain: 'evil-spoof.com' },
    dmarc: { result: 'fail', policy: 'reject', disposition: 'reject' }
  },
  hops: [
    {
      hop_number: 1,
      from_host: 'mail.evil-spoof.com',
      by_host: 'mx.google.com',
      ip: '185.220.101.5',
      delay_sec: 1.2,
      geo: { lat: 52.3676, lon: 4.9041, city: 'Amsterdam', country: 'Netherlands', asn: 'AS15169', org: 'Google LLC' }
    }
  ],
  domain_intel: {
    domain: 'evil-spoof.com',
    registrar: 'NameCheap Inc.',
    created_date: '2026-08-01T00:00:00Z',
    domain_age_days: 28,
    is_newly_registered: true,
    dnsbl_listings: ['Spamhaus ZEN', 'Barracuda BRBL']
  },
  links: [
    { url: 'https://evil-spoof.com/login', domain: 'evil-spoof.com', is_ip: false, is_shortened: false, threat_type: 'phishing' }
  ],
  attachments: [
    { filename: 'invoice.pdf.exe', size: 1048576, mime_type: 'application/x-dosexec', sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', is_executable: true }
  ],
  assessment: {
    overall_score: 94.5,
    risk_level: 'critical',
    classification: 'phishing',
    confidence: 0.98,
    indicators: ['SPF fail', 'Executable attachment', 'New domain'],
    explainability: 'Sender identity spoofed with executable malware payload.',
    factor_breakdown: { auth: 95, domain: 90, content: 85, infra: 90, links: 95 }
  },
  evidence_chain: {
    chain_id: 'chn-970a9e1e',
    hash: 'sha256-evidence-seal-mock',
    signature: 'rsa-sig-verified',
    verified: true,
    entries: [
      { timestamp: '2026-08-28T14:22:18Z', action: 'INGESTION', actor: 'SYSTEM_DAEMON', hash: 'hash1' }
    ]
  }
};

beforeEach(() => {
  (window as any).URL.createObjectURL = vi.fn(() => 'blob:mock-url');
  (window as any).URL.revokeObjectURL = vi.fn();
  localStorage.clear();
  sessionStorage.clear();
  localStorage.setItem('user', JSON.stringify({
    user_id: 'u1',
    username: 'analyst',
    full_name: 'SOC ANALYST',
    email: 'analyst@org.gov',
    role: 'analyst',
    tenant_id: 'tenant-1'
  }));
  localStorage.setItem('token', 'mock-jwt-token');

  vi.spyOn(api, 'getEmailDetail').mockResolvedValue(mockEmailDetail);
  vi.spyOn(api, 'listEmails').mockResolvedValue({
    results: [
      {
        submission_id: '970a9e1e-test',
        sender: 'attacker@evil-spoof.com',
        recipient: 'victim@target.org',
        subject: 'Urgent Wire Transfer Request',
        risk_score: 94.5,
        risk_level: 'critical',
        classification: 'phishing',
        created_at: new Date().toISOString()
      }
    ],
    total: 1,
    page: 1,
    limit: 50,
    page_size: 50
  } as any);
  vi.spyOn(api, 'getDashboardStats').mockResolvedValue({
    total_emails_analyzed: 42,
    risk_distribution: { critical: 12, high: 18, medium: 8, low: 4 },
    active_alerts_count: 5,
    open_cases_count: 3,
    avg_analysis_time_ms: 120
  } as any);
  vi.spyOn(api, 'listAlerts').mockResolvedValue([
    {
      alert_id: 'alt-1',
      title: 'Credential Harvesting Link Detected',
      severity: 'critical',
      reason: 'Domain flagged on Barracuda BRBL',
      acknowledged: false,
      created_at: new Date().toISOString()
    }
  ] as any);
  vi.spyOn(api, 'listCampaigns').mockResolvedValue([
    {
      campaign_id: 'cmp-1',
      name: 'Operation DarkPhish',
      threat_actor: 'APT29-Clone',
      severity: 'high',
      confidence: 0.92,
      submission_count: 8,
      shared_infra: ['185.220.101.5']
    }
  ] as any);
  vi.spyOn(api, 'listCases').mockResolvedValue([
    {
      case_id: 'case-970a9e1e',
      title: 'Urgent Wire Transfer Incident',
      severity: 'critical',
      status: 'open',
      assigned_analyst: 'analyst@org.gov',
      submission_ids: ['970a9e1e-test'],
      updated_at: new Date().toISOString()
    }
  ] as any);
});

afterEach(() => {
  cleanup();
});

describe('TraceX DOM Comprehensive Test Suite', () => {

  it('1. ThreatBadge renders correct visual styles and tier labels', () => {
    const { rerender } = render(<ThreatBadge type="risk" value="critical" size="sm" />);
    expect(screen.getByText(/CRITICAL/i)).toBeTruthy();

    rerender(<ThreatBadge type="classification" value="phishing" size="sm" />);
    expect(screen.getByText(/PHISHING/i)).toBeTruthy();

    rerender(<ThreatBadge type="trust" value="verified" size="sm" />);
    expect(screen.getByText(/VERIFIED/i)).toBeTruthy();
  });

  it('2. ScoreGauge renders numerical verdict and factor breakdown bars', async () => {
    render(
      <ScoreGauge
        score={88}
        riskLevel="high"
        showBreakdown={true}
        breakdown={{ auth: 85, domain: 90, content: 75, infra: 80, links: 70 }}
      />
    );
    await waitFor(() => {
      expect(screen.getByText('0.88')).toBeTruthy();
    });
    expect(screen.getByText(/HIGH/i)).toBeTruthy();
    expect(screen.getByText(/Auth \/ DNS \(Observed\)/i)).toBeTruthy();
    expect(screen.getByText(/NLP Model \(Predicted\)/i)).toBeTruthy();
  });

  it('3. DetailDrawer slides out with forensic telemetry and copy buttons', () => {
    const mockData = {
      type: 'ip' as const,
      title: '185.220.101.5',
      subtitle: 'Amsterdam, Netherlands',
      provenance: 'observed' as const,
      severity: 'high' as const,
      fields: [
        { label: 'IP Address', value: '185.220.101.5', isMono: true, isCopyable: true },
        { label: 'Autonomous System', value: 'AS15169', isMono: true }
      ],
      evidenceRef: 'RFC 5322 Received Header line 4',
      notes: 'Forensic origin evidence'
    };

    render(<DetailDrawer data={mockData} onClose={() => {}} />);
    expect(screen.getAllByText('185.220.101.5').length).toBeGreaterThan(0);
    expect(screen.getAllByText('AS15169').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Copy IP/i).length).toBeGreaterThan(0);
  });

  it('4. IngestModal provides file dropzone and supports .EML upload', () => {
    render(<IngestModal isOpen={true} onClose={() => {}} onIngestSuccess={() => {}} />);
    expect(screen.getAllByText(/Ingest Email Evidence/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/RFC 5322/i).length).toBeGreaterThan(0);
  });

  it('5. Navbar displays system operational status, live clock, and user role', () => {
    const mockUser = {
      user_id: 'u1',
      username: 'analyst',
      full_name: 'SOC ANALYST',
      email: 'analyst@org.gov',
      role: 'analyst' as const,
      tenant_id: 'tenant-1'
    };
    render(
      <Navbar
        user={mockUser}
        activeTab="dashboard"
        onOpenIngest={() => {}}
        onLogout={() => {}}
        onOpenCommandPalette={() => {}}
      />
    );
    expect(screen.getAllByText(/Operational/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Ingest/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/analyst/i).length).toBeGreaterThan(0);
  });

  it('6. DashboardPage renders SOC Threat Overview with KPI cards', async () => {
    render(<DashboardPage onSelectSubmission={() => {}} onViewAllInbox={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Security Threat Telemetry/i).length).toBeGreaterThan(0);
    });
    expect(screen.getAllByText(/Submissions Analyzed/i).length).toBeGreaterThan(0);
  });

  it('7. ThreatInboxPage renders forensic analysis table with search filter', async () => {
    render(<ThreatInboxPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Email Threat Analysis Desk/i).length).toBeGreaterThan(0);
    });
    expect(screen.getAllByPlaceholderText(/Search sender, subject, hash/i).length).toBeGreaterThan(0);
  });

  it('8. InvestigationPage renders case dossier with all 10 forensic tabs', async () => {
    render(
      <InvestigationPage
        submissionId="970a9e1e-test"
        onBack={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getAllByText(/CASE-970A9E1E/i).length).toBeGreaterThan(0);
    });

    expect(screen.getAllByText('Overview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Headers').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Authentication').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Relay Path').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Geolocation').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Domain Intel').length).toBeGreaterThan(0);
    expect(screen.getAllByText('URLs & Links').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Attachments').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Attribution Graph').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Chain of Custody').length).toBeGreaterThan(0);

    // Switch to Geolocation Tab
    fireEvent.click(screen.getAllByText('Geolocation')[0]);
    expect(screen.getAllByText(/OBSERVABLE INFRASTRUCTURE MAP/i).length).toBeGreaterThan(0);

    // Switch to Chain of Custody Tab
    fireEvent.click(screen.getAllByText('Chain of Custody')[0]);
    expect(screen.getAllByText(/Download Sealed PDF Dossier/i).length).toBeGreaterThan(0);
  });

  it('9. MapPage renders Global Observable Infrastructure Map and controls', async () => {
    render(<MapPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Observable Infrastructure/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByPlaceholderText(/Search IP, hostname, ASN/i)).toBeTruthy();
  });

  it('10. CampaignsPage renders Threat Campaigns correlation graph and clusters', async () => {
    render(<CampaignsPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Refresh Clusters/i).length).toBeGreaterThan(0);
    });
  });

  it('11. AlertsPage renders Threat Alerts with acknowledge triggers', async () => {
    render(<AlertsPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Threat Alert Stream/i).length).toBeGreaterThan(0);
    });
  });

  it('12. ReportsPage renders Forensic Incident Reports and export options', async () => {
    render(<ReportsPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Forensic Reports & Evidence Dossiers/i).length).toBeGreaterThan(0);
    });
  });

  it('13. CasesPage renders Incidents & Cases forensic management', async () => {
    render(<CasesPage onSelectSubmission={() => {}} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Incident & Forensic Case Desk/i).length).toBeGreaterThan(0);
    });
  });

  it('14. SettingsPage renders SOC platform configuration and engine switches', () => {
    render(<SettingsPage />);
    expect(screen.getAllByText(/Platform Configuration & Policy/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Intelligence Providers & Engine Status/i).length).toBeGreaterThan(0);
  });

  it('15. Root App mounts with responsive sidebar navigation and seamless routing', async () => {
    render(<App />);
    expect(screen.getAllByText('TraceX').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Threat Overview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Email Analysis').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Threat Campaigns').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Threat Alerts').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Infrastructure Map').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Forensic Reports').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Platform Config').length).toBeGreaterThan(0);
  });

});
