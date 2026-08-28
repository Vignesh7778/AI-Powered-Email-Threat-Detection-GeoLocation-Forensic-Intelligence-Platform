import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { RotateCcw, Maximize2, Server } from 'lucide-react';

export interface MapRelayPoint {
  hop: number;
  ip: string;
  lat: number;
  lon: number;
  city?: string;
  country?: string;
  isp?: string;
  asn?: string;
  confidence?: number;
  source?: string;
  timestamp?: string;
  isPrivate?: boolean;
}

interface LeafletInfrastructureMapProps {
  points: MapRelayPoint[];
  selectedHop?: number | null;
  onSelectHop?: (hop: number) => void;
  className?: string;
}

const createPinIcon = (hopNum: number, isSelected: boolean) => {
  const hopStr = hopNum < 10 ? `0${hopNum}` : `${hopNum}`;
  const pinFill = hopNum === 1 ? '#E8A33D' : '#E5484D';
  const scale = isSelected ? 'scale(1.15)' : 'scale(1.0)';

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
      <svg style="position: absolute; bottom: -4px; width: 24px; height: 8px; opacity: 0.45;" viewBox="0 0 24 8">
        <ellipse cx="12" cy="4" rx="10" ry="3" fill="#000000" filter="blur(1px)" />
      </svg>
      <svg width="38" height="48" viewBox="0 0 38 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M19 0C8.50659 0 0 8.50659 0 19C0 30.5 19 48 19 48C19 48 38 30.5 38 19C38 8.50659 29.4934 0 19 0Z"
          fill="${pinFill}"
        />
        <circle cx="19" cy="18" r="12" fill="#FFFFFF" />
        <text
          x="19"
          y="22"
          text-anchor="middle"
          fill="#0A0D10"
          font-family="'IBM Plex Mono', 'JetBrains Mono', monospace"
          font-size="11"
          font-weight="800"
        >${hopStr}</text>
      </svg>
    </div>
  `;

  return L.divIcon({
    className: 'custom-forensic-map-pin',
    html: svgHtml,
    iconSize: [38, 48],
    iconAnchor: [19, 48],
    popupAnchor: [0, -48]
  });
};

const MapAutoFitter: React.FC<{ points: MapRelayPoint[]; selectedHop?: number | null }> = ({ points, selectedHop }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedHop !== null && selectedHop !== undefined) {
      const selected = points.find(p => p.hop === selectedHop && p.lat && p.lon);
      if (selected) {
        map.flyTo([selected.lat, selected.lon], Math.max(map.getZoom(), 7), { duration: 0.8 });
        return;
      }
    }

    const valid = points.filter(p => p.lat && p.lon && !p.isPrivate);
    if (valid.length === 1) {
      map.setView([valid[0].lat, valid[0].lon], 5);
    } else if (valid.length > 1) {
      const bounds = L.latLngBounds(valid.map(p => [p.lat, p.lon]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    }
  }, [points, selectedHop, map]);

  return null;
};

export const LeafletInfrastructureMap: React.FC<LeafletInfrastructureMapProps> = ({
  points,
  selectedHop,
  onSelectHop,
  className = ''
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const validPoints = points.filter(p => p.lat !== undefined && p.lon !== undefined && !p.isPrivate);

  const handleFullscreen = () => {
    if (!mapContainerRef.current) return;
    if (!document.fullscreenElement) {
      mapContainerRef.current.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  if (validPoints.length === 0) {
    return (
      <div className={`w-full h-[480px] bg-[#0A0D10] border border-[#232A32] rounded-lg flex flex-col items-center justify-center p-8 text-center space-y-3 font-mono ${className}`}>
        <Server className="w-8 h-8 text-[#566270]" />
        <div className="text-sm font-bold text-[#E7EBEF]">No observable infrastructure locations available</div>
        <p className="text-xs text-[#8B96A3] max-w-md font-sans">
          Analyzed artifact contains only internal non-routable private addresses (RFC 1918 / localhost) or unresolvable transit nodes.
        </p>
      </div>
    );
  }

  const polylinePositions: [number, number][] = validPoints
    .sort((a, b) => a.hop - b.hop)
    .map(p => [p.lat, p.lon]);

  const defaultCenter: [number, number] = [validPoints[0].lat, validPoints[0].lon];

  return (
    <div
      ref={mapContainerRef}
      className={`relative w-full h-[520px] bg-[#0A0D10] border border-[#232A32] rounded-lg overflow-hidden select-none ${className}`}
    >
      <MapContainer
        center={defaultCenter}
        zoom={4}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapAutoFitter points={points} selectedHop={selectedHop} />

        {polylinePositions.length > 1 && (
          <Polyline
            positions={polylinePositions}
            pathOptions={{
              color: '#E8A33D',
              weight: 2.5,
              opacity: 0.85,
              dashArray: '6, 6'
            }}
          />
        )}

        {validPoints.map((p) => {
          const isSelected = selectedHop === p.hop;
          return (
            <Marker
              key={p.hop}
              position={[p.lat, p.lon]}
              icon={createPinIcon(p.hop, isSelected)}
              eventHandlers={{
                click: () => onSelectHop?.(p.hop)
              }}
            >
              <Popup>
                <div className="font-mono text-xs space-y-2 p-1 min-w-[220px]">
                  <div className="flex items-center justify-between border-b border-[#232A32] pb-1">
                    <span className="font-bold text-[#E8A33D]">Relay Node 0{p.hop}</span>
                    <span className="text-[10px] text-[#2DD4BF] font-semibold">● OBSERVED</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-[#E7EBEF]">
                    <div>IP: <span className="font-bold text-[#2DD4BF]">{p.ip}</span></div>
                    <div>Location: {p.city ? `${p.city}, ${p.country}` : p.country || 'Unknown'}</div>
                    {p.asn && <div>ASN: <span className="text-[#8B96A3]">{p.asn}</span></div>}
                    <div>ISP: <span className="text-[#8B96A3]">{p.isp || 'Authoritative Network'}</span></div>
                    {p.timestamp && <div className="text-[10px] text-[#566270]">Observed: {p.timestamp}</div>}
                  </div>
                  <div className="text-[9px] text-[#566270] pt-1 border-t border-[#232A32]">
                    Coord: [{p.lat.toFixed(4)}, {p.lon.toFixed(4)}]
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <div className="absolute top-3 right-3 z-[1000] flex items-center gap-2 bg-[#12161B]/90 backdrop-blur-xs border border-[#232A32] p-1.5 rounded">
        <button
          onClick={() => onSelectHop?.(-1)}
          className="p-1.5 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#191F26] rounded transition-colors font-mono text-[11px] flex items-center gap-1"
          title="Reset View to Fit All Markers"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Fit All</span>
        </button>
        <button
          onClick={handleFullscreen}
          className="p-1.5 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#191F26] rounded transition-colors"
          title="Toggle Fullscreen"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="absolute bottom-3 left-3 z-[1000] max-w-xl bg-[#12161B]/95 backdrop-blur-xs border border-[#232A32] px-3 py-2 rounded text-[10px] font-mono text-[#8B96A3] leading-relaxed shadow-lg">
        <span className="text-[#E8A33D] font-bold">Observable Infrastructure Disclaimer: </span>
        <span>IP geolocation represents estimated network infrastructure transit nodes and does not establish the physical location or identity of an attacker.</span>
      </div>
    </div>
  );
};
