import React, { useState, useEffect } from 'react';
import { Gauge, Inbox, AlertTriangle, FolderKanban, Menu } from 'lucide-react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { IngestModal } from './components/IngestModal';
import { CommandPalette } from './components/CommandPalette';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ThreatInboxPage } from './pages/ThreatInboxPage';
import { InvestigationPage } from './pages/InvestigationPage';
import { CasesPage } from './pages/CasesPage';
import { AlertsPage } from './pages/AlertsPage';
import { MapPage } from './pages/MapPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { UserProfile } from './types';
import { api } from './api/client';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserProfile | null>(() => api.getCurrentUser());
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<string | null>(null);
  const [globalSearch, setGlobalSearch] = useState<string>('');
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    if (user) {
      api.listAlerts(true)
        .then((a) => setAlertCount(a.length))
        .catch(() => setAlertCount(0));
    }
  }, [user]);

  // Global Keyboard Shortcuts (/ and Ctrl+K / Cmd+K)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.key === 'k' && (e.ctrlKey || e.metaKey)) || (e.key === '/' && !(document.activeElement instanceof HTMLInputElement) && !(document.activeElement instanceof HTMLTextAreaElement))) {
        e.preventDefault();
        setIsCommandPaletteOpen(true);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  if (!user) {
    return <LoginPage onLoginSuccess={(u) => setUser(u)} />;
  }

  const handleSelectSubmission = (submissionId: string) => {
    setSelectedSubmissionId(submissionId);
    setActiveTab('investigation');
    setIsMobileMenuOpen(false);
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
  };

  const primaryNavItems = [
    { id: 'dashboard', label: 'Overview', icon: Gauge },
    { id: 'inbox', label: 'Inbox', icon: Inbox },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle, badge: alertCount > 0 ? alertCount : undefined },
    { id: 'cases', label: 'Cases', icon: FolderKanban },
  ];

  return (
    <div className="flex fixed inset-0 bg-[#0A0D10] text-[#E7EBEF] overflow-hidden font-sans selection:bg-[#E8A33D]/20 selection:text-[#E8A33D]">
      {/* Sidebar (Persistent on Desktop, Slide-over on Mobile/Tablet) */}
      <Sidebar
        activeTab={activeTab}
        onChangeTab={(t) => {
          setActiveTab(t);
          setIsMobileMenuOpen(false);
        }}
        alertCount={alertCount}
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <Navbar
          user={user}
          activeTab={activeTab}
          selectedCaseId={selectedSubmissionId}
          onOpenIngest={() => setIsIngestOpen(true)}
          onLogout={handleLogout}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onNavigateBreadcrumb={(tab) => {
            setActiveTab(tab);
            setIsMobileMenuOpen(false);
          }}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />

        <main className="flex-1 overflow-y-auto bg-[#0A0D10] pb-16 lg:pb-0">
          {{
            dashboard: <DashboardPage onSelectSubmission={handleSelectSubmission} onViewAllInbox={() => setActiveTab('inbox')} />,
            inbox: <ThreatInboxPage onSelectSubmission={handleSelectSubmission} initialSearch={globalSearch} />,
            investigation: selectedSubmissionId ? (
              <InvestigationPage
                submissionId={selectedSubmissionId}
                onBack={() => setActiveTab('inbox')}
              />
            ) : (
              <ThreatInboxPage onSelectSubmission={handleSelectSubmission} initialSearch={globalSearch} />
            ),
            cases: <CasesPage onSelectSubmission={handleSelectSubmission} />,
            alerts: <AlertsPage onSelectSubmission={handleSelectSubmission} />,
            map: <MapPage onSelectSubmission={handleSelectSubmission} />,
            campaigns: <CampaignsPage onSelectSubmission={handleSelectSubmission} />,
            reports: <ReportsPage onSelectSubmission={handleSelectSubmission} />,
            settings: <SettingsPage />,
          }[activeTab] || <DashboardPage onSelectSubmission={handleSelectSubmission} onViewAllInbox={() => setActiveTab('inbox')} />}
        </main>

        {/* Mobile Bottom Navigation Bar (Visible only on <lg viewports) */}
        <nav className="lg:hidden absolute bottom-0 inset-x-0 h-14 bg-[#0D1117] border-t border-[#232A32] flex items-center justify-around px-2 z-30 select-none backdrop-blur-md bg-opacity-95">
          {primaryNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex flex-col items-center justify-center flex-1 py-1 relative min-h-[44px] transition-colors ${
                  isActive ? 'text-[#E8A33D]' : 'text-[#8B96A3] hover:text-[#E7EBEF]'
                }`}
              >
                <div className="relative">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#E8A33D]' : 'text-[#8B96A3]'}`} />
                  {item.badge !== undefined && (
                    <span className="absolute -top-1.5 -right-2 px-1 py-0.2 rounded-full text-[8px] font-mono font-bold bg-[#E5484D] text-white">
                      {item.badge}
                    </span>
                  )}
                </div>
                <span className="text-[10px] font-mono mt-0.5 font-medium">{item.label}</span>
                {isActive && <span className="absolute bottom-0 w-8 h-0.5 rounded-t bg-[#E8A33D]" />}
              </button>
            );
          })}

          {/* More Sections Trigger Button */}
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className={`flex flex-col items-center justify-center flex-1 py-1 relative min-h-[44px] transition-colors ${
              ['map', 'campaigns', 'reports', 'settings'].includes(activeTab)
                ? 'text-[#E8A33D]'
                : 'text-[#8B96A3] hover:text-[#E7EBEF]'
            }`}
          >
            <Menu className="w-4 h-4" />
            <span className="text-[10px] font-mono mt-0.5 font-medium">More</span>
            {['map', 'campaigns', 'reports', 'settings'].includes(activeTab) && (
              <span className="absolute bottom-0 w-8 h-0.5 rounded-t bg-[#E8A33D]" />
            )}
          </button>
        </nav>
      </div>

      <IngestModal
        isOpen={isIngestOpen}
        onClose={() => setIsIngestOpen(false)}
        onIngestSuccess={(submissionId) => {
          setIsIngestOpen(false);
          handleSelectSubmission(submissionId);
        }}
      />

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectSubmission={handleSelectSubmission}
      />
    </div>
  );
};
