import React from "react";
import { Loader2, BarChart3 } from "lucide-react";

export const LoaderForDashboard: React.FC = () => {
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      {/* Centered Loading Message */}
      <div className="flex flex-col items-center justify-center py-12 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
        <div className="relative">
          <BarChart3 className="w-16 h-16 text-gray-300 dark:text-gray-600" />
          <Loader2 className="w-8 h-8 text-purple-600 dark:text-purple-400 animate-spin absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
        <p className="mt-4 text-lg font-medium text-gray-700 dark:text-gray-300">
          Processing with AI models...
        </p>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Large datasets may take 5-10 minutes to process
        </p>
      </div>

      {/* Loading Metrics Cards - Subtle */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: "Total Comments", color: "bg-blue-100 dark:bg-blue-900/20" },
          { label: "Positive", color: "bg-green-100 dark:bg-green-900/20" },
          { label: "Negative", color: "bg-red-100 dark:bg-red-900/20" }
        ].map((item, i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="space-y-3">
              <div className={`h-3 ${item.color} rounded w-2/3 animate-pulse`} />
              <div className="h-10 bg-gray-100 dark:bg-gray-700/50 rounded w-1/2 animate-pulse" />
              <div className="h-2 bg-gray-100 dark:bg-gray-700/50 rounded w-3/4 animate-pulse" />
            </div>
          </div>
        ))}
      </div>

      {/* Loading Feature Sentiments Table - Cleaner */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="space-y-4">
          <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
                <div className="h-4 bg-gray-200 dark:bg-gray-600 rounded w-1/4 animate-pulse" />
                <div className="flex-1 flex gap-2">
                  <div className="h-4 bg-green-100 dark:bg-green-900/30 rounded flex-1 animate-pulse" />
                  <div className="h-4 bg-red-100 dark:bg-red-900/30 rounded flex-1 animate-pulse" />
                  <div className="h-4 bg-gray-100 dark:bg-gray-600/30 rounded flex-1 animate-pulse" />
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
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="space-y-4">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse" />
              <div className="h-64 bg-gradient-to-br from-gray-100 to-gray-50 dark:from-gray-700/50 dark:to-gray-800/50 rounded-lg flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-gray-400 dark:text-gray-500 animate-spin" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
