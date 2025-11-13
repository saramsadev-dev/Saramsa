"use client";

import { motion } from "framer-motion";
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
  // Use actual keywords from props, fallback to default words if empty
  const positiveWords = positiveKeywords.length > 0 
    ? positiveKeywords.slice(0, 9).map((word, index) => ({
        word,
        size: Math.max(10, 32 - index * 2),
        x: Math.random() * 80 + 10,
        y: Math.random() * 80 + 10,
      }))
    : [
        { word: "love", size: 32, x: 25, y: 30 },
        { word: "great", size: 28, x: 60, y: 20 },
        { word: "excellent", size: 24, x: 20, y: 60 },
        { word: "amazing", size: 20, x: 70, y: 50 },
        { word: "fantastic", size: 18, x: 45, y: 40 },
        { word: "perfect", size: 16, x: 30, y: 75 },
        { word: "helpful", size: 14, x: 80, y: 30 },
        { word: "useful", size: 12, x: 15, y: 45 },
        { word: "fast", size: 10, x: 85, y: 70 }
      ];

  const negativeWords = negativeKeywords.length > 0
    ? negativeKeywords.slice(0, 9).map((word, index) => ({
        word,
        size: Math.max(10, 32 - index * 2),
        x: Math.random() * 80 + 10,
        y: Math.random() * 80 + 10,
      }))
    : [
        { word: "slow", size: 32, x: 30, y: 35 },
        { word: "bad", size: 28, x: 65, y: 25 },
        { word: "terrible", size: 24, x: 25, y: 65 },
        { word: "awful", size: 20, x: 75, y: 55 },
        { word: "frustrating", size: 18, x: 50, y: 45 },
        { word: "confusing", size: 16, x: 35, y: 80 },
        { word: "broken", size: 14, x: 85, y: 35 },
        { word: "difficult", size: 12, x: 20, y: 50 },
        { word: "annoying", size: 10, x: 80, y: 75 }
      ];

  const WordCloud = ({ 
    words, 
    title, 
    color, 
    bgGradient 
  }: { 
    words: any[], 
    title: string, 
    color: string,
    bgGradient: string 
  }) => (
    <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle className={`text-lg font-semibold ${color}`}>
          {title}
        </CardTitle>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Display top sentiments which has a {title.toLowerCase().split(' ')[0]} tone in the feedback
        </p>
      </CardHeader>
      <CardContent>
        <div className={`relative h-64 ${bgGradient} rounded-lg overflow-hidden`}>
          {words.map((wordItem, index) => (
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
          
          {/* Floating Particles */}
          {Array.from({ length: 4 }, (_, i) => (
            <motion.div
              key={i}
              className={`absolute w-2 h-2 ${color.includes('green') ? 'bg-green-400' : 'bg-red-400'} rounded-full opacity-30`}
              style={{ 
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`
              }}
              animate={{
                y: [0, -10, 0],
                x: [0, 5, -5, 0],
                opacity: [0.3, 0.7, 0.3]
              }}
              transition={{
                duration: 3 + Math.random() * 2,
                repeat: Infinity,
                delay: i * 0.5,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );

  if (positiveKeywords.length === 0 && negativeKeywords.length === 0) {
    return (
      <div
        className={`flex items-center justify-center p-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg ${className}`}
      >
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 text-gray-400">💭</div>
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            No keywords available
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">
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
        color="text-green-600 dark:text-green-400"
        bgGradient="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/10 dark:to-emerald-900/10"
      />
      <WordCloud
        words={negativeWords}
        title="Negative Sentiments"
        color="text-red-600 dark:text-red-400"
        bgGradient="bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/10 dark:to-rose-900/10"
      />
    </div>
  );
}
