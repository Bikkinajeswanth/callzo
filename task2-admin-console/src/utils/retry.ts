export interface RetryOptions {
  maxRetries?: number;
  initialDelayMs?: number;
  backoffFactor?: number;
  onRetry?: (attempt: number, error: any) => void;
}

export async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelayMs = 600,
    backoffFactor = 2,
    onRetry,
  } = options;

  let attempt = 0;
  let delay = initialDelayMs;

  while (true) {
    try {
      return await fn();
    } catch (error) {
      attempt++;
      if (attempt >= maxRetries) {
        throw error;
      }
      if (onRetry) {
        onRetry(attempt, error);
      }
      // Add jitter to avoid thundering herds
      const jitter = Math.random() * 150;
      await new Promise((resolve) => setTimeout(resolve, delay + jitter));
      delay *= backoffFactor;
    }
  }
}
