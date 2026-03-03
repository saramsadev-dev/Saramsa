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
  positive: 'rgba(139, 95, 191, 0.75)',
  negative: 'rgba(90, 55, 134, 0.7)',
  neutral: 'rgba(100, 116, 139, 0.6)',
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
    <div className="bg-background/95 border border-border/70 rounded-xl p-4 shadow-md">
      {label !== undefined && (
        <p className="text-foreground font-medium mb-2 whitespace-nowrap">
          {label}
        </p>
      )}
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color ?? 'var(--muted-foreground)' }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="text-foreground font-medium">
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
        <div className="bg-card/80 rounded-2xl border border-border/60 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Feature Sentiment Distribution
            </h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={featureSentimentData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--border)"
                    opacity={0.35}
                  />
                  <XAxis
                    dataKey="name"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                    stroke="var(--muted-foreground)"
                  />
                  <YAxis
                    label={{
                      value: 'Value',
                      angle: -90,
                      position: 'insideLeft',
                      style: {
                        textAnchor: 'middle',
                        fill: 'var(--muted-foreground)',
                        fontSize: 12,
                      },
                    }}
                    tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                    stroke="var(--muted-foreground)"
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar
                    dataKey="positive"
                    fill={COLORS.positive}
                    name="Positive"
                    radius={[4, 4, 0, 0]}
                    animationDuration={800}
                  />
                  <Bar
                    dataKey="negative"
                    fill={COLORS.negative}
                    name="Negative"
                    radius={[4, 4, 0, 0]}
                    animationDuration={800}
                  />
                  <Bar
                    dataKey="neutral"
                    fill={COLORS.neutral}
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
        <div className="bg-card/80 rounded-2xl border border-border/60 overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              {selectedFeatures.length === 0
                ? 'Overall Sentiment Distribution'
                : `Sentiment Distribution (${selectedFeatures.length} Feature${
                    selectedFeatures.length > 1 ? 's' : ''
                  })`}
            </h3>

            <div className="h-64 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={aggregatedSentimentData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
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
                <div className="bg-background/80 rounded-full p-4 border border-border/70">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">
                      {totalSentiment}
                    </div>
                    <div className="text-xs text-muted-foreground">Total</div>
                  </div>
                </div>
              </div>
            </div>

            {selectedFeatures.length > 0 && (
              <div className="mt-4 p-3 bg-secondary/50 rounded-xl border border-border/60">
                <p className="text-sm text-muted-foreground">
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
