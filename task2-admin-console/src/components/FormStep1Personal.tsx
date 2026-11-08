import React from 'react';
import { Step1Personal, SaveStatus } from '../types';

interface FormStep1PersonalProps {
  data: Step1Personal;
  onChange: (field: string, value: string) => void;
  saveStatus: SaveStatus;
  error: string | null;
  onRetry: () => void;
}

export const FormStep1Personal: React.FC<FormStep1PersonalProps> = ({
  data,
  onChange,
  saveStatus,
  error,
  onRetry,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
          Step 1: Personal Details
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Provide the primary administrative contact for this account.
        </p>
      </div>

      {/* Name Input */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          Full Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={data.name}
          onChange={(e) => onChange('name', e.target.value)}
          placeholder="e.g. Sarah Jenkins"
          className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
        />
      </div>

      {/* Email Input */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          Email Address <span className="text-red-500">*</span>
        </label>
        <input
          type="email"
          value={data.email}
          onChange={(e) => onChange('email', e.target.value)}
          placeholder="e.g. sarah@enterprise.com"
          className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
        />
        <p className="text-[11px] text-slate-400 mt-1">Must contain an '@' symbol.</p>
      </div>

      {/* Save Status / Error Feedback */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-xs text-red-700 dark:text-red-300">
          <span>{error}</span>
          <button
            onClick={onRetry}
            className="underline font-semibold hover:text-red-900"
          >
            Retry Save
          </button>
        </div>
      )}

      {saveStatus === 'saving' && (
        <div className="text-xs text-sky-600 dark:text-sky-400 flex items-center space-x-1.5">
          <div className="w-2.5 h-2.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Autosaving draft...</span>
        </div>
      )}

      {saveStatus === 'saved' && !error && (
        <div className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center space-x-1">
          <span>✓ Draft saved automatically</span>
        </div>
      )}
    </div>
  );
};
