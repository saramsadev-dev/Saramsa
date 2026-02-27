'use client';

interface NavigationTabsProps {
  activeView: 'dashboard' | 'worklist';
  onViewChange: (view: 'dashboard' | 'worklist') => void;
}

export function NavigationTabs({ activeView, onViewChange }: NavigationTabsProps) {
  return (
    <div className="flex bg-secondary/70 rounded-2xl p-1 border border-border/60 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)]">
      <button
        onClick={() => onViewChange('dashboard')}
        className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
          activeView === 'dashboard' 
            ? 'bg-background/90 text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
            : 'text-muted-foreground hover:text-foreground'
        }`}
      >
        Dashboard
      </button>
      <button
        onClick={() => onViewChange('worklist')}
        className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
          activeView === 'worklist' 
            ? 'bg-background/90 text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
            : 'text-muted-foreground hover:text-foreground'
        }`}
      >
        Worklist View
      </button>
    </div>
  );
}
