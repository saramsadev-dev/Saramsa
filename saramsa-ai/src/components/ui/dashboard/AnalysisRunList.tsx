'use client';

import { useRef, useState } from 'react';
import { BarChart3, Loader2, Upload, FileText, Trash2 } from 'lucide-react';
import { AnalysisRunItem } from './AnalysisRunItem';
import { Button } from '../button';
import type { AnalysisHistoryEntry } from '@/store/features/analysis/analysisSlice';

interface AnalysisRunListProps {
  entries: AnalysisHistoryEntry[];
  selectedId: string | null;
  isLoading: boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, name: string) => void;
  projectName?: string;
  // Upload props
  topFile: File | null;
  topError: string | null;
  isAnalyzing: boolean;
  onFileSelect: (file: File | null) => void;
  onAnalyze: () => Promise<void>;
}

export function AnalysisRunList({
  entries, selectedId, isLoading, onSelect, onRename, projectName,
  topFile, topError, isAnalyzing, onFileSelect, onAnalyze,
}: AnalysisRunListProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0] ?? null;
    if (file) onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const removeFile = () => {
    onFileSelect(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <aside className="w-[280px] flex-shrink-0 h-full flex flex-col bg-card/60 border border-border/60 rounded-2xl overflow-hidden">
      {/* Header with project name */}
      <div className="px-4 py-3 border-b border-border/40">
        {projectName ? (
          <>
            <h2 className="text-sm font-semibold text-foreground truncate">{projectName}</h2>
            <p className="text-xs text-muted-foreground mt-1">Tasks</p>
          </>
        ) : (
          <h2 className="text-sm font-semibold text-foreground">Tasks</h2>
        )}
      </div>

      {/* Upload Zone */}
      <div className="px-2 py-2 border-b border-border/40">
        {!topFile ? (
          <div
            className={`border border-dashed rounded-lg px-2 py-2 cursor-pointer flex items-center gap-2 ${
              isDragging ? 'border-saramsa-brand/40 bg-secondary/60' : 'border-border/70'
            }`}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInputRef.current?.click();
              }
            }}
          >
            <Upload className="w-4 h-4 text-muted-foreground shrink-0" />
            <span className="text-xs text-muted-foreground flex-1">CSV or JSON</span>
            <Button
              variant="outline"
              size="sm"
              className="text-xs h-6 px-2 shrink-0"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
            >
              Browse
            </Button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 px-2 py-1 bg-secondary/60 rounded-lg border border-border/60">
              <FileText className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              <p className="text-xs text-foreground truncate flex-1">{topFile.name}</p>
              <button
                type="button"
                onClick={removeFile}
                className="p-0.5 text-muted-foreground hover:text-foreground shrink-0"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
            <Button
              onClick={onAnalyze}
              disabled={isAnalyzing}
              className="w-full bg-foreground text-background hover:bg-foreground/90 disabled:opacity-50 text-xs h-7 mt-1.5"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze'}
            </Button>
          </>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFileSelect(f);
          }}
          className="hidden"
        />
        {topError && (
          <p className="text-[11px] text-red-500 mt-1 leading-tight">{topError}</p>
        )}
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


