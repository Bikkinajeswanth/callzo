import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: string;
  iconBg?: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  trend,
  icon,
  isLoading,
}) => {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm transition hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3">
        {isLoading ? (
          <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-24 animate-pulse"></div>
        ) : (
          <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
            {value}
          </div>
        )}

        <div className="mt-1 flex items-center space-x-2 text-xs">
          {trend && (
            <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center">
              ↑ {trend}
            </span>
          )}
          {subValue && (
            <span className="text-slate-500 dark:text-slate-400">{subValue}</span>
          )}
        </div>
      </div>
    </div>
  );
};
