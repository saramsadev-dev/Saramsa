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
  const getCardStyles = () => {
    return "border-border/60 bg-card/80";
  };

  const getValueColor = (color: string) => {
    switch (color) {
      case "green":
        return "text-saramsa-brand";
      case "red":
        return "text-saramsa-gradient-to";
      case "blue":
      case "purple":
      case "orange":
      case "teal":
      default:
        return "text-foreground";
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
          <div className={`${getCardStyles()} border rounded-2xl p-6 shadow-sm transition-all duration-300 hover:shadow-md`}>
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
