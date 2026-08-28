import React, { useState, useEffect } from 'react';
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
  };

  const handleLogout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <div className="flex fixed inset-0 bg-[#0A0D10] text-[#E7EBEF] overflow-hidden font-sans selection:bg-[#E8A33D]/20 selection:text-[#E8A33D]">
      <Sidebar
        activeTab={activeTab}
        onChangeTab={(t) => {
          setActiveTab(t);
        }}
        alertCount={alertCount}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar
          user={user}
          activeTab={activeTab}
          selectedCaseId={selectedSubmissionId}
          onOpenIngest={() => setIsIngestOpen(true)}
          onLogout={handleLogout}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onNavigateBreadcrumb={(tab) => setActiveTab(tab)}
        />

        <main className="flex-1 overflow-y-auto bg-[#0A0D10]">
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
