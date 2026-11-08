import { useState, useEffect, useCallback, useRef } from 'react';
import { Account, AccountFilterParams } from '../types';
import { api } from '../services/api';

export function useAccounts(initialParams?: Partial<AccountFilterParams>) {
  const [params, setParams] = useState<AccountFilterParams>({
    page: 1,
    page_size: 10,
    sort_by: 'created_at',
    sort_dir: 'desc',
    search: '',
    status: '',
    country: '',
    plan: '',
    start_date: '',
    end_date: '',
    ...initialParams,
  });

  const [accounts, setAccounts] = useState<Account[]>([]);
  const [totalRecords, setTotalRecords] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stable row selection keyed by account.id
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Cache of selected account objects so multi-page selections retain metadata for CSV export
  const selectedAccountsCache = useRef<Map<string, Account>>(new Map());

  // Keep cache populated with loaded accounts
  useEffect(() => {
    accounts.forEach((acc) => {
      if (selectedIds.has(acc.id)) {
        selectedAccountsCache.current.set(acc.id, acc);
      }
    });
  }, [accounts, selectedIds]);

  // Ref to track in-flight requests and prevent race conditions
  const activeRequestId = useRef(0);

  const fetchAccounts = useCallback(
    async (isBackgroundRefresh: boolean = false) => {
      const requestId = ++activeRequestId.current;

      if (!isBackgroundRefresh) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }
      setError(null);

      try {
        const data = await api.getAccounts(params);

        // Only apply state if this is still the most recent request
        if (requestId === activeRequestId.current) {
          setAccounts(data.accounts);
          setTotalRecords(data.total_records);
          setTotalPages(data.total_pages);
        }
      } catch (err: any) {
        if (requestId === activeRequestId.current) {
          setError(err.message || 'Failed to load accounts');
        }
      } finally {
        if (requestId === activeRequestId.current) {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      }
    },
    [params]
  );

  // Fetch when parameters change
  useEffect(() => {
    fetchAccounts(false);
  }, [fetchAccounts]);

  // Periodic silent refresh (every 30 seconds) per Section 4.10
  useEffect(() => {
    const timer = setInterval(() => {
      fetchAccounts(true);
    }, 30000);

    return () => clearInterval(timer);
  }, [fetchAccounts]);

  // Stable Selection handlers
  const toggleSelectAllCurrentPage = () => {
    const newSelected = new Set(selectedIds);
    const currentPageIds = accounts.map((a) => a.id);
    const allSelected = currentPageIds.length > 0 && currentPageIds.every((id) => newSelected.has(id));

    if (allSelected) {
      currentPageIds.forEach((id) => {
        newSelected.delete(id);
        selectedAccountsCache.current.delete(id);
      });
    } else {
      currentPageIds.forEach((id) => {
        newSelected.add(id);
        const acc = accounts.find((a) => a.id === id);
        if (acc) selectedAccountsCache.current.set(id, acc);
      });
    }
    setSelectedIds(newSelected);
  };

  const toggleSelectAccount = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
      selectedAccountsCache.current.delete(id);
    } else {
      newSelected.add(id);
      const acc = accounts.find((a) => a.id === id);
      if (acc) selectedAccountsCache.current.set(id, acc);
    }
    setSelectedIds(newSelected);
  };

  const clearSelection = () => {
    selectedAccountsCache.current.clear();
    setSelectedIds(new Set());
  };

  const getSelectedAccounts = (): Account[] => {
    return Array.from(selectedAccountsCache.current.values());
  };

  return {
    accounts,
    totalRecords,
    totalPages,
    isLoading,
    isRefreshing,
    error,
    params,
    setParams,
    selectedIds,
    getSelectedAccounts,
    toggleSelectAllCurrentPage,
    toggleSelectAccount,
    clearSelection,
    refresh: () => fetchAccounts(false),
  };
}
