import React, { useState } from 'react';
import { X, Copy, Check, ExternalLink, ShieldAlert, Globe, Server, Link2, Hash, FileText } from 'lucide-react';
import { ThreatBadge } from './ThreatBadge';

export interface DetailDrawerData {
  type: 'ip' | 'domain' | 'url' | 'hash' | 'evidence' | 'node';
  title: string;
  subtitle?: string;
  provenance: 'observed' | 'prediction' | 'inference' | 'unknown';
  severity?: 'critical' | 'high' | 'medium' | 'low' | 'safe';
  fields: { label: string; value: string; isMono?: boolean; isCopyable?: boolean }[];
  evidenceRef?: string;
  notes?: string;
}

interface DetailDrawerProps {
  data: DetailDrawerData | null;
  onClose: () => void;
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({ data, onClose }) => {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!data) return null;

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const getIcon = () => {
    switch (data.type) {
      case 'ip': return <Server className="w-4 h-4 text-[#E8A33D]" />;
      case 'domain': return <Globe className="w-4 h-4 text-[#2DD4BF]" />;
      case 'url': return <Link2 className="w-4 h-4 text-[#8B8FE8]" />;
      case 'hash': return <Hash className="w-4 h-4 text-[#E8A33D]" />;
      default: return <FileText className="w-4 h-4 text-[#E7EBEF]" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity animate-in fade-in"
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div className="relative w-full max-w-md h-full bg-[#12161B] border-l border-[#232A32] shadow-2xl flex flex-col justify-between font-mono text-xs select-text z-10 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-[#232A32] flex items-center justify-between bg-[#0A0D10]/80">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-2 rounded bg-[#191F26] border border-[#232A32] flex-shrink-0">
              {getIcon()}
            </div>
            <div className="min-w-0">
              <div className="font-bold text-[#E7EBEF] text-xs font-sans uppercase tracking-wider flex items-center gap-2">
                <span>{data.type} Detail</span>
                <ThreatBadge type="trust" value={data.provenance} size="xs" />
              </div>
              <div className="text-[11px] text-[#8B96A3] truncate font-mono">{data.title}</div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded text-[#8B96A3] hover:text-white hover:bg-[#191F26] transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center flex-shrink-0"
            title="Close Drawer (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-4 sm:p-5 space-y-4 flex-1 overflow-y-auto">
          {data.severity && (
            <div className="p-3 rounded bg-[#0A0D10] border border-[#232A32] flex items-center justify-between">
              <span className="text-[10px] uppercase text-[#8B96A3]">Threat Assessment:</span>
              <ThreatBadge type="risk" value={data.severity} size="sm" />
            </div>
          )}

          {/* Technical Fields */}
          <div className="space-y-2">
            <div className="text-[10px] uppercase font-bold text-[#8B96A3] border-b border-[#232A32] pb-1">
              Authoritative Forensic Properties
            </div>
            <div className="space-y-1.5">
              {data.fields.map((f, i) => (
                <div key={i} className="p-2.5 rounded bg-[#0A0D10] border border-[#232A32] flex items-start justify-between gap-3">
                  <div className="space-y-0.5 flex-1 min-w-0">
                    <div className="text-[10px] text-[#8B96A3] uppercase">{f.label}</div>
                    <div className={`text-[11px] text-[#E7EBEF] break-all ${f.isMono !== false ? 'font-mono' : 'font-sans'}`}>
                      {f.value || 'UNAVAILABLE'}
                    </div>
                  </div>
                  {f.isCopyable && (
                    <button
                      onClick={() => handleCopy(f.value, f.label)}
                      className="p-1.5 text-[#8B96A3] hover:text-[#E8A33D] transition-colors flex-shrink-0 min-h-[30px] min-w-[30px] flex items-center justify-center"
                      title={`Copy ${f.label}`}
                    >
                      {copiedKey === f.label ? <Check className="w-3.5 h-3.5 text-[#2DD4BF]" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Evidence Citations */}
          {data.evidenceRef && (
            <div className="p-3 rounded bg-[#0A0D10] border border-[#232A32] space-y-1">
              <div className="text-[10px] uppercase text-[#2DD4BF] font-bold">Evidence Grounding Reference:</div>
              <p className="text-[11px] text-[#E7EBEF] font-sans break-all">{data.evidenceRef}</p>
            </div>
          )}

          {/* Notes */}
          {data.notes && (
            <div className="p-3 rounded bg-[#0A0D10] border border-[#232A32] space-y-1">
              <div className="text-[10px] uppercase text-[#8B96A3] font-bold">Forensic Analyst Note:</div>
              <p className="text-[11px] text-[#8B96A3] font-sans leading-relaxed">{data.notes}</p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#232A32] bg-[#0A0D10] flex items-center justify-between gap-3">
          <button
            onClick={() => handleCopy(data.title, 'primary')}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded bg-[#191F26] border border-[#232A32] text-[#E7EBEF] hover:text-white font-semibold transition-colors min-h-[38px]"
          >
            {copiedKey === 'primary' ? <Check className="w-3.5 h-3.5 text-[#2DD4BF]" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedKey === 'primary' ? 'Copied' : `Copy ${data.type.toUpperCase()}`}</span>
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] font-bold transition-all min-h-[38px]"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
