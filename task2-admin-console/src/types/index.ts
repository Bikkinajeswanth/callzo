export type AccountStatus = 'active' | 'trial' | 'suspended';
export type AccountPlan = 'basic' | 'pro' | 'enterprise';
export type CountryCode = 'US' | 'IN' | 'GB' | 'CA' | 'AU';

export interface Account {
  id: string;
  name: string;
  email: string;
  company: string;
  country: CountryCode;
  plan: AccountPlan;
  status: AccountStatus;
  monthly_minutes: number;
  monthly_sms: number;
  cost_cents: number;
  created_at: string;
  last_active: string;
}

export interface AccountsResponse {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  accounts: Account[];
}

export interface MonthlyTrend {
  month: string;
  minutes: number;
  sms: number;
  cost_cents: number;
  signups: number;
}

export interface SummaryData {
  total_accounts: number;
  active_accounts: number;
  trial_accounts: number;
  suspended_accounts: number;
  total_minutes: number;
  total_sms: number;
  total_cost_cents: number;
  trends: MonthlyTrend[];
}

export interface AccountFilterParams {
  search?: string;
  page: number;
  page_size: number;
  sort_by: string;
  sort_dir: 'asc' | 'desc';
  status?: string;
  country?: string;
  plan?: string;
  start_date?: string;
  end_date?: string;
}

export interface Step1Personal {
  name: string;
  email: string;
}

export interface Step2Subscription {
  plan: AccountPlan;
  billing_country: CountryCode;
}

export interface Step3Limits {
  minutes_cap: number | null;
  sms_cap: number | null;
}

export interface Step4Webhook {
  webhook_url: string;
}

export interface SettingsDraft {
  step1: Step1Personal;
  step2: Step2Subscription;
  step3: Step3Limits;
  step4: Step4Webhook;
  submitted?: boolean;
}

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';
