import type {
  UserProfile,
  EmailDetail,
  EmailListItem,
  DashboardStats,
  Case,
  Alert,
  CampaignGraph,
  EvidenceChain
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers || {});
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  async login(username: string, password: string): Promise<{ access_token: string; user: UserProfile }> {
    const data = await request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, email: username, password }),
    });
    const user: UserProfile = {
      user_id: data.user_id || 'usr-default',
      username: username.includes('@') ? username.split('@')[0] : username,
      full_name: username.replace('_', ' ').replace('@org.gov', '').toUpperCase(),
      email: data.email || (username.includes('@') ? username : `${username}@org.gov`),
      role: (data.role as any) || 'analyst',
      tenant_id: data.tenant_id,
    };
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(user));
    return { access_token: data.access_token, user };
  },

  getCurrentUser(): UserProfile | null {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  },

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  async getDashboardStats(): Promise<DashboardStats> {
    try {
      return await request<DashboardStats>('/dashboard/stats');
    } catch {
      return await request<DashboardStats>('/dashboard/summary');
    }
  },

  // In-memory & sessionStorage cache for resilient cross-lambda retrieval
  _detailCache: new Map<string, EmailDetail>(),

  cacheDetail(detail: EmailDetail) {
    if (!detail || !detail.submission_id) return;
    this._detailCache.set(detail.submission_id, detail);
    try {
      sessionStorage.setItem(`tracex_sub_${detail.submission_id}`, JSON.stringify(detail));
      const localIds: string[] = JSON.parse(sessionStorage.getItem('tracex_local_subs') || '[]');
      if (!localIds.includes(detail.submission_id)) {
        localIds.unshift(detail.submission_id);
        sessionStorage.setItem('tracex_local_subs', JSON.stringify(localIds.slice(0, 50)));
      }
    } catch {}
  },

  getCachedDetail(submissionId: string): EmailDetail | null {
    if (this._detailCache.has(submissionId)) {
      return this._detailCache.get(submissionId)!;
    }
    try {
      const stored = sessionStorage.getItem(`tracex_sub_${submissionId}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        this._detailCache.set(submissionId, parsed);
        return parsed;
      }
    } catch {}
    return null;
  },

  getLocalCachedSubmissions(): EmailListItem[] {
    try {
      const localIds: string[] = JSON.parse(sessionStorage.getItem('tracex_local_subs') || '[]');
      const items: EmailListItem[] = [];
      for (const id of localIds) {
        const det = this.getCachedDetail(id);
        if (det) {
          items.push({
            submission_id: det.submission_id,
            risk_level: det.assessment?.risk_level || 'medium',
            classification: det.assessment?.classification || 'suspicious',
            fraud_score: det.assessment?.fraud_score || 0.5,
            received_at: det.ingested_at,
            sender: det.sender || 'Unknown Sender',
            recipient: det.recipient || 'Internal Security',
            subject: det.subject || det.file_name || 'Uploaded Artifact',
            origin_ip: det.assessment?.origin?.originating_ip || 'N/A',
            origin_asn: det.assessment?.origin?.geolocation?.asn || 'AS-Custom',
            status: det.status || 'complete'
          });
        }
      }
      return items;
    } catch {
      return [];
    }
  },

  async listEmails(params?: {
    risk_level?: string;
    classification?: string;
    search?: string;
    page?: number;
    limit?: number;
    page_size?: number;
  }): Promise<{ results: EmailListItem[]; total: number; page: number; limit: number; page_size: number }> {
    const query = new URLSearchParams();
    if (params?.risk_level && params.risk_level !== 'all') query.set('risk_level', params.risk_level);
    if (params?.classification && params.classification !== 'all') query.set('classification', params.classification);
    if (params?.search) query.set('search', params.search);
    if (params?.page) query.set('page', String(params.page));
    const pageSize = params?.limit || params?.page_size;
    if (pageSize) {
      query.set('limit', String(pageSize));
      query.set('page_size', String(pageSize));
    }
    const qs = query.toString();
    const data = await request<any>(`/emails${qs ? `?${qs}` : ''}`).catch(() => ({ results: [], total: 0 }));
    let results: EmailListItem[] = Array.isArray(data) ? data : (data?.results || []);

    // Merge local cached submissions if not present in backend query response
    const localItems = this.getLocalCachedSubmissions();
    for (const item of localItems) {
      if (!results.some(r => r.submission_id === item.submission_id)) {
        results.unshift(item);
      }
    }

    const total = Math.max(data?.total ?? results.length, results.length);
    return { results, total, page: data?.page || 1, limit: pageSize || 25, page_size: pageSize || 25 };
  },

  async getEmailDetail(submissionId: string): Promise<EmailDetail> {
    try {
      const data = await request<EmailDetail>(`/emails/${submissionId}`);
      if (data) {
        this.cacheDetail(data);
      }
      return data;
    } catch (err: any) {
      const cached = this.getCachedDetail(submissionId);
      if (cached) {
        return cached;
      }
      throw err;
    }
  },

  async refreshEmail(submissionId: string): Promise<EmailDetail> {
    return request<EmailDetail>(`/emails/${submissionId}/refresh`, {
      method: 'POST',
    });
  },

  async ingestRawEmail(file: File): Promise<{ submission_id: string; status: string; detail?: EmailDetail }> {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await request<{ submission_id: string; status: string; detail?: EmailDetail }>('/emails/ingest', {
      method: 'POST',
      body: formData,
    });
    if (resp.detail) {
      this.cacheDetail(resp.detail);
    }
    return resp;
  },

  async getEvidenceChain(submissionId: string): Promise<EvidenceChain> {
    return request<EvidenceChain>(`/forensics/chain/${submissionId}`);
  },

  async listCases(): Promise<Case[]> {
    return request<Case[]>('/cases');
  },

  async createCase(data: { title: string; notes?: string; severity: string }): Promise<Case> {
    return request<Case>('/cases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateCase(caseId: string, data: { title?: string; notes?: string; severity?: string; status?: string; submission_ids?: string[] }): Promise<Case> {
    return request<Case>(`/cases/${caseId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async listAlerts(unacknowledgedOnly = false): Promise<Alert[]> {
    return request<Alert[]>(`/alerts?unacknowledged_only=${unacknowledgedOnly}`);
  },

  async acknowledgeAlert(alertId: string): Promise<Alert> {
    return request<Alert>(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
    });
  },

  async getCampaignGraph(campaignId: string): Promise<CampaignGraph> {
    return request<CampaignGraph>(`/campaigns/${campaignId}/graph`);
  },

  async listCampaigns(): Promise<any[]> {
    return request<any[]>('/campaigns').catch(() => []);
  },

  async getAssessment(submissionId: string) {
    const detail = await this.getEmailDetail(submissionId);
    return detail.assessment || null;
  },

  async getSubmission(submissionId: string) {
    return this.getEmailDetail(submissionId);
  },

  async refreshAnalysis(submissionId: string) {
    const detail = await this.refreshEmail(submissionId);
    return detail.assessment || null;
  },

  getReportUrl(submissionId: string, format: 'json' | 'pdf' = 'json'): string {
    return `${API_BASE}/emails/${submissionId}/report?format=${format}`;
  },

  async downloadReport(submissionId: string, format: 'json' | 'pdf' = 'json'): Promise<void> {
    try {
      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/emails/${submissionId}/report?format=${format}`, {
        headers,
      });
      if (!response.ok) {
        throw new Error(`Report export failed with status ${response.status}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = format === 'pdf' ? `forensic_report_${submissionId.slice(0, 8)}.pdf` : `forensic_evidence_${submissionId.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Download report error:', err);
      alert('Report download failed: ' + (err?.message || 'Unknown network error'));
    }
  },
};



