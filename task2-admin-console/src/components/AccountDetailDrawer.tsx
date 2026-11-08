import React, { useEffect, useState, useCallback } from 'react';
import { Account } from '../types';
import { api } from '../services/api';
import { formatCents, formatNumber, formatDate, formatTimeAgo } from '../utils/formatters';

interface AccountDetailDrawerProps {
  accountId: string | null;
  onClose: () => void;
  onOpenSettings: (account: Account) => void;
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  trial: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  suspended: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
};

const PLAN_COLORS: Record<string, string> = {
  basic: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
  pro: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  enterprise: 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
};

const FLAG_MAP: Record<string, string> = {
  US: '🇺🇸', IN: '🇮🇳', GB: '🇬🇧', CA: '🇨🇦', AU: '🇦🇺',
};

export const AccountDetailDrawer: React.FC<AccountDetailDrawerProps> = ({
  accountId,
  onClose,
  onOpenSettings,
}) => {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAccount = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAccountById(id);
      setAccount(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load account details');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (accountId) {
      fetchAccount(accountId);
    } else {
      setAccount(null);
    }
  }, [accountId, fetchAccount]);

  // Close on ESC key
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (accountId) {
      document.addEventListener('keydown', handleKey);
    }
    return () => document.removeEventListener('keydown', handleKey);
  }, [accountId, onClose]);

  if (!accountId) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Account details"
        className="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-slate-900 z-50 shadow-2xl flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            Account Details
          </h2>
          <button
            onClick={onClose}
            aria-label="Close drawer"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-200 dark:hover:text-white dark:hover:bg-slate-700 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex flex-col gap-4 p-6 animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-10 bg-slate-200 dark:bg-slate-700 rounded-lg" />
              ))}
            </div>
          )}

          {error && !loading && (
            <div className="p-6">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                <button
                  onClick={() => accountId && fetchAccount(accountId)}
                  className="mt-3 text-sm font-medium text-red-700 dark:text-red-400 underline underline-offset-2"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {account && !loading && (
            <div className="p-6 space-y-6">
              {/* Identity */}
              <div>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                      {account.name}
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{account.email}</p>
                    {account.company && (
                      <p className="text-sm text-slate-600 dark:text-slate-300 mt-0.5">
                        {account.company}
                      </p>
                    )}
                  </div>
                  <span className={`shrink-0 inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${STATUS_COLORS[account.status] ?? ''}`}>
                    {account.status}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${PLAN_COLORS[account.plan] ?? ''}`}>
                    {account.plan}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200">
                    {FLAG_MAP[account.country] || '🌍'} {account.country}
                  </span>
                  <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                    #{account.id}
                  </span>
                </div>
              </div>

              {/* Usage KPIs */}
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">
                  Current Period Usage
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {formatNumber(account.monthly_minutes)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Minutes</p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {formatNumber(account.monthly_sms)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">SMS</p>
                  </div>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {formatCents(account.cost_cents)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Cost</p>
                  </div>
                </div>
              </section>

              {/* Metadata */}
              <section>
                <h4 className="text-xs font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">
                  Account Info
                </h4>
                <dl className="space-y-2">
                  {[
                    { label: 'Created', value: formatDate(account.created_at) },
                    { label: 'Last Active', value: formatTimeAgo(account.last_active) },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between items-baseline text-sm">
                      <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
                      <dd className="font-medium text-slate-900 dark:text-white">{value}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            </div>
          )}
        </div>

        {/* Footer actions */}
        {account && !loading && (
          <div className="shrink-0 px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 flex gap-3">
            <button
              onClick={() => onOpenSettings(account)}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              Manage Settings
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </aside>
    </>
  );
};
