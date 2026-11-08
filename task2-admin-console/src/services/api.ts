import {
  Account,
  AccountsResponse,
  AccountFilterParams,
  SummaryData,
  SettingsDraft,
} from '../types';

// Supports environment override, falling back to Vite development proxy (/api) or direct localhost:8001
const API_BASE = (import.meta.env.VITE_API_URL as string) || (typeof window !== 'undefined' ? '/api' : 'http://localhost:8001');

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
      try {
        const body = await res.json();
        if (body.detail) {
          errorMsg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
        // Fallback to text
      }
      const error: any = new Error(errorMsg);
      error.status = res.status;
      throw error;
    }

    return await res.json();
  } catch (err: any) {
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      throw new Error('Network error: Unable to communicate with the Callzo API server.');
    }
    throw err;
  }
}

export const api = {
  getHealth: () => request<{ status: string; service: string }>('/health'),

  getAccounts: (params: AccountFilterParams): Promise<AccountsResponse> => {
    const query = new URLSearchParams();
    query.set('page', String(params.page));
    query.set('page_size', String(params.page_size));
    query.set('sort_by', params.sort_by);
    query.set('sort_dir', params.sort_dir);

    if (params.search) query.set('search', params.search);
    if (params.status) query.set('status', params.status);
    if (params.country) query.set('country', params.country);
    if (params.plan) query.set('plan', params.plan);
    if (params.start_date) query.set('start_date', params.start_date);
    if (params.end_date) query.set('end_date', params.end_date);

    return request<AccountsResponse>(`/accounts?${query.toString()}`);
  },

  getAccountById: (id: string): Promise<Account> => request<Account>(`/accounts/${encodeURIComponent(id)}`),

  getAccountsSummary: (startDate?: string, endDate?: string): Promise<SummaryData> => {
    const query = new URLSearchParams();
    if (startDate) query.set('start_date', startDate);
    if (endDate) query.set('end_date', endDate);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<SummaryData>(`/accounts/summary${qs}`);
  },

  getAccountSettings: (id: string): Promise<SettingsDraft> =>
    request<SettingsDraft>(`/accounts/${encodeURIComponent(id)}/settings`),

  saveAccountSettingsStep: (
    id: string,
    step: number,
    data: Record<string, any>
  ): Promise<{ status: string; step: number; draft: any }> =>
    request(`/accounts/${encodeURIComponent(id)}/settings/step/${step}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  submitAccountSettings: (id: string): Promise<{ status: string; message: string }> =>
    request(`/accounts/${encodeURIComponent(id)}/settings/submit`, {
      method: 'POST',
    }),
};
