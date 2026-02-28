'use client';

import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <div className="w-10 h-10 rounded-xl bg-muted animate-pulse" />
    );
  }

  const isLight = theme === 'light';
  const isDark = theme === 'dark';

  return (
    <Button
      onClick={() => setTheme(isLight ? 'dark' : 'light')}
      variant="ghost"
      size="icon"
      className="h-11 w-11 rounded-full bg-card/10 backdrop-blur-sm border border-white/20 dark:border-border/60 hover:bg-card/20 dark:hover:bg-accent/60 transition-all duration-300 group"
      aria-label={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
    >
      {isDark ? (
        <Sun className="w-5 h-5 text-white group-hover:text-saramsa-brand transition-colors" />
      ) : (
        <Moon className="w-5 h-5 text-muted-foreground group-hover:text-saramsa-brand transition-colors" />
      )}
    </Button>
  );
}
