'use client';

import { CheckCircle2, RefreshCw, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { CompactSentimentBar } from './CompactSentimentBar';

// Compact Sentiment Bar Component


interface FeatureSentiment {
  name: string;
  description: string;
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
  keywords: string[];
  comment_count?: number;
  isEdited?: boolean;
  sample_comments?: {
    positive?: string[];
    negative?: string[];
    neutral?: string[];
  };
}

interface FeatureSentimentsTableProps {
  features: FeatureSentiment[];
  selectedFeatures: string[];
  onFeatureToggle: (featureName: string) => void;
  onRegenerateAnalysis?: () => void;
  hasEditedFeaturesProp?: boolean;
  hasComments?: boolean; // Add this prop
}

export const FeatureSentimentsTable = ({
  features,
  selectedFeatures,
  onFeatureToggle,
  onRegenerateAnalysis,
  hasEditedFeaturesProp,
  hasComments
}: FeatureSentimentsTableProps) => {

  const getSentimentIcon = (positive: number, negative: number, neutral: number) => {
    const max = Math.max(positive, negative, neutral);
    if (max === positive) return <TrendingUp className="w-4 h-4 text-saramsa-brand" />;
    if (max === negative) return <TrendingDown className="w-4 h-4 text-saramsa-gradient-to" />;
    return <Minus className="w-4 h-4 text-muted-foreground" />;
  };

  const getSentimentColor = (positive: number, negative: number, neutral: number) => {
    const max = Math.max(positive, negative, neutral);
    if (max === positive) return 'text-saramsa-brand';
    if (max === negative) return 'text-saramsa-gradient-to';
    return 'text-muted-foreground';
  };

  if (!features || features.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">
          Feature Level Sentiments
        </h3>
        <div className="text-center py-8 border border-dashed border-border/60 rounded-2xl bg-background/60">
          <div className="w-14 h-14 mx-auto mb-4 bg-secondary/60 rounded-full flex items-center justify-center">
            <RefreshCw className="w-7 h-7 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground">
            No feature sentiment data available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative z-[900] space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-foreground">
            Feature Level Sentiments
          </h3>
          <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse"></div>
        </div>
        {hasEditedFeaturesProp && onRegenerateAnalysis && (
          <Button
            onClick={onRegenerateAnalysis}
            variant="outline"
            className="border-border/70 text-foreground hover:bg-secondary/60"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Regenerate Analysis
          </Button>
        )}
        {hasEditedFeaturesProp && !hasComments && (
          <div className="flex items-center gap-2 text-saramsa-gradient-to text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Comments not available for regeneration</span>
          </div>
        )}
      </div>
      
      <div className="overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-5 gap-4 pb-4 border-b border-border/70">
            <div className="text-sm font-semibold text-muted-foreground">
              Select
            </div>
            <div className="text-sm font-semibold text-muted-foreground">
              Feature
            </div>
            <div className="text-sm font-semibold text-muted-foreground col-span-2">
              Description
            </div>
            <div className="text-sm font-semibold text-center text-muted-foreground">
              Sentiment
            </div>
          </div>

          {/* Table Rows */}
          <div className="space-y-2">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className={`grid grid-cols-5 gap-4 py-4 rounded-xl transition-all duration-200 ${
                  selectedFeatures.includes(feature.name)
                    ? 'bg-secondary/60 border border-border/70'
                    : 'hover:bg-secondary/40 border border-transparent'
                }`}
              >
                {/* Checkbox Column */}
                <div className="flex items-center justify-center">
                  <Button
                    onClick={() => onFeatureToggle(feature.name)}
                    variant="ghost"
                    size="icon"
                    className={`h-5 w-5 rounded-full border-2 transition-all duration-200 ${
                      selectedFeatures.includes(feature.name)
                        ? 'bg-foreground border-foreground text-background'
                        : 'border-border/70 hover:border-saramsa-brand/50'
                    }`}
                  >
                    {selectedFeatures.includes(feature.name) && (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                
                {/* Feature Name Column */}
                <div className="text-sm text-foreground">
                  <div className="font-medium">
                    {feature.name}
                    {feature.comment_count && (
                      <span className="text-muted-foreground font-normal ml-1">
                        ({feature.comment_count})
                      </span>
                    )}
                    {feature.isEdited && (
                      <Badge className="ml-2 bg-secondary/70 text-foreground text-xs">
                        Edited
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Description Column - Expanded */}
                <div className="text-sm text-muted-foreground col-span-2">
                  <p className="line-clamp-3 leading-relaxed">
                    {feature.description}
                  </p>
                  {feature.keywords && feature.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {feature.keywords.slice(0, 4).map((keyword: string, i: number) => (
                        <span 
                          key={i} 
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-secondary/70 text-foreground"
                        >
                          {keyword}
                        </span>
                      ))}
                      {feature.keywords.length > 4 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-secondary/70 text-muted-foreground">
                          +{feature.keywords.length - 4}
                        </span>
                      )}
                    </div>
                  )}
                  {(feature.sample_comments?.positive?.length ||
                    feature.sample_comments?.negative?.length) && (
                    <div className="mt-3 space-y-2">
                      {feature.sample_comments?.positive?.length ? (
                        <div>
                          <p className="text-xs font-semibold text-emerald-600">
                            Positive Comments
                          </p>
                          <div className="mt-1 space-y-1">
                            {feature.sample_comments.positive.slice(0, 10).map((c, i) => (
                              <p key={`pos-${i}`} className="text-xs text-foreground/90">
                                {c}
                              </p>
                            ))}
                          </div>
                        </div>
                      ) : null}
                      {feature.sample_comments?.negative?.length ? (
                        <div>
                          <p className="text-xs font-semibold text-rose-600">
                            Negative Comments
                          </p>
                          <div className="mt-1 space-y-1">
                            {feature.sample_comments.negative.slice(0, 10).map((c, i) => (
                              <p key={`neg-${i}`} className="text-xs text-foreground/90">
                                {c}
                              </p>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
                
                {/* Compact Sentiment Visualization */}
                <div className="flex items-center justify-center">
                  <CompactSentimentBar 
                    positive={feature.sentiment.positive}
                    negative={feature.sentiment.negative}
                    neutral={feature.sentiment.neutral}
                  />
                </div>

              </div>
            ))}
          </div>
      </div>

      {/* Selection Status */}
      {selectedFeatures.length > 0 && (
        <div className="p-4 bg-secondary/60 rounded-xl border border-border/70">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-foreground rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4 text-background" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                Selected for Interactive Charts
              </p>
              <p className="text-xs text-muted-foreground">
                {selectedFeatures.join(', ')}
              </p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
