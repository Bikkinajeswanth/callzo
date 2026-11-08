import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';

export function App() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('callzo_theme');
      if (stored) return stored === 'dark';
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('callzo_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('callzo_theme', 'light');
    }
  }, [isDarkMode]);

  const handleToggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    // Short visual indicator for user feedback
    setTimeout(() => {
      setIsRefreshing(false);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      <Header
        isDarkMode={isDarkMode}
        onToggleTheme={handleToggleTheme}
        isRefreshing={isRefreshing}
        onRefresh={handleManualRefresh}
      />
      <DashboardPage
        isRefreshing={isRefreshing}
        onRefreshAll={handleManualRefresh}
      />
    </div>
  );
}

export default App;
