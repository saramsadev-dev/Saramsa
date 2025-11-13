'use client';

import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <div className="w-10 h-10 rounded-lg bg-muted animate-pulse" />
    );
  }

  const isLight = theme === 'light';
  const isDark = theme === 'dark';

  return (
    <button
      onClick={() => setTheme(isLight ? 'dark' : 'light')}
      className="p-3 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 dark:border-gray-700/50 hover:bg-white/20 dark:hover:bg-gray-800/80 transition-all duration-300 group"
      aria-label={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-white group-hover:text-saramsa-brand transition-colors" />
      ) : (
        <Moon className="w-5 h-5 text-gray-600 group-hover:text-saramsa-brand transition-colors" />
      )}
    </button>
  );
}
