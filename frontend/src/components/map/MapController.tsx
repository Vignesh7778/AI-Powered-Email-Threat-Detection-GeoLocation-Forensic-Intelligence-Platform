import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { InfrastructureNode } from './types';

interface MapControllerProps {
  nodes: InfrastructureNode[];
  selectedNodeId?: string | null;
  fitSignal: number;
  zoomInSignal: number;
  zoomOutSignal: number;
}

export const MapController: React.FC<MapControllerProps> = ({
  nodes,
  selectedNodeId,
  fitSignal,
  zoomInSignal,
  zoomOutSignal
}) => {
  const map = useMap();

  // Invalidate size on mount / resize
  useEffect(() => {
    map.invalidateSize();
    const handleResize = () => map.invalidateSize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [map]);

  // Handle Zoom In signal
  useEffect(() => {
    if (zoomInSignal > 0) {
      map.zoomIn();
    }
  }, [zoomInSignal, map]);

  // Handle Zoom Out signal
  useEffect(() => {
    if (zoomOutSignal > 0) {
      map.zoomOut();
    }
  }, [zoomOutSignal, map]);

  // Fit bounds to markers
  useEffect(() => {
    const valid = nodes.filter(n => n.lat !== undefined && n.lat !== null && n.lon !== undefined && n.lon !== null && !n.isPrivate);

    if (valid.length === 1) {
      map.setView([valid[0].lat!, valid[0].lon!], 7);
    } else if (valid.length > 1) {
      const bounds = L.latLngBounds(valid.map(n => [n.lat!, n.lon!]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    }
  }, [nodes, fitSignal, map]);

  // Pan to selected node
  useEffect(() => {
    if (!selectedNodeId) return;
    const sel = nodes.find(n => n.id === selectedNodeId && n.lat && n.lon);
    if (sel) {
      map.flyTo([sel.lat!, sel.lon!], Math.max(map.getZoom(), 7), { duration: 0.8 });
    }
  }, [selectedNodeId, nodes, map]);

  return null;
};
