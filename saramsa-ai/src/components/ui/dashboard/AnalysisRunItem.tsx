'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Pencil, Check, X } from 'lucide-react';
import type { AnalysisHistoryEntry } from '@/store/features/analysis/analysisSlice';

interface AnalysisRunItemProps {
  entry: AnalysisHistoryEntry;
  isActive: boolean;
  previousPositivePct: number | null;
  onClick: () => void;
  onRename: (id: string, name: string) => void;
  index: number;
}

export function AnalysisRunItem({ entry, isActive, previousPositivePct, onClick, onRename, index }: AnalysisRunItemProps) {
  const isPending = entry.status === 'analyzing';
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const formattedDate = (() => {
    try {
      const d = new Date(entry.analysis_date);
      if (isNaN(d.getTime())) return 'Unknown date';
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return 'Unknown date';
    }
  })();

  const displayName = entry.name || formattedDate;
  const trend = previousPositivePct !== null && !isPending ? entry.positive_pct - previousPositivePct : null;

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const startEditing = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPending) return;
    setEditValue(entry.name || '');
    setIsEditing(true);
  };

  const confirmRename = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    const trimmed = editValue.trim();
    onRename(entry.id, trimmed);
    setIsEditing(false);
  };

  const cancelEditing = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();
    if (e.key === 'Enter') confirmRename();
    if (e.key === 'Escape') cancelEditing();
  };

  return (
    <motion.div
      role="button"
      tabIndex={0}
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.2, delay: index * 0.04 }}
      onClick={isEditing ? undefined : onClick}
      onKeyDown={(e) => { if (!isEditing && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onClick(); } }}
      className={`w-full text-left px-3 py-3 rounded-xl border transition-all duration-200 cursor-pointer group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saramsa-brand/50 ${
        isPending
          ? 'bg-amber-500/10 border-amber-500/40 shadow-sm'
          : isActive
            ? 'bg-saramsa-brand/10 border-saramsa-brand/40 shadow-sm'
            : 'bg-card/60 border-border/40 hover:bg-secondary/60 hover:border-border/60'
      }`}
    >
      {/* Name / Date row */}
      <div className="flex items-center gap-2 mb-1">
        {isPending ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-500 flex-shrink-0" />
        ) : isActive ? (
          <span className="w-2 h-2 rounded-full bg-saramsa-brand animate-pulse flex-shrink-0" />
        ) : (
          <span className="w-2 h-2 rounded-full border border-muted-foreground/40 flex-shrink-0" />
        )}

        {isEditing ? (
          <div className="flex items-center gap-1 flex-1 min-w-0" onClick={e => e.stopPropagation()}>
            <input
              ref={inputRef}
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={formattedDate}
              className="flex-1 min-w-0 text-sm font-medium bg-background/80 border border-border/60 rounded-md px-1.5 py-0.5 text-foreground focus:outline-none focus:ring-1 focus:ring-saramsa-brand/50"
            />
            <span role="button" tabIndex={0} onClick={confirmRename} onKeyDown={e => { if (e.key === 'Enter') confirmRename(); }} className="p-0.5 text-green-500 hover:text-green-600 cursor-pointer" title="Save">
              <Check className="w-3.5 h-3.5" />
            </span>
            <span role="button" tabIndex={0} onClick={cancelEditing} onKeyDown={e => { if (e.key === 'Enter') cancelEditing(); }} className="p-0.5 text-muted-foreground hover:text-foreground cursor-pointer" title="Cancel">
              <X className="w-3.5 h-3.5" />
            </span>
          </div>
        ) : (
          <>
            <span className={`text-sm font-medium truncate ${isPending ? 'text-amber-600 dark:text-amber-400' : isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
              {isPending ? 'Analyzing...' : displayName}
            </span>
            {!isPending && (
              <span
                role="button"
                tabIndex={0}
                onClick={startEditing}
                onKeyDown={e => { if (e.key === 'Enter') startEditing(e as any); }}
                className="p-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground ml-auto flex-shrink-0 cursor-pointer"
                title="Rename"
              >
                <Pencil className="w-3 h-3" />
              </span>
            )}
            {isPending && (
              <span className="text-[10px] font-medium text-amber-500 ml-auto">In Progress</span>
            )}
            {!isPending && isActive && !isEditing && (
              <span className="text-[10px] font-medium text-saramsa-brand ml-auto group-hover:hidden">Viewing</span>
            )}
          </>
        )}
      </div>

      {/* Date subtitle when entry has a custom name */}
      {!isPending && !isEditing && entry.name && (
        <div className="pl-4 text-[10px] text-muted-foreground/60 mb-0.5">
          {formattedDate}
        </div>
      )}

      {/* Stats row */}
      <div className="flex items-center gap-3 pl-4 text-xs text-muted-foreground">
        {isPending ? (
          <span className="text-amber-600/70 dark:text-amber-400/70">Processing feedback data...</span>
        ) : (
          <>
            <span>{entry.comments_count} cmts</span>
            <span className="flex items-center gap-1">
              {entry.positive_pct}% pos
              {trend !== null && trend !== 0 && (
                <span className={trend > 0 ? 'text-green-500' : 'text-red-500'}>
                  {trend > 0 ? '\u2191' : '\u2193'}
                </span>
              )}
            </span>
          </>
        )}
      </div>
    </motion.div>
  );
}


