import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { MonthlyTrend } from '../types';
import { formatNumber, formatCents } from '../utils/formatters';

interface AnalyticsChartsProps {
  trends?: MonthlyTrend[];
  isLoading: boolean;
  retryAttempt: number;
  error: string | null;
  onRetry: () => void;
}

export const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({
  trends = [],
  isLoading,
  retryAttempt,
  error,
  onRetry,
}) => {
  const [activeMetric, setActiveMetric] = useState<'minutes' | 'sms' | 'cost' | 'signups'>('minutes');

  // 1. Error State with manual Retry per Section 4.6
  if (error) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-red-200 dark:border-red-900/50 rounded-xl p-8 shadow-sm text-center">
        <div className="w-12 h-12 mx-auto rounded-full bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 flex items-center justify-center mb-3">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">
          Analytics Engine Notice
        </h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
          {error}
        </p>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
          (The mock API simulates a 20% random HTTP 500 error rate for resilience testing).
        </p>
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Retry Analytics</span>
        </button>
      </div>
    );
  }

  // 2. Loading State with Retry Announcement
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center min-h-[340px]">
        <div className="w-10 h-10 border-4 border-sky-200 dark:border-sky-950 border-t-sky-600 rounded-full animate-spin"></div>
        <p className="mt-4 text-sm font-medium text-slate-600 dark:text-slate-300">
          {retryAttempt > 0
            ? `Retrying analytics request (Attempt ${retryAttempt} of 3 with exponential backoff)...`
            : 'Aggregating telephony trends...'}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      {/* Chart Header & Metric Selectors */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-white">
            Usage Trends & Telephony Metrics
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Historical progression across voice minutes, SMS volume, and billed costs.
          </p>
        </div>

        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-medium">
          <button
            onClick={() => setActiveMetric('minutes')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeMetric === 'minutes'
                ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Voice Minutes
          </button>
          <button
            onClick={() => setActiveMetric('sms')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeMetric === 'sms'
                ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            SMS
          </button>
          <button
            onClick={() => setActiveMetric('cost')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeMetric === 'cost'
                ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Cost ($)
          </button>
          <button
            onClick={() => setActiveMetric('signups')}
            className={`px-3 py-1.5 rounded-md transition ${
              activeMetric === 'signups'
                ? 'bg-white dark:bg-slate-700 text-sky-600 dark:text-sky-300 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Signups
          </button>
        </div>
      </div>

      {/* Chart Visualizations */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {activeMetric === 'cost' ? (
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-800" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis
                stroke="#94a3b8"
                fontSize={12}
                tickLine={false}
                tickFormatter={(v) => `$${Math.round(v / 100)}`}
              />
              <Tooltip
                formatter={(value: any) => [formatCents(Number(value)), 'Billed Cost']}
                contentStyle={{
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Area
                type="monotone"
                dataKey="cost_cents"
                stroke="#0284c7"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#costGradient)"
              />
            </AreaChart>
          ) : activeMetric === 'signups' ? (
            <BarChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-800" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} />
              <Tooltip
                formatter={(val: any) => [formatNumber(Number(val)), 'Signups']}
                contentStyle={{
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Bar dataKey="signups" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : (
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="metricGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-800" />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis
                stroke="#94a3b8"
                fontSize={12}
                tickLine={false}
                tickFormatter={(v) => formatNumber(v)}
              />
              <Tooltip
                formatter={(value: any) => [
                  formatNumber(Number(value)),
                  activeMetric === 'minutes' ? 'Call Minutes' : 'SMS Messages',
                ]}
                contentStyle={{
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                  fontSize: '12px',
                }}
                labelStyle={{ color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}
                itemStyle={{ color: '#f8fafc' }}
              />
              <Area
                type="monotone"
                dataKey={activeMetric}
                stroke="#0ea5e9"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#metricGradient)"
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
