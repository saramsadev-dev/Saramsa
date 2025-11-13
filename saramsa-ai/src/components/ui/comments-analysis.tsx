'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Send, Loader2, AlertCircle, CheckCircle, Heart, TrendingUp, Filter } from 'lucide-react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { analyzeComments } from '@/store/features/analysis/analysisSlice';

interface WishlistItem {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  votes: number;
  status: 'pending' | 'in-progress' | 'completed';
  createdAt: string;
}

interface AnalysisResult {
  data?: {
    sentiment_analysis?: string;
    key_insights?: string;
    recommendations?: string;
  };
}

export function CommentsAnalysisComponent() {
  const dispatch = useAppDispatch();
  const { loading, error: reduxError, isAnalyzing } = useAppSelector(state => state.analysis);
  
  const [comments, setComments] = useState<string>('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'wishlist'>('analysis');
  const [wishlistItems, setWishlistItems] = useState<WishlistItem[]>([
    {
      id: '1',
      title: 'Dark Mode Support',
      description: 'Add dark mode theme option for better user experience',
      priority: 'high',
      category: 'UI/UX',
      votes: 45,
      status: 'pending',
      createdAt: '2024-01-15'
    },
    {
      id: '2',
      title: 'Mobile App',
      description: 'Develop native mobile applications for iOS and Android',
      priority: 'medium',
      category: 'Platform',
      votes: 32,
      status: 'in-progress',
      createdAt: '2024-01-10'
    },
    {
      id: '3',
      title: 'Advanced Analytics',
      description: 'Implement detailed analytics dashboard with custom reports',
      priority: 'low',
      category: 'Features',
      votes: 18,
      status: 'pending',
      createdAt: '2024-01-05'
    }
  ]);

  const handleAnalyze = async () => {
    if (!comments.trim()) {
      setError('Please enter some comments to analyze');
      return;
    }

    setError(null);
    setResult(null);

    try {
      const commentsArray = comments.split('\n').filter(comment => comment.trim());
      const analysisResult = await dispatch(analyzeComments({ comments: commentsArray })).unwrap();
      setResult(analysisResult);
    } catch (error: unknown) {
      const err = error as { message?: string };
      setError(err.message || reduxError || 'Analysis failed');
    }
  };

  const handleClear = () => {
    setComments('');
    setResult(null);
    setError(null);
  };

  const handleVote = (itemId: string) => {
    setWishlistItems(prev => 
      prev.map(item => 
        item.id === itemId 
          ? { ...item, votes: item.votes + 1 }
          : item
      )
    );
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100 dark:bg-red-900/20';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'in-progress': return 'text-saramsa-brand bg-saramsa-accent/10 dark:bg-saramsa-accent/20';
      case 'pending': return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                Saramsa.ai
              </span>
            </div>

            {/* Navigation Tabs */}
            <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('analysis')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  activeTab === 'analysis' 
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Comments Analysis
              </button>
              <button
                onClick={() => setActiveTab('wishlist')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                  activeTab === 'wishlist' 
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Wishlist
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          {activeTab === 'analysis' ? (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-8">
              {/* Header */}
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-full flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                  Comments Analysis
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                  Analyze customer feedback and comments for insights
                </p>
              </div>

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center space-x-3"
                  >
                    <AlertCircle className="w-5 h-5 text-red-500" />
                    <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Input Section */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Enter Comments
                  </h3>
                  <div className="space-y-4">
                    <textarea
                      value={comments}
                      onChange={(e) => setComments(e.target.value)}
                      placeholder="Enter your comments here, one per line...
Example:
The app is great but slow
I love the new features
The UI needs improvement"
                      className="w-full h-64 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:border-[#E603EB] focus:ring-[#E603EB]/20 focus:outline-none transition-all duration-300 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    />
                    
                    <div className="flex space-x-3">
                      <button
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !comments.trim()}
                        className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center justify-center space-x-2 ${
                          comments.trim() && !isAnalyzing
                            ? 'bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 shadow-lg hover:shadow-xl'
                            : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        {isAnalyzing ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Analyzing...</span>
                          </>
                        ) : (
                          <>
                            <Send className="w-4 h-4" />
                            <span>Analyze Comments</span>
                          </>
                        )}
                      </button>
                      
                      <button
                        onClick={handleClear}
                        className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>

                {/* Results Section */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Analysis Results
                  </h3>
                  
                  <AnimatePresence>
                    {result ? (
                      <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="space-y-4"
                      >
                        <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                          <div className="flex items-center space-x-2 mb-2">
                            <CheckCircle className="w-5 h-5 text-green-500" />
                            <span className="font-medium text-green-800 dark:text-green-200">
                              Analysis Complete
                            </span>
                          </div>
                          <p className="text-green-600 dark:text-green-400 text-sm">
                            Successfully analyzed {comments.split('\n').filter(c => c.trim()).length} comments
                          </p>
                        </div>

                        <div className="space-y-4">
                          {result.analysisData?.overall && (
                            <div className="p-4 bg-saramsa-accent/10 dark:bg-saramsa-accent/20 border border-saramsa-brand/30 dark:border-saramsa-brand/50 rounded-lg">
                              <h4 className="font-semibold text-saramsa-brand dark:text-saramsa-brand mb-2">
                                Sentiment Analysis
                              </h4>
                              <div className="text-saramsa-brand/80 dark:text-saramsa-brand/90 text-sm">
                                <p>Positive: {result.analysisData.overall.positive}%</p>
                                <p>Negative: {result.analysisData.overall.negative}%</p>
                                <p>Neutral: {result.analysisData.overall.neutral}%</p>
                              </div>
                            </div>
                          )}

                          {result.analysisData?.features && result.analysisData.features.length > 0 && (
                            <div className="p-4 bg-saramsa-accent/10 dark:bg-saramsa-accent/20 border border-saramsa-brand/30 dark:border-saramsa-brand/50 rounded-lg">
                              <h4 className="font-semibold text-saramsa-brand dark:text-saramsa-brand mb-2">
                                Key Features
                              </h4>
                              <div className="text-saramsa-brand/80 dark:text-saramsa-brand/90 text-sm space-y-2">
                                {result.analysisData.features.map((feature: any, index: number) => (
                                  <div key={index}>
                                    <strong>{feature.name}:</strong> {feature.description}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {result.analysisData?.positive_keywords && result.analysisData.positive_keywords.length > 0 && (
                            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                              <h4 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">
                                Positive Keywords
                              </h4>
                              <div className="text-orange-600 dark:text-orange-400 text-sm">
                                {result.analysisData.positive_keywords.map((kw: any, index: number) => (
                                  <span key={index} className="inline-block bg-orange-100 dark:bg-orange-800 px-2 py-1 rounded mr-2 mb-1">
                                    {kw.keyword} ({kw.sentiment})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {result.analysisData?.negative_keywords && result.analysisData.negative_keywords.length > 0 && (
                            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                              <h4 className="font-semibold text-red-800 dark:text-red-200 mb-2">
                                Negative Keywords
                              </h4>
                              <div className="text-red-600 dark:text-red-400 text-sm">
                                {result.analysisData.negative_keywords.map((kw: any, index: number) => (
                                  <span key={index} className="inline-block bg-red-100 dark:bg-red-800 px-2 py-1 rounded mr-2 mb-1">
                                    {kw.keyword} ({kw.sentiment})
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ) : (
                      <div className="p-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-center">
                        <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500 dark:text-gray-400">
                          Analysis results will appear here after processing
                        </p>
                      </div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Features Info */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="w-8 h-8 bg-saramsa-accent/20 dark:bg-saramsa-accent/30 rounded-lg flex items-center justify-center mx-auto mb-2">
                    📊
                  </div>
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm">Sentiment Analysis</h4>
                  <p className="text-gray-500 dark:text-gray-400 text-xs">AI-powered sentiment detection</p>
                </div>
                
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-2">
                    💡
                  </div>
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm">Key Insights</h4>
                  <p className="text-gray-500 dark:text-gray-400 text-xs">Extract important patterns</p>
                </div>
                
                <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="w-8 h-8 bg-saramsa-accent/20 dark:bg-saramsa-accent/30 rounded-lg flex items-center justify-center mx-auto mb-2">
                    🎯
                  </div>
                  <h4 className="font-medium text-gray-900 dark:text-white text-sm">Recommendations</h4>
                  <p className="text-gray-500 dark:text-gray-400 text-xs">Actionable improvement suggestions</p>
                </div>
              </div>
            </div>
          ) : (
            /* Wishlist View */
            <div className="space-y-6">
              {/* Wishlist Header */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Feature Wishlist</h2>
                    <p className="text-gray-600 dark:text-gray-400">Vote for features you&apos;d like to see implemented</p>
                  </div>
                  <button className="px-4 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white rounded-lg hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 transition-all duration-200">
                    + Add Feature Request
                  </button>
                </div>
                
                {/* Filter Bar */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-gray-500" />
                    <select className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
                      <option>All Categories</option>
                      <option>UI/UX</option>
                      <option>Platform</option>
                      <option>Features</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-gray-500" />
                    <select className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm">
                      <option>Most Voted</option>
                      <option>Recently Added</option>
                      <option>High Priority</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Wishlist Items */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {wishlistItems.map((item) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-xl transition-all duration-300"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-gray-900 dark:text-white text-lg">
                        {item.title}
                      </h3>
                      <button
                        onClick={() => handleVote(item.id)}
                        className="flex items-center gap-1 text-gray-500 hover:text-red-500 transition-colors"
                      >
                        <Heart className="w-4 h-4" />
                        <span className="text-sm font-medium">{item.votes}</span>
                      </button>
                    </div>
                    
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                      {item.description}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}>
                          {item.priority}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                          {item.status}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {item.category}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
} 