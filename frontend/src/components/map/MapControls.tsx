import React from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, Minimize2, Layers } from 'lucide-react';
import { MapTheme } from './types';

interface MapControlsProps {
  currentTheme: MapTheme;
  onThemeChange: (theme: MapTheme) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitBounds: () => void;
  onResetView: () => void;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
}

export const MapControls: React.FC<MapControlsProps> = ({
  currentTheme,
  onThemeChange,
  onZoomIn,
  onZoomOut,
  onFitBounds,
  onResetView,
  isFullscreen,
  onToggleFullscreen
}) => {
  return (
    <div className="absolute top-3 right-3 z-[1000] flex flex-col items-end gap-2 pointer-events-auto font-mono text-xs select-none">
      {/* Theme Selector Strip */}
      <div className="flex items-center bg-[#12161B]/95 backdrop-blur-md border border-[#232A32] rounded p-0.5 shadow-xl">
        {(['dark', 'standard', 'satellite'] as MapTheme[]).map((t) => (
          <button
            key={t}
            onClick={() => onThemeChange(t)}
            className={`px-2.5 py-1 rounded text-[10px] uppercase font-bold transition-all ${
              currentTheme === t
                ? 'bg-[#191F26] text-[#E8A33D] border border-[#E8A33D]/40 shadow-sm'
                : 'text-[#8B96A3] hover:text-[#E7EBEF]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Map Action Buttons */}
      <div className="flex flex-col items-center bg-[#12161B]/95 backdrop-blur-md border border-[#232A32] rounded p-1 shadow-xl space-y-1">
        <button
          onClick={onZoomIn}
          className="p-1.5 rounded text-[#8B96A3] hover:text-white hover:bg-[#191F26] transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onZoomOut}
          className="p-1.5 rounded text-[#8B96A3] hover:text-white hover:bg-[#191F26] transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <div className="w-4 h-px bg-[#232A32] my-0.5" />
        <button
          onClick={onFitBounds}
          className="p-1.5 rounded text-[#8B96A3] hover:text-[#E8A33D] hover:bg-[#191F26] transition-colors"
          title="Fit Observable Infrastructure"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={onToggleFullscreen}
          className="p-1.5 rounded text-[#8B96A3] hover:text-white hover:bg-[#191F26] transition-colors"
          title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
        >
          {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
};
