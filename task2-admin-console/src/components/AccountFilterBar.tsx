import React from 'react';
import { AccountFilterParams } from '../types';

interface AccountFilterBarProps {
  params: AccountFilterParams;
  onChange: (updated: Partial<AccountFilterParams>) => void;
  onReset: () => void;
  selectedCount: number;
}

export const AccountFilterBar: React.FC<AccountFilterBarProps> = ({
  params,
  onChange,
  onReset,
  selectedCount,
}) => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm mb-4 space-y-3">
      {/* Search and Primary Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Search Input */}
        <div className="lg:col-span-2 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={params.search || ''}
            onChange={(e) => onChange({ search: e.target.value, page: 1 })}
            placeholder="Search account ID, name, email, company..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 transition"
          />
        </div>

        {/* Status Filter */}
        <div>
          <select
            value={params.status || ''}
            onChange={(e) => onChange({ status: e.target.value, page: 1 })}
            className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="trial">Trial</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>

        {/* Plan Filter */}
        <div>
          <select
            value={params.plan || ''}
            onChange={(e) => onChange({ plan: e.target.value, page: 1 })}
            className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">All Plans</option>
            <option value="basic">Basic</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>

        {/* Country Filter */}
        <div>
          <select
            value={params.country || ''}
            onChange={(e) => onChange({ country: e.target.value, page: 1 })}
            className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="">All Countries</option>
            <option value="US">United States (US)</option>
            <option value="IN">India (IN)</option>
            <option value="GB">United Kingdom (GB)</option>
            <option value="CA">Canada (CA)</option>
            <option value="AU">Australia (AU)</option>
          </select>
        </div>
      </div>

      {/* Date Range Picker & Selection Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
          <span className="font-medium text-slate-700 dark:text-slate-300">Signup Range:</span>
          <input
            type="date"
            value={params.start_date ? params.start_date.substring(0, 10) : ''}
            onChange={(e) => onChange({ start_date: e.target.value ? new Date(e.target.value).toISOString() : '', page: 1 })}
            className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          <span>to</span>
          <input
            type="date"
            value={params.end_date ? params.end_date.substring(0, 10) : ''}
            onChange={(e) => onChange({ end_date: e.target.value ? new Date(e.target.value).toISOString() : '', page: 1 })}
            className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
          {(params.search || params.status || params.plan || params.country || params.start_date || params.end_date) && (
            <button
              onClick={onReset}
              className="text-xs text-rose-600 dark:text-rose-400 hover:underline font-medium ml-2"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Stable Selection Summary */}
        {selectedCount > 0 && (
          <div className="flex items-center space-x-2 text-xs bg-sky-50 dark:bg-sky-950/70 border border-sky-200 dark:border-sky-900 px-3 py-1 rounded-lg text-sky-800 dark:text-sky-300">
            <span className="font-semibold">{selectedCount}</span> account{selectedCount > 1 ? 's' : ''} selected across pages
          </div>
        )}
      </div>
    </div>
  );
};
