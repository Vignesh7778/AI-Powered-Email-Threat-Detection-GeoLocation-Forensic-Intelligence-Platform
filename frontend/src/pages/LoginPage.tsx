import React, { useState } from 'react';
import {
  ShieldAlert, Globe, FileSearch, Workflow, Key, User,
  ArrowRight, CheckCircle2, ShieldCheck, Lock, RadioTower
} from 'lucide-react';
import { api } from '../api/client';
import { UserProfile } from '../types';

interface LoginPageProps {
  onLoginSuccess: (user: UserProfile) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('analyst@org.gov');
  const [password, setPassword] = useState('Analyst@2026!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.login(username, password);
      onLoginSuccess(response.user);
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify analyst credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const response = await api.login('analyst@org.gov', 'Analyst@2026!');
      onLoginSuccess(response.user);
    } catch (err: any) {
      setError(err?.message || 'Failed to authenticate.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0D10] text-[#E7EBEF] flex flex-col justify-between selection:bg-[#E8A33D]/20 selection:text-[#E8A33D]">
      {/* Top Bar */}
      <header className="h-16 px-4 sm:px-8 flex items-center justify-between border-b border-[#232A32] bg-[#0A0D10]/80 backdrop-blur-xs z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[#12161B] border border-[#E8A33D]/60 flex items-center justify-center text-[#E8A33D] font-mono font-black text-sm shadow-[0_0_12px_rgba(232,163,61,0.2)]">
            TX
          </div>
          <div>
            <div className="font-bold text-sm text-[#E7EBEF] tracking-tight font-sans flex items-center gap-1.5">
              <span>TraceX</span>
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-[#E8A33D15] text-[#E8A33D] border border-[#E8A33D30]">
                CORE
              </span>
            </div>
            <div className="text-[10px] text-[#8B96A3] font-mono leading-none">Forensic Intelligence</div>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="hidden sm:flex items-center gap-1.5 text-[#2DD4BF] bg-[#2DD4BF10] px-2.5 py-1 rounded border border-[#2DD4BF30]">
            <RadioTower className="w-3.5 h-3.5 animate-pulse" />
            <span>Forensic Node: AICTE-26106</span>
          </div>
          <span className="px-2.5 py-1 rounded bg-[#12161B] border border-[#232A32] text-[#8B96A3] text-[11px]">
            v2.4 Enterprise
          </span>
        </div>
      </header>

      {/* Main Split Body */}
      <div className="flex-1 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 p-4 sm:p-8 lg:p-12 items-center relative">
        {/* Subtle Background Equirectangular Topology Pattern */}
        <div className="absolute inset-0 pointer-events-none opacity-5 overflow-hidden flex items-center justify-center">
          <svg viewBox="0 0 1000 500" className="w-full h-full">
            <pattern id="dotGrid" width="30" height="30" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill="#E8A33D" />
            </pattern>
            <rect width="1000" height="500" fill="url(#dotGrid)" />
            <path
              d="M 150 120 L 280 80 L 340 140 L 260 250 Z M 450 100 L 650 70 L 820 90 L 710 240 Z M 470 200 L 570 260 L 540 360 Z M 740 320 L 840 370 Z"
              fill="none"
              stroke="#2DD4BF"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          </svg>
        </div>

        {/* LEFT COLUMN: Branding, Heading, 4 Capabilities */}
        <div className="lg:col-span-7 space-y-6 sm:space-y-8 z-10">
          <div className="space-y-3 sm:space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#12161B] border border-[#232A32] font-mono text-[11px] sm:text-xs text-[#E8A33D]">
              <span className="w-2 h-2 rounded-full bg-[#E8A33D] animate-pulse" />
              <span>Court-Admissible Email Forensic Workstation</span>
            </div>

            <h1 className="text-2xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#E7EBEF] font-sans leading-tight">
              AI-Powered <br />
              <span className="text-[#E8A33D]">Email Threat Detection</span>,<br />
              GeoLocation & Forensic Intelligence
            </h1>

            <p className="text-xs sm:text-sm text-[#8B96A3] font-sans max-w-xl leading-relaxed">
              TraceX empowers analysts to detect advanced email threats, trace malicious infrastructure, uncover origins, and generate evidence-backed intelligence with confidence.
            </p>
          </div>

          {/* 4 Key Forensic Capability Items */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 max-w-xl font-mono text-xs">
            <div className="p-3 sm:p-3.5 rounded bg-[#12161B] border border-[#232A32] space-y-1">
              <div className="flex items-center gap-2 text-[#E8A33D] font-bold">
                <ShieldAlert className="w-4 h-4" />
                <span>Threat Detection</span>
              </div>
              <div className="text-[11px] text-[#8B96A3] font-sans">AI & ML-Powered BEC and Phishing Detection</div>
            </div>

            <div className="p-3 sm:p-3.5 rounded bg-[#12161B] border border-[#232A32] space-y-1">
              <div className="flex items-center gap-2 text-[#2DD4BF] font-bold">
                <Globe className="w-4 h-4" />
                <span>Geo-Intelligence</span>
              </div>
              <div className="text-[11px] text-[#8B96A3] font-sans">Observable IP & Autonomous System Mapping</div>
            </div>

            <div className="p-3 sm:p-3.5 rounded bg-[#12161B] border border-[#232A32] space-y-1">
              <div className="flex items-center gap-2 text-[#8B8FE8] font-bold">
                <FileSearch className="w-4 h-4" />
                <span>Forensic Analysis</span>
              </div>
              <div className="text-[11px] text-[#8B96A3] font-sans">Cryptographic Evidence & Campaign Attribution</div>
            </div>

            <div className="p-3 sm:p-3.5 rounded bg-[#12161B] border border-[#232A32] space-y-1">
              <div className="flex items-center gap-2 text-[#E8A33D] font-bold">
                <Workflow className="w-4 h-4" />
                <span>Investigation</span>
              </div>
              <div className="text-[11px] text-[#8B96A3] font-sans">End-to-End Case Management & Sealed Reports</div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Authentication Card */}
        <div className="lg:col-span-5 z-10">
          <div className="bg-[#12161B] p-5 sm:p-8 rounded-lg border border-[#232A32] shadow-2xl space-y-5 sm:space-y-6">
            <div className="space-y-1">
              <h2 className="text-base sm:text-lg font-bold text-[#E7EBEF] font-sans tracking-tight">Welcome Back</h2>
              <p className="text-xs text-[#8B96A3] font-mono">Sign in to access your TraceX Workbench</p>
            </div>

            {error && (
              <div className="p-3 rounded bg-[#E5484D15] border border-[#E5484D40] flex items-start gap-2.5 text-xs text-[#E5484D] font-mono">
                <ShieldAlert className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 font-mono text-xs">
              <div className="space-y-1.5">
                <label className="block text-[11px] uppercase tracking-wider text-[#8B96A3]">
                  Analyst Identity / Email
                </label>
                <div className="relative">
                  <User className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="analyst@org.gov"
                    className="w-full pl-9 pr-3 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D] transition-colors min-h-[38px]"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-[11px] uppercase tracking-wider text-[#8B96A3]">
                  Access Token / Passphrase
                </label>
                <div className="relative">
                  <Key className="w-3.5 h-3.5 text-[#566270] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 bg-[#0A0D10] border border-[#232A32] rounded text-[#E7EBEF] placeholder-[#566270] focus:outline-hidden focus:border-[#E8A33D] transition-colors min-h-[38px]"
                  />
                </div>
              </div>

              <div className="pt-1 space-y-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] text-xs font-mono font-bold shadow-md transition-all disabled:opacity-50 min-h-[40px]"
                >
                  <span>{loading ? 'Authenticating...' : 'Authenticate & Access Workbench'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={handleDemoLogin}
                  disabled={loading}
                  className="w-full py-2 px-4 rounded bg-[#0A0D10] hover:bg-[#191F26] border border-[#232A32] text-[#8B96A3] hover:text-[#E7EBEF] text-xs font-mono transition-colors min-h-[38px]"
                >
                  Access Read-Only Dashboard
                </button>
              </div>
            </form>

            <div className="pt-4 border-t border-[#232A32] text-[10px] font-mono text-[#566270] flex items-center justify-between">
              <span className="flex items-center gap-1">
                <Lock className="w-3 h-3 text-[#2DD4BF]" /> Secure • Encrypted • Monitored
              </span>
              <span className="text-[#2DD4BF]">● Ready</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="px-4 sm:px-8 py-3 sm:py-4 border-t border-[#232A32] text-[11px] font-mono text-[#566270] flex flex-wrap items-center justify-between gap-3 bg-[#0A0D10]">
        <div>© 2026 TraceX Forensic Intelligence. All rights reserved.</div>
        <div className="flex items-center gap-4">
          <span className="hover:text-[#8B96A3] cursor-pointer">Help</span>
          <span>•</span>
          <span className="hover:text-[#8B96A3] cursor-pointer">Privacy</span>
          <span>•</span>
          <span className="hover:text-[#8B96A3] cursor-pointer">Terms</span>
        </div>
      </footer>
    </div>
  );
};
