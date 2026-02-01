import React, { useState, useEffect } from 'react';
import { Header } from '../components/Header';
import { RunsList } from './runs/RunsList';
import { RunDetail } from './runs/RunDetail';
import { Task } from '../types';

export const RunsView: React.FC = () => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const handleTaskSelect = (task: Task) => {
    setSelectedTask(task);
  };

  const handleBack = () => {
    setSelectedTask(null);
  };

  if (selectedTask) {
    return (
      <RunDetail 
        task={selectedTask} 
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      <Header 
        title="Runs"
        rightContent={
          <a 
            href="/docs" 
            className="text-xs text-fg-dim hover:text-fg-muted transition-colors"
          >
            Runs docs
          </a>
        }
      />
      
      {/* Filter Bar */}
      <div className="px-6 py-3 border-b border-border flex items-center gap-2 bg-bg">
        <div className="flex items-center gap-2 bg-bg-elevated border border-border rounded-md px-3 py-1.5 min-w-56">
          <svg className="w-3.5 h-3.5 text-fg-dim" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="Describe your filters..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-transparent border-none outline-none text-fg text-sm flex-1 placeholder-fg-dim"
          />
        </div>
        
        <button className="flex items-center gap-2 px-3 py-1.5 text-xs border border-border rounded-full bg-bg-elevated text-fg-muted hover:text-fg-secondary hover:border-fg-dim transition-all">
          <span>Root only</span>
          <div className="w-7 h-4 bg-fg-dim rounded-full relative">
            <div className="w-3 h-3 bg-white rounded-full absolute top-0.5 left-0.5 transition-transform"></div>
          </div>
        </button>
        
        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-border rounded-full bg-bg-elevated text-fg-muted hover:text-fg-secondary hover:border-fg-dim transition-all">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span>Created: 7 days</span>
        </button>
        
        <div className="flex-1"></div>
        
        <button className="px-3 py-1.5 text-xs border border-border rounded-md bg-bg-elevated text-fg-muted hover:text-fg-secondary hover:border-fg-dim transition-all">
          Bulk action
        </button>
      </div>
      
      <RunsList 
        searchQuery={searchQuery}
        onTaskSelect={handleTaskSelect}
      />
    </div>
  );
};