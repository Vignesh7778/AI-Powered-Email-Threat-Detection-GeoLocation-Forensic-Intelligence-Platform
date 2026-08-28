const BASE = (import.meta.env.VITE_GATEWAY_URL || '').replace(/\/$/, '');
export const auth = {
  get token() { return sessionStorage.getItem('access_token'); },
  get user() { try { return JSON.parse(sessionStorage.getItem('user') || 'null'); } catch { return null; } },
  save(data) { Object.entries(data).forEach(([k, v]) => v != null && sessionStorage.setItem(k, typeof v === 'string' ? v : JSON.stringify(v))); },
  clear() { sessionStorage.clear(); },
};
async function request(path, options = {}) {
  const headers = { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers };
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`;
  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!response.ok) { const detail = await response.json().catch(() => ({})); throw new Error(detail.detail || `${response.status} ${response.statusText}`); }
  return response.status === 204 ? null : response.json();
}
const get = (path, params) => request(path + (params ? `?${new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null))}` : ''));
const body = (method, path, value) => request(path, { method, body: JSON.stringify(value) });
export const api = {
  login: (email, password) => body('POST', '/auth/login', { email, password }),
  mfa: (mfa_token, code) => body('POST', '/auth/mfa/verify', { mfa_token, code }),
  dashboard: { summary: () => get('/api/v1/dashboard/summary'), trend: (days = 30) => get('/api/v1/dashboard/trend', { days }), domains: () => get('/api/v1/dashboard/top-domains') },
  emails: { list: (p) => get('/api/v1/emails', p), get: (id) => get(`/api/v1/emails/${id}`), patch: (id, v) => body('PATCH', `/api/v1/emails/${id}`, v), verdict: (id, v) => body('POST', `/api/v1/emails/${id}/verdict`, { analyst_verdict: v }), graph: (id) => get(`/api/v1/emails/${id}/graph`), custody: (id) => get(`/api/v1/emails/${id}/custody`), report: (id, format = 'json') => get(`/api/v1/emails/${id}/report`, { format }), bulk: (v) => body('POST', '/api/v1/emails/bulk-action', v), selfReport: (file) => { const f = new FormData(); f.append('file', file); return request('/api/v1/emails/self-report', { method: 'POST', body: f }); } },
  alerts: { list: (p) => get('/api/v1/alerts', p), acknowledge: (id) => body('POST', `/api/v1/alerts/${id}/acknowledge`) },
  cases: { list: (p) => get('/api/v1/cases', p), get: (id) => get(`/api/v1/cases/${id}`), create: (v) => body('POST', '/api/v1/cases', v), patch: (id, v) => body('PATCH', `/api/v1/cases/${id}`, v), comments: (id) => get(`/api/v1/cases/${id}/comments`), comment: (id, text) => body('POST', `/api/v1/cases/${id}/comments`, { body: text }) },
  geo: (p) => get('/api/v1/geo/heatmap', p), reports: { list: (p) => get('/api/v1/reports', p), schedules: () => get('/api/v1/reports/schedules'), createSchedule: (v) => body('POST', '/api/v1/reports/schedules', v) },
  rules: { thresholds: (t) => get(`/api/v1/tenants/${t}/rules/thresholds`), updateThresholds: (t, v) => body('PUT', `/api/v1/tenants/${t}/rules/thresholds`, v), watchlist: (t, k) => get(`/api/v1/tenants/${t}/watchlists/${k}`), add: (t, k, value) => body('POST', `/api/v1/tenants/${t}/watchlists/${k}`, { value }), remove: (t, k, id) => request(`/api/v1/tenants/${t}/watchlists/${k}/${id}`, { method: 'DELETE' }) },
  users: { list: (t) => get(`/api/v1/tenants/${t}/users`), update: (t, id, v) => body('PATCH', `/api/v1/tenants/${t}/users/${id}`, v) }, audit: (p) => get('/api/v1/audit-log', p), settings: { mailboxes: (t) => get(`/api/v1/tenants/${t}/integrations/mailboxes`), privacy: (t) => get(`/api/v1/tenants/${t}/privacy-config`), updatePrivacy: (t, v) => body('PUT', `/api/v1/tenants/${t}/privacy-config`, v) }
};
