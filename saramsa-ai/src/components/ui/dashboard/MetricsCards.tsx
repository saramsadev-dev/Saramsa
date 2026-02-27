'use client';

import { motion } from 'framer-motion';
interface Metric {
  title: string;
  value: string;
  color: 'blue' | 'green' | 'red' | 'purple' | 'orange' | 'teal';
  description?: string;
}

interface MetricsCardsProps {
  metrics: Metric[];
}

export function MetricsCards({ metrics }: MetricsCardsProps) {
  const getCardStyles = (color: string) => {
    switch (color) {
      case "blue":
        return "border-blue-200/70 dark:border-blue-500/60 bg-gradient-to-br from-blue-50/80 to-blue-100/80 dark:from-blue-900/20 dark:to-blue-800/30";
      case "green":
        return "border-green-200/70 dark:border-green-500/60 bg-gradient-to-br from-green-50/80 to-green-100/80 dark:from-green-900/20 dark:to-green-800/30";
      case "red":
        return "border-red-200/70 dark:border-red-500/60 bg-gradient-to-br from-red-50/80 to-red-100/80 dark:from-red-900/20 dark:to-red-800/30";
      case "purple":
        return "border-purple-200/70 dark:border-purple-500/60 bg-gradient-to-br from-purple-50/80 to-purple-100/80 dark:from-purple-900/20 dark:to-purple-800/30";
      case "orange":
        return "border-orange-200/70 dark:border-orange-500/60 bg-gradient-to-br from-orange-50/80 to-orange-100/80 dark:from-orange-900/20 dark:to-orange-800/30";
      case "teal":
        return "border-teal-200/70 dark:border-teal-500/60 bg-gradient-to-br from-teal-50/80 to-teal-100/80 dark:from-teal-900/20 dark:to-teal-800/30";
      default:
        return "border-border/60 bg-card/80";
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
          <div className={`${getCardStyles(metric.color)} border rounded-2xl p-6 shadow-[0_18px_50px_-40px_rgba(15,23,42,0.6)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_24px_60px_-36px_rgba(15,23,42,0.7)]`}>
            <div className="space-y-3">
              {/* Title */}
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted-foreground">
                  {metric.title}
                </h3>
              </div>

              {/* Value */}
              <div className="flex items-baseline gap-3">
                <span className={`text-3xl font-bold ${getValueColor(metric.color)}`}>
                  {metric.value}
                </span>
              </div>

              {/* Description */}
              {metric.description && (
                <p className="text-xs text-muted-foreground">
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
