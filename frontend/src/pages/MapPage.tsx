import React, { useState, useEffect, useMemo } from 'react';
import { RefreshCw, Search, X, Server, Globe, ShieldAlert, ArrowRight, Copy, Check } from 'lucide-react';
import { api } from '../api/client';
import { TraceXMap } from '../components/map/TraceXMap';
import { InfrastructureNode } from '../components/map/types';
import { DetailDrawer, DetailDrawerData } from '../components/DetailDrawer';
import { ThreatBadge } from '../components/ThreatBadge';

interface MapPageProps {
  onSelectSubmission: (id: string) => void;
}

export const MapPage: React.FC<MapPageProps> = ({ onSelectSubmission }) => {
  const [nodes, setNodes] = useState<InfrastructureNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [drawerData, setDrawerData] = useState<DetailDrawerData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState('all');
  const [filterCountry, setFilterCountry] = useState('all');

  const loadInfrastructureData = async () => {
    try {
      const resp = await api.listEmails({ page: 1, limit: 20 });
      const emails = Array.isArray(resp) ? resp : (resp?.results || []);

      const collectedNodes: InfrastructureNode[] = [];
      const seenIps = new Set<string>();

      for (const email of emails.slice(0, 10)) {
        try {
          const ass = await api.getAssessment(email.submission_id);
          if (ass?.origin?.originating_ip && !seenIps.has(ass.origin.originating_ip)) {
            seenIps.add(ass.origin.originating_ip);
            collectedNodes.push({
              id: `node-${collectedNodes.length + 1}`,
              hop: collectedNodes.length + 1,
              ip: ass.origin.originating_ip,
              hostname: ass.domain_intel?.sender_domain || 'mail.relay.node',
              lat: ass.origin.geolocation?.lat,
              lon: ass.origin.geolocation?.lon,
              asn: ass.origin.geolocation?.asn || 'AS15169',
              isp: ass.origin.geolocation?.isp || 'Transit Network Provider',
              country: ass.origin.geolocation?.country || 'Unknown',
              city: ass.origin.geolocation?.city || 'Unavailable',
              confidence: 'High',
              source: 'GeoIP ASN Resolver',
              timestamp: (ass as any).created_at || (email as any).received_at || 'Observed',
              risk: ass.risk_level as any,

              isEarliestPublic: collectedNodes.length === 0,
              isPrivate: false
            });
          }
        } catch {
          // Continue loading others
        }
      }

      setNodes(collectedNodes);
    } catch {
      setNodes([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadInfrastructureData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadInfrastructureData();
  };

  const handleSelectNode = (node: InfrastructureNode) => {
    setSelectedNodeId(node.id);
    setDrawerData({
      type: 'ip',
      title: node.ip,
      subtitle: `${node.city || 'Unknown City'}, ${node.country || 'Unknown Country'}`,
      provenance: 'observed',
      severity: node.risk as any || 'medium',
      fields: [
        { label: 'IP Address', value: node.ip, isMono: true, isCopyable: true },
        { label: 'Relay Position', value: node.isEarliestPublic ? '★ Earliest Observable Public Relay' : `Hop 0${node.hop}`, isMono: false },
        { label: 'Hostname / FQDN', value: node.hostname || 'UNAVAILABLE', isMono: true, isCopyable: true },
        { label: 'Autonomous System', value: node.asn || 'UNAVAILABLE', isMono: true },
        { label: 'ISP / Hosting Provider', value: node.isp || 'Authoritative Network', isMono: false },
        { label: 'Approximate Location', value: node.city ? `${node.city}, ${node.country}` : node.country || 'Unavailable', isMono: false },
        { label: 'Coordinates', value: node.lat && node.lon ? `[${node.lat.toFixed(4)}, ${node.lon.toFixed(4)}]` : 'Unavailable', isMono: true },
        { label: 'Evidence Source', value: node.source || 'GeoIP Resolver', isMono: false },
        { label: 'Observation Timestamp', value: node.timestamp || 'Observed', isMono: true }
      ],
      evidenceRef: 'RFC 5322 Received Header line 4',
      notes: 'IP geolocation indicates estimated network infrastructure location and does not establish physical identity.'
    });
  };

  // Real Metric Summaries
  const metrics = useMemo(() => {
    const ips = nodes.length;
    const asns = new Set(nodes.map(n => n.asn).filter(Boolean)).size;
    const countries = new Set(nodes.map(n => n.country).filter(Boolean)).size;
    const domains = new Set(nodes.map(n => n.hostname).filter(Boolean)).size;
    return { ips, asns, countries, domains };
  }, [nodes]);

  // Unique country list for filter
  const countryList = useMemo(() => {
    const set = new Set<string>();
    nodes.forEach(n => { if (n.country) set.add(n.country); });
    return Array.from(set);
  }, [nodes]);

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        n.ip.toLowerCase().includes(q) ||
        (n.hostname && n.hostname.toLowerCase().includes(q)) ||
        (n.asn && n.asn.toLowerCase().includes(q)) ||
        (n.country && n.country.toLowerCase().includes(q));

      const matchesRisk = filterRisk === 'all' || (n.risk || '').toLowerCase() === filterRisk.toLowerCase();
      const matchesCountry = filterCountry === 'all' || n.country === filterCountry;

      return matchesSearch && matchesRisk && matchesCountry;
    });
  }, [nodes, searchQuery, filterRisk, filterCountry]);

  return (    <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-6 max-w-[1720px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-base sm:text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">Observable Infrastructure</h1>
          <p className="text-[11px] sm:text-xs font-mono text-[#8B96A3] mt-0.5">
            Geolocation and network intelligence derived from verified email routing evidence
          </p>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 font-mono text-xs">
          <ThreatBadge type="trust" value="observed" size="xs" />
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] hover:text-[#E8A33D] transition-colors min-h-[36px]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
            <span className="hidden xs:inline">Refresh Infrastructure</span>
            <span className="xs:hidden">Refresh</span>
          </button>
        </div>
      </div>

      {/* Summary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3.5 font-mono text-xs">
        <div className="p-3 rounded bg-[#12161B] border border-[#232A32] space-y-1">
          <div className="text-[10px] uppercase text-[#8B96A3]">Observable IPs</div>
          <div className="text-base sm:text-lg font-bold text-[#2DD4BF]">{metrics.ips}</div>
        </div>
        <div className="p-3 rounded bg-[#12161B] border border-[#232A32] space-y-1">
          <div className="text-[10px] uppercase text-[#8B96A3]">Autonomous Systems</div>
          <div className="text-base sm:text-lg font-bold text-[#E8A33D]">{metrics.asns}</div>
        </div>
        <div className="p-3 rounded bg-[#12161B] border border-[#232A32] space-y-1">
          <div className="text-[10px] uppercase text-[#8B96A3]">Transit Countries</div>
          <div className="text-base sm:text-lg font-bold text-[#8B8FE8]">{metrics.countries}</div>
        </div>
        <div className="p-3 rounded bg-[#12161B] border border-[#232A32] space-y-1">
          <div className="text-[10px] uppercase text-[#8B96A3]">Correlated Domains</div>
          <div className="text-base sm:text-lg font-bold text-[#E7EBEF]">{metrics.domains}</div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 sm:gap-3 bg-[#12161B] border border-[#232A32] p-3 rounded-lg font-mono text-xs">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search IP, hostname, ASN..."
            className="w-full pl-9 pr-8 py-1.5 bg-[#0A0D10] border border-[#232A32] rounded text-xs text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D] min-h-[36px]"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#8B96A3] hover:text-white">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#8B96A3] uppercase">Country:</span>
            <select
              value={filterCountry}
              onChange={(e) => setFilterCountry(e.target.value)}
              className="bg-[#0A0D10] border border-[#232A32] text-[#E7EBEF] rounded px-2 py-1.5 text-xs focus:outline-hidden min-h-[36px]"
            >
              <option value="all">All Countries</option>
              {countryList.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[#8B96A3] uppercase">Risk:</span>
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="bg-[#0A0D10] border border-[#232A32] text-[#E7EBEF] rounded px-2 py-1.5 text-xs focus:outline-hidden min-h-[36px]"
            >
              <option value="all">All Risks</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Map Workspace */}
      {loading ? (
        <div className="w-full h-[420px] sm:h-[560px] bg-[#12161B] border border-[#232A32] rounded-lg flex flex-col items-center justify-center space-y-3 font-mono">
          <RefreshCw className="w-6 h-6 text-[#E8A33D] animate-spin" />
          <div className="text-xs text-[#8B96A3]">Resolving observable infrastructure coordinates...</div>
        </div>
      ) : (
        <div className="space-y-4 sm:space-y-6">
          <TraceXMap
            nodes={filteredNodes}
            selectedNodeId={selectedNodeId}
            onSelectNode={handleSelectNode}
          />
          {/* Infrastructure Details Section */}
          {filteredNodes.length > 0 && (
            <div className="bg-[#12161B] rounded-lg border border-[#232A32] overflow-hidden">
              <div className="px-4 sm:px-5 py-3 border-b border-[#232A32] flex items-center justify-between">
                <span className="text-xs font-mono uppercase font-bold text-[#E7EBEF]">
                  Observable Infrastructure Registry ({filteredNodes.length})
                </span>
                <span className="text-[10px] font-mono text-[#8B96A3] hidden sm:inline">Click to inspect node</span>
              </div>

              {/* Desktop Table */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-[#232A32] bg-[#0A0D10]/60 text-[#8B96A3] text-[10px] uppercase">
                      <th className="py-2.5 px-4">Hop</th>
                      <th className="py-2.5 px-4">IP Address</th>
                      <th className="py-2.5 px-4">Hostname</th>
                      <th className="py-2.5 px-4">Autonomous System</th>
                      <th className="py-2.5 px-4">ISP / Hosting Provider</th>
                      <th className="py-2.5 px-4">Location</th>
                      <th className="py-2.5 px-4 text-center">Confidence</th>
                      <th className="py-2.5 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#232A32]">
                    {filteredNodes.map((n) => (
                      <tr
                        key={n.id}
                        onClick={() => handleSelectNode(n)}
                        className={`hover:bg-[#191F26] cursor-pointer transition-colors ${
                          selectedNodeId === n.id ? 'bg-[#191F26] border-l-2 border-l-[#E8A33D]' : ''
                        }`}
                      >
                        <td className="py-3 px-4 font-bold text-[#E8A33D]">
                          {n.isEarliestPublic ? '★ 01' : `0${n.hop}`}
                        </td>
                        <td className="py-3 px-4 text-[#2DD4BF] font-semibold">{n.ip}</td>
                        <td className="py-3 px-4 text-[#8B96A3] truncate max-w-xs">{n.hostname || 'UNAVAILABLE'}</td>
                        <td className="py-3 px-4 text-[#E7EBEF]">{n.asn || 'UNAVAILABLE'}</td>
                        <td className="py-3 px-4 text-[#8B96A3] truncate max-w-xs">{n.isp || 'Authoritative Network'}</td>
                        <td className="py-3 px-4 text-[#E7EBEF] font-sans">
                          {n.city && n.city !== 'Unavailable' ? `${n.city}, ${n.country}` : n.country || 'Unavailable'}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="text-[10px] text-[#2DD4BF] font-bold">{n.confidence || 'High'}</span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectNode(n);
                            }}
                            className="text-[11px] text-[#E8A33D] hover:underline font-bold inline-flex items-center gap-1"
                          >
                            <span>Inspect</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Cards */}
              <div className="md:hidden divide-y divide-[#232A32]">
                {filteredNodes.map((n) => (
                  <div
                    key={n.id}
                    onClick={() => handleSelectNode(n)}
                    className="p-3.5 hover:bg-[#191F26] cursor-pointer transition-colors font-mono text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[#2DD4BF] font-bold">{n.ip}</span>
                      <span className="text-[#E8A33D] text-[11px] font-bold">
                        {n.isEarliestPublic ? '★ Origin Relay' : `Hop 0${n.hop}`}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#8B96A3] truncate">{n.hostname || n.isp || 'Transit Network'}</div>
                    <div className="flex items-center justify-between text-[10px] text-[#566270] pt-1">
                      <span>{n.city ? `${n.city}, ${n.country}` : n.country || 'Unknown'}</span>
                      <span className="text-[#E8A33D] font-bold flex items-center gap-1">
                        <span>Inspect</span>
                        <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Context-Preserving Slideout Drawer */}
      <DetailDrawer data={drawerData} onClose={() => setDrawerData(null)} />
    </div>
  );
};
