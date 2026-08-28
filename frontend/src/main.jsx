import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const iconPaths = {
  grid: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z',
  inbox: 'M4 5h16v11h-4l-2 3h-4l-2-3H4zM4 12h4l2 3h4l2-3h4',
  case: 'M4 7h16v11H4zM8 7V5h8v2M8 12h8',
  map: 'M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2zM9 3v16M15 5v16',
  report: 'M6 3h9l4 4v14H6zM14 3v5h5M9 12h6M9 16h6',
  rule: 'M4 5h16M7 5v5M4 12h16M15 12v5M4 19h16M10 19v-5',
  audit: 'M5 4h14v16H5zM8 8h8M8 12h8M8 16h5',
  search: 'm20 20-4.4-4.4M17 11a6 6 0 1 1-12 0 6 6 0 0 1 12 0Z',
  bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
  plus: 'M12 5v14M5 12h14',
  arrow: 'M5 12h13M13 6l6 6-6 6',
  chevron: 'm9 18 6-6-6-6',
  filter: 'M4 6h16M7 12h10M10 18h4',
  shield: 'M12 3 4 6v5c0 5 3.4 8.4 8 10 4.6-1.6 8-5 8-10V6zM8 12l2.5 2.5L16 9',
  close: 'M6 6l12 12M18 6 6 18',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  clock: 'M12 6v6l4 2',
  export: 'M12 3v12M8 7l4-4 4 4M5 14v5h14v-5',
  link: 'M10 14a4 4 0 0 0 5.6.1l2-2a4 4 0 0 0-5.6-5.6l-1.1 1.1M14 10a4 4 0 0 0-5.6-.1l-2 2A4 4 0 0 0 12 17.5l1.1-1.1',
  lock: 'M6 10h12v10H6zM8 10V7a4 4 0 0 1 8 0v3',
  check: 'm5 12 4 4L19 6',
  globe: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM3 12h18M12 3c2.1 2.4 3.2 5.4 3.2 9S14.1 18.6 12 21M12 3C9.9 5.4 8.8 8.4 8.8 12S9.9 18.6 12 21',
};

function Icon({ name, size = 18, stroke = 1.75 }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={iconPaths[name]} /></svg>;
}

const alerts = [
  { id: 'EML-48291', sender: 'Finance Department', address: 'accounts@aicte-finance.co', subject: 'Re: Revised vendor banking details — action today', score: 97, level: 'critical', time: '2m', flags: ['Brand mimic', 'DMARC fail', 'VPN origin'], campaign: 'Blue Quill' },
  { id: 'EML-48288', sender: 'Microsoft 365', address: 'support@micr0soft-id.net', subject: 'Your mailbox will be deactivated in 24 hours', score: 89, level: 'high', time: '8m', flags: ['Credential lure', 'Link mismatch'], campaign: 'Credential Drift' },
  { id: 'EML-48276', sender: 'KPMG Advisory', address: 'review@kpmg-advisors.org', subject: 'Q3 compliance review — secure document attached', score: 76, level: 'high', time: '16m', flags: ['New domain', 'Macro attachment'], campaign: '—' },
  { id: 'EML-48271', sender: 'HR Operations', address: 'people@aicte.org', subject: 'Updated remote work acknowledgment', score: 42, level: 'medium', time: '28m', flags: ['Unusual relay'], campaign: '—' },
  { id: 'EML-48264', sender: 'Indian Railways', address: 'alerts@irctc-notify.info', subject: 'Confirm your travel concession profile', score: 67, level: 'high', time: '41m', flags: ['Link shortener', 'SPF softfail'], campaign: 'Rail Switch' },
];

const nav = [
  ['Command center', 'grid'], ['Threat inbox', 'inbox'], ['Cases', 'case'], ['Threat map', 'map'], ['Reports', 'report'],
];
const lowerNav = [['Policies', 'rule'], ['Audit trail', 'audit']];

function RiskBadge({ level, score }) {
  return <span className={`risk-badge ${level}`}><span className="risk-dot" />{score ?? level}</span>;
}

function MiniMap() {
  return <div className="mini-map" aria-label="Map of threat origins">
    <div className="map-glow glow-one" /><div className="map-glow glow-two" />
    <svg viewBox="0 0 500 260" preserveAspectRatio="xMidYMid slice" className="map-lines" aria-hidden="true">
      <path d="M35 59C93 25 111 70 162 55s48-44 104-24 75-18 126 9 46 64 85 69" />
      <path d="M17 144c55-12 78 30 134 5s67 4 121 0 91-40 156-3 39 39 76 43" />
      <path d="M107 222c18-32 75-26 108-1s70-5 104-14 79 6 144-14" />
    </svg>
    <span className="map-label usa">N. Virginia</span><span className="map-label eu">Amsterdam</span><span className="map-label in">Bengaluru</span>
    <span className="map-pulse p1" /><span className="map-pulse p2" /><span className="map-pulse p3" />
    <div className="map-legend"><span><i className="dot red" /> Critical</span><span><i className="dot amber" /> Elevated</span></div>
  </div>;
}

function TrendChart() {
  return <svg className="trend-chart" viewBox="0 0 650 182" preserveAspectRatio="none" aria-label="Threat volume trend">
    <defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#d7f84b" stopOpacity=".27"/><stop offset="1" stopColor="#d7f84b" stopOpacity="0"/></linearGradient></defs>
    <g className="chart-grid"><path d="M0 30H650M0 75H650M0 120H650M0 165H650" /></g>
    <path className="chart-area" d="M0 137 C30 128, 42 133, 65 119 S95 133, 120 117 S154 135, 181 102 S215 119, 240 108 S277 125, 302 96 S336 117, 360 81 S394 94, 422 76 S455 91, 480 43 S516 77, 540 64 S574 83, 599 35 S626 50, 650 27 V182 H0Z" />
    <path className="chart-line" d="M0 137 C30 128, 42 133, 65 119 S95 133, 120 117 S154 135, 181 102 S215 119, 240 108 S277 125, 302 96 S336 117, 360 81 S394 94, 422 76 S455 91, 480 43 S516 77, 540 64 S574 83, 599 35 S626 50, 650 27" />
    <circle className="chart-point" cx="599" cy="35" r="4.5" /><line className="chart-marker" x1="599" x2="599" y1="35" y2="182" />
  </svg>;
}

function App() {
  const [activeNav, setActiveNav] = useState('Command center');
  const [activeFilter, setActiveFilter] = useState('All alerts');
  const [selectedAlert, setSelectedAlert] = useState(alerts[0]);
  const [drawer, setDrawer] = useState(false);
  const [reviewed, setReviewed] = useState([]);
  const [notice, setNotice] = useState('');

  const shownAlerts = useMemo(() => alerts.filter((alert) => {
    if (activeFilter === 'High confidence') return alert.score >= 85;
    if (activeFilter === 'Campaign-linked') return alert.campaign !== '—';
    return true;
  }).filter((alert) => !reviewed.includes(alert.id)), [activeFilter, reviewed]);

  const showNotice = (message) => { setNotice(message); window.setTimeout(() => setNotice(''), 2800); };
  const openAlert = (alert) => { setSelectedAlert(alert); setDrawer(true); };

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><span /></div><div><strong>SENTINEL</strong><small>threat operations</small></div></div>
      <div className="tenant"><span className="tenant-chip">AI</span><div><b>AICTE Cyber Cell</b><small>Production workspace</small></div><Icon name="chevron" size={15} /></div>
      <nav className="nav-stack">{nav.map(([label, icon]) => <button key={label} className={activeNav === label ? 'nav-item active' : 'nav-item'} onClick={() => { setActiveNav(label); showNotice(`${label} view selected`); }}><Icon name={icon} /><span>{label}</span>{label === 'Threat inbox' && <em>12</em>}</button>)}</nav>
      <div className="nav-divider" />
      <nav className="nav-stack lower">{lowerNav.map(([label, icon]) => <button key={label} className={activeNav === label ? 'nav-item active' : 'nav-item'} onClick={() => { setActiveNav(label); showNotice(`${label} view selected`); }}><Icon name={icon} /><span>{label}</span></button>)}</nav>
      <div className="sidebar-footer"><div className="live-dot" /><div><small>Pipeline status</small><b>All systems operational</b></div></div>
    </aside>

    <section className="workspace">
      <header className="topbar"><div className="crumb"><span>Operations</span><Icon name="chevron" size={14} /><b>Command center</b></div><div className="top-actions"><button className="search-button" onClick={() => showNotice('Search is ready for connected data')}><Icon name="search" size={17} />Search cases, senders, domains <kbd>⌘ K</kbd></button><button className="icon-button" aria-label="Notifications" onClick={() => showNotice('You have 3 new analyst notifications')}><Icon name="bell" size={18}/><i /></button><button className="profile"><span>BS</span><div><b>Bharath S.</b><small>Senior analyst</small></div><Icon name="chevron" size={14}/></button></div></header>

      <div className="content">
        <section className="title-row"><div><p className="eyebrow"><span className="pulse" />LIVE SECURITY POSTURE</p><h1>Good morning, Bharath.</h1><p className="subtitle">You have <b>3 high-priority decisions</b> waiting in the threat queue.</p></div><button className="primary-button" onClick={() => showNotice('Suspicious email intake opened')}><Icon name="plus" size={18} />Report an email</button></section>

        <section className="signal-banner"><div className="signal-icon"><Icon name="link" size={22}/></div><div className="signal-copy"><p className="eyebrow">EMERGING CAMPAIGN SIGNAL</p><h2>Blue Quill is targeting finance teams</h2><p>6 related messages observed in the last 42 minutes. Shared reply-to infrastructure detected.</p></div><div className="signal-meta"><span><b>0.82</b> cluster confidence</span><button onClick={() => showNotice('Campaign workspace opened')}>Investigate campaign <Icon name="arrow" size={16}/></button></div></section>

        <section className="stat-grid"><article className="stat-card"><div className="stat-icon neutral"><Icon name="inbox"/></div><div><small>Analyzed today</small><h3>3,842</h3><p><span className="up">↑ 12.8%</span> vs. prior 24h</p></div><svg className="spark" viewBox="0 0 80 26"><path d="M1 22 12 17 22 20 32 12 44 15 54 7 66 10 79 2"/></svg></article><article className="stat-card"><div className="stat-icon critical"><Icon name="shield"/></div><div><small>High-risk blocked</small><h3>47</h3><p><span className="up">↑ 6 today</span> above baseline</p></div><svg className="spark critical-line" viewBox="0 0 80 26"><path d="M1 23 10 21 20 16 31 20 41 10 49 12 59 4 68 10 79 2"/></svg></article><article className="stat-card"><div className="stat-icon lime"><Icon name="case"/></div><div><small>Active campaigns</small><h3>05</h3><p><span className="up">+1 new</span> since 09:00</p></div><svg className="spark lime-line" viewBox="0 0 80 26"><path d="M1 20 9 16 18 20 28 11 38 14 48 11 56 16 66 6 79 9"/></svg></article><article className="stat-card"><div className="stat-icon violet"><Icon name="clock"/></div><div><small>Median time to triage</small><h3>4m 18s</h3><p><span className="down">↓ 22 sec</span> this week</p></div><svg className="spark violet-line" viewBox="0 0 80 26"><path d="M1 7 12 10 22 5 31 14 40 12 49 18 59 14 69 22 79 17"/></svg></article></section>

        <section className="dashboard-grid">
          <article className="panel trend-panel"><div className="panel-heading"><div><p className="eyebrow">THREAT VOLUME</p><h2>Risk signal is rising</h2></div><div className="chart-totals"><div><b>158</b><small>last 24h</small></div><div><b className="coral-text">+31%</b><small>above usual</small></div></div></div><TrendChart/><div className="chart-axis"><span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>Now</span></div><div className="chart-note"><span className="note-pin" />Spike correlates with Blue Quill campaign activity <button onClick={() => showNotice('Showing campaign-linked threat volume')}>View analysis <Icon name="arrow" size={14}/></button></div></article>
          <article className="panel origin-panel"><div className="panel-heading"><div><p className="eyebrow">ORIGIN INTELLIGENCE</p><h2>Where attempts originate</h2></div><button className="text-button" onClick={() => showNotice('Threat map opened')}>Open map <Icon name="arrow" size={14}/></button></div><MiniMap/><div className="origin-list"><div><span className="country-dot india"/>India <b>34</b><em>+18%</em></div><div><span className="country-dot usa"/>United States <b>27</b><em>+8%</em></div><div><span className="country-dot nl"/>Netherlands <b>19</b><em>new</em></div></div></article>
        </section>

        <section className="queue-section"><div className="queue-header"><div><p className="eyebrow">PRIORITY QUEUE</p><h2>Make the next call</h2></div><div className="queue-controls"><button className="filter-button" onClick={() => showNotice('Filters are available when connected to data')}><Icon name="filter" size={16}/>Filters</button><button className="text-button" onClick={() => showNotice('Full threat inbox opened')}>View all 12 <Icon name="arrow" size={15}/></button></div></div><div className="filter-tabs">{['All alerts', 'High confidence', 'Campaign-linked'].map(filter => <button key={filter} onClick={() => setActiveFilter(filter)} className={activeFilter === filter ? 'selected' : ''}>{filter}{filter === 'All alerts' && <span>12</span>}</button>)}</div><div className="alert-list">{shownAlerts.map(alert => <article key={alert.id} className="alert-row"><button className="alert-main" onClick={() => openAlert(alert)}><div className="sender-avatar">{alert.sender.split(' ').slice(0,2).map(x=>x[0]).join('')}</div><div className="email-summary"><div className="summary-top"><b>{alert.sender}</b><span>{alert.address}</span></div><strong>{alert.subject}</strong><div className="flag-row">{alert.flags.map(flag => <span key={flag}>{flag}</span>)}{alert.campaign !== '—' && <span className="campaign-flag"><Icon name="link" size={12}/>{alert.campaign}</span>}</div></div></button><div className="alert-score"><RiskBadge level={alert.level} score={`${alert.score} risk`} /><small>{alert.time} ago</small></div><button className="row-action" aria-label={`Inspect ${alert.id}`} onClick={() => openAlert(alert)}><Icon name="arrow" size={17}/></button></article>)}</div></section>
      </div>
    </section>

    {drawer && <div className="drawer-wrap"><div className="drawer-shade" onClick={() => setDrawer(false)} /><aside className="detail-drawer"><div className="drawer-head"><div><p className="eyebrow">EMAIL TRACE · {selectedAlert.id}</p><h2>Decision brief</h2></div><button className="icon-button" aria-label="Close detail" onClick={() => setDrawer(false)}><Icon name="close"/></button></div><div className="decision-card"><RiskBadge level={selectedAlert.level} score={`${selectedAlert.score}/100`} /><p>This message claims to be from <b>{selectedAlert.sender}</b>, but its sender infrastructure and authentication history do not align with the claimed organization.</p><div className="confidence"><span>Assessment confidence</span><b>High · 91%</b><div><i /></div></div></div><section className="signal-list"><p className="eyebrow">WHY IT WAS FLAGGED</p><div><span className="signal-num">01</span><article><b>Sender identity mismatch</b><small><code>{selectedAlert.address.split('@')[1]}</code> was registered 4 days ago and resembles a protected domain.</small></article><strong>31%</strong></div><div><span className="signal-num">02</span><article><b>Authentication failed</b><small>SPF, DKIM, and DMARC checks did not align with the displayed sender.</small></article><strong>25%</strong></div><div><span className="signal-num">03</span><article><b>Suspicious destination</b><small>Link display text does not match its resolved destination.</small></article><strong>22%</strong></div></section><section className="safe-preview"><div><span><Icon name="lock" size={14}/> Safe rendered preview</span><button onClick={() => showNotice('Raw headers unlocked for this demo')}>View headers</button></div><p><b>From:</b> {selectedAlert.sender} &lt;{selectedAlert.address}&gt;</p><h3>{selectedAlert.subject}</h3><div className="preview-lines"><i/><i/><i/><i/></div></section><footer className="drawer-footer"><button className="quiet-button" onClick={() => { setReviewed([...reviewed, selectedAlert.id]); setDrawer(false); showNotice(`${selectedAlert.id} marked reviewed`); }}><Icon name="check" size={16}/>Mark reviewed</button><button className="primary-button compact" onClick={() => showNotice(`${selectedAlert.id} escalated into a case`)}>Escalate to case <Icon name="arrow" size={16}/></button></footer></aside></div>}
    {notice && <div className="toast"><Icon name="check" size={16}/>{notice}</div>}
  </main>;
}

createRoot(document.getElementById('root')).render(<App />);
