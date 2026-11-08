import React from 'react';
import { Step2Subscription, SaveStatus, AccountPlan, CountryCode } from '../types';

interface FormStep2SubscriptionProps {
  data: Step2Subscription;
  onChange: (field: string, value: string) => void;
  saveStatus: SaveStatus;
  error: string | null;
  onRetry: () => void;
}

export const FormStep2Subscription: React.FC<FormStep2SubscriptionProps> = ({
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
          Step 2: Subscription & Billing
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Select subscription tier and verified billing country jurisdiction.
        </p>
      </div>

      {/* Plan Selection */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          Subscription Plan
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(['basic', 'pro', 'enterprise'] as AccountPlan[]).map((plan) => (
            <button
              key={plan}
              type="button"
              onClick={() => onChange('plan', plan)}
              className={`py-2 px-3 text-xs font-medium rounded-lg border capitalize text-center transition ${
                data.plan === plan
                  ? 'border-sky-600 bg-sky-50 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 font-semibold shadow-sm'
                  : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
              }`}
            >
              {plan}
            </button>
          ))}
        </div>
      </div>

      {/* Billing Country Selection */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          Billing Country <span className="text-red-500">*</span>
        </label>
        <select
          value={data.billing_country}
          onChange={(e) => onChange('billing_country', e.target.value as CountryCode)}
          className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
        >
          <option value="US">United States (US)</option>
          <option value="IN">India (IN)</option>
          <option value="GB">United Kingdom (GB)</option>
          <option value="CA">Canada (CA)</option>
          <option value="AU">Australia (AU)</option>
        </select>
      </div>

      {/* Deliberate Section 4.8 Handling & UX Alert */}
      {error && (
        <div className="p-3 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-900 rounded-lg text-xs space-y-2">
          <div className="flex items-start space-x-2 text-amber-800 dark:text-amber-200">
            <span className="text-amber-600 font-bold">⚠️</span>
            <div>
              <p className="font-semibold">Server-Side Validation Condition Detected</p>
              <p className="mt-0.5 text-amber-700 dark:text-amber-300">{error}</p>
            </div>
          </div>
          <div className="pt-1 flex items-center justify-between border-t border-amber-200/60 dark:border-amber-900/60">
            <span className="text-[11px] text-amber-600 dark:text-amber-400">
              Preserved all other step data. Click to re-verify and confirm:
            </span>
            <button
              onClick={onRetry}
              className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded text-xs shadow-sm transition"
            >
              Re-verify Country
            </button>
          </div>
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
