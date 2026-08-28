import React, { useState, useEffect } from 'react';
import { Search, Plus, Filter, LayoutGrid, List, RefreshCw, X, FolderKanban, ArrowRight, ShieldAlert, CheckCircle2, ChevronRight, Clock, User } from 'lucide-react';
import { api } from '../api/client';
import { ThreatBadge } from '../components/ThreatBadge';
import { DetailDrawer, DetailDrawerData } from '../components/DetailDrawer';

interface CasesPageProps {
  onSelectSubmission: (id: string) => void;
}

const STAGES = ['OPEN', 'INVESTIGATING', 'CONTAINED', 'RESOLVED', 'CLOSED'];

export const CasesPage: React.FC<CasesPageProps> = ({ onSelectSubmission }) => {
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban');
  const [drawerData, setDrawerData] = useState<DetailDrawerData | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newSeverity, setNewSeverity] = useState('high');
  const [newStage, setNewStage] = useState('open');
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadCases = async () => {
    try {
      const data = await api.listCases();
      setCases(Array.isArray(data) ? data : []);
    } catch {
      setCases([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadCases();
  };

  const handleStatusChange = async (caseId: string, newStatus: string) => {
    setUpdatingId(caseId);
    try {
      await api.updateCase(caseId, { status: newStatus.toLowerCase() });
      setCases(prev => prev.map(c => c.case_id === caseId ? { ...c, status: newStatus.toLowerCase(), updated_at: new Date().toISOString() } : c));
    } catch (err: any) {
      alert('Failed to update stage: ' + (err?.message || 'Error'));
    } finally {
      setUpdatingId(null);
    }
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const created = await api.createCase({
        title: newTitle.trim(),
        severity: newSeverity,
        notes: 'Case created via Forensic Case Desk.'
      });
      if (newStage !== 'open') {
        await api.updateCase(created.case_id, { status: newStage.toLowerCase() });
      }
      setIsCreateModalOpen(false);
      setNewTitle('');
      loadCases();
    } catch (err: any) {
      alert('Failed to create case: ' + (err?.message || 'Error'));
    }
  };

  const handleCaseClick = (c: any) => {
    setDrawerData({
      type: 'evidence',
      title: c.title,
      subtitle: `Case Ref: CASE-${c.case_id.slice(0, 8).toUpperCase()}`,
      provenance: 'observed',
      severity: c.severity,
      fields: [
        { label: 'Case Identifier', value: c.case_id, isMono: true, isCopyable: true },
        { label: 'Investigation Stage', value: (c.status || 'OPEN').toUpperCase(), isMono: false },
        { label: 'Assigned Investigator', value: c.assigned_analyst || 'analyst@org.gov', isMono: false },
        { label: 'Severity Verdict', value: (c.severity || 'MEDIUM').toUpperCase(), isMono: false },
        { label: 'Linked Artifacts', value: `${c.submission_ids?.length || 0} Ingested Email(s)`, isMono: false },
        { label: 'Last Modified', value: new Date(c.updated_at).toLocaleString(), isMono: true }
      ],
      evidenceRef: c.submission_ids?.[0] ? `Linked Submission #${c.submission_ids[0].slice(0, 8).toUpperCase()}` : 'No attached artifacts',
      notes: c.notes || 'Forensic investigation case record with verified evidentiary chain of custody.'
    });
  };

  const filteredCases = cases.filter((c) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      c.title?.toLowerCase().includes(q) ||
      c.case_id?.toLowerCase().includes(q) ||
      c.assigned_analyst?.toLowerCase().includes(q);

    const matchesSeverity = filterSeverity === 'all' || (c.severity || '').toLowerCase() === filterSeverity.toLowerCase();
    const matchesStatus = filterStatus === 'all' || (c.status || '').toLowerCase() === filterStatus.toLowerCase();

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  return (
    <div className="p-6 space-y-6 max-w-[1600px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      {/* Top Header & Workstation Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">Incident & Case Management Desk</h1>
          <p className="text-xs font-mono text-[#8B96A3] mt-0.5">
            Active forensic investigation lifecycle tracking across triage, containment, and resolution stages
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center bg-[#12161B] border border-[#232A32] rounded p-0.5 font-mono text-xs">
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-colors ${
                viewMode === 'kanban' ? 'bg-[#191F26] text-[#E8A33D] font-bold shadow-sm' : 'text-[#8B96A3] hover:text-white'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Kanban</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-colors ${
                viewMode === 'table' ? 'bg-[#191F26] text-[#E8A33D] font-bold shadow-sm' : 'text-[#8B96A3] hover:text-white'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] text-xs font-mono font-bold shadow-md transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ Create Case</span>
          </button>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E8A33D] transition-colors"
            title="Refresh Cases"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#12161B] border border-[#232A32] p-3 rounded-lg font-mono text-xs">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1 max-w-md">
            <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Case ID, title, analyst..."
              className="w-full pl-8 pr-7 py-1.5 bg-[#0A0D10] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-none focus:border-[#E8A33D]"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white">
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5">
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
              <option value="low">Low</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#8B96A3] uppercase">Stage:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-[#0A0D10] border border-[#232A32] text-[#E7EBEF] rounded px-2 py-1 text-xs focus:outline-none"
            >
              <option value="all">All Stages</option>
              {STAGES.map(s => <option key={s} value={s.toLowerCase()}>{s}</option>)}
            </select>
          </div>
        </div>

        <div className="text-[11px] text-[#8B96A3]">
          Showing <span className="text-[#E8A33D] font-bold">{filteredCases.length}</span> of {cases.length} Active Cases
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="w-full h-80 bg-[#12161B] border border-[#232A32] rounded-lg flex flex-col items-center justify-center space-y-3 font-mono">
          <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin" />
          <div className="text-xs text-[#8B96A3]">Loading active investigation cases...</div>
        </div>
      ) : cases.length === 0 ? (
        <div className="w-full h-80 bg-[#12161B] border border-[#232A32] rounded-lg flex flex-col items-center justify-center p-8 text-center space-y-3 font-mono">
          <FolderKanban className="w-10 h-10 text-[#566270]" />
          <div className="text-sm font-bold text-[#E7EBEF]">No active cases in repository</div>
          <p className="text-xs text-[#8B96A3] max-w-md font-sans">
            Ingest an email artifact to automatically correlate findings and spawn evidentiary investigation cases.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-4 py-2 rounded bg-[#E8A33D] text-[#0A0D10] text-xs font-bold font-mono"
          >
            + Create First Case
          </button>
        </div>
      ) : viewMode === 'kanban' ? (
        /* Dense, High-Density Kanban Grid */
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 items-start">
          {STAGES.map((stage) => {
            const stageCases = filteredCases.filter(c => (c.status || 'OPEN').toUpperCase() === stage);
            return (
              <div
                key={stage}
                className="bg-[#12161B] rounded-lg border border-[#232A32] p-3 flex flex-col justify-between font-mono text-xs min-h-[500px]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between border-b border-[#232A32] pb-2.5 mb-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#E8A33D]" />
                    <span className="font-bold text-[#E7EBEF] text-[11px] uppercase tracking-wider">{stage}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-[#0A0D10] border border-[#232A32] text-[#E8A33D] text-[10px] font-bold">
                    {stageCases.length}
                  </span>
                </div>

                {/* Cards Container */}
                <div className="space-y-2.5 flex-1 overflow-y-auto pr-0.5">
                  {stageCases.length > 0 ? (
                    stageCases.map((c) => (
                      <div
                        key={c.case_id}
                        onClick={() => handleCaseClick(c)}
                        className="p-3.5 rounded-md bg-[#0A0D10] border border-[#232A32] hover:border-[#E8A33D] cursor-pointer space-y-2.5 transition-all group shadow-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[#E8A33D] font-bold text-[10px] tracking-wide">
                            CASE-{c.case_id.slice(0, 8).toUpperCase()}
                          </span>
                          <ThreatBadge type="risk" value={c.severity} size="xs" />
                        </div>

                        <div className="text-[#E7EBEF] font-sans font-semibold text-xs leading-snug group-hover:text-[#E8A33D] transition-colors">
                          {c.title}
                        </div>

                        {/* Metadata Footer */}
                        <div className="text-[10px] text-[#8B96A3] flex items-center justify-between pt-2 border-t border-[#232A32]">
                          <span className="truncate max-w-[110px]">{c.assigned_analyst || 'analyst@org.gov'}</span>
                          <span>{new Date(c.updated_at).toLocaleDateString()}</span>
                        </div>

                        {/* Action Toolbar */}
                        <div className="pt-1.5 border-t border-[#232A32]/60 flex items-center justify-between gap-1 text-[10px]">
                          {/* Stage Mover Dropdown */}
                          <select
                            value={(c.status || 'open').toUpperCase()}
                            onClick={(e) => e.stopPropagation()}
                            onChange={(e) => handleStatusChange(c.case_id, e.target.value)}
                            disabled={updatingId === c.case_id}
                            className="bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E7EBEF] rounded px-1.5 py-0.5 text-[9px] focus:outline-none"
                          >
                            {STAGES.map(s => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>

                          {c.submission_ids?.[0] && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectSubmission(c.submission_ids[0]);
                              }}
                              className="text-[#2DD4BF] hover:underline flex items-center gap-0.5 font-bold"
                            >
                              <span>Inspect</span>
                              <ArrowRight className="w-2.5 h-2.5" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="py-16 text-center text-[#566270] text-[11px] font-mono">
                      No cases in this stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Dense Table View */
        <div className="bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                <th className="py-2.5 px-4">Severity</th>
                <th className="py-2.5 px-4">Case ID</th>
                <th className="py-2.5 px-4">Title & Subject</th>
                <th className="py-2.5 px-4">Stage</th>
                <th className="py-2.5 px-4">Assigned Analyst</th>
                <th className="py-2.5 px-4">Last Updated</th>
                <th className="py-2.5 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#232A32]">
              {filteredCases.map((c) => (
                <tr
                  key={c.case_id}
                  onClick={() => handleCaseClick(c)}
                  className="hover:bg-[#191F26] cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4"><ThreatBadge type="risk" value={c.severity} size="xs" /></td>
                  <td className="py-3 px-4 text-[#E8A33D] font-bold">CASE-{c.case_id.slice(0, 8).toUpperCase()}</td>
                  <td className="py-3 px-4 text-[#E7EBEF] font-sans font-semibold truncate max-w-sm">{c.title}</td>
                  <td className="py-3 px-4">
                    <select
                      value={(c.status || 'open').toUpperCase()}
                      onClick={(e) => e.stopPropagation()}
                      onChange={(e) => handleStatusChange(c.case_id, e.target.value)}
                      className="bg-[#0A0D10] border border-[#232A32] text-[#E8A33D] rounded px-2 py-0.5 text-[10px] font-bold focus:outline-none"
                    >
                      {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                  <td className="py-3 px-4 text-[#8B96A3]">{c.assigned_analyst || 'analyst@org.gov'}</td>
                  <td className="py-3 px-4 text-[#566270]">{new Date(c.updated_at).toLocaleString()}</td>
                  <td className="py-3 px-4 text-center">
                    {c.submission_ids?.[0] ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectSubmission(c.submission_ids[0]);
                        }}
                        className="text-[#E8A33D] hover:underline font-bold text-[11px]"
                      >
                        Inspect →
                      </button>
                    ) : (
                      <span className="text-[#566270]">View Detail</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Case Creation Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4 font-mono select-none">
          <div className="w-full max-w-md bg-[#12161B] border border-[#3A4551] rounded-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#232A32] pb-2">
              <span className="font-bold text-sm text-[#E7EBEF]">Create Forensic Investigation Case</span>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-[#8B96A3] hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-3.5 text-xs">
              <div className="space-y-1">
                <label className="text-[10px] uppercase text-[#8B96A3]">Case Title / Brief:</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Executive Impersonation Wire Fraud"
                  className="w-full px-3 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-[#E7EBEF] focus:outline-none focus:border-[#E8A33D]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase text-[#8B96A3]">Initial Stage:</label>
                  <select
                    value={newStage}
                    onChange={(e) => setNewStage(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-[#E7EBEF] focus:outline-none"
                  >
                    {STAGES.map(s => <option key={s} value={s.toLowerCase()}>{s}</option>)}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase text-[#8B96A3]">Severity Level:</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-[#E7EBEF] focus:outline-none"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-3 py-1.5 rounded bg-[#0A0D10] border border-[#232A32] text-[#8B96A3]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-[#E8A33D] text-[#0A0D10] font-bold"
                >
                  Save Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Case Slideout Context Drawer */}
      <DetailDrawer data={drawerData} onClose={() => setDrawerData(null)} />
    </div>
  );
};
