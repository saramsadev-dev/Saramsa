'use client';

import { useState } from 'react';
import { CheckCircle2, Circle, Edit, RefreshCw, X, TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Checkbox } from '../../ui/checkbox';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import React from 'react';
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
}

interface FeatureSentimentsTableProps {
  features: FeatureSentiment[];
  selectedFeatures: string[];
  onFeatureToggle: (featureName: string) => void;
  onKeywordsUpdate: (featureName: string, keywords: string[]) => void;
  onRegenerateAnalysis?: () => void;
  hasEditedFeaturesProp?: boolean;
  hasComments?: boolean; // Add this prop
}

export const FeatureSentimentsTable = ({
  features,
  selectedFeatures,
  onFeatureToggle,
  onKeywordsUpdate,
  onRegenerateAnalysis,
  hasEditedFeaturesProp,
  hasComments
}: FeatureSentimentsTableProps) => {
  const [editingFeature, setEditingFeature] = useState<string | null>(null);
  const [editingKeywords, setEditingKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const handleEditKeywords = (feature: FeatureSentiment) => {
    setEditingFeature(feature.name);
    setEditingKeywords([...feature.keywords]);
    setIsDialogOpen(true);
  };

  const handleAddKeyword = () => {
    if (newKeyword.trim() && !editingKeywords.includes(newKeyword.trim())) {
      setEditingKeywords([...editingKeywords, newKeyword.trim()]);
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keywordToRemove: string) => {
    setEditingKeywords(editingKeywords.filter(k => k !== keywordToRemove));
  };

  const handleSaveKeywords = () => {
    if (editingFeature && onKeywordsUpdate) {
      onKeywordsUpdate(editingFeature, editingKeywords);
    }
    setIsDialogOpen(false);
    setEditingFeature(null);
    setEditingKeywords([]);
    setNewKeyword('');
  };

  const handleCancelEdit = () => {
    setIsDialogOpen(false);
    setEditingFeature(null);
    setEditingKeywords([]);
    setNewKeyword('');
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleCancelEdit();
    }
  };

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDialogOpen) {
        handleCancelEdit();
      }
    };

    if (isDialogOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isDialogOpen]);

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

  const hasEditedFeaturesLocal = features.some(f => f.isEdited);

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
          <div className="grid grid-cols-6 gap-4 pb-4 border-b border-border/70">
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
            <div className="text-sm font-semibold text-center text-muted-foreground">
              Actions
            </div>
          </div>

          {/* Table Rows */}
          <div className="space-y-2">
            {features.map((feature, index) => (
              <div 
                key={index} 
                className={`grid grid-cols-6 gap-4 py-4 rounded-xl transition-all duration-200 ${
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
                </div>
                
                {/* Compact Sentiment Visualization */}
                <div className="flex items-center justify-center">
                  <CompactSentimentBar 
                    positive={feature.sentiment.positive}
                    negative={feature.sentiment.negative}
                    neutral={feature.sentiment.neutral}
                  />
                </div>

                {/* Actions Column */}
                <div className="flex items-center justify-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEditKeywords(feature)}
                    className="text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Edit
                  </Button>
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

      {/* Keywords Edit Modal - full-screen overlay, always centered */}
      {isDialogOpen && (
        <div
          className="fixed inset-0 bg-slate-950/40 flex items-center justify-center z-[1000] px-4"
          onClick={handleBackdropClick}
        >
          <div
            className="bg-background/95 text-foreground p-6 md:p-8 rounded-2xl shadow-2xl max-w-5xl w-full mx-4 border border-border/70"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                  Feature Keyword Editing
                </p>
                <h3 className="text-xl font-semibold">
                  Edit keywords for <span className="text-saramsa-brand">{editingFeature}</span>
                </h3>
              </div>
              <Button
                onClick={handleCancelEdit}
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full border border-border/70 bg-background/80 text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Main Layout: central options panel anchored near top */}
            <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)] gap-6 md:gap-8 items-start">
              {/* Center options panel */}
              <div className="bg-card/90 rounded-xl border border-border/70 p-5 md:p-6 space-y-5">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold tracking-wide text-foreground">
                    Options
                  </h4>
                  {editingKeywords.length > 0 && (
                    <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      {editingKeywords.length} keyword{editingKeywords.length > 1 ? 's' : ''} selected
                    </span>
                  )}
                </div>

                {/* Current Keywords */}
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    Current Keywords
                  </Label>
                  <div className="flex flex-wrap gap-2 min-h-[48px] px-3 py-2 rounded-xl bg-background/80 border border-border/70">
                    {editingKeywords.map((keyword, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="text-xs bg-saramsa-brand/10 border-saramsa-brand/40 text-saramsa-brand cursor-pointer hover:bg-saramsa-gradient-to/10 hover:border-saramsa-gradient-to/60 transition-colors"
                        onClick={() => handleRemoveKeyword(keyword)}
                      >
                        {keyword} x
                      </Badge>
                    ))}
                    {editingKeywords.length === 0 && (
                      <span className="text-muted-foreground text-sm">
                        No keywords added yet. Start by adding a few below.
                      </span>
                    )}
                  </div>
                </div>

                {/* Add New Keyword */}
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    Add New Keyword
                  </Label>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Input
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      placeholder="Enter keyword..."
                      onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                      className="bg-background/80 border-border/70 text-foreground placeholder:text-muted-foreground"
                    />
                    <Button
                      onClick={handleAddKeyword}
                      disabled={!newKeyword.trim()}
                      size="sm"
                      className="bg-foreground text-background hover:bg-foreground/90 disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
                    >
                      Add Keyword
                    </Button>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={handleCancelEdit}
                    className="border-border/70 text-muted-foreground hover:bg-secondary/70 hover:text-foreground"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveKeywords}
                    className="bg-foreground text-background hover:bg-foreground/90"
                  >
                    Save Changes
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
