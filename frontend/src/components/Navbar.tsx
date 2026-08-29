import React, { useState, useEffect } from 'react';
import { Search, Upload, LogOut, Clock, ChevronRight, Menu } from 'lucide-react';
import { UserProfile } from '../types';

interface NavbarProps {
  user: UserProfile;
  activeTab: string;
  selectedCaseId?: string | null;
  onOpenIngest: () => void;
  onLogout: () => void;
  onOpenCommandPalette: () => void;
  onNavigateBreadcrumb?: (tab: string) => void;
  onToggleMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  activeTab,
  selectedCaseId,
  onOpenIngest,
  onLogout,
  onOpenCommandPalette,
  onNavigateBreadcrumb,
  onToggleMobileMenu
}) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
      const tzAbbr = new Intl.DateTimeFormat([], { timeZoneName: 'short' })
        .formatToParts(now)
        .find(p => p.type === 'timeZoneName')?.value || '';
      setTime(`${timeStr} ${tzAbbr}`.trim());
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
      crumbs.push({ label: 'Email Analysis', tab: 'inbox' });
    } else if (activeTab === 'investigation') {
      crumbs.push({ label: 'Investigations', tab: 'inbox' });
      crumbs.push({ label: selectedCaseId ? `CASE-${selectedCaseId.slice(0, 8).toUpperCase()}` : 'Investigation', tab: 'investigation' });
    } else if (activeTab === 'cases') {
      crumbs.push({ label: 'Incidents & Cases', tab: 'cases' });
    } else if (activeTab === 'campaigns') {
      crumbs.push({ label: 'Threat Campaigns', tab: 'campaigns' });
    } else if (activeTab === 'map') {
      crumbs.push({ label: 'Infrastructure Map', tab: 'map' });
    } else if (activeTab === 'reports') {
      crumbs.push({ label: 'Forensic Reports', tab: 'reports' });
    } else if (activeTab === 'settings') {
      crumbs.push({ label: 'Platform Config', tab: 'settings' });
    }
    return crumbs;
  };

  return (
    <header className="h-14 bg-[#0A0D10] border-b border-[#232A32] px-3 sm:px-5 flex items-center justify-between z-20 select-none flex-shrink-0">
      {/* Left: Mobile Menu Trigger, Mobile Brand, Breadcrumbs & Search */}
      <div className="flex items-center gap-2 sm:gap-3 flex-1 min-w-0 mr-2">
        {/* Mobile Hamburger Trigger */}
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 -ml-1 rounded text-[#8B96A3] hover:text-[#E8A33D] hover:bg-[#12161B] transition-colors focus:outline-hidden min-h-[40px] min-w-[40px] flex items-center justify-center"
          aria-label="Open Navigation Drawer"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Mobile Mini Logo */}
        <div className="lg:hidden flex items-center gap-1.5 flex-shrink-0">
          <div className="w-7 h-7 rounded bg-[#12161B] border border-[#E8A33D]/50 flex items-center justify-center text-[#E8A33D] font-mono font-bold text-xs">
            TX
          </div>
          <span className="font-bold text-sm text-[#E7EBEF] hidden xs:inline tracking-tight">TraceX</span>
        </div>

        {/* Breadcrumb Path (Hidden on small mobile, visible sm+) */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono text-[#8B96A3] truncate">
          {getBreadcrumbs().map((crumb, idx, arr) => (
            <React.Fragment key={idx}>
              <button
                onClick={() => onNavigateBreadcrumb?.(crumb.tab)}
                className={`hover:text-[#E8A33D] transition-colors truncate max-w-[120px] md:max-w-none ${
                  idx === arr.length - 1 ? 'text-[#E7EBEF] font-bold' : 'text-[#8B96A3]'
                }`}
              >
                {crumb.label}
              </button>
              {idx < arr.length - 1 && <ChevronRight className="w-3 h-3 text-[#566270] flex-shrink-0" />}
            </React.Fragment>
          ))}
        </div>

        {/* Global Search (Full Bar on md+, Icon button on mobile) */}
        <div
          onClick={onOpenCommandPalette}
          className="hidden md:flex relative w-full max-w-xs xl:max-w-sm items-center bg-[#12161B] border border-[#232A32] hover:border-[#3A4551] rounded px-3 py-1.5 cursor-pointer text-xs font-mono text-[#566270] transition-colors ml-auto md:ml-2"
        >
          <Search className="w-3.5 h-3.5 text-[#566270] mr-2 flex-shrink-0" />
          <span className="truncate">Search IP, domain, hash, case...</span>
          <kbd className="ml-auto text-[9px] px-1 py-0.2 bg-[#191F26] border border-[#232A32] text-[#8B96A3] rounded hidden lg:inline">
            Ctrl+K
          </kbd>
        </div>

        {/* Mobile Search Icon Trigger */}
        <button
          onClick={onOpenCommandPalette}
          className="md:hidden p-2 rounded text-[#8B96A3] hover:text-[#E8A33D] hover:bg-[#12161B] transition-colors min-h-[40px] min-w-[40px] flex items-center justify-center ml-auto"
          aria-label="Open Command Search"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>

      {/* Right: Operational Status, Ingestion CTA, User Profile */}
      <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
        <div className="hidden xl:flex items-center gap-1.5 font-mono text-[11px] text-[#2DD4BF] bg-[#2DD4BF10] px-2.5 py-1 rounded border border-[#2DD4BF30]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4BF] animate-pulse" />
          <span>Operational</span>
        </div>

        <div className="hidden lg:flex items-center gap-1.5 font-mono text-[11px] text-[#8B96A3] bg-[#12161B] px-2.5 py-1 rounded border border-[#232A32]">
          <Clock className="w-3 h-3 text-[#E8A33D]" />
          <span>{time}</span>
        </div>

        <button
          onClick={onOpenIngest}
          className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded bg-[#E8A33D] hover:bg-[#E8A33D]/90 text-[#0A0D10] text-xs font-mono font-bold shadow-sm transition-all min-h-[36px]"
        >
          <Upload className="w-3.5 h-3.5" />
          <span className="hidden xs:inline">+ Ingest .EML</span>
          <span className="xs:hidden">Ingest</span>
        </button>

        <div className="flex items-center gap-1.5 sm:gap-2 pl-2 sm:pl-3 border-l border-[#232A32]">
          <div className="w-7 h-7 rounded bg-[#12161B] border border-[#3A4551] flex items-center justify-center text-[#E8A33D] font-mono text-[11px] font-bold flex-shrink-0">
            {(user.username || 'AN').slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden 2xl:block text-left font-mono">
            <div className="text-[11px] font-semibold text-[#E7EBEF] leading-none">{user.full_name || user.username}</div>
            <div className="text-[9px] text-[#E8A33D] uppercase tracking-wider mt-0.5">{user.role}</div>
          </div>
          <button
            onClick={onLogout}
            title="Sign out of TraceX"
            className="p-1.5 sm:p-2 rounded text-[#8B96A3] hover:text-[#E5484D] hover:bg-[#191F26] border border-transparent hover:border-[#232A32] transition-colors min-h-[36px] min-w-[36px] flex items-center justify-center"
            aria-label="Sign Out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};
