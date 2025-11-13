'use client';

import { motion } from 'framer-motion';
interface Metric {
  title: string;
  value: string;
  color: 'blue' | 'green' | 'red';
  description?: string;
}

interface MetricsCardsProps {
  metrics: Metric[];
}

export function MetricsCards({ metrics }: MetricsCardsProps) {
  const getCardStyles = (color: string) => {
    switch (color) {
      case "blue":
        return "border-saramsa-brand/20 dark:border-saramsa-brand/30 bg-saramsa-accent/10 dark:bg-saramsa-accent/20";
      case "green":
        return "border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/10";
      case "red":
        return "border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-900/10";
      default:
        return "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800";
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
          <div className={`${getCardStyles(metric.color)} border-2 hover:shadow-lg transition-all duration-300 rounded-xl p-6`}>
            <div className="space-y-3">
              {/* Title */}
              <h3 className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {metric.title}
              </h3>

              {/* Value */}
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-gray-900 dark:text-white">
                  {metric.value}
                </span>
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
