import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { StatusIndicator } from './StatusIndicator';

interface HeaderProps {
  title: string;
  showBackButton?: boolean;
  onBack?: () => void;
  rightContent?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ 
  title, 
  showBackButton, 
  onBack, 
  rightContent 
}) => {
  return (
    <header className="px-6 py-4 border-b border-border flex items-center justify-between bg-bg min-h-16">
      <div className="flex items-center gap-4">
        {showBackButton && onBack ? (
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-accent hover:text-accent-hover font-semibold transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="text-base">{title}</span>
          </button>
        ) : (
          <h1 className="text-base font-semibold text-fg">{title}</h1>
        )}
        <StatusIndicator />
      </div>
      
      <div className="flex items-center gap-5">
        {rightContent || (
          <a 
            href="/docs" 
            className="text-xs text-fg-dim hover:text-fg-muted transition-colors"
          >
            Runs docs
          </a>
        )}
      </div>
    </header>
  );
};
