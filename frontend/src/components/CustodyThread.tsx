import React, { useState } from 'react';

export interface CustodyNode {
  id: string;
  label: string;
  subLabel?: string;
  type: 'hop' | 'event' | 'evidence' | 'gateway';
  tier: 'fact' | 'prediction' | 'inference' | 'unknown';
  hashLink?: string;
  detail?: string;
}

interface CustodyThreadProps {
  nodes: CustodyNode[];
  orientation?: 'horizontal' | 'vertical';
  onSelectNode?: (nodeId: string) => void;
  selectedNodeId?: string;
}

export const CustodyThread: React.FC<CustodyThreadProps> = ({
  nodes,
  orientation = 'horizontal',
  onSelectNode,
  selectedNodeId
}) => {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'fact': return '#2DD4BF';
      case 'prediction': return '#E8A33D';
      case 'inference': return '#8B8FE8';
      default: return '#566270';
    }
  };

  const isVertical = orientation === 'vertical';

  return (
    <div className={`w-full overflow-x-auto select-none p-3 ${isVertical ? 'space-y-4' : 'flex items-center min-w-max py-4'}`}>
      {nodes.map((node, index) => {
        const isLast = index === nodes.length - 1;
        const color = getTierColor(node.tier);
        const isHovered = hoveredNode === node.id;
        const isSelected = selectedNodeId === node.id;
        const isDiamond = node.type === 'hop' || node.type === 'gateway';

        return (
          <div
            key={node.id}
            className={`flex ${isVertical ? 'flex-col items-start' : 'items-center'}`}
          >
            {/* Node Box */}
            <div
              onClick={() => onSelectNode?.(node.id)}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              className={`relative cursor-pointer transition-all duration-150 p-2.5 rounded bg-[#12161B] border ${
                isSelected
                  ? 'border-[#E8A33D] shadow-[0_0_12px_rgba(232,163,61,0.25)]'
                  : isHovered
                  ? 'border-[#3A4551] bg-[#191F26]'
                  : 'border-[#232A32]'
              } min-w-[170px] max-w-[240px]`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {/* Node Shape: Diamond vs Circle */}
                {isDiamond ? (
                  <div
                    className="w-3.5 h-3.5 rotate-45 border flex-shrink-0 flex items-center justify-center"
                    style={{ borderColor: color, backgroundColor: `${color}15` }}
                  >
                    <div className="w-1 h-1 rounded-full" style={{ backgroundColor: color }} />
                  </div>
                ) : (
                  <div
                    className="w-3.5 h-3.5 rounded-full border flex-shrink-0 flex items-center justify-center"
                    style={{ borderColor: color, backgroundColor: `${color}15` }}
                  >
                    <div className="w-1 h-1 rounded-full" style={{ backgroundColor: color }} />
                  </div>
                )}

                <div className="font-mono text-xs font-semibold text-[#E7EBEF] truncate flex-1">
                  {node.label}
                </div>
              </div>

              {node.subLabel && (
                <div className="font-mono text-[10px] text-[#8B96A3] truncate">
                  {node.subLabel}
                </div>
              )}

              <div className="mt-2 pt-1.5 border-t border-[#232A32] flex items-center justify-between text-[9px] font-mono">
                <span className="uppercase font-semibold" style={{ color }}>
                  ● {node.tier === 'fact' ? 'OBSERVED' : node.tier === 'prediction' ? 'PREDICTED' : node.tier === 'inference' ? 'INFERRED' : 'UNKNOWN'}
                </span>
                <span className="text-[#566270] uppercase">{node.type}</span>
              </div>

              {/* Hover Tooltip */}
              {isHovered && node.detail && (
                <div className="absolute left-0 bottom-full mb-2 z-30 p-2.5 rounded bg-[#191F26] border border-[#3A4551] shadow-2xl text-[10px] font-mono text-[#E7EBEF] w-64 pointer-events-none">
                  <div className="text-[9px] uppercase font-bold text-[#8B96A3] mb-1">Evidence Telemetry:</div>
                  <div>{node.detail}</div>
                  {node.hashLink && (
                    <div className="mt-1.5 pt-1 border-t border-[#232A32] text-[#2DD4BF] truncate">
                      Sealed: {node.hashLink}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Connecting Edge Link */}
            {!isLast && (
              <div
                className={`flex items-center justify-center ${
                  isVertical ? 'py-2 pl-6' : 'px-3'
                }`}
              >
                {isVertical ? (
                  <div className="flex flex-col items-center">
                    <div className="w-px h-6 bg-[#232A32]" />
                    {node.hashLink && (
                      <span className="font-mono text-[9px] text-[#566270] my-0.5">
                        {node.hashLink.slice(0, 16)}...
                      </span>
                    )}
                    <div className="w-0 h-0 border-l-[3px] border-r-[3px] border-t-[5px] border-transparent border-t-[#566270]" />
                  </div>
                ) : (
                  <div className="flex items-center">
                    <div className="w-6 h-px bg-[#232A32]" />
                    {node.hashLink && (
                      <span className="font-mono text-[8px] text-[#566270] px-1 whitespace-nowrap">
                        ──{node.hashLink.slice(0, 12)}...──▶
                      </span>
                    )}
                    {!node.hashLink && (
                      <div className="w-0 h-0 border-t-[3px] border-b-[3px] border-l-[5px] border-transparent border-l-[#566270]" />
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
