import React from "react";
import { Loader2, BarChart3 } from "lucide-react";

export const LoaderForDashboard: React.FC = () => {
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      {/* Centered Loading Message */}
      <div className="flex flex-col items-center justify-center py-12 bg-card/80 rounded-2xl shadow-sm border border-border/60">
        <div className="relative">
          <BarChart3 className="w-16 h-16 text-muted-foreground/70" />
          <Loader2 className="w-8 h-8 text-muted-foreground animate-spin absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="mt-4 text-lg font-medium text-muted-foreground">
          Processing with AI models...
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          Large datasets may take 5-10 minutes to process
        </p>
      </div>

      {/* Loading Metrics Cards - Subtle */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Total Comments", color: "bg-secondary/60" },
          { label: "Positive", color: "bg-secondary/60" },
          { label: "Negative", color: "bg-secondary/60" }
        ].map((item, i) => (
          <div
            key={i}
            className="bg-card/80 rounded-2xl shadow-sm border border-border/60 p-6"
          >
            <div className="space-y-3">
              <div className={`h-3 ${item.color} rounded w-2/3 animate-pulse`} />
              <div className="h-10 bg-secondary/40 rounded w-1/2 animate-pulse" />
              <div className="h-2 bg-secondary/40 rounded w-3/4 animate-pulse" />
            </div>
          </div>
        ))}
      </div>

      {/* Loading Feature Sentiments Table - Cleaner */}
      <div className="bg-card/80 rounded-2xl shadow-sm border border-border/60 p-6">
        <div className="space-y-4">
          <div className="h-5 bg-secondary/60 rounded w-48 animate-pulse" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-3 bg-secondary/40 rounded-xl">
                <div className="h-4 bg-secondary/60 rounded w-1/4 animate-pulse" />
                <div className="flex-1 flex gap-2">
                  <div className="h-4 bg-secondary/40 rounded flex-1 animate-pulse" />
                  <div className="h-4 bg-secondary/40 rounded flex-1 animate-pulse" />
                  <div className="h-4 bg-secondary/40 rounded flex-1 animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Loading Charts - Better Visual */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {["Sentiment Distribution", "Feature Analysis"].map((title, i) => (
          <div
            key={i}
            className="bg-card/80 rounded-2xl shadow-sm border border-border/60 p-6"
          >
            <div className="space-y-4">
              <div className="h-5 bg-secondary/60 rounded w-40 animate-pulse" />
              <div className="h-64 bg-secondary/40 rounded-xl flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-muted-foreground animate-spin" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
