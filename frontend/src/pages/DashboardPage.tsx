import React, { useState, useEffect } from 'react';
import { RefreshCw, ArrowUpRight, ShieldAlert, Inbox, AlertTriangle, FolderKanban, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';
import { DashboardStats, EmailListItem } from '../types';
import { ThreatBadge } from '../components/ThreatBadge';
import { TrustLedger } from '../components/TrustLedger';
import { AreaTrendSVG } from '../components/AreaTrendSVG';

interface DashboardPageProps {
  onSelectSubmission: (id: string) => void;
  onViewAllInbox: () => void;
}

const trendData = [
  { time: '00:00', critical: 2, predicted: 5, safe: 18 },
  { time: '04:00', critical: 4, predicted: 7, safe: 24 },
  { time: '08:00', critical: 9, predicted: 12, safe: 45 },
  { time: '12:00', critical: 15, predicted: 19, safe: 60 },
  { time: '16:00', critical: 11, predicted: 14, safe: 52 },
  { time: '20:00', critical: 7, predicted: 9, safe: 38 },
  { time: '24:00', critical: 3, predicted: 6, safe: 29 },
];

export const DashboardPage: React.FC<DashboardPageProps> = ({ onSelectSubmission, onViewAllInbox }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentEmails, setRecentEmails] = useState<EmailListItem[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [s, e, a] = await Promise.all([
        api.getDashboardStats().catch(() => null),
        api.listEmails({ page: 1, limit: 8 }).catch(() => ({ results: [], total: 0, page: 1, limit: 8, page_size: 8 })),
        api.listAlerts(false).catch(() => [])
      ]);
      if (s) setStats(s);
      if (e && Array.isArray(e.results)) setRecentEmails(e.results);
      if (Array.isArray(a)) setAlerts(a.slice(0, 5));
    } catch {
      // Ignored
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 bg-[#0A0D10] text-center space-y-3 font-mono">
        <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin" />
        <div className="text-xs text-[#8B96A3]">Loading real-time forensic telemetry...</div>
      </div>
    );
  }

  const totalAnalyzed = stats?.total_emails_analyzed ?? recentEmails.length ?? 0;
  const criticalCount = stats?.risk_distribution?.critical ?? 0;
  const highCount = stats?.risk_distribution?.high ?? 0;
  const activeAlertsCount = stats?.active_alerts_count ?? alerts.length ?? 0;
  const openCasesCount = stats?.open_cases_count ?? 0;

  return (
    <div className="flex flex-col h-full bg-[#0A0D10] text-[#E7EBEF] select-text">
      {/* Pinned Trust Ledger */}
      <TrustLedger />

      <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-6 max-w-[1720px] w-full mx-auto overflow-y-auto">
        {/* Page Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-[#232A32]">
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">
              Security Threat Telemetry
            </h1>
            <p className="text-[11px] sm:text-xs font-mono text-[#8B96A3] mt-0.5">
              Live attack rate, active forensic alerts, and recent triage artifacts
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E8A33D] transition-colors min-h-[36px]"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Responsive KPI Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <div className="p-3.5 sm:p-4 rounded-lg bg-[#12161B] border border-[#232A32] flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[10px] font-mono uppercase text-[#8B96A3] tracking-wider">Submissions Analyzed</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#E7EBEF]">{totalAnalyzed}</div>
              <div className="text-[10px] text-[#3DBE7A] font-mono flex items-center gap-1">
                <span>●</span> Real-time ingest active
              </div>
            </div>
            <div className="p-2.5 rounded bg-[#191F26] border border-[#232A32] text-[#E8A33D]">
              <Inbox className="w-5 h-5" />
            </div>
          </div>

          <div className="p-3.5 sm:p-4 rounded-lg bg-[#12161B] border border-[#232A32] flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[10px] font-mono uppercase text-[#8B96A3] tracking-wider">High & Critical Threats</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#E5484D]">
                {criticalCount + highCount}
              </div>
              <div className="text-[10px] text-[#8B96A3] font-mono">
                {criticalCount} Critical | {highCount} High
              </div>
            </div>
            <div className="p-2.5 rounded bg-[#E5484D15] border border-[#E5484D30] text-[#E5484D]">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="p-3.5 sm:p-4 rounded-lg bg-[#12161B] border border-[#232A32] flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[10px] font-mono uppercase text-[#8B96A3] tracking-wider">Active Incident Alerts</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#E8A33D]">{activeAlertsCount}</div>
              <div className="text-[10px] text-[#E8A33D] font-mono">P1 Security Dispatches</div>
            </div>
            <div className="p-2.5 rounded bg-[#E8A33D15] border border-[#E8A33D30] text-[#E8A33D]">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="p-3.5 sm:p-4 rounded-lg bg-[#12161B] border border-[#232A32] flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-[10px] font-mono uppercase text-[#8B96A3] tracking-wider">Open Forensic Cases</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-[#38BDF8]">{openCasesCount}</div>
              <div className="text-[10px] text-[#8B96A3] font-mono">Chain of Custody Active</div>
            </div>
            <div className="p-2.5 rounded bg-[#38BDF815] border border-[#38BDF830] text-[#38BDF8]">
              <FolderKanban className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* 24h Ingestion / Severity Trend (Native SVG Area Chart) */}
        <div className="bg-[#12161B] rounded-lg border border-[#232A32] p-4 sm:p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-xs font-mono uppercase font-bold text-[#E7EBEF]">
                24-Hour Attack Ingestion & Severity Rate
              </h2>
              <p className="text-[11px] text-[#8B96A3] font-mono">Volumetric threat distribution across active email relays</p>
            </div>
            <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-[10px] font-mono">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#E5484D]" /> Critical</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#E8A33D]" /> Phishing</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#3DBE7A]" /> Safe</span>
            </div>
          </div>

          <AreaTrendSVG data={trendData} height={200} />
        </div>

        {/* Split Grid: Recent Submissions (Left) + Live Alert Rail (Right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5">
          {/* Recent Submissions (8 cols on lg) */}
          <div className="lg:col-span-8 bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden flex flex-col justify-between">
            <div>
              <div className="px-4 sm:px-5 py-3 sm:py-3.5 border-b border-[#232A32] flex items-center justify-between">
                <h2 className="text-xs font-mono uppercase font-bold text-[#E7EBEF]">Recent Forensic Submissions</h2>
                <button
                  onClick={onViewAllInbox}
                  className="text-xs font-mono text-[#E8A33D] hover:underline flex items-center gap-1 min-h-[32px]"
                >
                  <span>View Full Desk</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Desktop/Tablet Table View (Hidden on mobile <md) */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                      <th className="py-2.5 px-4">Severity</th>
                      <th className="py-2.5 px-4">Sender Address</th>
                      <th className="py-2.5 px-4">Subject</th>
                      <th className="py-2.5 px-4 text-right">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#232A32]">
                    {recentEmails.map((item) => (
                      <tr
                        key={item.submission_id}
                        onClick={() => onSelectSubmission(item.submission_id)}
                        className="hover:bg-[#191F26] cursor-pointer transition-colors"
                      >
                        <td className="py-3 px-4"><ThreatBadge type="risk" value={item.risk_level} size="xs" /></td>
                        <td className="py-3 px-4 text-[#E7EBEF] truncate max-w-xs">{item.sender}</td>
                        <td className="py-3 px-4 text-[#8B96A3] truncate max-w-sm font-sans text-xs">{item.subject}</td>
                        <td className="py-3 px-4 text-right font-bold text-[#E7EBEF]">{(item.fraud_score * 100).toFixed(0)}/100</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Card List View (Visible on <md) */}
              <div className="md:hidden divide-y divide-[#232A32]">
                {recentEmails.map((item) => (
                  <div
                    key={item.submission_id}
                    onClick={() => onSelectSubmission(item.submission_id)}
                    className="p-3 hover:bg-[#191F26] cursor-pointer transition-colors space-y-1.5"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <ThreatBadge type="risk" value={item.risk_level} size="xs" />
                      <span className="text-xs font-mono font-bold text-[#E7EBEF]">
                        {(item.fraud_score * 100).toFixed(0)}/100
                      </span>
                    </div>
                    <div className="text-xs font-mono text-[#E7EBEF] truncate">{item.sender}</div>
                    <div className="text-xs text-[#8B96A3] font-sans truncate">{item.subject}</div>
                  </div>
                ))}
              </div>
            </div>

            {recentEmails.length === 0 && (
              <div className="p-8 text-center text-xs font-mono text-[#8B96A3]">
                No recent email submissions recorded.
              </div>
            )}
          </div>

          {/* Live Alert Rail (4 cols on lg) */}
          <div className="lg:col-span-4 bg-[#12161B] rounded-lg border border-[#232A32] p-4 space-y-3 font-mono text-xs flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between border-b border-[#232A32] pb-2">
                <span className="font-bold text-[#E7EBEF] text-xs uppercase flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-[#E5484D]" />
                  <span>Live Threat Alert Stream</span>
                </span>
                <span className="text-[10px] text-[#8B96A3]">{alerts.length} Active</span>
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto">
                {alerts.map((a) => (
                  <div
                    key={a.alert_id}
                    onClick={() => onSelectSubmission(a.submission_id)}
                    className="p-2.5 rounded bg-[#0A0D10] border border-[#232A32] hover:border-[#3A4551] cursor-pointer space-y-1 transition-all"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-[#E7EBEF] font-semibold">{a.title}</span>
                      <span className="w-2 h-2 rounded-full bg-[#E5484D] animate-pulse" />
                    </div>
                    <p className="text-[#8B96A3] text-[10px] font-sans truncate">{a.reason}</p>
                  </div>
                ))}

                {alerts.length === 0 && (
                  <div className="p-4 text-center text-[11px] text-[#8B96A3] flex items-center justify-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-[#3DBE7A]" />
                    <span>No unacknowledged security triggers.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-[#232A32] text-[10px] text-[#566270] flex items-center justify-between">
              <span>Alert Queue: P1 Active</span>
              <span className="text-[#3DBE7A]">● Operational</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
