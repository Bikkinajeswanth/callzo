import { useState, useEffect, useCallback, useRef } from 'react';
import { SummaryData } from '../types';
import { api } from '../services/api';
import { fetchWithRetry } from '../utils/retry';

export function useSummary(startDate?: string, endDate?: string) {
  const [data, setData] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const activeRequestId = useRef(0);

  const loadSummary = useCallback(async () => {
    const requestId = ++activeRequestId.current;
    setIsLoading(true);
    setError(null);
    setRetryAttempt(0);

    try {
      const result = await fetchWithRetry<SummaryData>(
        () => api.getAccountsSummary(startDate, endDate),
        {
          maxRetries: 3,
          initialDelayMs: 600,
          backoffFactor: 1.8,
          onRetry: (attempt) => {
            if (requestId === activeRequestId.current) {
              setRetryAttempt(attempt);
            }
          },
        }
      );

      if (requestId === activeRequestId.current) {
        setData(result);
        setError(null);
      }
    } catch (err: any) {
      if (requestId === activeRequestId.current) {
        setError(err.message || 'Analytics metrics temporarily unavailable.');
      }
    } finally {
      if (requestId === activeRequestId.current) {
        setIsLoading(false);
      }
    }
  }, [startDate, endDate]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  return {
    data,
    isLoading,
    retryAttempt,
    error,
    reload: loadSummary,
  };
}
