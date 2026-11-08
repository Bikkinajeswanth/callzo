import { useState, useEffect, useRef, useCallback } from 'react';
import { SettingsDraft, SaveStatus } from '../types';
import { api } from '../services/api';

export function useSettingsDraft(accountId: string | null) {
  const [draft, setDraft] = useState<SettingsDraft>({
    step1: { name: '', email: '' },
    step2: { plan: 'pro', billing_country: 'US' },
    step3: { minutes_cap: null, sms_cap: null },
    step4: { webhook_url: '' },
    submitted: false,
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [saveStatus, setSaveStatus] = useState<Record<number, SaveStatus>>({
    1: 'idle',
    2: 'idle',
    3: 'idle',
    4: 'idle',
  });
  const [stepErrors, setStepErrors] = useState<Record<number, string | null>>({
    1: null,
    2: null,
    3: null,
    4: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Debounce timers per step
  const debounceTimers = useRef<Record<number, NodeJS.Timeout | null>>({
    1: null,
    2: null,
    3: null,
    4: null,
  });

  // Load existing draft when opening modal
  useEffect(() => {
    if (!accountId) return;

    let isMounted = true;
    setIsLoading(true);
    setGeneralError(null);
    setSubmitSuccess(false);

    api
      .getAccountSettings(accountId)
      .then((data) => {
        if (isMounted) {
          setDraft(data);
          setSaveStatus({ 1: 'saved', 2: 'saved', 3: 'saved', 4: 'saved' });
        }
      })
      .catch((err) => {
        if (isMounted) {
          setGeneralError(err.message || 'Failed to load account settings');
        }
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
      // Clear timers
      Object.values(debounceTimers.current).forEach((t) => t && clearTimeout(t));
    };
  }, [accountId]);

  // Client validation for each step
  const validateStep = (step: number, data: any): string | null => {
    if (step === 1) {
      if (!data.name || !data.name.trim()) return 'Name is required';
      if (!data.email || !data.email.includes('@')) return 'A valid email containing @ is required';
    } else if (step === 2) {
      if (!data.billing_country) return 'Billing country is required';
      if (!['US', 'IN', 'GB', 'CA', 'AU'].includes(data.billing_country)) {
        return 'Billing country must be one of: US, IN, GB, CA, AU';
      }
    } else if (step === 3) {
      if (data.minutes_cap !== null && data.minutes_cap !== '' && Number(data.minutes_cap) < 0) {
        return 'Minutes cap cannot be negative';
      }
      if (data.sms_cap !== null && data.sms_cap !== '' && Number(data.sms_cap) < 0) {
        return 'SMS cap cannot be negative';
      }
    } else if (step === 4) {
      if (data.webhook_url && !data.webhook_url.startsWith('http://') && !data.webhook_url.startsWith('https://')) {
        return 'Webhook URL must start with http:// or https://';
      }
    }
    return null;
  };

  // Perform save to API
  const saveStepToApi = useCallback(
    async (step: number, stepData: any, isExplicitRetry: boolean = false) => {
      if (!accountId) return;

      const clientErr = validateStep(step, stepData);
      if (clientErr) {
        setStepErrors((prev) => ({ ...prev, [step]: clientErr }));
        setSaveStatus((prev) => ({ ...prev, [step]: 'error' }));
        return;
      }

      setSaveStatus((prev) => ({ ...prev, [step]: 'saving' }));
      setStepErrors((prev) => ({ ...prev, [step]: null }));

      try {
        const payloadToSend = {
          ...stepData,
          ...(isExplicitRetry ? { _revalidated: true } : {}),
        };

        await api.saveAccountSettingsStep(accountId, step, payloadToSend);
        setSaveStatus((prev) => ({ ...prev, [step]: 'saved' }));
        setStepErrors((prev) => ({ ...prev, [step]: null }));
      } catch (err: any) {
        const errMsg = err.message || `Failed to save Step ${step}`;

        // Handle Deliberate Step 4 -> Step 2 validation behavior per Section 4.8
        if (errMsg.includes('billing_country is required')) {
          setStepErrors((prev) => ({
            ...prev,
            2: 'Server validation warning: billing_country verification required after webhook configuration.',
          }));
          setSaveStatus((prev) => ({ ...prev, 2: 'error' }));
        } else {
          setStepErrors((prev) => ({ ...prev, [step]: errMsg }));
          setSaveStatus((prev) => ({ ...prev, [step]: 'error' }));
        }
      }
    },
    [accountId]
  );

  // Autosave update triggered from UI
  const updateStepField = (step: number, field: string, value: any) => {
    const stepKey = `step${step}` as keyof SettingsDraft;
    const currentStepData = { ...(draft[stepKey] as any), [field]: value };

    // 1. Immediately update local state to preserve responsiveness and prevent losing user keystrokes
    setDraft((prev) => ({
      ...prev,
      [stepKey]: currentStepData,
    }));

    // Mark as unsaved/idle
    setSaveStatus((prev) => ({ ...prev, [step]: 'idle' }));
    setStepErrors((prev) => ({ ...prev, [step]: null }));

    // 2. Debounce the network autosave (800ms)
    if (debounceTimers.current[step]) {
      clearTimeout(debounceTimers.current[step]!);
    }

    debounceTimers.current[step] = setTimeout(() => {
      saveStepToApi(step, currentStepData);
    }, 800);
  };

  // Explicit retry for a failed step
  const retryStepSave = (step: number) => {
    const stepKey = `step${step}` as keyof SettingsDraft;
    saveStepToApi(step, draft[stepKey], true);
  };

  // Submit all 4 steps
  const submitWizard = async () => {
    if (!accountId) return;

    // Check if any step is in error
    const hasErrors = Object.values(stepErrors).some((e) => e !== null);
    if (hasErrors) {
      setGeneralError('Please resolve all validation errors before final submission.');
      return;
    }

    setIsSubmitting(true);
    setGeneralError(null);

    try {
      await api.submitAccountSettings(accountId);
      setSubmitSuccess(true);
      setDraft((prev) => ({ ...prev, submitted: true }));
    } catch (err: any) {
      setGeneralError(err.message || 'Failed to submit account settings.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
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
  };
}
