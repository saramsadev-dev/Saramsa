'use client';

import { motion } from 'framer-motion';
interface Metric {
  title: string;
  value: string;
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange' | 'teal';
  description?: string;
  duration?: string; // Add duration support
  status?: 'success' | 'failure' | 'processing' | 'pending';
}

interface MetricsCardsProps {
  metrics: Metric[];
}

export function MetricsCards({ metrics }: MetricsCardsProps) {
  const getCardStyles = (color: string) => {
    switch (color) {
      case "blue":
        return "border-blue-300 dark:border-blue-600 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/30";
      case "green":
        return "border-green-300 dark:border-green-600 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/30";
      case "red":
        return "border-red-300 dark:border-red-600 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/30";
      case "purple":
        return "border-purple-300 dark:border-purple-600 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/30";
      case "orange":
        return "border-orange-300 dark:border-orange-600 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/30";
      case "teal":
        return "border-teal-300 dark:border-teal-600 bg-gradient-to-br from-teal-50 to-teal-100 dark:from-teal-900/20 dark:to-teal-800/30";
      default:
        return "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800";
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'success':
        return <span className="text-green-600 dark:text-green-400 text-lg">✅</span>;
      case 'failure':
        return <span className="text-red-600 dark:text-red-400 text-lg">❌</span>;
      case 'processing':
        return <span className="text-purple-600 dark:text-purple-400 text-lg animate-spin">⚙️</span>;
      case 'pending':
        return <span className="text-blue-600 dark:text-blue-400 text-lg">⏳</span>;
      default:
        return null;
    }
  };

  const getValueColor = (color: string) => {
    switch (color) {
      case "blue":
        return "text-blue-700 dark:text-blue-300";
      case "green":
        return "text-green-700 dark:text-green-300";
      case "red":
        return "text-red-700 dark:text-red-300";
      case "purple":
        return "text-purple-700 dark:text-purple-300";
      case "orange":
        return "text-orange-700 dark:text-orange-300";
      case "teal":
        return "text-teal-700 dark:text-teal-300";
      default:
        return "text-gray-900 dark:text-white";
    }
  };



  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {metrics.map((metric, index) => (
        <motion.div
          key={metric.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: index * 0.1 }}
        >
          <div className={`${getCardStyles(metric.color)} border-2 hover:shadow-xl hover:scale-105 transition-all duration-300 rounded-xl p-6`}>
            <div className="space-y-3">
              {/* Title and Status */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {metric.title}
                </h3>
                {getStatusIcon(metric.status)}
              </div>

              {/* Value */}
              <div className="flex items-baseline gap-3">
                <span className={`text-3xl font-bold ${getValueColor(metric.color)}`}>
                  {metric.value}
                </span>
                {metric.duration && (
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
                    {metric.duration}
                  </span>
                )}
              </div>

              {/* Description */}
              {metric.description && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {metric.description}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
