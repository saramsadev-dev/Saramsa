'use client';

import { BarChart3, Loader2 } from 'lucide-react';
import { AnalysisRunItem } from './AnalysisRunItem';
import type { AnalysisHistoryEntry } from '@/store/features/analysis/analysisSlice';

interface AnalysisRunListProps {
  entries: AnalysisHistoryEntry[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, name: string) => void;
  projectName?: string;
}

export function AnalysisRunList({ entries, selectedId, isLoading, onSelect, onRename, projectName }: AnalysisRunListProps) {
  return (
    <aside className="w-[280px] flex-shrink-0 sticky top-6 self-start max-h-[calc(100vh-120px)] flex flex-col bg-card/60 border border-border/60 rounded-2xl overflow-hidden">
      {/* Header with project name */}
      <div className="px-4 py-3 border-b border-border/40">
        {projectName && (
          <p className="text-xs text-muted-foreground mb-1 truncate">{projectName}</p>
        )}
        <h2 className="text-sm font-semibold text-foreground">Analysis Runs</h2>
      </div>

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5 min-h-0">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
            <Loader2 className="w-6 h-6 animate-spin mb-2" />
            <span className="text-xs">Loading history...</span>
          </div>
        ) : entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
            <BarChart3 className="w-8 h-8 mb-2 opacity-40" />
            <span className="text-xs text-center">No analysis runs yet.<br />Upload feedback to get started.</span>
          </div>
        ) : (
          entries.map((entry, i) => (
            <AnalysisRunItem
              key={entry.id}
              entry={entry}
              isActive={selectedId === entry.id}
              previousPositivePct={i < entries.length - 1 ? entries[i + 1].positive_pct : null}
              onClick={() => onSelect(entry.id)}
              onRename={onRename}
              index={i}
            />
          ))
        )}
      </div>
    </aside>
  );
}
