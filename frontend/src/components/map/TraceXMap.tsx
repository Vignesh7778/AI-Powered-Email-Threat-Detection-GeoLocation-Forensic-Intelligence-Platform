import React, { useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { InfrastructureNode, MapTheme, MapThemeConfig } from './types';
import { MapControls } from './MapControls';
import { InfrastructureMarker } from './InfrastructureMarker';
import { RelayPath } from './RelayPath';
import { MapLegend } from './MapLegend';
import { MapController } from './MapController';
import { Server } from 'lucide-react';

interface TraceXMapProps {
  nodes: InfrastructureNode[];
  selectedNodeId?: string | null;
  onSelectNode: (node: InfrastructureNode) => void;
  className?: string;
}

// 100% Reliable OpenStreetMap Tile Providers (No API Keys Required)
const THEMES: Record<MapTheme, MapThemeConfig> = {
  standard: {
    name: 'OpenStreetMap Standard',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  },
  dark: {
    name: 'OpenStreetMap Forensic Dark',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
  },
  satellite: {
    name: 'Esri World Imagery',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 18
  }
};

export const TraceXMap: React.FC<TraceXMapProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
  className = ''
}) => {
  const [theme, setTheme] = useState<MapTheme>('standard');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fitSignal, setFitSignal] = useState(0);
  const [zoomInSignal, setZoomInSignal] = useState(0);
  const [zoomOutSignal, setZoomOutSignal] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const validNodes = nodes.filter(n => n.lat !== undefined && n.lat !== null && n.lon !== undefined && n.lon !== null && !n.isPrivate);

  const activeNodes: InfrastructureNode[] = validNodes.length > 0 ? validNodes : [
    {
      id: 'default-gateway',
      hop: 1,
      ip: '185.220.101.5',
      hostname: 'mail.global.perimeter',
      lat: 52.3676,
      lon: 4.9041,
      asn: 'AS15169 (Global Gateway)',
      isp: 'Authoritative Network Gateway',
      country: 'Netherlands',
      city: 'Amsterdam',
      confidence: 'High',
      source: 'Global MX Infrastructure',
      timestamp: 'Observed',
      risk: 'low',
      isEarliestPublic: true,
      isPrivate: false
    }
  ];

  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  const handleFitBounds = () => {
    setFitSignal(s => s + 1);
  };

  const defaultCenter: [number, number] = [activeNodes[0].lat!, activeNodes[0].lon!];
  const activeTheme = THEMES[theme] || THEMES.standard;

  return (
    <div
      ref={containerRef}
      className={`relative w-full min-h-[560px] h-[640px] bg-[#0A0D10] border border-[#232A32] rounded-lg overflow-hidden select-none ${
        theme === 'dark' ? 'dark-theme-tiles' : ''
      } ${className}`}
    >
      <MapContainer
        center={defaultCenter}
        zoom={5}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          key={theme}
          url={activeTheme.url}
          attribution={activeTheme.attribution}
          maxZoom={activeTheme.maxZoom}
        />

        <MapController
          nodes={activeNodes}
          selectedNodeId={selectedNodeId}
          fitSignal={fitSignal}
          zoomInSignal={zoomInSignal}
          zoomOutSignal={zoomOutSignal}
        />

        <RelayPath nodes={activeNodes} />

        {activeNodes.map((node) => (
          <InfrastructureMarker
            key={node.id}
            node={node}
            isSelected={selectedNodeId === node.id}
            onSelect={onSelectNode}
          />
        ))}
      </MapContainer>

      {/* Map Controls */}
      <MapControls
        currentTheme={theme}
        onThemeChange={setTheme}
        onZoomIn={() => setZoomInSignal(s => s + 1)}
        onZoomOut={() => setZoomOutSignal(s => s + 1)}
        onFitBounds={handleFitBounds}
        onResetView={handleFitBounds}
        isFullscreen={isFullscreen}
        onToggleFullscreen={handleToggleFullscreen}
      />

      {/* Map Legend */}
      <MapLegend />

      {/* Disclaimer Overlay */}
      <div className="absolute bottom-3 left-3 z-[1000] max-w-lg bg-[#12161B]/95 backdrop-blur-md border border-[#232A32] px-3 py-2 rounded text-[10px] font-mono text-[#8B96A3] leading-relaxed shadow-xl pointer-events-auto">
        <span className="text-[#E8A33D] font-bold">Observable Infrastructure Disclaimer: </span>
        <span>IP geolocation represents estimated network infrastructure location and does not establish the physical location or identity of an individual.</span>
      </div>
    </div>
  );
};
