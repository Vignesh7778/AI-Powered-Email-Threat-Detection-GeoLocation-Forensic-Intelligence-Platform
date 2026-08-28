# UX Design — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform

## 1. Who uses this and why that matters

Before laying out pages, it helps to separate the audiences, because they want very different things from the same data:

| User | Comes here to... | Mental mode |
|---|---|---|
| **Security Analyst / SOC operator** | Triage incoming alerts fast, decide real vs. false alarm | Speed, scanning, pattern recognition |
| **Administrator / IT Manager** | See organizational risk posture, manage users/policies | Oversight, trends, control |
| **Investigator / Forensic examiner** | Dig deep into one case, build an evidentiary trail | Depth, precision, documentation |
| **Executive / Compliance officer** | Understand risk exposure and outcomes, not mechanics | Summary, confidence, accountability |

A single "one-size-fits-all" dashboard fails all four. The design below gives each a natural home while sharing one underlying data model.

---

## 2. Core design principles

1. **Triage first, depth on demand.** The first screen after login should let someone decide "is this bad?" in under 10 seconds. Full forensic depth is one click away, not the default view.
2. **Confidence, not false certainty.** Attribution is probabilistic. Every score, map pin, or "likely origin" claim should visually communicate *how sure* the system is (e.g., high/medium/low bands), never presented as flat fact.
3. **Progressive disclosure.** Headers, WHOIS, relay chains, IP reputation — this is a lot of dense information. Default views stay human-readable ("This email was likely sent from a data center in Country X, not the claimed sender's usual location"); raw technical detail is expandable, not front-loaded.
4. **Narrative over raw logs.** A forensic report should read like a story an investigator or a non-technical stakeholder (legal, executive) can follow: what happened, how confident we are, what we recommend — not a dump of header fields.
5. **Evidence integrity is visible.** Anywhere a case can be exported, shared, or acted on, the interface should visibly reflect chain-of-custody status (e.g., "locked for evidence," timestamps, who accessed it) so trust in the record is built into the UI, not bolted on.
6. **Calm alerting.** This is a security tool people live in all day. Alerts should be prioritized and grouped rather than a wall of red — alarm fatigue is a real usability failure mode here.

---

## 3. Information architecture (site map)

```
Login / MFA
│
├── Dashboard (role-aware home)
├── Threat Inbox / Alert Queue
│   └── Email Detail & Trace View  → the core investigative screen
│       ├── Overview tab
│       ├── Header & Authentication tab
│       ├── Origin & Geolocation tab
│       ├── Attribution & Correlation tab
│       └── Forensic Report tab
├── Campaigns / Case Management
│   └── Case Detail (groups multiple related emails)
├── Geolocation & Threat Map (org-wide view)
├── Reports & Export Center
├── Rules, Policies & Watchlists
├── User & Access Management (admin)
├── Audit Log / Chain of Custody
└── Settings (integrations, retention, notification preferences)
```

---

## 4. Page-by-page UX design

### 4.1 Login & Access
- Standard credential entry + mandatory MFA (this platform touches sensitive forensic data, so this is a UX requirement, not just security).
- Role-based redirect: analysts land on the Alert Queue; executives land on the Dashboard summary; investigators land on Case Management.

### 4.2 Dashboard (home)
The "state of the union" screen. Different by role, but structurally:
- **Top strip**: today's snapshot — emails scanned, threats caught, high-confidence fraud cases open, average time-to-triage.
- **Risk trend chart**: threats over time, so spikes (a new campaign) are visually obvious.
- **Top offending regions/domains this week**: a compact mini-map or ranked list — teases the full geolocation map.
- **Active campaigns needing attention**: cases with rising email counts.
- **Quick action**: "Report a suspicious email" — lets a non-analyst employee submit something for review, feeding the pipeline.

*UX intent:* answer "should I be worried today?" at a glance, then route people to where they need to act.

### 4.3 Threat Inbox / Alert Queue
This is the analyst's main working screen — think of it like a smarter, security-flavored email inbox.
- **List view** with each row showing: sender, subject, fraud-risk score (color-coded band, not just a number), key flags as small icons (spoofed domain, failed DKIM, suspicious link, geolocation mismatch), and time received.
- **Filters/sorting**: by risk level, authentication failure type, campaign membership, date, department targeted.
- **Bulk triage actions**: mark reviewed, escalate to case, mark false positive — analysts process volume, so multi-select matters.
- **Saved views**: e.g., "Executive impersonation attempts," "Payment fraud pattern" — recurring queries analysts don't want to rebuild daily.

*UX intent:* let someone scan 50 emails and correctly prioritize the 3 that matter without opening each one.

### 4.4 Email Detail & Trace View (the heart of the product)
Opened from the queue. Structured as tabs so density is manageable:

**Overview tab**
- Plain-language summary at the top: *"This email claims to be from [Company Finance] but was likely sent from a hosting provider in [Region], not [Company]'s mail servers. Authentication failed. Risk: High."*
- Visual fraud-score gauge with the contributing factors listed beneath in order of weight.
- Rendered email preview (safely sandboxed, links disabled/defanged) so the analyst sees what the recipient saw.

**Header & Authentication tab**
- SPF/DKIM/DMARC results shown as clear pass/fail/neutral badges with one-line plain explanations, not raw header dumps.
- A visual relay-path timeline: each hop the email took, shown left-to-right or as connected nodes, flagging the anomalous hop.
- "Show raw headers" toggle for those who want the technical source — collapsed by default.

**Origin & Geolocation tab**
- A map pinpointing the estimated originating IP location, with a confidence ring/radius rather than a precise pin — visually honest about uncertainty.
- Infrastructure type called out plainly: residential, data center, known VPN/proxy, TOR exit node, cloud provider.
- Domain intelligence panel: registration age, registrar, hosting history — framed as "why this looks suspicious" rather than a WHOIS printout.

**Attribution & Correlation tab**
- "This sender/domain/IP has been seen in X other incidents" with links to those cases.
- A relationship graph (interactive node diagram) connecting this email to related domains, IPs, and past campaigns — collapsible for users who just want the summary sentence version.

**Forensic Report tab**
- One-click generation of a clean, exportable narrative report (PDF/structured document) suitable for legal, compliance, or law enforcement handoff.
- Shows evidence-lock status and chain-of-custody trail directly on this tab.

*UX intent:* this screen has to serve a fast-scanning analyst and a slow, careful investigator simultaneously — tabs plus a plain-language top layer solve that tension.

### 4.5 Campaigns / Case Management
- Kanban or list board of "cases," each bundling multiple related fraudulent emails (same campaign, same actor cluster).
- Case detail page: timeline of all related emails, shared infrastructure indicators, affected recipients/departments, current investigation status, and assigned analyst.
- Notes/comments thread per case for team collaboration and audit trail.

*UX intent:* fraud rarely arrives as one isolated email — this is where the "connect the dots across many emails" work happens.

### 4.6 Geolocation & Threat Map (org-wide)
- A larger, standalone version of the mini-map on the dashboard: heat-map of where attacks are estimated to originate from, filterable by date range, threat type, and confidence level.
- Clicking a region/cluster drills into the relevant emails/cases from there.

*UX intent:* useful for spotting geographic patterns (a sudden cluster from one region signaling a new campaign) at an organizational level, not per-email.

### 4.7 Reports & Export Center
- Central library of generated forensic reports, scheduled recurring reports (e.g., weekly exec summary), and export history.
- Export format options suited to the audience (detailed technical report vs. executive summary vs. law-enforcement-ready package).

### 4.8 Rules, Policies & Watchlists
- Where admins configure sensitivity thresholds, add domains/IPs to watchlists or allowlists, set auto-actions (e.g., auto-quarantine above a risk threshold), and define what counts as "high-risk" for their organization.
- Presented as readable rule cards/toggles, not raw config files.

### 4.9 User & Access Management
- Standard admin screen: roles, permissions, department mapping (who sees what), MFA enforcement status.

### 4.10 Audit Log / Chain of Custody
- Append-only, searchable log of who viewed, exported, or acted on which case/email and when.
- Exists as its own page because in forensic/legal contexts, this record itself is a deliverable, not just a debugging tool.

### 4.11 Settings
- Mail system integrations (which mailboxes/domains are being monitored), notification preferences, data retention and masking configuration (ties to the privacy/compliance requirement in the brief).

---

## 5. Key UX flows worth designing carefully

**Flow A — Analyst triage (most frequent path)**
Alert Queue → scan risk scores → open one Email Detail (Overview tab) → decide: dismiss / escalate to case / generate report. This path should take seconds per email for the majority of low-risk items.

**Flow B — Deep investigation (least frequent, highest stakes)**
Case Management → Case Detail → multiple Email Detail tabs (Header, Origin, Attribution) → annotate findings → generate Forensic Report → export with chain-of-custody intact.

**Flow C — Executive/compliance check-in (glance-only)**
Dashboard → trend chart + top campaigns → maybe one Report export. Never needs to touch header-level detail.

**Flow D — Employee self-report**
Any user → "Report suspicious email" quick action → confirmation only → disappears into the analyst's queue. This should be the simplest flow in the entire product — a non-technical person submitting a tip shouldn't see any of the complexity above.

---

## 6. Visual/interaction language suggestions

- **Risk color coding**: consistent across every page (e.g., red/amber/green or a 4-band scale) — a color used for "high risk" on the dashboard must mean the same thing in the queue and the detail view.
- **Confidence indicators**: use visual weight (opacity, ring thickness, "high/medium/low" labels) rather than false-precision percentages like "87.3% likely" for attribution claims.
- **Plain-language-first, technical-detail-second**: every dense technical panel (headers, WHOIS, relay chains) should have a one-sentence human summary above it.
- **Sandboxed previews**: any rendered email/link content should be visually marked as "safe preview" so analysts don't second-guess whether they're at risk clicking around.

---

## 7. Summary

The site map centers on one core screen — **Email Detail & Trace View** — because that's where detection, forensics, geolocation, and attribution all converge. Everything else (Dashboard, Queue, Case Management, Map, Reports) exists to either **route people into** that screen efficiently or **summarize its output** for people who don't need the full depth. Designing around that center, with progressive disclosure and visible confidence levels throughout, keeps the product usable for a fast-moving analyst and rigorous enough for a forensic investigator at the same time.
