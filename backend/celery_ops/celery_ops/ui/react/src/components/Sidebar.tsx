import React from 'react';
import { Grid3X3, Activity, Users, List } from 'lucide-react';

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const navItems = [
  { id: 'tasks', label: 'Tasks', icon: Grid3X3 },
  { id: 'runs', label: 'Runs', icon: Activity },
  { id: 'workers', label: 'Workers', icon: Users },
  { id: 'queues', label: 'Queues', icon: List },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSectionChange }) => {
  return (
    <aside className="w-60 bg-bg-sidebar border-r border-border flex-shrink-0 flex flex-col">
      <div className="p-5 border-b border-border flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center font-bold text-white flex-shrink-0">
          Co
        </div>
        <div>
          <div className="font-semibold text-fg">Celery Ops</div>
          <div className="text-xs text-fg-muted">Environment: default</div>
        </div>
      </div>
      
      <nav className="py-4 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-all border-l-3 ${
                isActive
                  ? 'text-fg bg-accent-bg border-l-accent'
                  : 'text-fg-muted border-l-transparent hover:text-fg-secondary hover:bg-bg-hover'
              }`}
            >
              <Icon className={`w-4.5 h-4.5 flex-shrink-0 ${isActive ? 'opacity-100' : 'opacity-70'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-border text-xs text-fg-dim text-center">
        Ops-only, best-effort. <a href="/docs" className="text-accent hover:text-accent-hover">API</a>
      </div>
    </aside>
  );
};
