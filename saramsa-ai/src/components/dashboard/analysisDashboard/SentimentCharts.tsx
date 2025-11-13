'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface FeatureSentiment {
  name: string;
  positive: number;
  negative: number;
  neutral: number;
}

interface SentimentData {
  name: string;
  value: number;
  color?: string;
}

interface SentimentChartsProps {
  featureSentimentData: FeatureSentiment[];
  sentimentData: SentimentData[];
  selectedFeatures?: string[];
}

const COLORS = {
  positive: '#8b5cf6',
  negative: '#ef4444',
  neutral: '#64748b',
} as const;

const SENTIMENT_COLOR_MAP: Record<string, string> = {
  Positive: COLORS.positive,
  Negative: COLORS.negative,
  Neutral: COLORS.neutral,
};

interface CustomTooltipPayload {
  color?: string;
  name?: string | number;
  value?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: CustomTooltipPayload[];
  label?: string | number;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-xl p-4 shadow-2xl">
      {label !== undefined && (
        <p className="text-white font-medium mb-2 whitespace-nowrap">
          {label}
        </p>
      )}
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color ?? '#64748b' }}
          />
          <span className="text-slate-300">{entry.name}:</span>
          <span className="text-white font-medium">
            {entry.value ?? 0}
          </span>
        </div>
      ))}
    </div>
  );
};

export function SentimentCharts({
  featureSentimentData,
  sentimentData,
  selectedFeatures = [],
}: SentimentChartsProps) {
  // Aggregated sentiment for selected features (or fallback to overall data)
  const aggregatedSentimentData = useMemo(() => {
    if (selectedFeatures.length > 0) {
      const filtered = featureSentimentData.filter((feature) =>
        selectedFeatures.includes(feature.name)
      );

      if (!filtered.length) return sentimentData;

      const totalPositive = filtered.reduce(
        (sum, f) => sum + f.positive,
        0
      );
      const totalNegative = filtered.reduce(
        (sum, f) => sum + f.negative,
        0
      );
      const totalNeutral = filtered.reduce(
        (sum, f) => sum + f.neutral,
        0
      );

      const base = [
        { name: 'Positive', value: totalPositive },
        { name: 'Negative', value: totalNegative },
        { name: 'Neutral', value: totalNeutral },
      ];

      return base.map((item) => ({
        ...item,
        color: SENTIMENT_COLOR_MAP[item.name] ?? COLORS.neutral,
      }));
    }

    // No selection: ensure each item has a color
    return sentimentData.map((item) => ({
      ...item,
      color:
        item.color ??
        SENTIMENT_COLOR_MAP[item.name] ??
        COLORS.neutral,
    }));
  }, [selectedFeatures, featureSentimentData, sentimentData]);

  const totalSentiment = useMemo(
    () => aggregatedSentimentData.reduce((sum, item) => sum + item.value, 0),
    [aggregatedSentimentData]
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feature Sentiment Bar Chart */}
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Feature Sentiment Distribution
            </h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={featureSentimentData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <defs>
                    <linearGradient
                      id="positiveGradient"
                      x1="0%"
                      y1="0%"
                      x2="0%"
                      y2="100%"
                    >
                      <stop
                        offset="0%"
                        stopColor={COLORS.positive}
                        stopOpacity={0.8}
                      />
                      <stop
                        offset="100%"
                        stopColor={COLORS.positive}
                        stopOpacity={1}
                      />
                    </linearGradient>
                    <linearGradient
                      id="negativeGradient"
                      x1="0%"
                      y1="0%"
                      x2="0%"
                      y2="100%"
                    >
                      <stop
                        offset="0%"
                        stopColor={COLORS.negative}
                        stopOpacity={0.8}
                      />
                      <stop
                        offset="100%"
                        stopColor={COLORS.negative}
                        stopOpacity={1}
                      />
                    </linearGradient>
                    <linearGradient
                      id="neutralGradient"
                      x1="0%"
                      y1="0%"
                      x2="0%"
                      y2="100%"
                    >
                      <stop
                        offset="0%"
                        stopColor={COLORS.neutral}
                        stopOpacity={0.8}
                      />
                      <stop
                        offset="100%"
                        stopColor={COLORS.neutral}
                        stopOpacity={1}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#374151"
                    opacity={0.3}
                  />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    stroke="#6B7280"
                  />
                  <YAxis
                    label={{
                      value: 'Value',
                      angle: -90,
                      position: 'insideLeft',
                      style: {
                        textAnchor: 'middle',
                        fill: '#6B7280',
                        fontSize: 12,
                      },
                    }}
                    tick={{ fontSize: 12, fill: '#6B7280' }}
                    stroke="#6B7280"
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar
                    dataKey="positive"
                    fill="url(#positiveGradient)"
                    name="Positive"
                    radius={[4, 4, 0, 0]}
                    animationDuration={800}
                  />
                  <Bar
                    dataKey="negative"
                    fill="url(#negativeGradient)"
                    name="Negative"
                    radius={[4, 4, 0, 0]}
                    animationDuration={800}
                  />
                  <Bar
                    dataKey="neutral"
                    fill="url(#neutralGradient)"
                    name="Neutral"
                    radius={[4, 4, 0, 0]}
                    animationDuration={800}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="bg-white dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              {selectedFeatures.length === 0
                ? 'Overall Sentiment Distribution'
                : `Sentiment Distribution (${selectedFeatures.length} Feature${
                    selectedFeatures.length > 1 ? 's' : ''
                  })`}
            </h3>

            <div className="h-64 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <defs>
                    <filter id="glow">
                      <feGaussianBlur
                        stdDeviation="3"
                        result="coloredBlur"
                      />
                      <feMerge>
                        <feMergeNode in="coloredBlur" />
                        <feMergeNode in="SourceGraphic" />
                      </feMerge>
                    </filter>
                  </defs>
                  <Pie
                    data={aggregatedSentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    filter="url(#glow)"
                    animationDuration={800}
                  >
                    {aggregatedSentimentData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        stroke={entry.color}
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              {/* Center floating stats */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="bg-slate-800/60 backdrop-blur-md rounded-full p-4 border border-saramsa-brand/30">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">
                      {totalSentiment}
                    </div>
                    <div className="text-xs text-slate-300">Total</div>
                  </div>
                </div>
              </div>
            </div>

            {selectedFeatures.length > 0 && (
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <p className="text-sm text-green-800 dark:text-green-200">
                  <span className="font-medium">Interactive Mode:</span>{' '}
                  Chart shows aggregated sentiment for selected features only.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
