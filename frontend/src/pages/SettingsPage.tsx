import React, { useState } from 'react';
import { Check, ShieldCheck, Server, Globe, Key, Lock, Cpu, Clock, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [retentionStop, setRetentionStop] = useState(3);
  const [maskingLevel, setMaskingLevel] = useState<'FULL' | 'MASKED' | 'RESTRICTED'>('MASKED');
  const [saved, setSaved] = useState(false);

  const stops = ['7 Days', '30 Days', '90 Days', '180 Days (Standard)', '365 Days (Annual)'];

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-3 sm:p-5 lg:p-6 space-y-4 sm:space-y-6 max-w-[1200px] w-full mx-auto bg-[#0A0D10] text-[#E7EBEF]">
      <div className="flex items-center justify-between pb-3 sm:pb-4 border-b border-[#232A32]">
        <div>
          <h1 className="text-base sm:text-lg font-bold text-[#E7EBEF] tracking-tight font-sans">
            Platform Configuration & Policy
          </h1>
          <p className="text-[11px] sm:text-xs font-mono text-[#8B96A3] mt-0.5">
            Configurable tenant privacy controls, audit retention horizons, and intelligence providers
          </p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4 sm:space-y-6 font-mono text-xs">
        {/* System Provider Health Matrix */}
        <div className="p-4 sm:p-5 rounded-lg bg-[#12161B] border border-[#232A32] space-y-4">
          <div className="text-xs sm:text-sm font-bold text-[#E7EBEF] font-sans border-b border-[#232A32] pb-2">
            1. Intelligence Providers & Engine Status
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3.5 rounded bg-[#0A0D10] border border-[#232A32] flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="font-bold text-[#E7EBEF] flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-[#8B8FE8]" /> Groq AI Reasoning
                </div>
                <div className="text-[10px] text-[#8B96A3]">LPU Inference Engine</div>
              </div>
              <span className="text-[10px] text-[#2DD4BF] font-bold">CONNECTED</span>
            </div>

            <div className="p-3.5 rounded bg-[#0A0D10] border border-[#232A32] flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="font-bold text-[#E7EBEF] flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-[#2DD4BF]" /> GeoIP ASN Engine
                </div>
                <div className="text-[10px] text-[#8B96A3]">MaxMind GeoLite2 / ip-api</div>
              </div>
              <span className="text-[10px] text-[#2DD4BF] font-bold">OPERATIONAL</span>
            </div>

            <div className="p-3.5 rounded bg-[#0A0D10] border border-[#232A32] flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="font-bold text-[#E7EBEF] flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-[#E8A33D]" /> Root Nameservers
                </div>
                <div className="text-[10px] text-[#8B96A3]">DNS TXT / SPF Resolver</div>
              </div>
              <span className="text-[10px] text-[#2DD4BF] font-bold">ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Retention Slider with Named Stops */}
        <div className="p-4 sm:p-5 rounded-lg bg-[#12161B] border border-[#232A32] space-y-4">
          <div className="text-xs sm:text-sm font-bold text-[#E7EBEF] font-sans border-b border-[#232A32] pb-2">
            2. Evidence & Audit Retention Horizon
          </div>
          <div className="space-y-3 max-w-xl">
            <div className="flex justify-between text-xs text-[#E8A33D] font-bold">
              <span>Selected Horizon: {stops[retentionStop]}</span>
            </div>
            <input
              type="range"
              min="0"
              max="4"
              step="1"
              value={retentionStop}
              onChange={(e) => setRetentionStop(parseInt(e.target.value))}
              className="w-full accent-[#E8A33D] bg-[#0A0D10]"
            />
            <div className="flex justify-between text-[10px] text-[#566270]">
              <span>7d</span>
              <span>30d</span>
              <span>90d</span>
              <span>180d</span>
              <span>365d</span>
            </div>
          </div>
        </div>

        {/* Masking Level as 3 Radio Cards */}
        <div className="p-4 sm:p-5 rounded-lg bg-[#12161B] border border-[#232A32] space-y-4">
          <div className="text-xs sm:text-sm font-bold text-[#E7EBEF] font-sans border-b border-[#232A32] pb-2">
            3. PII Privacy Masking Policy
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { id: 'FULL', title: 'FULL DISCLOSURE', desc: 'Raw headers and emails visible to cleared investigators.' },
              { id: 'MASKED', title: 'MASKED (RECOMMENDED)', desc: 'Redacts local parts (e.g. j***@domain.com) in UI.' },
              { id: 'RESTRICTED', title: 'RESTRICTED VAULT', desc: 'Strict cryptographic role-based access for court evidence.' }
            ].map((card) => (
              <div
                key={card.id}
                onClick={() => setMaskingLevel(card.id as any)}
                className={`p-3.5 sm:p-4 rounded border cursor-pointer transition-all space-y-1.5 ${
                  maskingLevel === card.id
                    ? 'bg-[#191F26] border-[#E8A33D]'
                    : 'bg-[#0A0D10] border-[#232A32] hover:border-[#3A4551]'
                }`}
              >
                <div className="font-bold text-[#E7EBEF] text-xs">{card.title}</div>
                <div className="text-[11px] text-[#8B96A3] font-sans">{card.desc}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            className="flex items-center gap-2 px-4 py-2.5 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] text-xs font-mono font-bold transition-all min-h-[40px]"
          >
            {saved ? <Check className="w-4 h-4" /> : null}
            <span>{saved ? 'Policy Saved' : 'Save Governance Policy'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
