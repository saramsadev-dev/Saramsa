"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Badge } from "../badge";
import { Button } from "../button";
import { Smile, Meh, Frown, RotateCcw } from "lucide-react";

interface AdvancedWordCloudProps {
  positiveKeywords: string[];
  negativeKeywords: string[];
  className?: string;
}

interface WordItem {
  word: string;
  size: number;
  frequency: number;
  x: number;
  y: number;
  color: string;
}

export function AdvancedWordCloud({
  positiveKeywords,
  negativeKeywords,
  className = "",
}: AdvancedWordCloudProps) {
  const [activeSentiment, setActiveSentiment] = useState<'positive' | 'neutral' | 'negative'>('positive');

  const wordData = {
    positive: positiveKeywords.length > 0 
      ? positiveKeywords.slice(0, 10).map((word, index) => ({
          word,
          size: Math.max(20, 40 - index * 2),
          frequency: Math.max(50, 150 - index * 10),
          x: Math.random() * 80 + 10,
          y: Math.random() * 80 + 10,
          color: ['#10B981', '#059669', '#047857', '#065F46'][index % 4]
        }))
      : [
          { word: 'amazing', size: 40, frequency: 145, x: 20, y: 30, color: '#10B981' },
          { word: 'excellent', size: 32, frequency: 120, x: 60, y: 15, color: '#059669' },
          { word: 'love', size: 36, frequency: 134, x: 15, y: 65, color: '#047857' },
          { word: 'fantastic', size: 28, frequency: 98, x: 70, y: 50, color: '#065F46' },
          { word: 'great', size: 35, frequency: 128, x: 45, y: 40, color: '#10B981' },
          { word: 'perfect', size: 30, frequency: 105, x: 25, y: 80, color: '#059669' },
          { word: 'helpful', size: 26, frequency: 89, x: 80, y: 25, color: '#047857' },
          { word: 'smooth', size: 24, frequency: 76, x: 55, y: 75, color: '#065F46' },
          { word: 'intuitive', size: 22, frequency: 67, x: 10, y: 45, color: '#10B981' },
          { word: 'fast', size: 20, frequency: 58, x: 85, y: 60, color: '#059669' }
        ],
    neutral: [
      { word: 'okay', size: 32, frequency: 156, x: 25, y: 35, color: '#6B7280' },
      { word: 'fine', size: 28, frequency: 134, x: 65, y: 20, color: '#4B5563' },
      { word: 'average', size: 30, frequency: 142, x: 20, y: 70, color: '#374151' },
      { word: 'normal', size: 24, frequency: 98, x: 70, y: 55, color: '#1F2937' },
      { word: 'standard', size: 26, frequency: 112, x: 45, y: 45, color: '#6B7280' },
      { word: 'usual', size: 22, frequency: 87, x: 15, y: 55, color: '#4B5563' },
      { word: 'expected', size: 20, frequency: 76, x: 80, y: 35, color: '#374151' },
      { word: 'typical', size: 18, frequency: 64, x: 55, y: 75, color: '#1F2937' },
      { word: 'common', size: 16, frequency: 52, x: 10, y: 25, color: '#6B7280' },
      { word: 'basic', size: 14, frequency: 43, x: 85, y: 65, color: '#4B5563' }
    ],
    negative: negativeKeywords.length > 0
      ? negativeKeywords.slice(0, 10).map((word, index) => ({
          word,
          size: Math.max(20, 40 - index * 2),
          frequency: Math.max(30, 100 - index * 8),
          x: Math.random() * 80 + 10,
          y: Math.random() * 80 + 10,
          color: ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'][index % 4]
        }))
      : [
          { word: 'terrible', size: 38, frequency: 87, x: 30, y: 25, color: '#EF4444' },
          { word: 'slow', size: 34, frequency: 76, x: 15, y: 60, color: '#DC2626' },
          { word: 'confusing', size: 32, frequency: 71, x: 70, y: 40, color: '#B91C1C' },
          { word: 'broken', size: 30, frequency: 65, x: 50, y: 70, color: '#991B1B' },
          { word: 'frustrating', size: 28, frequency: 59, x: 20, y: 80, color: '#EF4444' },
          { word: 'difficult', size: 26, frequency: 54, x: 80, y: 15, color: '#DC2626' },
          { word: 'buggy', size: 24, frequency: 48, x: 10, y: 40, color: '#B91C1C' },
          { word: 'annoying', size: 22, frequency: 42, x: 65, y: 75, color: '#991B1B' },
          { word: 'complicated', size: 20, frequency: 38, x: 45, y: 30, color: '#EF4444' },
          { word: 'disappointing', size: 18, frequency: 34, x: 85, y: 55, color: '#DC2626' }
        ]
  };

  const sentimentConfig = {
    positive: { 
      icon: Smile, 
      color: 'text-green-600', 
      bgColor: 'bg-green-50 dark:bg-green-900/20',
      borderColor: 'border-green-200 dark:border-green-800',
      label: 'Positive',
      count: wordData.positive.reduce((sum, word) => sum + word.frequency, 0)
    },
    neutral: { 
      icon: Meh, 
      color: 'text-muted-foreground', 
      bgColor: 'bg-secondary/40 dark:bg-background/20',
      borderColor: 'border-border/60 dark:border-border/60',
      label: 'Neutral',
      count: wordData.neutral.reduce((sum, word) => sum + word.frequency, 0)
    },
    negative: { 
      icon: Frown, 
      color: 'text-red-600', 
      bgColor: 'bg-red-50 dark:bg-red-900/20',
      borderColor: 'border-red-200 dark:border-red-800',
      label: 'Negative',
      count: wordData.negative.reduce((sum, word) => sum + word.frequency, 0)
    }
  };

  const currentWords = wordData[activeSentiment];
  const currentConfig = sentimentConfig[activeSentiment];

  if (positiveKeywords.length === 0 && negativeKeywords.length === 0) {
    return (
      <div
        className={`flex items-center justify-center p-8 border-2 border-dashed border-border/60 dark:border-border/60 rounded-xl ${className}`}
      >
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 text-muted-foreground">...</div>
          <p className="text-muted-foreground dark:text-muted-foreground text-sm">
            No keywords available
          </p>
          <p className="text-muted-foreground dark:text-muted-foreground text-xs mt-1">
            Keywords will appear here after analysis
          </p>
        </div>
      </div>
    );
  }

  return (
    <Card className={`bg-card/90 dark:bg-card/95 border-border/60 dark:border-border/60 ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-foreground dark:text-foreground">
              Sentiment Word Analysis
            </CardTitle>
            <p className="text-sm text-muted-foreground dark:text-muted-foreground mt-1">
              Most frequently mentioned words by sentiment
            </p>
          </div>
          
          <Button variant="outline" size="sm" className="gap-2">
            <RotateCcw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Sentiment Toggle */}
        <div className="flex gap-2">
          {Object.entries(sentimentConfig).map(([key, config]) => {
            const IconComponent = config.icon;
            const isActive = activeSentiment === key;
            
            return (
              <Button
                key={key}
                onClick={() => setActiveSentiment(key as any)}
                variant="ghost"
                className={`flex-1 p-4 rounded-xl border-2 transition-all duration-300 ${
                  isActive 
                    ? `${config.bgColor} ${config.borderColor} ${config.color}` 
                    : 'bg-secondary/40 dark:bg-secondary/40/50 border-border/60 dark:border-border/60 text-muted-foreground dark:text-muted-foreground hover:bg-accent/60 dark:hover:bg-accent/60'
                }`}
              >
                <div className="flex items-center justify-center gap-2 mb-2">
                  <IconComponent className="w-5 h-5" />
                  <span className="font-medium">{config.label}</span>
                </div>
                <div className="text-xl font-bold">
                  {config.count.toLocaleString()}
                </div>
                <div className="text-xs opacity-75">
                  mentions
                </div>
              </Button>
            );
          })}
        </div>

        {/* Word Cloud Visualization */}
        <div className={`relative h-80 rounded-xl ${currentConfig.bgColor} border ${currentConfig.borderColor} overflow-hidden`}>
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-5">
            <svg className="w-full h-full" viewBox="0 0 400 320">
              <defs>
                <pattern id="wordPattern" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
                  <circle cx="30" cy="30" r="2" fill="currentColor" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#wordPattern)" />
            </svg>
          </div>

          {/* Animated Words */}
          {currentWords.map((wordItem, index) => (
            <motion.div
              key={`${activeSentiment}-${wordItem.word}`}
              className="absolute cursor-pointer select-none group"
              style={{
                left: `${wordItem.x}%`,
                top: `${wordItem.y}%`,
                fontSize: `${wordItem.size}px`,
                color: wordItem.color,
                fontWeight: 600,
                transform: 'translate(-50%, -50%)'
              }}
              initial={{ 
                opacity: 0, 
                scale: 0,
                rotate: -180
              }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                rotate: 0,
                y: [0, -5, 0]
              }}
              transition={{
                duration: 0.8,
                delay: index * 0.1,
                y: {
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: index * 0.2
                }
              }}
              whileHover={{ 
                scale: 1.2,
                rotate: [0, 5, -5, 0],
                transition: { duration: 0.3 }
              }}
            >
              {wordItem.word}
              
              {/* Hover Tooltip */}
              <motion.div
                className="absolute top-full left-1/2 -translate-x-1/2 mt-2 px-2 py-1 bg-background dark:bg-secondary/40 text-white dark:text-foreground text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10"
                initial={{ opacity: 0, y: 5 }}
                whileHover={{ opacity: 1, y: 0 }}
              >
                {wordItem.frequency} mentions
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-foreground dark:border-b-foreground" />
              </motion.div>
            </motion.div>
          ))}

          {/* Floating Particles */}
          {Array.from({ length: 6 }, (_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full opacity-20"
              style={{ 
                backgroundColor: currentWords[i % currentWords.length]?.color || '#6B7280',
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`
              }}
              animate={{
                y: [0, -20, 0],
                x: [0, 10, -10, 0],
                opacity: [0.2, 0.6, 0.2]
              }}
              transition={{
                duration: 4 + Math.random() * 2,
                repeat: Infinity,
                delay: i * 0.5,
                ease: "easeInOut"
              }}
            />
          ))}

          {/* Statistics Overlay */}
          <div className="absolute top-4 right-4 space-y-1">
            <Badge 
              variant="secondary" 
              className={`${currentConfig.bgColor} ${currentConfig.color} border-0`}
            >
              {currentWords.length} unique words
            </Badge>
            <Badge 
              variant="secondary" 
              className={`${currentConfig.bgColor} ${currentConfig.color} border-0`}
            >
              {currentConfig.count} total mentions
            </Badge>
          </div>
        </div>

        {/* Top Words List */}
        <div>
          <h4 className="font-medium text-foreground dark:text-foreground mb-3">
            Top 5 Words ({currentConfig.label})
          </h4>
          <div className="grid grid-cols-5 gap-2">
            {currentWords.slice(0, 5).map((wordItem, index) => (
              <motion.div
                key={wordItem.word}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="text-center p-2 bg-secondary/40 dark:bg-secondary/40/50 rounded-xl"
              >
                <div 
                  className="text-lg font-semibold mb-1"
                  style={{ color: wordItem.color }}
                >
                  {wordItem.word}
                </div>
                <div className="text-xs text-muted-foreground dark:text-muted-foreground">
                  {wordItem.frequency}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
