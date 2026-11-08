import React from 'react';
import { Step4Webhook, SaveStatus } from '../types';

interface FormStep4WebhookProps {
  data: Step4Webhook;
  onChange: (field: string, value: string) => void;
  saveStatus: SaveStatus;
  error: string | null;
  onRetry: () => void;
}

export const FormStep4Webhook: React.FC<FormStep4WebhookProps> = ({
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
          Step 4: Webhook Integration
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Configure an endpoint to receive real-time call lifecycle events for this account.
        </p>
      </div>

      {/* Webhook URL Input */}
      <div>
        <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
          Webhook Endpoint URL (Optional)
        </label>
        <input
          type="url"
          value={data.webhook_url}
          onChange={(e) => onChange('webhook_url', e.target.value)}
          placeholder="https://api.yourdomain.com/v1/telephony-events"
          className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
        />
        <p className="text-[11px] text-slate-400 mt-1">
          If provided, URL must begin with <span className="font-mono text-slate-600 dark:text-slate-300">http://</span> or <span className="font-mono text-slate-600 dark:text-slate-300">https://</span>.
        </p>
      </div>

      {/* Save Status / Error Feedback */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 rounded-lg flex items-center justify-between text-xs text-red-700 dark:text-red-300">
          <span>{error}</span>
          <button onClick={onRetry} className="underline font-semibold hover:text-red-900">
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
