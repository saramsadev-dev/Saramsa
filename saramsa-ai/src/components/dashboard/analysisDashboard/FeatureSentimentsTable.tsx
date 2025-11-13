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
      <div className="bg-white dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
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
    <div className="bg-white dark:bg-slate-900/50 backdrop-blur-xl rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700/50 overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Feature Level Sentiments
            </h3>
            <div className="w-2 h-2 bg-saramsa-brand rounded-full animate-pulse"></div>
          </div>
          {hasEditedFeaturesProp && onRegenerateAnalysis && (
            <Button
              onClick={onRegenerateAnalysis}
              className="bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white"
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
                className={`grid grid-cols-6 gap-4 py-4 rounded-lg transition-all duration-200 ${
                  selectedFeatures.includes(feature.name)
                    ? 'bg-saramsa-accent/10 dark:bg-saramsa-accent/20 border border-saramsa-brand/30 dark:border-saramsa-brand/50'
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                {/* Checkbox Column */}
                <div className="flex items-center justify-center">
                  <button
                    onClick={() => onFeatureToggle(feature.name)}
                    className={`w-5 h-5 rounded-full border-2 transition-all duration-200 flex items-center justify-center ${
                      selectedFeatures.includes(feature.name)
                        ? 'bg-saramsa-brand border-saramsa-brand text-white'
                        : 'border-slate-300 dark:border-slate-600 hover:border-saramsa-brand/50'
                    }`}
                  >
                    {selectedFeatures.includes(feature.name) && (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
                
                {/* Feature Name Column */}
                <div className="text-sm text-slate-900 dark:text-white">
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
                    className="text-[#E603EB] hover:text-[#E603EB]/80 hover:bg-[#E603EB]/10"
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
                <p className="text-xs text-saramsa-brand/70 dark:text-saramsa-brand/80">
                  {selectedFeatures.join(', ')}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Keywords Edit Modal */}
      {isDialogOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleBackdropClick}
        >
          <div 
            className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Edit Keywords for {editingFeature}
              </h3>
              <button 
                onClick={handleCancelEdit} 
                className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              {/* Current Keywords */}
              <div className="space-y-2">
                <Label>Current Keywords</Label>
                <div className="flex flex-wrap gap-1 min-h-[40px] p-2 border border-gray-200 dark:border-gray-700 rounded-md">
                  {editingKeywords.map((keyword, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className="text-xs bg-gray-50 dark:bg-gray-700 cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20"
                      onClick={() => handleRemoveKeyword(keyword)}
                    >
                      {keyword} ×
                    </Badge>
                  ))}
                  {editingKeywords.length === 0 && (
                    <span className="text-gray-400 text-sm">No keywords</span>
                  )}
                </div>
              </div>

              {/* Add New Keyword */}
              <div className="space-y-2">
                <Label>Add New Keyword</Label>
                <div className="flex gap-2">
                  <Input
                    value={newKeyword}
                    onChange={(e) => setNewKeyword(e.target.value)}
                    placeholder="Enter keyword..."
                    onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                  />
                  <Button
                    onClick={handleAddKeyword}
                    disabled={!newKeyword.trim()}
                    size="sm"
                  >
                    Add
                  </Button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="outline"
                  onClick={handleCancelEdit}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveKeywords}
                  className="bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white"
                >
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
