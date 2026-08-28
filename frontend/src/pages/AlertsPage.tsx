import React, { useState, useEffect } from 'react';
import { ShieldAlert, RefreshCw, CheckCircle2, Search, X, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import { ThreatBadge } from '../components/ThreatBadge';

interface AlertsPageProps {
  onSelectSubmission: (id: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ onSelectSubmission }) => {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');

  const loadData = async () => {
    try {
      const data = await api.listAlerts(false);
      setAlerts(Array.isArray(data) ? data : []);
    } catch {
      setAlerts([]);
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

  const handleAck = async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      setAlerts(prev => prev.map(a => a.alert_id === id ? { ...a, acknowledged: true } : a));
    } catch {
      // Ignored
    }
  };

  const filtered = alerts.filter((a) => {
    const q = search.toLowerCase().trim();
    const matchesSearch = !q || a.title?.toLowerCase().includes(q) || a.reason?.toLowerCase().includes(q);
    const matchesSeverity = filterSeverity === 'all' || (a.severity || '').toLowerCase() === filterSeverity.toLowerCase();
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="p-6 space-y-6 max-w-[1600px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">Threat Alert Stream</h1>
          <p className="text-xs font-mono text-[#8B96A3] mt-0.5">
            High and Critical security triggers requiring immediate security analyst acknowledgment
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E8A33D] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
            <span>Refresh Alerts</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 font-mono text-xs bg-[#12161B] border border-[#232A32] p-3 rounded-lg">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search alerts by title or trigger rule..."
            className="w-full pl-9 pr-8 py-1.5 bg-[#0A0D10] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-none focus:border-[#E8A33D]"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[10px] text-[#8B96A3] uppercase">Severity:</span>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-[#0A0D10] border border-[#232A32] text-[#E7EBEF] rounded px-2 py-1 text-xs focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden">
        <table className="w-full text-left font-mono text-xs">
          <thead>
            <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
              <th className="py-2.5 px-4">Severity</th>
              <th className="py-2.5 px-4">Alert Trigger Title</th>
              <th className="py-2.5 px-4">Reason / Rule</th>
              <th className="py-2.5 px-4">Score</th>
              <th className="py-2.5 px-4">Status</th>
              <th className="py-2.5 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#232A32]">
            {loading ? (
              <tr>
                <td colSpan={6} className="py-16 text-center text-[#8B96A3]">
                  <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin mx-auto mb-2" />
                  <div>Loading active threat alerts...</div>
                </td>
              </tr>
            ) : filtered.length > 0 ? (
              filtered.map((a) => (
                <tr key={a.alert_id} className="hover:bg-[#191F26] transition-colors">
                  <td className="py-3 px-4"><ThreatBadge type="risk" value={a.severity} size="xs" /></td>
                  <td
                    className="py-3 px-4 text-[#E7EBEF] font-semibold cursor-pointer hover:text-[#E8A33D] transition-colors font-sans"
                    onClick={() => onSelectSubmission(a.submission_id)}
                  >
                    {a.title}
                  </td>
                  <td className="py-3 px-4 text-[#8B96A3] font-sans text-xs truncate max-w-sm">{a.reason}</td>
                  <td className="py-3 px-4 font-bold text-[#E7EBEF]">{(a.fraud_score * 100).toFixed(0)}/100</td>
                  <td className="py-3 px-4">
                    {a.acknowledged ? (
                      <span className="text-[10px] text-[#2DD4BF] font-bold">ACKNOWLEDGED</span>
                    ) : (
                      <span className="text-[10px] text-[#E8A33D] font-bold animate-pulse">PENDING REVIEW</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {!a.acknowledged ? (
                      <button
                        onClick={() => handleAck(a.alert_id)}
                        className="px-2.5 py-1 rounded bg-[#0A0D10] border border-[#E8A33D]/40 text-[#E8A33D] hover:bg-[#E8A33D] hover:text-[#0A0D10] text-[10px] font-bold transition-all"
                      >
                        Acknowledge
                      </button>
                    ) : (
                      <button
                        onClick={() => onSelectSubmission(a.submission_id)}
                        className="text-[#8B96A3] hover:text-white text-[11px] inline-flex items-center gap-1"
                      >
                        <span>Inspect</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-16 text-center text-[#8B96A3]">
                  <CheckCircle2 className="w-8 h-8 mx-auto text-[#566270] mb-2" />
                  <div>No active threat alerts triggered.</div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
