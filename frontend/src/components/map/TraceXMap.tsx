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

  if (validNodes.length === 0) {
    return (
      <div className={`w-full min-h-[480px] bg-[#12161B] border border-[#232A32] rounded-lg flex flex-col items-center justify-center p-8 text-center space-y-3 font-mono ${className}`}>
        <Server className="w-10 h-10 text-[#566270]" />
        <div className="text-sm font-bold text-[#E7EBEF]">No observable infrastructure locations available</div>
        <p className="text-xs text-[#8B96A3] max-w-md font-sans leading-relaxed">
          Analyze an email containing observable public infrastructure to populate this map with verified geographic coordinates and relay routing paths.
        </p>
      </div>
    );
  }

  const defaultCenter: [number, number] = [validNodes[0].lat!, validNodes[0].lon!];
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
          nodes={nodes}
          selectedNodeId={selectedNodeId}
          fitSignal={fitSignal}
          zoomInSignal={zoomInSignal}
          zoomOutSignal={zoomOutSignal}
        />

        <RelayPath nodes={nodes} />

        {validNodes.map((node) => (
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
