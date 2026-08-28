import React, { useRef, useEffect, useState } from 'react';
import { Network } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: 'campaign' | 'domain' | 'ip' | 'email' | 'submission';
  x: number;
  y: number;
  vx: number;
  vy: number;
}

interface Edge {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

interface ForceGraphSVGProps {
  nodes: { id: string; label: string; type: string }[];
  edges: { source: string; target: string; relation: string }[];
  className?: string;
}

export const ForceGraphSVG: React.FC<ForceGraphSVGProps> = ({
  nodes: initialNodes,
  edges,
  className = ''
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const nodesRef = useRef<Node[]>([]);
  const animRef = useRef<number | null>(null);
  const [, setTick] = useState(0);

  const width = 700;
  const height = 400;

  // Initialize nodes with distributed circular layout
  useEffect(() => {
    const total = initialNodes.length || 1;
    nodesRef.current = initialNodes.map((n, i) => {
      const angle = (i / total) * 2 * Math.PI;
      const radius = n.type === 'campaign' ? 0 : 120 + Math.random() * 40;
      return {
        id: n.id,
        label: n.label,
        type: n.type as any,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0
      };
    });

    let ticks = 0;
    const maxTicks = 140;

    const simulate = () => {
      ticks++;
      const nodes = nodesRef.current;
      const k = 0.05; // spring constant
      const repulsion = 1800;

      // Pairwise repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 10);
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
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);
        if (sourceNode && targetNode) {
          const dx = targetNode.x - sourceNode.x;
          const dy = targetNode.y - sourceNode.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const targetDist = 90;
          const force = (dist - targetDist) * k;
          const fx = (dx / (dist || 1)) * force;
          const fy = (dy / (dist || 1)) * force;

          sourceNode.vx += fx;
          sourceNode.vy += fy;
          targetNode.vx -= fx;
          targetNode.vy -= fy;
        }
      }

      // Center gravity & dampening
      let totalDisplacement = 0;
      for (const node of nodes) {
        const dx = width / 2 - node.x;
        const dy = height / 2 - node.y;
        node.vx += dx * 0.005;
        node.vy += dy * 0.005;

        node.vx *= 0.85;
        node.vy *= 0.85;

        node.x += node.vx;
        node.y += node.vy;

        // Bound to container
        node.x = Math.max(30, Math.min(width - 30, node.x));
        node.y = Math.max(30, Math.min(height - 30, node.y));

        totalDisplacement += Math.abs(node.vx) + Math.abs(node.vy);
      }

      setTick(t => t + 1);

      if (ticks < maxTicks && totalDisplacement > 0.5) {
        animRef.current = requestAnimationFrame(simulate);
      }
    };

    animRef.current = requestAnimationFrame(simulate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [initialNodes, edges]);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'campaign': return '#E8A33D';
      case 'domain': return '#2DD4BF';
      case 'ip': return '#8B8FE8';
      case 'submission': return '#E5484D';
      default: return '#566270';
    }
  };

  const nodes = nodesRef.current;

  return (
    <div className={`relative w-full h-[420px] bg-[#0A0D10] border border-[#232A32] rounded-lg overflow-hidden select-none ${className}`}>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
        {/* Render Edges */}
        {edges.map((e, idx) => {
          const s = nodes.find(n => n.id === e.source);
          const t = nodes.find(n => n.id === e.target);
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
                strokeWidth="1.2"
                strokeDasharray="4 3"
              />
              <text
                x={midX}
                y={midY - 4}
                textAnchor="middle"
                fill="#566270"
                fontSize="8"
                fontFamily="IBM Plex Mono"
              >
                {e.relation}
              </text>
            </g>
          );
        })}

        {/* Render Nodes (Diamond for Infra/IP, Circle for Events) */}
        {nodes.map((n) => {
          const color = getNodeColor(n.type);
          const isSelected = selectedNode === n.id;
          const isDiamond = n.type === 'ip' || n.type === 'domain';

          return (
            <g
              key={n.id}
              transform={`translate(${n.x}, ${n.y})`}
              onClick={() => setSelectedNode(n.id)}
              className="cursor-pointer group"
            >
              {isDiamond ? (
                <rect
                  x="-7"
                  y="-7"
                  width="14"
                  height="14"
                  transform="rotate(45)"
                  fill="#12161B"
                  stroke={color}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                />
              ) : (
                <circle
                  r={n.type === 'campaign' ? 12 : 8}
                  fill="#12161B"
                  stroke={color}
                  strokeWidth={isSelected ? '2.5' : '1.5'}
                />
              )}

              {/* Node Label */}
              <text
                x="0"
                y={isDiamond ? 18 : 16}
                textAnchor="middle"
                fill="#E7EBEF"
                fontSize="9"
                fontFamily="IBM Plex Mono"
                fontWeight="500"
              >
                {n.label.length > 20 ? n.label.slice(0, 18) + '...' : n.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Legend */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-3 bg-[#12161B]/90 border border-[#232A32] px-3 py-1.5 rounded font-mono text-[10px]">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rotate-45 border border-[#E8A33D] bg-[#E8A33D20]" /> Campaign</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rotate-45 border border-[#2DD4BF] bg-[#2DD4BF20]" /> Domain</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rotate-45 border border-[#8B8FE8] bg-[#8B8FE820]" /> IP Infra</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full border border-[#E5484D] bg-[#E5484D20]" /> Incident</span>
      </div>

      <div className="absolute bottom-3 right-3 z-10 text-[9px] font-mono text-[#566270]">
        Native Physics: RAF Force Simulation
      </div>
    </div>
  );
};
