import React, { useState } from 'react';
import { useAccounts } from '../hooks/useAccounts';
import { useSummary } from '../hooks/useSummary';
import { MetricCard } from '../components/MetricCard';
import { AnalyticsCharts } from '../components/AnalyticsCharts';
import { AccountFilterBar } from '../components/AccountFilterBar';
import { AccountTable } from '../components/AccountTable';
import { SettingsWizardModal } from '../components/SettingsWizardModal';
import { formatCents, formatNumber } from '../utils/formatters';

interface DashboardPageProps {
  isRefreshing: boolean;
  onRefreshAll: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({}) => {
  // Account list state
  const {
    accounts,
    totalRecords,
    totalPages,
    isLoading: isAccountsLoading,
    params,
    setParams,
    selectedIds,
    toggleSelectAllCurrentPage,
    toggleSelectAccount,
    refresh: refreshAccounts,
  } = useAccounts();

  // Summary and analytics state with retry handling for deliberate 20% HTTP 500
  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    retryAttempt,
    error: summaryError,
    reload: reloadSummary,
  } = useSummary(params.start_date, params.end_date);

  // Settings Wizard Modal state
  const [editingAccountId, setEditingAccountId] = useState<string | null>(null);

  const handleFilterChange = (updated: any) => {
    setParams((prev) => ({ ...prev, ...updated }));
  };

  const handleResetFilters = () => {
    setParams({
      page: 1,
      page_size: 10,
      sort_by: 'created_at',
      sort_dir: 'desc',
      search: '',
      status: '',
      country: '',
      plan: '',
      start_date: '',
      end_date: '',
    });
  };

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            Telephony Usage & Billing Console
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Real-time multi-tenant telephony consumption, billing caps, and tenant configuration.
          </p>
        </div>
      </div>

      {/* KPI Metric Overview Cards */}
      <section aria-label="Key Performance Indicators" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Tenants"
          value={summaryData ? formatNumber(summaryData.total_accounts) : '—'}
          subValue={
            summaryData
              ? `${summaryData.active_accounts} active · ${summaryData.trial_accounts} trial · ${summaryData.suspended_accounts} suspended`
              : undefined
          }
          isLoading={isSummaryLoading}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          }
        />

        <MetricCard
          label="Call Minutes"
          value={summaryData ? formatNumber(summaryData.total_minutes) : '—'}
          subValue="Aggregated VoIP call consumption"
          trend="+12.4% vs last period"
          isLoading={isSummaryLoading}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          }
        />

        <MetricCard
          label="SMS Usage"
          value={summaryData ? formatNumber(summaryData.total_sms) : '—'}
          subValue="Inbound & outbound messaging"
          trend="+8.1%"
          isLoading={isSummaryLoading}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          }
        />

        <MetricCard
          label="Total Billed Cost"
          value={summaryData ? formatCents(summaryData.total_cost_cents) : '—'}
          subValue="Calculated from exact integer cents"
          trend="+15.3%"
          isLoading={isSummaryLoading}
          icon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </section>

      {/* Analytics Visualization Section with 20% Random 500 Failure Handling */}
      <section aria-label="Usage Analytics">
        <AnalyticsCharts
          trends={summaryData?.trends}
          isLoading={isSummaryLoading}
          retryAttempt={retryAttempt}
          error={summaryError}
          onRetry={reloadSummary}
        />
      </section>

      {/* Customer Accounts Directory Section */}
      <section aria-label="Accounts Directory">
        <AccountFilterBar
          params={params}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
          selectedCount={selectedIds.size}
        />

        <AccountTable
          accounts={accounts}
          isLoading={isAccountsLoading}
          totalRecords={totalRecords}
          totalPages={totalPages}
          params={params}
          onParamChange={handleFilterChange}
          selectedIds={selectedIds}
          onToggleSelectAll={toggleSelectAllCurrentPage}
          onToggleSelectOne={toggleSelectAccount}
          onOpenSettings={(id) => setEditingAccountId(id)}
        />
      </section>

      {/* 4-Step Account Settings Modal */}
      {editingAccountId && (
        <SettingsWizardModal
          accountId={editingAccountId}
          onClose={() => setEditingAccountId(null)}
          onSuccess={() => {
            refreshAccounts();
            reloadSummary();
          }}
        />
      )}
    </main>
  );
};
