import React, { useEffect, useRef } from 'react';
import { useSettingsDraft } from '../hooks/useSettingsDraft';
import { FormStep1Personal } from './FormStep1Personal';
import { FormStep2Subscription } from './FormStep2Subscription';
import { FormStep3Limits } from './FormStep3Limits';
import { FormStep4Webhook } from './FormStep4Webhook';

interface SettingsWizardModalProps {
  accountId: string | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const SettingsWizardModal: React.FC<SettingsWizardModalProps> = ({
  accountId,
  onClose,
  onSuccess,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  const {
    draft,
    currentStep,
    setCurrentStep,
    saveStatus,
    stepErrors,
    isLoading,
    isSubmitting,
    submitSuccess,
    generalError,
    updateStepField,
    retryStepSave,
    submitWizard,
  } = useSettingsDraft(accountId);

  // Keyboard accessibility: Escape key to close modal per Section 4.11
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!accountId) return null;

  const steps = [
    { number: 1, title: 'Personal' },
    { number: 2, title: 'Subscription' },
    { number: 3, title: 'Limits' },
    { number: 4, title: 'Webhook' },
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="wizard-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in"
    >
      <div
        ref={modalRef}
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl w-full max-w-lg overflow-hidden flex flex-col transition"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 id="wizard-modal-title" className="text-sm font-bold text-slate-900 dark:text-white">
              Account Configuration Wizard
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Editing tenant <span className="font-mono text-sky-600 dark:text-sky-400">{accountId}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close settings wizard"
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            ✕
          </button>
        </div>

        {/* Step Progress Indicators */}
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
          {steps.map((s) => {
            const isActive = currentStep === s.number;
            const hasError = stepErrors[s.number] !== null;
            const isSaved = saveStatus[s.number] === 'saved';

            return (
              <button
                key={s.number}
                type="button"
                onClick={() => setCurrentStep(s.number)}
                className={`flex items-center space-x-1.5 text-xs transition font-medium focus:outline-none focus:ring-1 focus:ring-sky-500 rounded px-1.5 py-0.5 ${
                  isActive
                    ? 'text-sky-600 dark:text-sky-400 font-bold'
                    : hasError
                    ? 'text-red-500 dark:text-red-400 font-semibold'
                    : isSaved
                    ? 'text-slate-700 dark:text-slate-300'
                    : 'text-slate-400'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${
                    hasError
                      ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300'
                      : isActive
                      ? 'bg-sky-600 text-white'
                      : isSaved
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  {hasError ? '!' : isSaved && !isActive ? '✓' : s.number}
                </span>
                <span className="hidden sm:inline">{s.title}</span>
              </button>
            );
          })}
        </div>

        {/* Modal Body / Active Step Content */}
        <div className="p-6 flex-1 min-h-[260px]">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center h-48 space-y-3">
              <div className="w-8 h-8 border-3 border-sky-200 dark:border-sky-950 border-t-sky-600 rounded-full animate-spin"></div>
              <p className="text-xs text-slate-500">Restoring saved draft from server...</p>
            </div>
          ) : submitSuccess ? (
            <div className="text-center py-8 space-y-3">
              <div className="w-12 h-12 mx-auto rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl">
                ✓
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Configuration Activated
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                All 4 steps were saved and successfully verified with the Callzo platform.
              </p>
              <button
                onClick={() => {
                  onSuccess();
                  onClose();
                }}
                className="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
              >
                Done
              </button>
            </div>
          ) : (
            <div>
              {currentStep === 1 && (
                <FormStep1Personal
                  data={draft.step1}
                  onChange={(f, v) => updateStepField(1, f, v)}
                  saveStatus={saveStatus[1]}
                  error={stepErrors[1]}
                  onRetry={() => retryStepSave(1)}
                />
              )}
              {currentStep === 2 && (
                <FormStep2Subscription
                  data={draft.step2}
                  onChange={(f, v) => updateStepField(2, f, v)}
                  saveStatus={saveStatus[2]}
                  error={stepErrors[2]}
                  onRetry={() => retryStepSave(2)}
                />
              )}
              {currentStep === 3 && (
                <FormStep3Limits
                  data={draft.step3}
                  onChange={(f, v) => updateStepField(3, f, v)}
                  saveStatus={saveStatus[3]}
                  error={stepErrors[3]}
                  onRetry={() => retryStepSave(3)}
                />
              )}
              {currentStep === 4 && (
                <FormStep4Webhook
                  data={draft.step4}
                  onChange={(f, v) => updateStepField(4, f, v)}
                  saveStatus={saveStatus[4]}
                  error={stepErrors[4]}
                  onRetry={() => retryStepSave(4)}
                />
              )}

              {/* General Form Error Announcement */}
              {generalError && (
                <div className="mt-4 p-3 bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-900 rounded-lg text-xs text-red-700 dark:text-red-300">
                  {generalError}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        {!submitSuccess && !isLoading && (
          <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCurrentStep((prev) => Math.max(1, prev - 1))}
              disabled={currentStep === 1}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-700 transition"
            >
              Back
            </button>

            <div className="flex items-center space-x-2">
              {currentStep < 4 ? (
                <button
                  type="button"
                  onClick={() => setCurrentStep((prev) => Math.min(4, prev + 1))}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 transition focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  Continue →
                </button>
              ) : (
                <button
                  type="button"
                  onClick={submitWizard}
                  disabled={isSubmitting}
                  className="px-5 py-1.5 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white shadow-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 flex items-center space-x-1.5"
                >
                  {isSubmitting ? (
                    <>
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <span>Submit & Apply</span>
                  )}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
