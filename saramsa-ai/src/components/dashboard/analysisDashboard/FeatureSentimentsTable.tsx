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
    if (max === positive) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (max === negative) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-500" />;
  };

  const getSentimentColor = (positive: number, negative: number, neutral: number) => {
    const max = Math.max(positive, negative, neutral);
    if (max === positive) return 'text-green-600';
    if (max === negative) return 'text-red-600';
    return 'text-slate-600';
  };

  const hasEditedFeaturesLocal = features.some(f => f.isEdited);

  if (!features || features.length === 0) {
    return (
      <div className="bg-card/90 dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-foreground mb-4">
          Feature Level Sentiments
        </h3>
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
            <RefreshCw className="w-8 h-8 text-slate-400" />
          </div>
          <p className="text-slate-500 dark:text-slate-400">
            No feature sentiment data available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card/90 dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 relative z-[900]">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-foreground">
              Feature Level Sentiments
            </h3>
            <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse"></div>
          </div>
          {hasEditedFeaturesProp && onRegenerateAnalysis && (
            <Button
              onClick={onRegenerateAnalysis}
              className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Regenerate Analysis
            </Button>
          )}
          {hasEditedFeaturesProp && !hasComments && (
            <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400 text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>Comments not available for regeneration</span>
            </div>
          )}
        </div>
        
        <div className="overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-6 gap-4 pb-4 border-b border-slate-200 dark:border-slate-700">
            <div className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              Select
            </div>
            <div className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              Feature
            </div>
            <div className="text-sm font-semibold text-slate-600 dark:text-slate-400 col-span-2">
              Description
            </div>
            <div className="text-sm font-semibold text-center text-slate-600 dark:text-slate-400">
              Sentiment
            </div>
            <div className="text-sm font-semibold text-center text-slate-600 dark:text-slate-400">
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
                    ? 'bg-saramsa-accent/10 dark:bg-saramsa-accent/20 border border-saramsa-brand/30 dark:border-saramsa-brand/50'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-transparent'
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
                        ? 'bg-saramsa-brand border-saramsa-brand text-white'
                        : 'border-slate-300 dark:border-slate-600 hover:border-saramsa-brand/50'
                    }`}
                  >
                    {selectedFeatures.includes(feature.name) && (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                
                {/* Feature Name Column */}
                <div className="text-sm text-slate-900 dark:text-foreground">
                  <div className="font-medium">
                    {feature.name}
                    {feature.comment_count && (
                      <span className="text-slate-500 dark:text-slate-400 font-normal ml-1">
                        ({feature.comment_count})
                      </span>
                    )}
                    {feature.isEdited && (
                      <Badge className="ml-2 bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 text-xs">
                        Edited
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Description Column - Expanded */}
                <div className="text-sm text-slate-600 dark:text-slate-400 col-span-2">
                  <p className="line-clamp-3 leading-relaxed">
                    {feature.description}
                  </p>
                  {feature.keywords && feature.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {feature.keywords.slice(0, 4).map((keyword: string, i: number) => (
                        <span 
                          key={i} 
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                        >
                          {keyword}
                        </span>
                      ))}
                      {feature.keywords.length > 4 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-slate-100 dark:bg-slate-800 text-slate-500">
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
                    className="text-saramsa-brand hover:text-saramsa-brand/95 hover:bg-saramsa-brand/10"
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
          <div className="mt-6 p-4 bg-saramsa-accent/10 dark:bg-saramsa-accent/20 rounded-xl border border-saramsa-brand/30 dark:border-saramsa-brand/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-saramsa-brand rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-sm font-medium text-saramsa-brand dark:text-saramsa-brand">
                  Selected for Interactive Charts
                </p>
                <p className="text-xs text-saramsa-brand/70 dark:text-saramsa-brand/95">
                  {selectedFeatures.join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Keywords Edit Modal - full-screen overlay, always centered */}
      {isDialogOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[1000] px-4"
          onClick={handleBackdropClick}
        >
          <div
            className="bg-slate-950/95 dark:bg-slate-950/95 text-white p-6 md:p-8 rounded-2xl shadow-2xl max-w-5xl w-full mx-4 border border-slate-800"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
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
                className="h-9 w-9 rounded-full border border-slate-700 bg-slate-900/80 text-slate-300 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Main Layout: central options panel anchored near top */}
            <div className="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)] gap-6 md:gap-8 items-start">
              {/* Center options panel */}
              <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 md:p-6 space-y-5">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-semibold tracking-wide text-slate-100">
                    Options
                  </h4>
                  {editingKeywords.length > 0 && (
                    <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400">
                      {editingKeywords.length} keyword{editingKeywords.length > 1 ? 's' : ''} selected
                    </span>
                  )}
                </div>

                {/* Current Keywords */}
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                    Current Keywords
                  </Label>
                  <div className="flex flex-wrap gap-2 min-h-[48px] px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800">
                    {editingKeywords.map((keyword, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="text-xs bg-slate-900/80 border-saramsa-brand/40 text-slate-100 cursor-pointer hover:bg-red-500/10 hover:border-red-500/60 transition-colors"
                        onClick={() => handleRemoveKeyword(keyword)}
                      >
                        {keyword} x
                      </Badge>
                    ))}
                    {editingKeywords.length === 0 && (
                      <span className="text-slate-500 text-sm">
                        No keywords added yet. Start by adding a few below.
                      </span>
                    )}
                  </div>
                </div>

                {/* Add New Keyword */}
                <div className="space-y-2">
                  <Label className="text-xs uppercase tracking-[0.16em] text-slate-400">
                    Add New Keyword
                  </Label>
                  <div className="flex flex-col sm:flex-row gap-3">
                    <Input
                      value={newKeyword}
                      onChange={(e) => setNewKeyword(e.target.value)}
                      placeholder="Enter keyword..."
                      onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                      className="bg-slate-950/80 border-slate-800 text-slate-100 placeholder:text-slate-500"
                    />
                    <Button
                      onClick={handleAddKeyword}
                      disabled={!newKeyword.trim()}
                      size="sm"
                      className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
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
                    className="border-slate-700 text-slate-200 hover:bg-slate-800 hover:text-white"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveKeywords}
                    className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white shadow-lg shadow-[0_18px_40px_-24px_rgba(230,3,235,0.6)]"
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
