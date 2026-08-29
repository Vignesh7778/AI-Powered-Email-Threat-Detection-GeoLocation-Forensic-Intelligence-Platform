import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, X, Inbox, ArrowRight, Filter } from 'lucide-react';
import { api } from '../api/client';
import { EmailListItem } from '../types';
import { ThreatBadge } from '../components/ThreatBadge';

interface ThreatInboxPageProps {
  onSelectSubmission: (id: string) => void;
  initialSearch?: string;
}

export const ThreatInboxPage: React.FC<ThreatInboxPageProps> = ({ onSelectSubmission, initialSearch = '' }) => {
  const [emails, setEmails] = useState<EmailListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState(initialSearch);
  const [filterRisk, setFilterRisk] = useState<string>('all');

  useEffect(() => {
    if (initialSearch !== undefined) {
      setSearch(initialSearch);
    }
  }, [initialSearch]);

  const loadData = async () => {
    try {
      const resp = await api.listEmails({ page: 1, limit: 50 });
      const list = Array.isArray(resp) ? resp : (resp?.results || []);
      setEmails(list);
    } catch {
      setEmails([]);
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

  const filtered = emails.filter((item) => {
    const query = (search || '').toLowerCase().trim();
    const matchesSearch =
      !query ||
      (item.sender && item.sender.toLowerCase().includes(query)) ||
      (item.subject && item.subject.toLowerCase().includes(query)) ||
      (item.submission_id && item.submission_id.toLowerCase().includes(query)) ||
      (item.classification && item.classification.toLowerCase().includes(query));

    const itemRisk = (item.risk_level || 'unknown').toLowerCase();
    const matchesRisk = filterRisk === 'all' || itemRisk === filterRisk.toLowerCase();
    return matchesSearch && matchesRisk;
  });

  return (
    <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-5 max-w-[1720px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-base sm:text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">
            Email Threat Analysis Desk
          </h1>
          <p className="text-[11px] sm:text-xs font-mono text-[#8B96A3] mt-0.5">
            Forensic triage repository of ingested RFC 5322 message artifacts
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-xs font-mono text-[#8B96A3] hover:text-[#E8A33D] transition-colors min-h-[36px]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Mobile/Tablet Horizontal Filter Bar (<lg) */}
      <div className="lg:hidden space-y-2.5 bg-[#12161B] p-3 sm:p-4 rounded-lg border border-[#232A32]">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search sender, subject, hash, ID..."
            className="w-full pl-8 pr-7 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D] min-h-[38px]"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white p-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Horizontal Severity Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <span className="text-[10px] font-mono uppercase text-[#8B96A3] flex-shrink-0 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3 text-[#E8A33D]" /> Tier:
          </span>
          {['all', 'critical', 'high', 'medium', 'low'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterRisk(lvl)}
              className={`px-3 py-1 rounded text-[11px] font-mono uppercase transition-colors flex-shrink-0 min-h-[32px] ${
                filterRisk === lvl
                  ? 'bg-[#E8A33D] text-[#0A0D10] font-bold shadow-sm'
                  : 'bg-[#0A0D10] text-[#8B96A3] hover:text-white border border-[#232A32]'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Desktop Filter Rail (3 cols) + Results (9 cols on lg) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5">
        {/* Desktop Left Filter Rail (3 cols, hidden on <lg) */}
        <div className="hidden lg:block lg:col-span-3 bg-[#12161B] rounded-lg border border-[#232A32] p-4 space-y-4 font-mono text-xs h-fit sticky top-4">
          <div className="font-bold text-[#E7EBEF] uppercase text-xs border-b border-[#232A32] pb-2 flex items-center justify-between">
            <span>Triage Filters</span>
            <span className="text-[10px] text-[#E8A33D] font-normal">{filtered.length} matches</span>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase text-[#8B96A3]">Search Query:</label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Sender, subject, ID..."
                className="w-full pl-8 pr-7 py-1.5 bg-[#0A0D10] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D]"
              />
              {search && (
                <button
                  onClick={() => setSearch('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase text-[#8B96A3]">Severity Tier:</label>
            <div className="space-y-1">
              {['all', 'critical', 'high', 'medium', 'low'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterRisk(lvl)}
                  className={`w-full text-left px-2.5 py-1.5 rounded text-[11px] uppercase transition-colors flex items-center justify-between min-h-[34px] ${
                    filterRisk === lvl
                      ? 'bg-[#E8A33D] text-[#0A0D10] font-bold'
                      : 'bg-[#0A0D10] text-[#8B96A3] hover:text-white border border-[#232A32]'
                  }`}
                >
                  <span>{lvl}</span>
                  {filterRisk === lvl && <span className="text-[9px] font-mono">ACTIVE</span>}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Container (12 cols on mobile, 9 cols on lg) */}
        <div className="lg:col-span-9 bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden flex flex-col justify-between">
          {/* 1. Desktop & Tablet Table View (Visible on md+) */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                  <th className="py-2.5 px-4">Severity</th>
                  <th className="py-2.5 px-4">Case Ref</th>
                  <th className="py-2.5 px-4">Sender Address</th>
                  <th className="py-2.5 px-4">Subject</th>
                  <th className="py-2.5 px-4">Classification</th>
                  <th className="py-2.5 px-4 text-center">Score Scan</th>
                  <th className="py-2.5 px-4 text-center">Triage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#232A32]">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-16 text-center text-[#8B96A3] font-mono text-xs">
                      <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin mx-auto mb-2" />
                      <div>Loading threat records...</div>
                    </td>
                  </tr>
                ) : filtered.length > 0 ? (
                  filtered.map((item) => {
                    const score = Math.round((item.fraud_score || 0) * 100);
                    const barColor = score >= 75 ? '#E5484D' : score >= 50 ? '#E8A33D' : score >= 25 ? '#E8A33D' : '#3DBE7A';
                    return (
                      <tr
                        key={item.submission_id}
                        onClick={() => onSelectSubmission(item.submission_id)}
                        className="hover:bg-[#191F26] cursor-pointer transition-colors"
                      >
                        <td className="py-3 px-4">
                          <ThreatBadge type="risk" value={item.risk_level} size="xs" />
                        </td>
                        <td className="py-3 px-4 text-[#E8A33D] font-bold">
                          {item.submission_id.slice(0, 8).toUpperCase()}
                        </td>
                        <td className="py-3 px-4 text-[#E7EBEF] font-semibold truncate max-w-xs">
                          {item.sender || 'Unknown Sender'}
                        </td>
                        <td className="py-3 px-4 text-[#8B96A3] truncate max-w-sm font-sans text-xs">
                          {item.subject || 'No Subject'}
                        </td>
                        <td className="py-3 px-4">
                          <ThreatBadge type="classification" value={item.classification} size="xs" />
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-16 h-2 rounded bg-[#232A32] overflow-hidden">
                              <div style={{ width: `${score}%`, backgroundColor: barColor }} className="h-full" />
                            </div>
                            <span className="font-bold text-[11px] text-[#E7EBEF]">{score}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="text-[11px] text-[#E8A33D] hover:underline font-semibold flex items-center justify-center gap-1">
                            <span>Inspect</span>
                            <ArrowRight className="w-3 h-3" />
                          </span>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="py-16 text-center text-[#8B96A3] font-mono text-xs">
                      <Inbox className="w-8 h-8 mx-auto text-[#566270] opacity-50 mb-2" />
                      <div>No email incidents found matching filter.</div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* 2. Mobile Responsive Card List View (<md) */}
          <div className="md:hidden divide-y divide-[#232A32]">
            {loading ? (
              <div className="py-12 text-center text-[#8B96A3] font-mono text-xs">
                <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin mx-auto mb-2" />
                <div>Loading threat records...</div>
              </div>
            ) : filtered.length > 0 ? (
              filtered.map((item) => {
                const score = Math.round((item.fraud_score || 0) * 100);
                const barColor = score >= 75 ? '#E5484D' : score >= 50 ? '#E8A33D' : '#3DBE7A';
                return (
                  <div
                    key={item.submission_id}
                    onClick={() => onSelectSubmission(item.submission_id)}
                    className="p-3.5 hover:bg-[#191F26] cursor-pointer transition-colors space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <ThreatBadge type="risk" value={item.risk_level} size="xs" />
                        <ThreatBadge type="classification" value={item.classification} size="xs" />
                      </div>
                      <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-[#E7EBEF]">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: barColor }} />
                        <span>{score}/100</span>
                      </div>
                    </div>

                    <div className="space-y-0.5 font-mono">
                      <div className="text-xs text-[#E7EBEF] font-semibold truncate">{item.sender}</div>
                      <div className="text-xs text-[#8B96A3] font-sans line-clamp-2">{item.subject}</div>
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-[#566270] pt-1">
                      <span>REF: {item.submission_id.slice(0, 8).toUpperCase()}</span>
                      <span className="text-[#E8A33D] font-bold flex items-center gap-1">
                        <span>Investigate</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-12 text-center text-[#8B96A3] font-mono text-xs">
                <Inbox className="w-8 h-8 mx-auto text-[#566270] opacity-50 mb-2" />
                <div>No email incidents found matching filter.</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
