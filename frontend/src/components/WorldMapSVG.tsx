import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, MapPin } from 'lucide-react';

interface GeoPoint {
  hop: number;
  ip: string;
  lat: number;
  lon: number;
  city?: string;
  country?: string;
  isp?: string;
  isPrivate?: boolean;
}

interface WorldMapSVGProps {
  points: GeoPoint[];
  selectedHop?: number | null;
  onSelectHop?: (hop: number) => void;
  className?: string;
}

// Stylized low-poly equirectangular landmass paths
const WORLD_LAND_PATHS = [
  // North America
  "M 150 120 L 190 90 L 280 80 L 320 100 L 340 140 L 300 200 L 260 250 L 220 230 L 180 200 L 140 160 Z",
  // Greenland
  "M 330 50 L 370 40 L 390 70 L 350 90 Z",
  // South America
  "M 260 260 L 310 270 L 340 330 L 310 420 L 280 430 L 260 360 L 250 290 Z",
  // Eurasia
  "M 450 100 L 520 80 L 650 70 L 820 90 L 860 140 L 780 200 L 710 240 L 620 220 L 540 210 L 480 180 L 440 140 Z",
  // Africa
  "M 470 200 L 550 200 L 570 260 L 540 360 L 490 380 L 460 300 L 450 230 Z",
  // Australia
  "M 740 320 L 820 310 L 840 370 L 790 400 L 730 370 Z",
  // UK / Europe islands
  "M 430 110 L 450 105 L 445 125 Z"
];

export const WorldMapSVG: React.FC<WorldMapSVGProps> = ({
  points,
  selectedHop,
  onSelectHop,
  className = ''
}) => {
  const [scale, setScale] = useState(1);
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [activeTooltip, setActiveTooltip] = useState<GeoPoint | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const mapWidth = 960;
  const mapHeight = 480;

  // Convert (lat, lon) to (x, y) coordinates on equirectangular projection
  const project = (lat: number, lon: number) => {
    const x = ((lon + 180) / 360) * mapWidth;
    const y = ((90 - lat) / 180) * mapHeight;
    return { x, y };
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - translate.x, y: e.clientY - translate.y });
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    setTranslate({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handlePointerUp = () => setIsDragging(false);

  // Auto-focus on selected hop if requested
  useEffect(() => {
    if (selectedHop !== null && selectedHop !== undefined) {
      const pt = points.find(p => p.hop === selectedHop && !p.isPrivate);
      if (pt) {
        const { x, y } = project(pt.lat, pt.lon);
        setScale(1.8);
        setTranslate({
          x: -(x * 1.8 - mapWidth / 2),
          y: -(y * 1.8 - mapHeight / 2)
        });
        setActiveTooltip(pt);
      }
    }
  }, [selectedHop]);

  // Build hop route polyline string
  const validPoints = points.filter(p => !p.isPrivate && p.lat && p.lon);
  const routePath = validPoints
    .map((p, idx) => {
      const { x, y } = project(p.lat, p.lon);
      return `${idx === 0 ? 'M' : 'L'} ${x} ${y}`;
    })
    .join(' ');

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-[440px] bg-[#0A0D10] border border-[#232A32] rounded-lg overflow-hidden select-none cursor-grab active:cursor-grabbing ${className}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
    >
      {/* Precision Grid Overlay */}
      <svg
        viewBox={`0 0 ${mapWidth} ${mapHeight}`}
        className="w-full h-full"
        style={{ touchAction: 'none' }}
      >
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#191F26" strokeWidth="0.75" />
          </pattern>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        <rect width={mapWidth} height={mapHeight} fill="url(#grid)" />

        {/* Scalable & Translatable Map Group */}
        <g
          transform={`translate(${translate.x}, ${translate.y}) scale(${scale})`}
          style={{ transition: isDragging ? 'none' : 'transform 200ms cubic-bezier(0.16, 1, 0.3, 1)' }}
        >
          {/* Equator and Meridian Reference Lines */}
          <line x1="0" y1={mapHeight / 2} x2={mapWidth} y2={mapHeight / 2} stroke="#232A32" strokeDasharray="4 4" strokeWidth="0.75" />
          <line x1={mapWidth / 2} y1="0" x2={mapWidth / 2} y2={mapHeight} stroke="#232A32" strokeDasharray="4 4" strokeWidth="0.75" />

          {/* Landmass Paths */}
          {WORLD_LAND_PATHS.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="#12161B"
              stroke="#232A32"
              strokeWidth="1.2"
              strokeLinejoin="round"
            />
          ))}

          {/* Hop Route Polyline Connection */}
          {routePath && (
            <path
              d={routePath}
              fill="none"
              stroke="#E8A33D"
              strokeWidth="1.5"
              strokeDasharray="6 4"
              className="animate-pulse"
            />
          )}

          {/* Hop Coordinate Nodes */}
          {validPoints.map((p) => {
            const { x, y } = project(p.lat, p.lon);
            const isSelected = selectedHop === p.hop;

            return (
              <g
                key={p.hop}
                transform={`translate(${x}, ${y})`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectHop?.(p.hop);
                  setActiveTooltip(p);
                }}
                className="cursor-pointer group"
              >
                {/* Outer Ring */}
                <circle
                  r={isSelected ? 10 : 7}
                  fill="#0A0D10"
                  stroke={isSelected ? '#E8A33D' : '#2DD4BF'}
                  strokeWidth="2"
                  filter="url(#glow)"
                />
                {/* Inner Core */}
                <circle
                  r={isSelected ? 4 : 2.5}
                  fill={isSelected ? '#E8A33D' : '#2DD4BF'}
                />
                {/* Hop Label Badge */}
                <rect
                  x="10"
                  y="-12"
                  width="44"
                  height="16"
                  rx="2"
                  fill="#12161B"
                  stroke="#232A32"
                  strokeWidth="1"
                />
                <text
                  x="32"
                  y="-1"
                  textAnchor="middle"
                  fill="#E7EBEF"
                  fontSize="9"
                  fontFamily="IBM Plex Mono"
                  fontWeight="600"
                >
                  Hop {p.hop}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Floating Coordinate HUD & Info Card */}
      {activeTooltip && (
        <div className="absolute top-3 left-3 z-20 p-3 rounded bg-[#12161B]/95 border border-[#232A32] shadow-2xl font-mono text-xs max-w-xs space-y-1 backdrop-blur-sm">
          <div className="flex items-center justify-between border-b border-[#232A32] pb-1">
            <span className="text-[#E8A33D] font-bold">Hop {activeTooltip.hop}: {activeTooltip.ip}</span>
            <span className="text-[10px] text-[#2DD4BF]">● OBSERVED</span>
          </div>
          <div className="text-[11px] text-[#E7EBEF]">
            Location: {activeTooltip.city ? `${activeTooltip.city}, ${activeTooltip.country}` : activeTooltip.country || 'Unavailable'}
          </div>
          <div className="text-[10px] text-[#8B96A3] truncate">ISP: {activeTooltip.isp || 'Authoritative Transit Provider'}</div>
          <div className="text-[9px] text-[#566270] pt-0.5">Coord: [{activeTooltip.lat.toFixed(2)}, {activeTooltip.lon.toFixed(2)}]</div>
        </div>
      )}

      {/* Map Controls */}
      <div className="absolute bottom-3 right-3 z-20 flex items-center gap-1.5 bg-[#12161B] border border-[#232A32] p-1 rounded">
        <button
          onClick={() => setScale(s => Math.min(s + 0.4, 4))}
          className="p-1 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#191F26] rounded transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => setScale(s => Math.max(s - 0.4, 0.8))}
          className="p-1 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#191F26] rounded transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => {
            setScale(1);
            setTranslate({ x: 0, y: 0 });
          }}
          className="p-1 text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#191F26] rounded transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Non-Routable Nodes Sidebar */}
      <div className="absolute bottom-3 left-3 z-20 bg-[#12161B]/90 border border-[#232A32] px-2.5 py-1.5 rounded font-mono text-[10px] text-[#566270]">
        <span>Notice: IP geolocation reflects transit server infrastructure, not physical attacker location.</span>
      </div>
    </div>
  );
};
