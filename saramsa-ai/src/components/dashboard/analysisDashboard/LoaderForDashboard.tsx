import React from "react";

export const LoaderForDashboard: React.FC = () => {
  return (
    <div className="space-y-6" aria-busy="true" aria-live="polite">
      {/* Summary Info */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        Loading analysis…
      </div>

      {/* Loading Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            </div>
          </div>
        ))}
      </div>

      {/* Loading Feature Sentiments Table */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/6" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Loading Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
              <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
