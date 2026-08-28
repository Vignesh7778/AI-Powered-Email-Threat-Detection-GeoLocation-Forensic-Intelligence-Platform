import React, { useState, useEffect, useRef } from 'react';
import { Share2, RefreshCw, ZoomIn, ZoomOut, RotateCcw, Maximize2, Network, ArrowRight } from 'lucide-react';
import { api } from '../api/client';
import { ThreatBadge } from '../components/ThreatBadge';
import { DetailDrawer, DetailDrawerData } from '../components/DetailDrawer';

interface CampaignsPageProps {
  onSelectSubmission: (id: string) => void;
}

interface GraphNode {
  id: string;
  label: string;
  type: 'campaign' | 'domain' | 'ip' | 'submission';
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export const CampaignsPage: React.FC<CampaignsPageProps> = ({ onSelectSubmission }) => {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [drawerData, setDrawerData] = useState<DetailDrawerData | null>(null);

  // Pan and Zoom states
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const graphContainerRef = useRef<HTMLDivElement>(null);
  const animRef = useRef<number | null>(null);
  const [, setTick] = useState(0);

  const canvasWidth = 1000;
  const canvasHeight = 600;

  const loadCampaigns = async () => {
    try {
      const data = await api.listCampaigns();
      setCampaigns(data);
      if (data && data.length > 0) {
        setSelectedCampaignId(data[0].campaign_id);
      }
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  // Fetch real campaign graph data
  useEffect(() => {
    if (!selectedCampaignId) {
      setGraphData(null);
      return;
    }

    api.getCampaignGraph(selectedCampaignId)
      .then((raw) => {
        if (!raw || !raw.nodes || raw.nodes.length === 0) {
          setGraphData(null);
          return;
        }

        // Initialize positions distributed evenly in circle
        const total = raw.nodes.length;
        const initialNodes: GraphNode[] = raw.nodes.map((n: any, idx: number) => {
          const angle = (idx / total) * 2 * Math.PI;
          const radius = n.type === 'campaign' ? 0 : 200 + (idx % 3) * 40;
          return {
            id: n.id,
            label: n.label || n.id,
            type: n.type || 'domain',
            x: canvasWidth / 2 + Math.cos(angle) * radius,
            y: canvasHeight / 2 + Math.sin(angle) * radius,
            vx: 0,
            vy: 0
          };
        });

        setGraphData({ nodes: initialNodes, edges: raw.edges || [] });
        setScale(1);
        setTranslate({ x: 0, y: 0 });
      })
      .catch(() => setGraphData(null));
  }, [selectedCampaignId]);

  // Run Physics Simulation
  useEffect(() => {
    if (!graphData || graphData.nodes.length === 0) return;

    let iterations = 0;
    const maxIterations = 160;
    const nodes = graphData.nodes;
    const edges = graphData.edges;

    const simulate = () => {
      iterations++;
      const repulsion = 4500;
      const k = 0.04;

      // Node repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 20);
          const force = repulsion / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }

      // Edge spring attraction
      for (const edge of edges) {
        const s = nodes.find(n => n.id === edge.source);
        const t = nodes.find(n => n.id === edge.target);
        if (s && t) {
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const targetDist = 140;
          const force = (dist - targetDist) * k;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          s.vx += fx;
          s.vy += fy;
          t.vx -= fx;
          t.vy -= fy;
        }
      }

      // Gravity to center & bounds
      let displacement = 0;
      for (const node of nodes) {
        const dx = canvasWidth / 2 - node.x;
        const dy = canvasHeight / 2 - node.y;
        node.vx += dx * 0.008;
        node.vy += dy * 0.008;

        node.vx *= 0.82;
        node.vy *= 0.82;

        node.x += node.vx;
        node.y += node.vy;

        node.x = Math.max(60, Math.min(canvasWidth - 60, node.x));
        node.y = Math.max(60, Math.min(canvasHeight - 60, node.y));

        displacement += Math.abs(node.vx) + Math.abs(node.vy);
      }

      setTick(t => t + 1);

      if (iterations < maxIterations && displacement > 0.4) {
        animRef.current = requestAnimationFrame(simulate);
      }
    };

    animRef.current = requestAnimationFrame(simulate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [graphData]);

  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - translate.x, y: e.clientY - translate.y });
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setTranslate({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handlePointerUp = () => setIsDragging(false);

  const handleNodeClick = (node: GraphNode) => {
    setDrawerData({
      type: node.type === 'ip' ? 'ip' : node.type === 'domain' ? 'domain' : 'node',
      title: node.label,
      subtitle: `Attribution Entity (${node.type.toUpperCase()})`,
      provenance: node.type === 'campaign' ? 'prediction' : 'observed',
      severity: node.type === 'submission' ? 'critical' : node.type === 'campaign' ? 'high' : 'medium',
      fields: [
        { label: 'Entity Identifier', value: node.id, isMono: true, isCopyable: true },
        { label: 'Entity Classification', value: node.type.toUpperCase(), isMono: false },
        { label: 'Cluster Assignment', value: selectedCampaignId || 'Active Campaign', isMono: true },
        { label: 'Topology Weight', value: 'Evidence-Correlated Node', isMono: false }
      ],
      evidenceRef: `Associated with campaign cluster ${selectedCampaignId}`,
      notes: 'Correlated across multiple analyzed email headers, shared IP ranges, and registrar records.'
    });
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'campaign': return '#E8A33D';
      case 'domain': return '#2DD4BF';
      case 'ip': return '#8B8FE8';
      case 'submission': return '#E5484D';
      default: return '#566270';
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">Threat Campaign Intelligence</h1>
          <p className="text-xs font-mono text-[#8B96A3] mt-0.5">
            Clustered threat campaigns correlated across shared subnets, domains, and IOC vectors
          </p>
        </div>

        <button
          onClick={() => {
            setRefreshing(true);
            loadCampaigns();
          }}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#12161B] border border-[#232A32] text-xs font-mono text-[#8B96A3] hover:text-[#E8A33D] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#E8A33D]' : ''}`} />
          <span>Refresh Clusters</span>
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="w-full h-[520px] bg-[#12161B] border border-[#232A32] rounded-lg flex flex-col items-center justify-center p-8 text-center space-y-3 font-mono">
          <Network className="w-10 h-10 text-[#566270]" />
          <div className="text-sm font-bold text-[#E7EBEF]">No campaign correlations available</div>
          <p className="text-xs text-[#8B96A3] max-w-md font-sans leading-relaxed">
            Campaign relationships will appear after multiple analyzed artifacts share verified infrastructure, sending subnets, or threat indicators.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left: Campaign Selection Rail (4 cols) */}
          <div className="lg:col-span-4 space-y-3">
            <div className="text-xs font-mono uppercase tracking-wider text-[#8B96A3] font-bold px-1">
              Active Threat Clusters ({campaigns.length})
            </div>

            <div className="space-y-2 max-h-[640px] overflow-y-auto">
              {campaigns.map((camp) => {
                const isSelected = selectedCampaignId === camp.campaign_id;
                return (
                  <div
                    key={camp.campaign_id}
                    onClick={() => setSelectedCampaignId(camp.campaign_id)}
                    className={`p-4 rounded-lg border transition-all cursor-pointer font-mono text-xs space-y-2.5 ${
                      isSelected
                        ? 'bg-[#191F26] border-[#E8A33D] shadow-md'
                        : 'bg-[#12161B] border-[#232A32] hover:border-[#3A4551]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#E7EBEF] font-sans text-sm">{camp.name}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-[#E8A33D15] text-[#E8A33D] border border-[#E8A33D40]">
                        {camp.status || 'ACTIVE'}
                      </span>
                    </div>

                    <p className="text-[#8B96A3] font-sans text-xs line-clamp-2 leading-relaxed">
                      {camp.description}
                    </p>

                    <div className="pt-2 border-t border-[#232A32] flex items-center justify-between text-[11px] text-[#8B96A3]">
                      <div>
                        Actor: <span className="text-[#E8A33D] font-semibold">{camp.threat_actor || 'Unknown'}</span>
                      </div>
                      <div className="text-[#E8A33D] hover:underline font-semibold flex items-center gap-1">
                        <span>Inspect Topology</span>
                        <ArrowRight className="w-3 h-3" />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Full Available Graph Container (8 cols) */}
          <div className="lg:col-span-8 bg-[#12161B] rounded-lg border border-[#232A32] p-4 flex flex-col justify-between space-y-3">
            <div className="flex items-center justify-between border-b border-[#232A32] pb-2 font-mono text-xs">
              <div>
                <span className="font-bold text-[#E7EBEF] uppercase flex items-center gap-2">
                  <Share2 className="w-4 h-4 text-[#E8A33D]" />
                  <span>Attribution Topology Canvas</span>
                </span>
                <span className="text-[10px] text-[#8B96A3] font-sans">
                  Click any node to open context drawer. Pan and zoom supported.
                </span>
              </div>
              <ThreatBadge type="trust" value="model_prediction" size="xs" />
            </div>

            {/* SVG Canvas */}
            <div
              ref={graphContainerRef}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              className="relative w-full h-[540px] bg-[#0A0D10] border border-[#232A32] rounded overflow-hidden cursor-grab active:cursor-grabbing select-none"
            >
              <svg viewBox={`0 0 ${canvasWidth} ${canvasHeight}`} className="w-full h-full">
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="8"
                    markerHeight="6"
                    refX="18"
                    refY="3"
                    orient="auto"
                  >
                    <polygon points="0 0, 8 3, 0 6" fill="#566270" />
                  </marker>
                </defs>

                <g transform={`translate(${translate.x}, ${translate.y}) scale(${scale})`}>
                  {/* Edges */}
                  {graphData?.edges.map((e, idx) => {
                    const s = graphData.nodes.find(n => n.id === e.source);
                    const t = graphData.nodes.find(n => n.id === e.target);
                    if (!s || !t) return null;

                    const midX = (s.x + t.x) / 2;
                    const midY = (s.y + t.y) / 2;

                    return (
                      <g key={idx}>
                        <line
                          x1={s.x}
                          y1={s.y}
                          x2={t.x}
                          y2={t.y}
                          stroke="#232A32"
                          strokeWidth="1.5"
                          strokeDasharray="4 3"
                          markerEnd="url(#arrowhead)"
                        />
                        <text
                          x={midX}
                          y={midY - 4}
                          textAnchor="middle"
                          fill="#566270"
                          fontSize="9"
                          fontFamily="IBM Plex Mono"
                        >
                          {e.relation}
                        </text>
                      </g>
                    );
                  })}

                  {/* Nodes */}
                  {graphData?.nodes.map((n) => {
                    const color = getNodeColor(n.type);
                    const isDiamond = n.type === 'ip' || n.type === 'domain';
                    const isCampaign = n.type === 'campaign';

                    return (
                      <g
                        key={n.id}
                        transform={`translate(${n.x}, ${n.y})`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleNodeClick(n);
                        }}
                        className="cursor-pointer group"
                      >
                        {isDiamond ? (
                          <rect
                            x="-10"
                            y="-10"
                            width="20"
                            height="20"
                            transform="rotate(45)"
                            fill="#12161B"
                            stroke={color}
                            strokeWidth="2"
                          />
                        ) : (
                          <circle
                            r={isCampaign ? 18 : 12}
                            fill="#12161B"
                            stroke={color}
                            strokeWidth="2"
                          />
                        )}

                        {/* Node Text Label with background pill */}
                        <g transform={`translate(0, ${isCampaign ? 26 : 20})`}>
                          <rect
                            x="-60"
                            y="-9"
                            width="120"
                            height="18"
                            rx="3"
                            fill="#12161B"
                            stroke="#232A32"
                            strokeWidth="1"
                          />
                          <text
                            x="0"
                            y="3"
                            textAnchor="middle"
                            fill="#E7EBEF"
                            fontSize="10"
                            fontFamily="IBM Plex Mono"
                            fontWeight="600"
                          >
                            {n.label.length > 18 ? n.label.slice(0, 16) + '...' : n.label}
                          </text>
                        </g>
                      </g>
                    );
                  })}
                </g>
              </svg>

              {/* Floating Canvas Controls */}
              <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 bg-[#12161B]/90 backdrop-blur-xs border border-[#232A32] p-1 rounded font-mono text-xs">
                <button
                  onClick={() => setScale(s => Math.min(s + 0.25, 3))}
                  className="p-1 text-[#8B96A3] hover:text-white rounded"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => setScale(s => Math.max(s - 0.25, 0.5))}
                  className="p-1 text-[#8B96A3] hover:text-white rounded"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    setScale(1);
                    setTranslate({ x: 0, y: 0 });
                  }}
                  className="p-1 text-[#8B96A3] hover:text-white rounded"
                  title="Fit Graph"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Legend */}
              <div className="absolute bottom-3 left-3 z-10 flex flex-wrap items-center gap-3 bg-[#12161B]/90 backdrop-blur-xs border border-[#232A32] px-3 py-1.5 rounded font-mono text-[10px]">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#E8A33D]" /> Campaign Cluster</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rotate-45 border border-[#2DD4BF] bg-[#2DD4BF20]" /> Domain Node</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rotate-45 border border-[#8B8FE8] bg-[#8B8FE820]" /> IP Infrastructure</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-[#E5484D]" /> Incident Artifact</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Node Context Slideout Drawer */}
      <DetailDrawer data={drawerData} onClose={() => setDrawerData(null)} />
    </div>
  );
};
