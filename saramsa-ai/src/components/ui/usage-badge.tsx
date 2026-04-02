"use client";

import { useState, useEffect, useCallback } from "react";
import { Zap } from "lucide-react";
import { getUsage, type UsageData } from "@/lib/billingService";

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function UsageBadge() {
  const [usage, setUsage] = useState<UsageData | null>(null);

  const fetchUsage = useCallback(() => {
    getUsage()
      .then((data) => {
        setUsage(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchUsage();

    // Listen for custom event to refetch usage after analysis completes
    const handleRefetch = () => {
      fetchUsage();
    };
    window.addEventListener('usage-updated', handleRefetch);

    // Poll every 30 seconds as fallback
    const interval = setInterval(fetchUsage, 30000);

    return () => {
      window.removeEventListener('usage-updated', handleRefetch);
      clearInterval(interval);
    };
  }, [fetchUsage]);

  if (!usage) return null;

  const { llm_tokens_used } = usage.usage;
  const { llm_token_limit } = usage.limits;
  const pct = llm_token_limit > 0 ? (llm_tokens_used / llm_token_limit) * 100 : 0;
  const barColor =
    pct >= 90 ? "bg-destructive" : pct >= 70 ? "bg-yellow-500" : "bg-saramsa-brand";

  return (
    <div
      className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-secondary/60 dark:bg-secondary/30 border border-border/40 text-xs"
      title={`${llm_tokens_used.toLocaleString()} / ${llm_token_limit.toLocaleString()} tokens used this month`}
    >
      <Zap className="w-3.5 h-3.5 text-saramsa-brand shrink-0" />
      <span className="text-muted-foreground whitespace-nowrap">
        {formatTokens(llm_tokens_used)}
        <span className="mx-0.5 opacity-50">/</span>
        {formatTokens(llm_token_limit)}
      </span>
      <div className="w-12 h-1.5 rounded-full bg-muted/50 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}
