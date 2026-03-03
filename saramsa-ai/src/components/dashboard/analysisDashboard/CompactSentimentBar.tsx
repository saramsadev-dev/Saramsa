import { motion } from "framer-motion";

interface CompactSentimentBarProps {
  positive: number;
  negative: number;
  neutral: number;
}

export const CompactSentimentBar = ({
  positive,
  negative,
  neutral,
}: CompactSentimentBarProps) => {
  const total = positive + negative + neutral;

  const positivePercent = total > 0 ? (positive / total) * 100 : 0;
  const negativePercent = total > 0 ? (negative / total) * 100 : 0;
  const neutralPercent = total > 0 ? (neutral / total) * 100 : 0;

  const tinySegmentMinWidth = (percent: number) =>
    percent > 0 && percent < 5 ? "2px" : "0px";

  return (
    <div className="group relative">
      {/* Stacked Capsule Bar */}
      <div className="flex items-center bg-secondary/60 rounded-full h-6 w-20 overflow-hidden border border-border/60">
        {/* Positive segment */}
        {positivePercent > 0 && (
          <motion.div
            className="bg-saramsa-brand/70 h-full"
            initial={{ width: 0 }}
            animate={{ width: `${positivePercent}%` }}
            transition={{ duration: 0.8, delay: 0.1 }}
            style={{ minWidth: tinySegmentMinWidth(positivePercent) }}
          />
        )}

        {/* Negative segment */}
        {negativePercent > 0 && (
          <motion.div
            className="bg-saramsa-gradient-to/70 h-full"
            initial={{ width: 0 }}
            animate={{ width: `${negativePercent}%` }}
            transition={{ duration: 0.8, delay: 0.2 }}
            style={{ minWidth: tinySegmentMinWidth(negativePercent) }}
          />
        )}

        {/* Neutral segment */}
        {neutralPercent > 0 && (
          <motion.div
            className="bg-muted-foreground/50 h-full"
            initial={{ width: 0 }}
            animate={{ width: `${neutralPercent}%` }}
            transition={{ duration: 0.8, delay: 0.3 }}
            style={{ minWidth: tinySegmentMinWidth(neutralPercent) }}
          />
        )}
      </div>

      {/* Hover Tooltip (CSS handles show/hide, no Framer needed) */}
      <div
        className="
          absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 
          bg-background/95 text-foreground 
          text-xs rounded-xl shadow-lg opacity-0 group-hover:opacity-100 
          transition-opacity duration-200 whitespace-nowrap z-10
        "
      >
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-saramsa-brand rounded-full" />
            <span>{positivePercent.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-saramsa-gradient-to rounded-full" />
            <span>{negativePercent.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-muted-foreground/60 rounded-full" />
            <span>{neutralPercent.toFixed(1)}%</span>
          </div>
        </div>
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-background/95" />
      </div>
    </div>
  );
};
