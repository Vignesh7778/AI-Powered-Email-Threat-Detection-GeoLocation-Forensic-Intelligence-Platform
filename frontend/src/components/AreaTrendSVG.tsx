import React, { useState } from 'react';

interface TrendDataPoint {
  time: string;
  critical: number;
  predicted: number;
  safe: number;
}

interface AreaTrendSVGProps {
  data: TrendDataPoint[];
  height?: number;
  className?: string;
}

export const AreaTrendSVG: React.FC<AreaTrendSVGProps> = ({
  data,
  height = 200,
  className = ''
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const width = 800;
  const padding = { top: 20, right: 20, bottom: 30, left: 35 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const maxVal = Math.max(
    ...data.map(d => Math.max(d.critical, d.predicted, d.safe)),
    10
  );

  const getX = (idx: number) => padding.left + (idx / (data.length - 1)) * chartW;
  const getY = (val: number) => padding.top + chartH - (val / maxVal) * chartH;

  // Build area path string
  const buildAreaPath = (key: 'critical' | 'predicted' | 'safe') => {
    if (data.length === 0) return '';
    const points = data.map((d, i) => `${getX(i)},${getY(d[key])}`);
    const firstX = getX(0);
    const lastX = getX(data.length - 1);
    const baseY = padding.top + chartH;
    return `M ${firstX},${baseY} L ${points.join(' L ')} L ${lastX},${baseY} Z`;
  };

  const buildLinePath = (key: 'critical' | 'predicted' | 'safe') => {
    if (data.length === 0) return '';
    return data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d[key])}`).join(' ');
  };

  return (
    <div className={`relative w-full select-none ${className}`}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        onMouseLeave={() => setHoverIndex(null)}
      >
        <defs>
          <linearGradient id="gradCrit" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#E5484D" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#E5484D" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="gradPred" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#E8A33D" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#E8A33D" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="gradSafe" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3DBE7A" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#3DBE7A" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Horizontal Gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
          const y = padding.top + chartH * (1 - pct);
          const labelVal = Math.round(maxVal * pct);
          return (
            <g key={i}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#191F26"
                strokeWidth="1"
              />
              <text
                x={padding.left - 8}
                y={y + 3}
                textAnchor="end"
                fill="#566270"
                fontSize="9"
                fontFamily="IBM Plex Mono"
              >
                {labelVal}
              </text>
            </g>
          );
        })}

        {/* Area Fills */}
        <path d={buildAreaPath('safe')} fill="url(#gradSafe)" />
        <path d={buildAreaPath('predicted')} fill="url(#gradPred)" />
        <path d={buildAreaPath('critical')} fill="url(#gradCrit)" />

        {/* Contour Lines */}
        <path d={buildLinePath('safe')} fill="none" stroke="#3DBE7A" strokeWidth="1.5" />
        <path d={buildLinePath('predicted')} fill="none" stroke="#E8A33D" strokeWidth="1.5" />
        <path d={buildLinePath('critical')} fill="none" stroke="#E5484D" strokeWidth="2" />

        {/* Time X-Axis Ticks */}
        {data.map((d, i) => {
          const x = getX(i);
          return (
            <g key={i}>
              <line
                x1={x}
                y1={padding.top + chartH}
                x2={x}
                y2={padding.top + chartH + 4}
                stroke="#232A32"
                strokeWidth="1"
              />
              <text
                x={x}
                y={padding.top + chartH + 16}
                textAnchor="middle"
                fill="#8B96A3"
                fontSize="9"
                fontFamily="IBM Plex Mono"
              >
                {d.time}
              </text>
            </g>
          );
        })}

        {/* Interactive Hover Vertical Crosshair */}
        {data.map((d, i) => {
          const x = getX(i);
          return (
            <rect
              key={i}
              x={x - chartW / (data.length * 2)}
              y={padding.top}
              width={chartW / data.length}
              height={chartH}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
              className="cursor-crosshair"
            />
          );
        })}

        {hoverIndex !== null && (
          <g>
            <line
              x1={getX(hoverIndex)}
              y1={padding.top}
              x2={getX(hoverIndex)}
              y2={padding.top + chartH}
              stroke="#E8A33D"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
            {/* Tooltip circles */}
            <circle cx={getX(hoverIndex)} cy={getY(data[hoverIndex].critical)} r="4" fill="#E5484D" stroke="#0A0D10" strokeWidth="1.5" />
            <circle cx={getX(hoverIndex)} cy={getY(data[hoverIndex].predicted)} r="3.5" fill="#E8A33D" stroke="#0A0D10" strokeWidth="1.5" />
            <circle cx={getX(hoverIndex)} cy={getY(data[hoverIndex].safe)} r="3.5" fill="#3DBE7A" stroke="#0A0D10" strokeWidth="1.5" />
          </g>
        )}
      </svg>

      {/* Floating Hover Card */}
      {hoverIndex !== null && (
        <div
          className="absolute top-2 z-10 p-2 rounded bg-[#12161B] border border-[#232A32] shadow-xl text-[10px] font-mono pointer-events-none space-y-1"
          style={{ left: `${(hoverIndex / (data.length - 1)) * 80 + 5}%` }}
        >
          <div className="font-bold text-[#E7EBEF] border-b border-[#232A32] pb-0.5">{data[hoverIndex].time} Telemetry</div>
          <div className="text-[#E5484D]">Critical Threats: {data[hoverIndex].critical}</div>
          <div className="text-[#E8A33D]">Predicted Phish: {data[hoverIndex].predicted}</div>
          <div className="text-[#3DBE7A]">Legitimate: {data[hoverIndex].safe}</div>
        </div>
      )}
    </div>
  );
};
