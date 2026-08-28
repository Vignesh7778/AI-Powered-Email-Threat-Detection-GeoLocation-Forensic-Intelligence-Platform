import React from 'react';

interface ThreatBadgeProps {
  type: 'risk' | 'classification' | 'status' | 'trust';
  value?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
}

export const ThreatBadge: React.FC<ThreatBadgeProps> = ({ type, value, size = 'md' }) => {
  const val = (value || 'unknown').toString().toLowerCase().trim();

  // Trust-Tier Provenance (Truth Label)
  if (type === 'trust') {
    const tierConfig: Record<string, { label: string; dot: string; text: string; bg: string; border: string }> = {
      observed: { label: 'OBSERVED', dot: '#2DD4BF', text: '#2DD4BF', bg: '#2DD4BF10', border: '#2DD4BF30' },
      verified: { label: 'VERIFIED', dot: '#2DD4BF', text: '#2DD4BF', bg: '#2DD4BF10', border: '#2DD4BF30' },
      fact: { label: 'OBSERVED', dot: '#2DD4BF', text: '#2DD4BF', bg: '#2DD4BF10', border: '#2DD4BF30' },
      model_prediction: { label: 'MODEL PREDICTION', dot: '#E8A33D', text: '#E8A33D', bg: '#E8A33D10', border: '#E8A33D30' },
      prediction: { label: 'PREDICTION', dot: '#E8A33D', text: '#E8A33D', bg: '#E8A33D10', border: '#E8A33D30' },
      llm_inference: { label: 'LLM INFERENCE', dot: '#8B8FE8', text: '#8B8FE8', bg: '#8B8FE810', border: '#8B8FE830' },
      inference: { label: 'INFERENCE', dot: '#8B8FE8', text: '#8B8FE8', bg: '#8B8FE810', border: '#8B8FE830' },
      unknown: { label: 'UNKNOWN', dot: '#566270', text: '#8B96A3', bg: '#56627010', border: '#232A32' },
      unavailable: { label: 'UNAVAILABLE', dot: '#566270', text: '#8B96A3', bg: '#56627010', border: '#232A32' }
    };

    const cfg = tierConfig[val] || tierConfig.unknown;

    return (
      <span
        className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-[10px] uppercase font-semibold border select-none"
        style={{ color: cfg.text, backgroundColor: cfg.bg, borderColor: cfg.border }}
      >
        <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: cfg.dot }} />
        <span>{cfg.label}</span>
      </span>
    );
  }

  // Verdict Severity & Threat Classification
  const getStyle = () => {
    if (type === 'risk') {
      switch (val) {
        case 'critical':
          return 'bg-[#E5484D15] text-[#E5484D] border-[#E5484D50]';
        case 'high':
          return 'bg-[#E8A33D15] text-[#E8A33D] border-[#E8A33D50]';
        case 'medium':
          return 'bg-[#E8A33D10] text-[#E8A33D] border-[#E8A33D30]';
        case 'low':
          return 'bg-[#8B96A310] text-[#8B96A3] border-[#232A32]';
        case 'clean':
        case 'safe':
        case 'legitimate':
          return 'bg-[#3DBE7A15] text-[#3DBE7A] border-[#3DBE7A50]';
        default:
          return 'bg-[#12161B] text-[#8B96A3] border-[#232A32]';
      }
    }

    if (type === 'classification') {
      switch (val) {
        case 'phishing':
          return 'bg-[#E5484D15] text-[#E5484D] border-[#E5484D40]';
        case 'bec_fraud':
          return 'bg-[#E8A33D15] text-[#E8A33D] border-[#E8A33D40]';
        case 'impersonation':
          return 'bg-[#E8A33D15] text-[#E8A33D] border-[#E8A33D40]';
        case 'suspicious':
          return 'bg-[#E8A33D10] text-[#E8A33D] border-[#E8A33D30]';
        case 'legitimate':
          return 'bg-[#3DBE7A15] text-[#3DBE7A] border-[#3DBE7A40]';
        default:
          return 'bg-[#12161B] text-[#8B96A3] border-[#232A32]';
      }
    }

    return 'bg-[#12161B] text-[#E7EBEF] border-[#232A32]';
  };

  const sizeClasses = {
    xs: 'text-[9px] px-1.5 py-0.5',
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-semibold',
    lg: 'text-sm px-3.5 py-1.5 font-bold',
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border font-mono uppercase tracking-wider ${getStyle()} ${sizeClasses} select-none`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      <span>{val.replace(/_/g, ' ')}</span>
    </span>
  );
};
