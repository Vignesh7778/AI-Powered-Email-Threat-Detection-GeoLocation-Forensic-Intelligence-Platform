import React, { useState, useEffect } from 'react';
import { Download, RefreshCw, FileText, Search, X, ArrowRight, Printer } from 'lucide-react';
import { api } from '../api/client';
import { ThreatBadge } from '../components/ThreatBadge';

interface ReportsPageProps {
  onSelectSubmission: (id: string) => void;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ onSelectSubmission }) => {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const res = await api.listEmails({ page: 1, limit: 50 });
      setEmails(Array.isArray(res) ? res : (res?.results || []));
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

  const handleDownload = async (e: React.MouseEvent, submissionId: string, format: 'json' | 'pdf') => {
    e.stopPropagation();
    setDownloadingId(`${submissionId}-${format}`);
    try {
      await api.downloadReport(submissionId, format);
    } finally {
      setTimeout(() => setDownloadingId(null), 1000);
    }
  };

  const filtered = emails.filter((item) => {
    const query = search.toLowerCase().trim();
    if (!query) return true;
    return (
      item.sender?.toLowerCase().includes(query) ||
      item.subject?.toLowerCase().includes(query) ||
      item.submission_id?.toLowerCase().includes(query) ||
      item.classification?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-6 max-w-[1720px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-base sm:text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">
            Forensic Reports & Evidence Dossiers
          </h1>
          <p className="text-[11px] sm:text-xs font-mono text-[#8B96A3] mt-0.5">
            Court-admissible PDF investigation reports and machine-readable JSON evidence packages
          </p>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-white transition-colors min-h-[36px]"
          >
            <Printer className="w-3.5 h-3.5" />
            <span className="hidden xs:inline">Print View</span>
          </button>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E8A33D] transition-colors min-h-[36px]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
            <span className="hidden xs:inline">Refresh Dossiers</span>
            <span className="xs:hidden">Refresh</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
        <div className="relative w-full max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search report dossiers by Case ID, sender, or subject..."
            className="w-full pl-9 pr-8 py-1.5 bg-[#12161B] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D] min-h-[36px]"
          />
          {search && (
            <button onClick={() => setSearch('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white p-0.5">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="text-[11px] text-[#8B96A3] hidden sm:inline">
          Showing <span className="text-[#E7EBEF] font-bold">{filtered.length}</span> verified evidentiary packages
        </div>
      </div>

      <div className="bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden">
        {/* Desktop Table View */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                <th className="py-2.5 px-4">Case Reference</th>
                <th className="py-2.5 px-4">Sender / Target</th>
                <th className="py-2.5 px-4">Subject</th>
                <th className="py-2.5 px-4">Threat Classification</th>
                <th className="py-2.5 px-4 text-right">Risk Score</th>
                <th className="py-2.5 px-4 text-center">Export Dossiers</th>
                <th className="py-2.5 px-4 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232A32]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-[#8B96A3]">
                    <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin mx-auto mb-2" />
                    <div>Loading forensic dossier catalog...</div>
                  </td>
                </tr>
              ) : filtered.length > 0 ? (
                filtered.map((e) => (
                  <tr
                    key={e.submission_id}
                    onClick={() => onSelectSubmission(e.submission_id)}
                    className="hover:bg-[#191F26] transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4 text-[#E8A33D] font-bold">
                      CASE-{e.submission_id.slice(0, 8).toUpperCase()}
                    </td>
                    <td className="py-3 px-4 text-[#E7EBEF] font-semibold truncate max-w-xs">
                      {e.sender || 'Unknown'}
                    </td>
                    <td className="py-3 px-4 text-[#8B96A3] truncate max-w-sm font-sans text-xs">
                      {e.subject || 'No Subject'}
                    </td>
                    <td className="py-3 px-4">
                      <ThreatBadge type="classification" value={e.classification} size="xs" />
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-[#E7EBEF]">
                      {(e.fraud_score * 100).toFixed(0)}/100
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={(evt) => handleDownload(evt, e.submission_id, 'pdf')}
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0A0D10] border border-[#E8A33D]/40 text-[#E8A33D] hover:bg-[#E8A33D] hover:text-[#0A0D10] text-[10px] font-bold transition-all min-h-[28px]"
                          title="Download court-admissible PDF report"
                        >
                          <Download className="w-3 h-3" />
                          <span>{downloadingId === `${e.submission_id}-pdf` ? 'Sealing...' : 'PDF'}</span>
                        </button>
                        <button
                          onClick={(evt) => handleDownload(evt, e.submission_id, 'json')}
                          className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0A0D10] border border-[#232A32] text-[#8B96A3] hover:text-white text-[10px] font-bold transition-all min-h-[28px]"
                          title="Export machine-readable JSON package"
                        >
                          <Download className="w-3 h-3" />
                          <span>{downloadingId === `${e.submission_id}-json` ? 'Exporting...' : 'JSON'}</span>
                        </button>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="text-[11px] text-[#E8A33D] hover:underline font-semibold inline-flex items-center gap-0.5">
                        <span>Open</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-[#8B96A3]">
                    <FileText className="w-8 h-8 mx-auto text-[#566270] mb-2" />
                    <div>No forensic dossiers found matching current search filter.</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Responsive Cards View */}
        <div className="md:hidden divide-y divide-[#232A32]">
          {loading ? (
            <div className="py-12 text-center text-[#8B96A3] font-mono text-xs">
              <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin mx-auto mb-2" />
              <div>Loading forensic dossier catalog...</div>
            </div>
          ) : filtered.length > 0 ? (
            filtered.map((e) => (
              <div
                key={e.submission_id}
                onClick={() => onSelectSubmission(e.submission_id)}
                className="p-3.5 hover:bg-[#191F26] cursor-pointer transition-colors space-y-2 font-mono text-xs"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[#E8A33D] font-bold text-xs">
                    CASE-{e.submission_id.slice(0, 8).toUpperCase()}
                  </span>
                  <ThreatBadge type="classification" value={e.classification} size="xs" />
                </div>

                <div className="text-xs text-[#E7EBEF] font-semibold truncate">{e.sender}</div>
                <div className="text-xs text-[#8B96A3] font-sans line-clamp-2">{e.subject}</div>

                <div className="flex items-center justify-between pt-2 border-t border-[#232A32]">
                  <div className="text-[11px] font-bold text-[#E7EBEF]">
                    Score: {(e.fraud_score * 100).toFixed(0)}/100
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(evt) => handleDownload(evt, e.submission_id, 'pdf')}
                      className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0A0D10] border border-[#E8A33D]/40 text-[#E8A33D] hover:bg-[#E8A33D] hover:text-[#0A0D10] text-[10px] font-bold transition-all min-h-[30px]"
                    >
                      <Download className="w-3 h-3" />
                      <span>{downloadingId === `${e.submission_id}-pdf` ? '...' : 'PDF'}</span>
                    </button>
                    <button
                      onClick={(evt) => handleDownload(evt, e.submission_id, 'json')}
                      className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#0A0D10] border border-[#232A32] text-[#8B96A3] hover:text-white text-[10px] font-bold transition-all min-h-[30px]"
                    >
                      <Download className="w-3 h-3" />
                      <span>{downloadingId === `${e.submission_id}-json` ? '...' : 'JSON'}</span>
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="py-12 text-center text-[#8B96A3] font-mono text-xs">
              <FileText className="w-8 h-8 mx-auto text-[#566270] mb-2" />
              <div>No forensic dossiers found matching current search filter.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
