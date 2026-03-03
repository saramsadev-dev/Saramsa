"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../card";

interface KeywordCloudProps {
  positiveKeywords: string[];
  negativeKeywords: string[];
  className?: string;
}

export function KeywordCloud({
  positiveKeywords,
  negativeKeywords,
  className = "",
}: KeywordCloudProps) {
  const seededPosition = (seed: string) => {
    let hash = 0;
    for (let i = 0; i < seed.length; i += 1) {
      hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
    }
    const x = ((hash % 8000) / 100) + 10;
    const y = (((hash / 97) % 8000) / 100) + 10;
    return { x, y };
  };

  const positiveWords = useMemo(() => {
    if (positiveKeywords.length === 0) return [];
    return positiveKeywords.slice(0, 9).map((word, index) => {
      const pos = seededPosition(`pos:${word}:${index}`);
      return {
        word,
        size: Math.max(10, 32 - index * 2),
        x: pos.x,
        y: pos.y,
      };
    });
  }, [positiveKeywords]);

  const negativeWords = useMemo(() => {
    if (negativeKeywords.length === 0) return [];
    return negativeKeywords.slice(0, 9).map((word, index) => {
      const pos = seededPosition(`neg:${word}:${index}`);
      return {
        word,
        size: Math.max(10, 32 - index * 2),
        x: pos.x,
        y: pos.y,
      };
    });
  }, [negativeKeywords]);

  const WordCloud = ({ 
    words, 
    title, 
    color
  }: { 
    words: any[], 
    title: string, 
    color: string
  }) => (
    <Card className="bg-card/80 border border-border/60">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-foreground">
          {title}
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Display top sentiments which has a {title.toLowerCase().split(' ')[0]} tone in the feedback
        </p>
      </CardHeader>
      <CardContent>
        <div className="relative h-64 bg-secondary/40 rounded-xl overflow-hidden">
          {words.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-sm text-muted-foreground">No keywords</p>
            </div>
          ) : words.map((wordItem, index) => (
            <motion.div
              key={wordItem.word}
              className={`absolute cursor-pointer select-none font-medium ${color}`}
              style={{
                left: `${wordItem.x}%`,
                top: `${wordItem.y}%`,
                fontSize: `${wordItem.size}px`,
                transform: 'translate(-50%, -50%)'
              }}
              initial={{ 
                opacity: 0, 
                scale: 0
              }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                y: [0, -3, 0]
              }}
              transition={{
                duration: 0.8,
                delay: index * 0.1,
                y: {
                  duration: 2 + Math.random(),
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: index * 0.3
                }
              }}
              whileHover={{ 
                scale: 1.2,
                transition: { duration: 0.2 }
              }}
            >
              {wordItem.word}
            </motion.div>
          ))}

        </div>
      </CardContent>
    </Card>
  );

  if (positiveKeywords.length === 0 && negativeKeywords.length === 0) {
    return (
      <div
        className={`flex items-center justify-center p-8 border-2 border-dashed border-border/60 dark:border-border/60 rounded-xl ${className}`}
      >
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 text-muted-foreground">💭</div>
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
    <div className={`grid grid-cols-1 lg:grid-cols-2 gap-6 ${className}`}>
      <WordCloud
        words={positiveWords}
        title="Positive Sentiments"
        color="text-saramsa-brand"
      />
      <WordCloud
        words={negativeWords}
        title="Negative Sentiments"
        color="text-saramsa-gradient-to"
      />
    </div>
  );
}
