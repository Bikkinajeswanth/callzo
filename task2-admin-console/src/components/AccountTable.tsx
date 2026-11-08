import React from 'react';
import { Account, AccountFilterParams } from '../types';
import { formatCents, formatNumber, formatTimeAgo } from '../utils/formatters';

interface AccountTableProps {
  accounts: Account[];
  isLoading: boolean;
  totalRecords: number;
  totalPages: number;
  params: AccountFilterParams;
  onParamChange: (updated: Partial<AccountFilterParams>) => void;
  selectedIds: Set<string>;
  selectedAccounts?: Account[];
  onToggleSelectAll: () => void;
  onToggleSelectOne: (id: string) => void;
  onOpenSettings: (accountId: string) => void;
  onViewDetails?: (accountId: string) => void;
}

export const AccountTable: React.FC<AccountTableProps> = ({
  accounts,
  isLoading,
  totalRecords,
  totalPages,
  params,
  onParamChange,
  selectedIds,
  selectedAccounts = [],
  onToggleSelectAll,
  onToggleSelectOne,
  onOpenSettings,
  onViewDetails,
}) => {
  const currentPageIds = accounts.map((a) => a.id);
  const isAllCurrentPageSelected =
    currentPageIds.length > 0 && currentPageIds.every((id) => selectedIds.has(id));
  const isPartiallySelected =
    currentPageIds.some((id) => selectedIds.has(id)) && !isAllCurrentPageSelected;

  const handleSort = (field: string) => {
    if (params.sort_by === field) {
      onParamChange({ sort_dir: params.sort_dir === 'asc' ? 'desc' : 'asc' });
    } else {
      onParamChange({ sort_by: field, sort_dir: 'asc' });
    }
  };

  const getSortIcon = (field: string) => {
    if (params.sort_by !== field) return '↕';
    return params.sort_dir === 'asc' ? '↑' : '↓';
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            Active
          </span>
        );
      case 'trial':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
            Trial
          </span>
        );
      case 'suspended':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
            Suspended
          </span>
        );
      default:
        return <span>{status}</span>;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm overflow-hidden">
      {/* Table Title and Summary Info */}
      <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              Customer Accounts Directory
            </h2>
            {selectedIds.size > 0 && (
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-100 dark:bg-sky-950 text-sky-800 dark:text-sky-300">
                {selectedIds.size} Selected
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Showing {accounts.length} of {totalRecords} accounts
          </p>
        </div>

        {/* Bulk Actions & Page Size Selector */}
        <div className="flex items-center space-x-3">
          {selectedIds.size > 0 && (
            <button
              onClick={() => {
                // Use selectedAccounts cache if populated, otherwise fall back to matching on current page
                const exportList = selectedAccounts.length > 0
                  ? selectedAccounts
                  : accounts.filter((a) => selectedIds.has(a.id));

                const headers = 'ID,Name,Email,Company,Country,Plan,Status,Minutes,SMS,Cost_USD';
                const rows = exportList.map(
                  (a) =>
                    `${a.id},"${a.name}","${a.email}","${a.company || ''}",${a.country},${a.plan},${a.status},${a.monthly_minutes},${a.monthly_sms},${(a.cost_cents / 100).toFixed(2)}`
                );
                const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
                const encodedUri = encodeURI(csvContent);
                const link = document.createElement('a');
                link.setAttribute('href', encodedUri);
                link.setAttribute(
                  'download',
                  `callzo_selected_tenants_${new Date().toISOString().substring(0, 10)}.csv`
                );
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-sky-600 hover:bg-sky-700 text-white shadow-sm transition flex items-center space-x-1"
              title={`Export ${selectedIds.size} selected account(s) to CSV`}
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Export CSV ({selectedIds.size})</span>
            </button>
          )}

          <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
            <span>Rows:</span>
            <select
              value={params.page_size}
              onChange={(e) => onParamChange({ page_size: Number(e.target.value), page: 1 })}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
      </div>

      {/* Responsive Table Container */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs">
          <thead className="bg-slate-50 dark:bg-slate-800/60 font-semibold text-slate-600 dark:text-slate-300">
            <tr>
              {/* Select All Checkbox */}
              <th scope="col" className="px-4 py-3 w-10">
                <input
                  type="checkbox"
                  checked={isAllCurrentPageSelected}
                  ref={(input) => {
                    if (input) input.indeterminate = isPartiallySelected;
                  }}
                  onChange={onToggleSelectAll}
                  aria-label="Select all accounts on this page"
                  className="rounded border-slate-300 text-sky-600 focus:ring-sky-500 w-4 h-4 cursor-pointer"
                />
              </th>

              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('id')}>
                Account ID {getSortIcon('id')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('name')}>
                Customer {getSortIcon('name')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('company')}>
                Company {getSortIcon('company')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('country')}>
                Country {getSortIcon('country')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('plan')}>
                Plan {getSortIcon('plan')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('status')}>
                Status {getSortIcon('status')}
              </th>
              <th scope="col" className="px-4 py-3 text-right cursor-pointer hover:text-slate-900" onClick={() => handleSort('monthly_minutes')}>
                Minutes {getSortIcon('monthly_minutes')}
              </th>
              <th scope="col" className="px-4 py-3 text-right cursor-pointer hover:text-slate-900" onClick={() => handleSort('monthly_sms')}>
                SMS {getSortIcon('monthly_sms')}
              </th>
              <th scope="col" className="px-4 py-3 text-right cursor-pointer hover:text-slate-900" onClick={() => handleSort('cost_cents')}>
                Cost {getSortIcon('cost_cents')}
              </th>
              <th scope="col" className="px-4 py-3 cursor-pointer hover:text-slate-900" onClick={() => handleSort('last_active')}>
                Last Active {getSortIcon('last_active')}
              </th>
              <th scope="col" className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-900">
            {isLoading ? (
              // Skeleton loading state
              Array.from({ length: params.page_size }).map((_, idx) => (
                <tr key={idx} className="animate-pulse">
                  <td className="px-4 py-3.5"><div className="h-4 w-4 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-16 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-28 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-20 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-8 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-12 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-14 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5 text-right"><div className="h-4 w-12 bg-slate-200 dark:bg-slate-800 rounded ml-auto"></div></td>
                  <td className="px-4 py-3.5 text-right"><div className="h-4 w-10 bg-slate-200 dark:bg-slate-800 rounded ml-auto"></div></td>
                  <td className="px-4 py-3.5 text-right"><div className="h-4 w-14 bg-slate-200 dark:bg-slate-800 rounded ml-auto"></div></td>
                  <td className="px-4 py-3.5"><div className="h-4 w-16 bg-slate-200 dark:bg-slate-800 rounded"></div></td>
                  <td className="px-4 py-3.5 text-center"><div className="h-6 w-14 bg-slate-200 dark:bg-slate-800 rounded mx-auto"></div></td>
                </tr>
              ))
            ) : accounts.length === 0 ? (
              // Empty State
              <tr>
                <td colSpan={12} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                  <div className="w-10 h-10 mx-auto mb-2 text-slate-400">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <p className="font-medium text-sm">No accounts found</p>
                  <p className="text-xs text-slate-400">Try adjusting your search criteria or resetting filters.</p>
                </td>
              </tr>
            ) : (
              // Data Rows
              accounts.map((acc) => {
                const isSelected = selectedIds.has(acc.id);
                return (
                  <tr
                    key={acc.id}
                    className={`transition hover:bg-slate-50/80 dark:hover:bg-slate-800/40 ${
                      isSelected ? 'bg-sky-50/70 dark:bg-sky-950/40' : ''
                    }`}
                  >
                    {/* Row Checkbox with Stable Selection */}
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => onToggleSelectOne(acc.id)}
                        aria-label={`Select account ${acc.name}`}
                        className="rounded border-slate-300 text-sky-600 focus:ring-sky-500 w-4 h-4 cursor-pointer"
                      />
                    </td>

                    <td className="px-4 py-3 font-mono font-medium text-slate-600 dark:text-slate-400">
                      {acc.id}
                    </td>

                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900 dark:text-white">{acc.name}</div>
                      <div className="text-[11px] text-slate-400">{acc.email}</div>
                    </td>

                    <td className="px-4 py-3 font-medium text-slate-700 dark:text-slate-300">
                      {acc.company}
                    </td>

                    <td className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">
                      {acc.country}
                    </td>

                    <td className="px-4 py-3 capitalize text-slate-700 dark:text-slate-300">
                      {acc.plan}
                    </td>

                    <td className="px-4 py-3">
                      {getStatusBadge(acc.status)}
                    </td>

                    <td className="px-4 py-3 text-right font-medium text-slate-900 dark:text-slate-100">
                      {formatNumber(acc.monthly_minutes)}
                    </td>

                    <td className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                      {formatNumber(acc.monthly_sms)}
                    </td>

                    <td className="px-4 py-3 text-right font-semibold text-sky-600 dark:text-sky-400">
                      {formatCents(acc.cost_cents)}
                    </td>

                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      {formatTimeAgo(acc.last_active)}
                    </td>

                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {onViewDetails && (
                          <button
                            onClick={() => onViewDetails(acc.id)}
                            className="px-2.5 py-1 text-xs font-semibold rounded bg-slate-50 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition focus:outline-none focus:ring-2 focus:ring-slate-400"
                            title="View account details"
                          >
                            View
                          </button>
                        )}
                        <button
                          onClick={() => onOpenSettings(acc.id)}
                          className="px-2.5 py-1 text-xs font-semibold rounded bg-sky-50 hover:bg-sky-100 dark:bg-sky-950/60 dark:hover:bg-sky-900 text-sky-700 dark:text-sky-300 transition focus:outline-none focus:ring-2 focus:ring-sky-500"
                          title="Configure 4-Step Account Settings"
                        >
                          Settings
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <div>
          Page <span className="font-semibold text-slate-800 dark:text-slate-200">{params.page}</span> of{' '}
          <span className="font-semibold text-slate-800 dark:text-slate-200">{totalPages || 1}</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onParamChange({ page: params.page - 1 })}
            disabled={params.page <= 1 || isLoading}
            className="px-3 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-700 font-medium transition"
          >
            Previous
          </button>
          <button
            onClick={() => onParamChange({ page: params.page + 1 })}
            disabled={params.page >= totalPages || isLoading}
            className="px-3 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-700 font-medium transition"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};
