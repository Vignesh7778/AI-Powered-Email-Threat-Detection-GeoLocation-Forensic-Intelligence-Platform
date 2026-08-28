import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { InfrastructureNode } from './types';

interface InfrastructureMarkerProps {
  node: InfrastructureNode;
  isSelected: boolean;
  onSelect: (node: InfrastructureNode) => void;
}

// Generate SVG Teardrop Map Pin Marker matching the user reference image
const createPinIcon = (node: InfrastructureNode, isSelected: boolean) => {
  const hopStr = node.hop < 10 ? `0${node.hop}` : `${node.hop}`;
  const isEarliest = node.isEarliestPublic;

  // Pin Fill & Accent colors
  let pinFill = '#E5484D'; // Vibrant Crimson / Red from reference image
  let ringFill = '#FFFFFF';
  let textColor = '#0A0D10';
  let shadowOpacity = 0.45;

  if (isEarliest) {
    pinFill = '#E8A33D'; // Amber for Earliest Public
    ringFill = '#FFFFFF';
    textColor = '#0A0D10';
    shadowOpacity = 0.6;
  } else if (node.risk === 'critical') {
    pinFill = '#E5484D';
  } else if (node.risk === 'high') {
    pinFill = '#EA580C';
  } else if (node.risk === 'medium') {
    pinFill = '#E8A33D';
  } else if (node.risk === 'verified') {
    pinFill = '#2DD4BF';
  }

  const scale = isSelected ? 'scale(1.15)' : 'scale(1.0)';
  const labelContent = isEarliest ? `★${hopStr}` : hopStr;

  const svgHtml = `
    <div style="
      position: relative;
      width: 38px;
      height: 48px;
      transform: ${scale};
      transition: transform 150ms cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
    ">
      <!-- Ground Drop Shadow -->
      <svg style="position: absolute; bottom: -4px; width: 24px; height: 8px; opacity: ${shadowOpacity};" viewBox="0 0 24 8">
        <ellipse cx="12" cy="4" rx="10" ry="3" fill="#000000" filter="blur(1px)" />
      </svg>

      <!-- Teardrop Location Pin -->
      <svg width="38" height="48" viewBox="0 0 38 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="pinGrad-${node.id}" x1="19" y1="0" x2="19" y2="46" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="${pinFill}" />
            <stop offset="100%" stop-color="${pinFill}" stop-opacity="0.85" />
          </linearGradient>
          <filter id="pinShadow-${node.id}" x="0" y="0" width="38" height="48" filterUnits="userSpaceOnUse">
            <feDropShadow dx="0" dy="3" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.5"/>
          </filter>
        </defs>

        <!-- Pin Body -->
        <path
          d="M19 0C8.50659 0 0 8.50659 0 19C0 30.5 19 48 19 48C19 48 38 30.5 38 19C38 8.50659 29.4934 0 19 0Z"
          fill="url(#pinGrad-${node.id})"
          filter="url(#pinShadow-${node.id})"
        />

        <!-- Inner White Circular Pill Badge -->
        <circle cx="19" cy="18" r="12" fill="${ringFill}" />

        <!-- Hop Number Text -->
        <text
          x="19"
          y="22"
          text-anchor="middle"
          fill="${textColor}"
          font-family="'IBM Plex Mono', 'JetBrains Mono', monospace"
          font-size="11"
          font-weight="800"
        >${labelContent}</text>
      </svg>
    </div>
  `;

  return L.divIcon({
    className: 'custom-forensic-map-pin',
    html: svgHtml,
    iconSize: [38, 48],
    iconAnchor: [19, 48], // Point anchored exactly to the lat/lon coordinate
    popupAnchor: [0, -48]
  });
};

export const InfrastructureMarker: React.FC<InfrastructureMarkerProps> = ({
  node,
  isSelected,
  onSelect
}) => {
  if (!node.lat || !node.lon) return null;

  return (
    <Marker
      position={[node.lat, node.lon]}
      icon={createPinIcon(node, isSelected)}
      eventHandlers={{
        click: () => onSelect(node)
      }}
    >
      <Popup className="forensic-leaflet-popup">
        <div className="font-mono text-xs space-y-2 p-1 min-w-[240px] text-[#E7EBEF]">
          <div className="flex items-center justify-between border-b border-[#232A32] pb-1">
            <span className="font-bold text-[#E8A33D]">
              {node.isEarliestPublic ? '★ Earliest Public Relay' : `Relay Node 0${node.hop}`}
            </span>
            <span className="text-[10px] text-[#2DD4BF] font-semibold">● OBSERVED</span>
          </div>

          <div className="space-y-1 text-[11px]">
            <div>IP Address: <span className="font-bold text-[#2DD4BF]">{node.ip}</span></div>
            {node.hostname && <div className="truncate text-[#8B96A3]">Host: {node.hostname}</div>}
            {node.asn && <div>ASN: <span className="text-[#8B96A3]">{node.asn}</span></div>}
            <div>ISP / Network: <span className="text-[#8B96A3]">{node.isp || 'Authoritative Network'}</span></div>
            <div>
              Location: {node.city && node.city !== 'Unknown' && node.city !== 'Unavailable' ? `${node.city}, ` : ''}{node.country || 'Unavailable'}
            </div>
            {node.timestamp && <div className="text-[10px] text-[#566270]">Timestamp: {node.timestamp}</div>}
          </div>

          <div className="text-[9px] text-[#566270] pt-1 border-t border-[#232A32] flex items-center justify-between">
            <span>Coord: [{node.lat.toFixed(4)}, {node.lon.toFixed(4)}]</span>
            <span className="text-[#E8A33D]">Click to inspect →</span>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};
