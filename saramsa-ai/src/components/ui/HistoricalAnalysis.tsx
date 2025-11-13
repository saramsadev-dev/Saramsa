'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiRequest } from '@/lib/apiRequest';
import { Calendar, TrendingUp, TrendingDown, BarChart3, History } from 'lucide-react';

interface AnalysisData {
  id: string;
  version: number;
  quarter: string;
  analysis_date: string;
  is_latest: boolean;
  sentimentsummary?: {
    positive: number;
    negative: number;
    neutral: number;
  };
  counts?: {
    total: number;
    positive: number;
    negative: number;
    neutral: number;
  };
  featureasba?: Array<{
    name: string;
    sentiment: {
      positive: number;
      negative: number;
      neutral: number;
    };
    description: string;
    keywords: string[];
  }>;
}

interface HistoricalAnalysisProps {
  projectId: string;
}

export function HistoricalAnalysis({ projectId }: HistoricalAnalysisProps) {
  const [analyses, setAnalyses] = useState<AnalysisData[]>([]);
  const [selectedQuarter, setSelectedQuarter] = useState<string>('');
  const [cumulativeData, setCumulativeData] = useState<any>(null);
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('history');

  useEffect(() => {
    if (projectId) {
      loadAnalysisHistory();
    }
  }, [projectId]);

  const loadAnalysisHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiRequest('get', `/insights/analysis/history/?project_id=${projectId}`, undefined, true);
      
      if (response.data.success) {
        setAnalyses(response.data.analyses);
        if (response.data.analyses.length > 0) {
          setSelectedQuarter(response.data.analyses[response.data.analyses.length - 1].quarter);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load analysis history');
    } finally {
      setLoading(false);
    }
  };

  const loadCumulativeAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiRequest('get', `/insights/analysis/cumulative/?project_id=${projectId}`, undefined, true);
      
      if (response.data.success) {
        setCumulativeData(response.data.cumulative_analysis);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load cumulative analysis');
    } finally {
      setLoading(false);
    }
  };

  const loadComparison = async (quarter1: string, quarter2: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiRequest('get', `/insights/analysis/compare/?project_id=${projectId}&quarter1=${quarter1}&quarter2=${quarter2}`, undefined, true);
      
      if (response.data.success) {
        setComparisonData(response.data.comparison);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  };

  const getSelectedAnalysis = () => {
    return analyses.find(a => a.quarter === selectedQuarter);
  };

  const getQuarterOptions = () => {
    return analyses.map(a => a.quarter).filter((quarter, index, self) => self.indexOf(quarter) === index);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 60) return 'text-green-600';
    if (sentiment > 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <BarChart3 className="w-4 h-4 text-gray-600" />;
  };

  if (loading && analyses.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Historical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Historical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadAnalysisHistory} variant="outline">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (analyses.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5" />
            Historical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-500">No historical analysis data available.</p>
            <p className="text-sm text-gray-400 mt-2">
              Upload feedback data to start building your analysis history.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="w-5 h-5" />
          Historical Analysis
        </CardTitle>
        <CardDescription>
          View and compare analysis data across different quarters
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="cumulative">Cumulative</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
          </TabsList>

          <TabsContent value="history" className="space-y-4">
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium">Select Quarter:</label>
              <Select value={selectedQuarter} onChange={(e) => setSelectedQuarter(e.target.value)}>
                {getQuarterOptions().map(quarter => (
                  <option key={quarter} value={quarter}>
                    {quarter}
                  </option>
                ))}
              </Select>
            </div>

            {selectedQuarter && (
              <div className="space-y-4">
                {(() => {
                  const analysis = getSelectedAnalysis();
                  if (!analysis) return null;

                  return (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Sentiment Overview</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm">Positive:</span>
                              <span className={`font-medium ${getSentimentColor(analysis.sentimentsummary?.positive || 0)}`}>
                                {analysis.sentimentsummary?.positive?.toFixed(1) || 0}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm">Negative:</span>
                              <span className={`font-medium ${getSentimentColor(analysis.sentimentsummary?.negative || 0)}`}>
                                {analysis.sentimentsummary?.negative?.toFixed(1) || 0}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm">Neutral:</span>
                              <span className="text-gray-600 font-medium">
                                {analysis.sentimentsummary?.neutral?.toFixed(1) || 0}%
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Feedback Count</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-blue-600">
                            {analysis.counts?.total || 0}
                          </div>
                          <p className="text-sm text-gray-500">
                            Total comments analyzed
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Analysis Date</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-sm">
                            {formatDate(analysis.analysis_date)}
                          </div>
                          <Badge variant={analysis.is_latest ? "default" : "secondary"}>
                            {analysis.is_latest ? "Latest" : `v${analysis.version}`}
                          </Badge>
                        </CardContent>
                      </Card>
                    </div>
                  );
                })()}
              </div>
            )}
          </TabsContent>

          <TabsContent value="cumulative" className="space-y-4">
            <div className="flex items-center gap-4">
              <Button onClick={loadCumulativeAnalysis} disabled={loading}>
                {loading ? 'Loading...' : 'Load Cumulative Analysis'}
              </Button>
            </div>

            {cumulativeData && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Total Analyses</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-blue-600">
                        {cumulativeData.total_analyses}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Total Comments</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {cumulativeData.total_comments}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Quarters Covered</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-purple-600">
                        {cumulativeData.quarters_covered.length}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Latest Quarter</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-lg font-semibold">
                        {cumulativeData.latest_quarter}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Quarters Covered</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {cumulativeData.quarters_covered.map((quarter: string) => (
                        <Badge key={quarter} variant="outline">
                          {quarter}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="compare" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Quarter 1:</label>
                <Select onChange={(e) => {
                  const value = e.target.value;
                  if (comparisonData?.quarter2?.quarter) {
                    loadComparison(value, comparisonData.quarter2.quarter);
                  }
                }}>
                  <option value="">Select first quarter</option>
                  {getQuarterOptions().map(quarter => (
                    <option key={quarter} value={quarter}>
                      {quarter}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Quarter 2:</label>
                <Select onChange={(e) => {
                  const value = e.target.value;
                  if (comparisonData?.quarter1?.quarter) {
                    loadComparison(comparisonData.quarter1.quarter, value);
                  }
                }}>
                  <option value="">Select second quarter</option>
                  {getQuarterOptions().map(quarter => (
                    <option key={quarter} value={quarter}>
                      {quarter}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            {comparisonData && (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Comparison Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-sm text-gray-500 mb-1">Sentiment Change</div>
                        <div className="flex items-center justify-center gap-2">
                          {getTrendIcon(comparisonData.comparison.sentiment_change.positive_change)}
                          <span className="font-medium">
                            {comparisonData.comparison.sentiment_change.positive_change > 0 ? '+' : ''}
                            {comparisonData.comparison.sentiment_change.positive_change.toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="text-sm text-gray-500 mb-1">Feature Change</div>
                        <div className="flex items-center justify-center gap-2">
                          {getTrendIcon(comparisonData.comparison.feature_change)}
                          <span className="font-medium">
                            {comparisonData.comparison.feature_change > 0 ? '+' : ''}
                            {comparisonData.comparison.feature_change}
                          </span>
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="text-sm text-gray-500 mb-1">Comment Change</div>
                        <div className="flex items-center justify-center gap-2">
                          {getTrendIcon(comparisonData.comparison.comment_change)}
                          <span className="font-medium">
                            {comparisonData.comparison.comment_change > 0 ? '+' : ''}
                            {comparisonData.comparison.comment_change}
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
