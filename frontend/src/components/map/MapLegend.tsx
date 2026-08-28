import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div className="absolute bottom-3 right-3 z-[1000] bg-[#12161B]/95 backdrop-blur-md border border-[#232A32] px-3 py-2 rounded shadow-xl font-mono text-[10px] text-[#8B96A3] space-y-1.5 pointer-events-auto select-none">
      <div className="text-[9px] uppercase font-bold text-[#E7EBEF] border-b border-[#232A32] pb-0.5">
        Map Topology Legend
      </div>
      <div className="flex items-center gap-2">
        <div className="w-4 h-3.5 rounded bg-[#12161B] border border-[#2DD4BF] text-[#2DD4BF] text-[9px] flex items-center justify-center font-bold">
          01
        </div>
        <span>Transit Relay Hop</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-4 h-3.5 rounded bg-[#191F26] border border-[#E8A33D] text-[#E8A33D] text-[9px] flex items-center justify-center font-bold">
          ★
        </div>
        <span>Earliest Observable Public Relay</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-4 h-0.5 border-b border-dashed border-[#E8A33D]" />
        <span>Reconstructed Mail Routing Path</span>
      </div>
    </div>
  );
};
