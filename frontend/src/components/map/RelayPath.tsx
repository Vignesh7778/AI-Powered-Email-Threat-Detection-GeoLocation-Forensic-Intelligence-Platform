import React from 'react';
import { Polyline } from 'react-leaflet';
import { InfrastructureNode } from './types';

interface RelayPathProps {
  nodes: InfrastructureNode[];
}

export const RelayPath: React.FC<RelayPathProps> = ({ nodes }) => {
  const validNodes = nodes
    .filter(n => n.lat !== undefined && n.lat !== null && n.lon !== undefined && n.lon !== null && !n.isPrivate)
    .sort((a, b) => a.hop - b.hop);

  if (validNodes.length < 2) return null;

  const positions: [number, number][] = validNodes.map(n => [n.lat!, n.lon!]);

  return (
    <>
      {/* Outer Subtle Shadow Polyline */}
      <Polyline
        positions={positions}
        pathOptions={{
          color: '#E8A33D',
          weight: 6,
          opacity: 0.15,
          lineCap: 'round',
          lineJoin: 'round'
        }}
      />
      {/* Core Restrained Amber Relay Path */}
      <Polyline
        positions={positions}
        pathOptions={{
          color: '#E8A33D',
          weight: 2,
          opacity: 0.85,
          dashArray: '6, 6',
          lineCap: 'round',
          lineJoin: 'round'
        }}
      />
    </>
  );
};
