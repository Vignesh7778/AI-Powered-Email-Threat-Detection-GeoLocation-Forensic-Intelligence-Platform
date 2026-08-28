import React, { useState, useEffect } from 'react';

interface ScoreGaugeProps {
  score: number; // 0 - 100
  riskLevel?: string;
  showBreakdown?: boolean;
  breakdown?: {
    auth: number;
    domain: number;
    content: number;
    infra: number;
    links: number;
  };
  onWhyClick?: () => void;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  riskLevel = 'medium',
  showBreakdown = true,
  breakdown,
  onWhyClick
}) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(Math.min(100, Math.max(0, score)));
    }, 50);
    return () => clearTimeout(timer);
  }, [score]);

  const normalized = (animatedScore / 100).toFixed(2);
  const strokeColor = score >= 75 ? '#E5484D' : score >= 50 ? '#E8A33D' : score >= 25 ? '#E8A33D' : '#3DBE7A';

  // Arc calculation for SVG circular gauge
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * (circumference * 0.75);

  const defaultBreakdown = breakdown || {
    auth: 15,
    domain: 25,
    content: 30,
    infra: 15,
    links: 15
  };

  return (
    <div className="w-full space-y-4 font-mono select-none">
      {/* Top Section: Arc Gauge + Numerical Verdict */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
          <svg className="w-full h-full transform -rotate-135" viewBox="0 0 120 120">
            {/* Background Arc */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="transparent"
              stroke="#232A32"
              strokeWidth="8"
              strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
              strokeLinecap="round"
            />
            {/* Value Arc */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="transparent"
              stroke={strokeColor}
              strokeWidth="8"
              strokeDasharray={`${circumference * 0.75} ${circumference * 0.25}`}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 420ms cubic-bezier(0.16, 1, 0.3, 1)' }}
            />
          </svg>

          {/* Center Numerical Score */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-xl font-bold font-mono tracking-tight text-[#E7EBEF]">
              {normalized}
            </span>
            <span className="text-[9px] uppercase font-bold text-[#8B96A3] mt-0.5">
              Score
            </span>
          </div>
        </div>

        {/* Level & Action */}
        <div className="space-y-2 flex-1">
          <div className="text-[10px] uppercase tracking-wider text-[#8B96A3]">Composite Risk Verdict</div>
          <div className="text-base font-bold font-sans tracking-tight uppercase" style={{ color: strokeColor }}>
            {riskLevel} Threat Level
          </div>
          <p className="text-[11px] text-[#8B96A3] font-sans">
            Calibrated against multi-source evidence weights.
          </p>

          {onWhyClick && (
            <button
              onClick={onWhyClick}
              className="text-[11px] text-[#E8A33D] hover:underline underline-offset-2 flex items-center gap-1 font-semibold"
            >
              <span>Inspect Factor Contributions →</span>
            </button>
          )}
        </div>
      </div>

      {/* Factor-Weight Stacked Bar with Trust-Tier Color Coding */}
      {showBreakdown && (
        <div className="pt-3 border-t border-[#232A32] space-y-2">
          <div className="flex items-center justify-between text-[10px] uppercase text-[#8B96A3]">
            <span>Contributing Factor Weights:</span>
            <span>100% Total</span>
          </div>

          <div className="h-2 w-full rounded bg-[#232A32] overflow-hidden flex">
            <div style={{ width: `${defaultBreakdown.auth}%`, backgroundColor: '#2DD4BF' }} title="Authentication (Observed): 15%" />
            <div style={{ width: `${defaultBreakdown.domain}%`, backgroundColor: '#2DD4BF' }} title="Domain Intel (Observed): 25%" />
            <div style={{ width: `${defaultBreakdown.content}%`, backgroundColor: '#E8A33D' }} title="NLP Urgency (Predicted): 30%" />
            <div style={{ width: `${defaultBreakdown.infra}%`, backgroundColor: '#2DD4BF' }} title="Infrastructure (Observed): 15%" />
            <div style={{ width: `${defaultBreakdown.links}%`, backgroundColor: '#8B8FE8' }} title="Links / Inference (Inferred): 15%" />
          </div>

          <div className="flex flex-wrap items-center gap-3 text-[10px] text-[#8B96A3] pt-1">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#2DD4BF]" /> Auth / DNS (Observed)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#E8A33D]" /> NLP Model (Predicted)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#8B8FE8]" /> Groq AI (Inferred)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
