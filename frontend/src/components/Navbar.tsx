import React, { useState, useEffect, useRef } from 'react';
import { Search, Upload, LogOut, Clock, RadioTower, ChevronRight } from 'lucide-react';
import { UserProfile } from '../types';

interface NavbarProps {
  user: UserProfile;
  activeTab: string;
  selectedCaseId?: string | null;
  onOpenIngest: () => void;
  onLogout: () => void;
  onOpenCommandPalette: () => void;
  onNavigateBreadcrumb?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  activeTab,
  selectedCaseId,
  onOpenIngest,
  onLogout,
  onOpenCommandPalette,
  onNavigateBreadcrumb
}) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toUTCString().slice(17, 25) + ' UTC');
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const getBreadcrumbs = () => {
    const crumbs = [{ label: 'TraceX', tab: 'dashboard' }];
    if (activeTab === 'dashboard') {
      crumbs.push({ label: 'Security Overview', tab: 'dashboard' });
    } else if (activeTab === 'inbox') {
      crumbs.push({ label: 'Email Analysis Desk', tab: 'inbox' });
    } else if (activeTab === 'investigation') {
      crumbs.push({ label: 'Investigations', tab: 'inbox' });
      crumbs.push({ label: selectedCaseId ? `CASE-${selectedCaseId.slice(0, 8).toUpperCase()}` : 'Case Investigation', tab: 'investigation' });
    } else if (activeTab === 'cases') {
      crumbs.push({ label: 'Incident & Case Desk', tab: 'cases' });
    } else if (activeTab === 'campaigns') {
      crumbs.push({ label: 'Threat Campaigns', tab: 'campaigns' });
    } else if (activeTab === 'map') {
      crumbs.push({ label: 'Observable Infrastructure', tab: 'map' });
    } else if (activeTab === 'reports') {
      crumbs.push({ label: 'Forensic Dossiers & Reports', tab: 'reports' });
    } else if (activeTab === 'settings') {
      crumbs.push({ label: 'Platform Governance', tab: 'settings' });
    }
    return crumbs;
  };

  return (
    <header className="h-14 bg-[#0A0D10] border-b border-[#232A32] px-5 flex items-center justify-between z-20 select-none">
      {/* Left: Breadcrumbs & Command Palette Quick Search */}
      <div className="flex items-center gap-4 flex-1 max-w-2xl min-w-0">
        {/* Breadcrumb Path */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-[#8B96A3] truncate">
          {getBreadcrumbs().map((crumb, idx, arr) => (
            <React.Fragment key={idx}>
              <button
                onClick={() => onNavigateBreadcrumb?.(crumb.tab)}
                className={`hover:text-[#E8A33D] transition-colors truncate ${
                  idx === arr.length - 1 ? 'text-[#E7EBEF] font-bold' : 'text-[#8B96A3]'
                }`}
              >
                {crumb.label}
              </button>
              {idx < arr.length - 1 && <ChevronRight className="w-3 h-3 text-[#566270] flex-shrink-0" />}
            </React.Fragment>
          ))}
        </div>

        {/* Global Search Bar (Trigger for Command Palette) */}
        <div
          onClick={onOpenCommandPalette}
          className="relative w-full max-w-sm flex items-center bg-[#12161B] border border-[#232A32] hover:border-[#3A4551] rounded px-3 py-1.5 cursor-pointer text-xs font-mono text-[#566270] transition-colors"
        >
          <Search className="w-3.5 h-3.5 text-[#566270] mr-2" />
          <span className="truncate">Search IP, domain, email, hash, case...</span>
          <kbd className="ml-auto text-[9px] px-1 py-0.2 bg-[#191F26] border border-[#232A32] text-[#8B96A3] rounded">
            Ctrl + K
          </kbd>
        </div>
      </div>

      {/* Right: Operational Status, Ingestion CTA, User Profile */}
      <div className="flex items-center gap-3">
        <div className="hidden lg:flex items-center gap-1.5 font-mono text-[11px] text-[#2DD4BF] bg-[#2DD4BF10] px-2.5 py-1 rounded border border-[#2DD4BF30]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" />
          <span>Operational</span>
        </div>

        <div className="hidden md:flex items-center gap-1.5 font-mono text-[11px] text-[#8B96A3] bg-[#12161B] px-2.5 py-1 rounded border border-[#232A32]">
          <Clock className="w-3 h-3 text-[#E8A33D]" />
          <span>{time}</span>
        </div>

        <button
          onClick={onOpenIngest}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] text-xs font-mono font-bold shadow-sm transition-all"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>+ Ingest .EML</span>
        </button>

        <div className="flex items-center gap-2 pl-3 border-l border-[#232A32]">
          <div className="w-7 h-7 rounded bg-[#12161B] border border-[#3A4551] flex items-center justify-center text-[#E8A33D] font-mono text-[11px] font-bold">
            {(user.username || 'AN').slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden xl:block text-left font-mono">
            <div className="text-[11px] font-semibold text-[#E7EBEF] leading-none">{user.full_name || user.username}</div>
            <div className="text-[9px] text-[#E8A33D] uppercase tracking-wider mt-0.5">{user.role}</div>
          </div>
          <button
            onClick={onLogout}
            title="Sign out of TraceX"
            className="p-1.5 rounded text-[#8B96A3] hover:text-[#E5484D] hover:bg-[#191F26] border border-transparent hover:border-[#232A32] transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
