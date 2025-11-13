'use client';

interface NavigationTabsProps {
  activeView: 'dashboard' | 'worklist';
  onViewChange: (view: 'dashboard' | 'worklist') => void;
}

export function NavigationTabs({ activeView, onViewChange }: NavigationTabsProps) {
  return (
    <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
      <button
        onClick={() => onViewChange('dashboard')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          activeView === 'dashboard' 
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' 
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }`}
      >
        Dashboard
      </button>
      <button
        onClick={() => onViewChange('worklist')}
        className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          activeView === 'worklist' 
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' 
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }`}
      >
        Worklist View
      </button>
    </div>
  );
}
