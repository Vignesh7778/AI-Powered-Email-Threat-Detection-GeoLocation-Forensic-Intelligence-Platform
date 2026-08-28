import React from 'react';
import {
  Gauge, Inbox, AlertTriangle, FolderKanban,
  MapPin, Share2, FileDown, Settings, RadioTower
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onChangeTab: (tab: string) => void;
  alertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onChangeTab, alertCount }) => {
  const sections = [
    {
      group: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Threat Overview', icon: Gauge },
      ]
    },
    {
      group: 'INVESTIGATIONS',
      items: [
        { id: 'inbox', label: 'Email Analysis', icon: Inbox },
        { id: 'cases', label: 'Incidents & Cases', icon: FolderKanban },
        { id: 'campaigns', label: 'Threat Campaigns', icon: Share2 },
      ]
    },
    {
      group: 'INTELLIGENCE',
      items: [
        { id: 'alerts', label: 'Threat Alerts', icon: AlertTriangle, badge: alertCount > 0 ? alertCount : undefined },
        { id: 'map', label: 'Infrastructure Map', icon: MapPin },
      ]
    },
    {
      group: 'EVIDENCE & REPORTING',
      items: [
        { id: 'reports', label: 'Forensic Reports', icon: FileDown },
      ]
    },
    {
      group: 'SYSTEM',
      items: [
        { id: 'settings', label: 'Platform Config', icon: Settings },
      ]
    }
  ];

  return (
    <aside className="w-60 bg-[#0A0D10] border-r border-[#232A32] flex flex-col justify-between p-3.5 z-30 select-none">
      <div className="space-y-5">
        {/* Brand Header */}
        <div className="flex items-center gap-2.5 px-2 py-1.5 border-b border-[#232A32] pb-3">
          <div className="w-8 h-8 rounded bg-[#12161B] border border-[#E8A33D]/50 flex items-center justify-center text-[#E8A33D] font-mono font-black text-sm tracking-tighter shadow-sm">
            TX
          </div>
          <div>
            <div className="font-bold text-sm text-[#E7EBEF] tracking-tight flex items-center gap-1.5 font-display">
              <span>TraceX</span>
              <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-[#E8A33D15] text-[#E8A33D] border border-[#E8A33D30]">CORE</span>
            </div>
            <div className="text-[10px] text-[#8B96A3] font-mono">Forensic Intelligence</div>
          </div>
        </div>

        {/* Categorized Navigation */}
        <nav className="space-y-4">
          {sections.map((sec) => (
            <div key={sec.group} className="space-y-1">
              <div className="px-2 text-[9px] font-mono uppercase tracking-widest text-[#566270] font-semibold font-sans">
                {sec.group}
              </div>
              <div className="space-y-0.5">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onChangeTab(item.id)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-[#191F26] text-[#E8A33D] font-semibold border-l-2 border-[#E8A33D] shadow-sm'
                          : 'text-[#8B96A3] hover:text-[#E7EBEF] hover:bg-[#12161B]'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#E8A33D]' : 'text-[#8B96A3]'}`} />
                        <span>{item.label}</span>
                      </div>
                      {item.badge !== undefined && (
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-bold bg-[#E5484D15] text-[#E5484D] border border-[#E5484D40]">
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </div>

      {/* System Telemetry Footer */}
      <div className="p-2.5 rounded bg-[#12161B] border border-[#232A32] text-[10px] font-mono text-[#8B96A3] space-y-1">
        <div className="flex items-center justify-between text-[#E7EBEF]">
          <span className="text-[#8B96A3]">Node Ref</span>
          <span className="text-[#E8A33D] font-semibold">PS-26106</span>
        </div>
        <div className="flex items-center justify-between text-[9px] text-[#566270]">
          <span>AICTE Cyber Cell</span>
          <span className="text-[#2DD4BF] flex items-center gap-1">
            <RadioTower className="w-3 h-3 animate-pulse" /> Verified
          </span>
        </div>
      </div>
    </aside>
  );
};


