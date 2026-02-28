'use client';

import { useEffect, useState, useMemo, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import { 
  analyzeComments, 
  getLatestAnalysis, 
  getConsolidatedDashboardData,
  generateUserStories,
  setAnalysisData, 
  setDeepAnalysis, 
  setLoadedComments,
  clearAnalysisData,
  clearError 
} from '../../../store/features/analysis/analysisSlice';
import { fetchProjects } from '../../../store/features/projects/projectsSlice';
import { fetchIntegrationAccounts } from '../../../store/features/integrations/integrationsSlice';
import { 
  clearCurrentProjectUserStories,
  setCurrentProjectUserStories,
  fetchUserStoriesByProject
} from '../../../store/features/userStories/userStoriesSlice';


import type { AnalysisData } from '@/types/analysis';
import { apiRequest } from '@/lib/apiRequest';
import { Sparkles } from 'lucide-react';
import { AnalysisProjectSelector } from './AnalysisProjectSelector';
import { UploadPanel } from './UploadPanel';
import { MetricsCards } from './MetricsCards';
import { FeatureSentimentsTable } from '../../dashboard/analysisDashboard/FeatureSentimentsTable';
import { SentimentCharts } from '../../dashboard/analysisDashboard/SentimentCharts';
import { KeywordCloud } from './KeywordCloud';
import { AdvancedWordCloud } from './AdvancedWordCloud';
// import { NavigationTabs } from './NavigationTabs'; // Inlined below
import { UserStoryList } from '../userStoryList';

import { LoaderForDashboard } from '@/components/dashboard/analysisDashboard/LoaderForDashboard';
import { Button } from '@/components/ui/button';

// Local interface for the component
interface LocalFeatureSentiment {
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

interface DashboardProps {
  data?: AnalysisData;
  onProjectSelect?: (projectId: string) => void;
  initialProjectId?: string;
  skipBootstrapFetches?: boolean; // when true, parent handles projects/integrations fetching
}

type ValidationResult = { isValid: true } | { isValid: false; error: string };

const MAX_SIZE_BYTES: Record<string, number> = {
  'text/csv': 250 * 1024 * 1024,
  'application/json': 250 * 1024 * 1024,
  'audio/mpeg': 500 * 1024 * 1024,
};

const ACCEPTED_TYPES = new Set(Object.keys(MAX_SIZE_BYTES));

function isAcceptedType(type: string): boolean {
  return ACCEPTED_TYPES.has(type) || type.includes('csv') || type.includes('json');
}

function acceptedByFileName(name: string): boolean {
  const lower = name.toLowerCase();
  return lower.endsWith('.csv') || lower.endsWith('.json');
}

function validateFile(file: File): ValidationResult {
  const typeOk = isAcceptedType(file.type) || acceptedByFileName(file.name);
  if (!typeOk) {
    return { isValid: false, error: 'Unsupported file type. Use CSV or JSON.' };
  }

  const typeForLimit =
    file.type && isAcceptedType(file.type)
      ? file.type
      : (file.name.toLowerCase().endsWith('.json') ? 'application/json' : 'text/csv');
  const limit = MAX_SIZE_BYTES[typeForLimit];
  if (limit && file.size > limit) {
    return { isValid: false, error: 'File is too large. Maximum size is 250 MB for CSV and JSON.' };
  }

  return { isValid: true };
}

export function DashboardComponent({ data, onProjectSelect, initialProjectId, skipBootstrapFetches = false }: DashboardProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { 
    analysisData, 
    deepAnalysis, 
    loading, 
    error, 
    isAnalyzing,
    analyzingByProject,
    loadedComments,
    latestAnalysis,
    projectContext,
  } = useSelector((state: RootState) => state.analysis);
  
  const { analysis: jiraAnalysis, isAnalyzing: isJiraAnalyzing } = useSelector((state: RootState) => state.jira);
  const { projects, loading: projectsLoading } = useSelector((state: RootState) => state.projects);
  const { user } = useSelector((state: RootState) => state.auth);
  const { 
    currentProjectUserStories, 
  } = useSelector((state: RootState) => state.userStories);
  
  const [activeView, setActiveView] = useState<'dashboard' | 'user-stories'>('dashboard');
  const [topFile, setTopFile] = useState<File | null>(null);
 
  const [topError, setTopError] = useState<string | null>(null);
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [editedKeywords, setEditedKeywords] = useState<{ [key: string]: string[] }>({});
  const [currentProjectId, setCurrentProjectId] = useState<string>("");
  const [personalProjectId, setPersonalProjectId] = useState<string>('');
  const [isGeneratingUserStories, setIsGeneratingUserStories] = useState<boolean>(false);
  
  // Declare all refs at the top to prevent recreation on every render
  const didInitRef = useRef(false);
  const hasConsolidatedFetchRef = useRef(false);
  const lastFetchedProjectRef = useRef<string | null>(null);
  const lastProcessedAnalysisIdRef = useRef<string | null>(null);
  useEffect(() => {
    const contextProjectId = projectContext?.project_id;
    if (!contextProjectId) return;

    if (projectContext?.is_draft) {
      setPersonalProjectId(contextProjectId);
    }

    if (!currentProjectId) {
      setCurrentProjectId(contextProjectId);
    }

    if (typeof window !== 'undefined') {
      localStorage.setItem('project_id', contextProjectId);
    }
  }, [projectContext]); // Removed currentProjectId from dependencies to prevent loop
  const [wordCloudView, setWordCloudView] = useState<'split' | 'advanced'>('split');

  const projectId = typeof window !== 'undefined' ? localStorage.getItem('project_id') : null;
  const analyzingKey = currentProjectId || projectId || 'personal';
  const isProjectAnalyzing = !!analyzingByProject[analyzingKey] || false;
  const selectedPlatform = useMemo((): 'azure' | 'jira' | null => {
    if (!projects || !projects.length) return null;
    const pid = currentProjectId || projectId || '';
    const proj = projects.find((p: any) => p.id === pid);
    const provider = proj?.externalLinks?.[0]?.provider;
    return provider === 'jira' ? 'jira' : provider === 'azure' ? 'azure' : null;
  }, [projects, currentProjectId, projectId]);
  // Handle keyword updates
  const handleKeywordsUpdate = (featureName: string, keywords: string[]) => {
    setEditedKeywords(prev => ({
      ...prev,
      [featureName]: keywords
    }));
  };


  // Handle regeneration of analysis
  const handleRegenerateAnalysis = async () => {
    if (!loadedComments || loadedComments.length === 0) {
      console.error('No comments available for regeneration');
      
        // Try to load comments from backend
        const regenerationProjectId = currentProjectId || personalProjectId || '';
        if (regenerationProjectId || !currentProjectId) {
          try {
            const queryParam = regenerationProjectId ? `project_id=${regenerationProjectId}` : 'is_personal=true';
            console.log('🔄 Loading comments from backend for regeneration, query:', queryParam);
            const response = await apiRequest('get', `/insights/comments/?${queryParam}`, undefined, true);
          if (response.data.success && response.data.data.comments && response.data.data.comments.length > 0) {
            dispatch(setLoadedComments(response.data.data.comments));
            console.log(`✅ Loaded ${response.data.data.comments.length} comments from backend for regeneration`);
            if (!regenerationProjectId && response.data.data.project_id) {
              setPersonalProjectId(response.data.data.project_id);
            }
            // Continue with regeneration using the loaded comments
          } else {
            console.log('⚠️ No comments found in backend for this context');
            alert('No comments found for this analysis. Please upload a file with comments first.');
            return;
          }
        } catch (error: any) {
          console.error('❌ Error loading comments from backend:', error);
          console.error('Error details:', {
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data,
            url: error.config?.url
          });
          alert('Failed to load comments from backend. Please try again or upload a new file.');
          return;
        }
      } else {
        alert('No project ID available. Please select a project first.');
        return;
      }
    }

    try {
      // Call the new backend endpoint for keyword updates and regeneration
      const response = await apiRequest('post', '/insights/keywords/update/', {
        project_id: currentProjectId || personalProjectId || undefined,
        updated_keywords: editedKeywords,
        comments: loadedComments
      }, true);

      if (response.data.success) {
        // Update the analysis data with the new results
        dispatch(setAnalysisData(response.data));
        
        // Clear edited keywords after successful regeneration
        setEditedKeywords({});
        
        console.log('Analysis regenerated successfully:', response.data);
      }
    } catch (error) {
      console.error('Failed to regenerate analysis:', error);
      alert('Failed to regenerate analysis. Please try again.');
    }
  };

  // Clear all stored data (comments and analysis)
  const handleClearData = () => {
    if (confirm('Are you sure you want to clear all stored data? This will remove comments and analysis results.')) {
      dispatch(setLoadedComments(null));
      dispatch(clearAnalysisData());
      setEditedKeywords({});
      console.log('All stored data cleared');
    }
  };

  // Use analysis data directly (no cumulative view)
  const activeAnalysisData = analysisData;

  // Transform features to include edited status
  const transformedFeatures = useMemo(() => {
    if (!activeAnalysisData?.analysisData?.features) return [];
    
    return activeAnalysisData.analysisData.features.map((feature: any) => ({
      name: feature.name || feature.feature,  // Backend uses "feature" field, fallback to "name"
      description: feature.description || '',
      sentiment: {
        positive: feature.positive || feature.sentiment?.positive || 0,
        negative: feature.negative || feature.sentiment?.negative || 0,
        neutral: feature.neutral || feature.sentiment?.neutral || 0,
      },
      keywords: feature.keywords || [],
      comment_count: feature.comment_count,
      isEdited: editedKeywords[feature.name || feature.feature] !== undefined
    })) as LocalFeatureSentiment[];
  }, [activeAnalysisData?.analysisData?.features, editedKeywords]);

  const hasAnalysisResults = useMemo(() => {
    if (!activeAnalysisData?.analysisData) return false;
    const counts = activeAnalysisData.analysisData.counts;
    const features = activeAnalysisData.analysisData.features;
    const positiveKeywords = activeAnalysisData.analysisData.positive_keywords;
    const negativeKeywords = activeAnalysisData.analysisData.negative_keywords;

    const totalComments = counts?.total ?? 0;
    const hasFeatureData = Array.isArray(features) && features.length > 0;
    const hasKeywordData =
      (Array.isArray(positiveKeywords) && positiveKeywords.length > 0) ||
      (Array.isArray(negativeKeywords) && negativeKeywords.length > 0);

    return totalComments > 0 || hasFeatureData || hasKeywordData;
  }, [activeAnalysisData?.analysisData]);

  console.log("Dashboard data:0------->", {
    activeAnalysisData,
    hasAnalysisData: !!activeAnalysisData?.analysisData,
    analysisDataStructure: activeAnalysisData?.analysisData ? {
      hasOverall: !!activeAnalysisData.analysisData.overall,
      hasCounts: !!activeAnalysisData.analysisData.counts,
      featuresCount: activeAnalysisData.analysisData.features?.length,
      hasPositiveKeywords: !!activeAnalysisData.analysisData.positive_keywords?.length,
      hasNegativeKeywords: !!activeAnalysisData.analysisData.negative_keywords?.length
    } : null,
    hasAnalysisResults
  });
  const userStoryFromDeepAnalysis = useMemo(() => {
    if (!deepAnalysis?.work_items || deepAnalysis.work_items.length === 0) {
      return null;
    }

    const derivedId =
      deepAnalysis.id ||
      (deepAnalysis.projectId ? `consolidated_${deepAnalysis.projectId}` : currentProjectId ? `consolidated_${currentProjectId}` : undefined);

    if (!derivedId) {
      return null;
    }

    return {
      id: derivedId,
      type: deepAnalysis.type || 'user_story',
      userId: deepAnalysis.userId,
      projectId: deepAnalysis.projectId || currentProjectId,
      process_template: deepAnalysis.process_template || 'Agile',
      platform: deepAnalysis.platform,
      work_items: deepAnalysis.work_items,
      summary: deepAnalysis.summary,
      comments_count: deepAnalysis.comments_count || 0,
      generated_at: deepAnalysis.createdAt || deepAnalysis.generated_at || new Date().toISOString()
    };
  }, [deepAnalysis]);

  useEffect(() => {
    if (!userStoryFromDeepAnalysis) return;
    if (currentProjectUserStories && currentProjectUserStories.length > 0) return;

    console.log('🔍 Storing user story from deep analysis:', userStoryFromDeepAnalysis);
    dispatch(setCurrentProjectUserStories([userStoryFromDeepAnalysis]));
  }, [dispatch, userStoryFromDeepAnalysis, currentProjectUserStories]);
  
  // Log when analysis data changes
  useEffect(() => {
    console.log('Redux analysis state updated:', {
      analysisData,
      deepAnalysis,
      loading,
      error,
      isAnalyzing,
      loadedComments
    });
  }, [analysisData, deepAnalysis, loading, error, isAnalyzing, loadedComments]);

  // Process latestAnalysis from getConsolidatedDashboardData and set analysisData
  useEffect(() => {
    if (!latestAnalysis) {
      console.log('🔍 Dashboard: No latestAnalysis available');
      return;
    }
    
    const analysisId = latestAnalysis.analysis?.id;
    
    // Skip if we've already processed this analysis
    if (analysisId && lastProcessedAnalysisIdRef.current === analysisId) {
      console.log('🔍 Dashboard: Analysis already processed, skipping', { analysisId });
      return;
    }
    
    console.log('🔍 Dashboard: Processing latestAnalysis from consolidated data:', {
      exists: latestAnalysis.exists,
      hasAnalysis: !!latestAnalysis.analysis,
      analysisId: analysisId,
      lastProcessedId: lastProcessedAnalysisIdRef.current
    });
    
    if (latestAnalysis.exists && latestAnalysis.analysis) {
      const a = latestAnalysis.analysis; // Extract the nested analysis data
      console.log('🔍 Dashboard: Analysis data from consolidated fetch:', {
        id: a.id,
        hasAnalysisData: !!a.analysisData,
        hasUserStories: !!a.userStories,
        analysisDataKeys: a.analysisData ? Object.keys(a.analysisData) : [],
        allKeys: Object.keys(a)
      });
      
      // The backend now returns data in the new format (analysisData field)
      // Check if data is already in the correct frontend format
      if (a.analysisData) {
        // Data is already in the new format, use it directly
        console.log('🔍 Dashboard: Using new format data directly from consolidated fetch');
        console.log('🔍 Dashboard: Setting analysisData with structure:', {
          id: a.id,
          hasAnalysisData: !!a.analysisData,
          counts: a.analysisData.counts,
          featuresCount: a.analysisData.features?.length,
          overall: a.analysisData.overall
        });
        dispatch(setAnalysisData(a));
        dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
        lastProcessedAnalysisIdRef.current = a.id;
      } else if (a.result?.overall && a.result?.counts && a.result?.features !== undefined) {
        // Data is nested under result field - normalize it and merge metadata
        console.log('🔍 Dashboard: Using result field data, normalizing from consolidated fetch');
        const normalized = normalizeAnalysis(a.result);
        // Merge metadata from the analysis object
        if (normalized) {
          normalized.id = a.id || normalized.id;
          normalized.projectId = a.projectId || normalized.projectId;
          normalized.userId = a.userId || normalized.userId;
          normalized.createdAt = a.createdAt || a.analysis_date || normalized.createdAt;
          normalized.analysisType = a.analysis_type || normalized.analysisType;
        }
        dispatch(setAnalysisData(normalized));
        dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
        lastProcessedAnalysisIdRef.current = normalized?.id || a.id;
      } else if (a.sentimentsummary && a.counts && a.featureasba !== undefined) {
        // Data is in the old format, normalize it
        console.log('🔍 Dashboard: Using old format data, normalizing from consolidated fetch');
        const normalized = normalizeAnalysis(a);
        dispatch(setAnalysisData(normalized));
        dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
        lastProcessedAnalysisIdRef.current = normalized?.id || a.id;
      } else if (a.overall && a.counts && a.features !== undefined) {
        // Fallback: data is in the old format, normalize it
        console.log('🔍 Dashboard: Using old format data (fallback), normalizing from consolidated fetch');
        const normalized = normalizeAnalysis(a);
        dispatch(setAnalysisData(normalized));
        dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
        lastProcessedAnalysisIdRef.current = normalized?.id || a.id;
      } else if (a.commentAnalysis) {
        // Fallback: use commentAnalysis if available
        console.log('🔍 Dashboard: Using commentAnalysis as fallback from consolidated fetch');
        const ca = Array.isArray(a.commentAnalysis)
          ? (typeof a.commentAnalysis[0] === 'string' ? JSON.parse(a.commentAnalysis[0]) : a.commentAnalysis[0])
          : a.commentAnalysis;
        const normalized = normalizeAnalysis(ca);
        dispatch(setAnalysisData(normalized));
        dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
        lastProcessedAnalysisIdRef.current = normalized?.id || a.id;
      } else {
        console.log('🔍 Dashboard: No analysis data found in consolidated fetch, analysis structure:', Object.keys(a), 'has result:', !!a.result);
        dispatch(setAnalysisData(null));
        dispatch(setDeepAnalysis(null));
        lastProcessedAnalysisIdRef.current = null;
      }
    } else {
      console.log('🔍 Dashboard: No analysis exists for project in consolidated fetch', {
        exists: latestAnalysis.exists,
        hasAnalysis: !!latestAnalysis.analysis
      });
      dispatch(setAnalysisData(null));
      dispatch(setDeepAnalysis(null));
      lastProcessedAnalysisIdRef.current = null;
    }
  }, [latestAnalysis, dispatch]);

  // Extract user stories from consolidated data and set in Redux store
  useEffect(() => {
    console.log('🔍 Dashboard useEffect triggered - latestAnalysis:', latestAnalysis);
    console.log('🔍 Dashboard useEffect - latestAnalysis.analysis:', latestAnalysis?.analysis);
    console.log('🔍 Dashboard useEffect - latestAnalysis.analysis.userStories:', latestAnalysis?.analysis?.userStories);
    console.log('🔍 Dashboard useEffect - work_items:', latestAnalysis?.analysis?.userStories?.work_items);
    
    if (latestAnalysis?.analysis?.userStories?.work_items) {
      const workItems = latestAnalysis.analysis.userStories.work_items;
      console.log('🔍 Dashboard: Extracting user stories from consolidated data:', workItems.length, 'items');
      console.log('🔍 Dashboard: User stories platform from data:', latestAnalysis.analysis.userStories.platform);
      console.log('🔍 Dashboard: Selected platform:', selectedPlatform);
      console.log('🔍 Dashboard: Work items sample:', workItems[0]);
      
      // Convert work items to user stories format for compatibility
      const userStoriesData = [{
        id: `consolidated_${currentProjectId}`,
        type: 'user_story',
        userId: user?.id || user?.user_id || '',
        projectId: currentProjectId,
        process_template: latestAnalysis.analysis.userStories.process_template || 'Agile',
        platform: latestAnalysis.analysis.userStories.platform || selectedPlatform || 'azure',
        generated_at: latestAnalysis.analysis.userStories.generated_at,
        work_items: workItems,
        summary: latestAnalysis.analysis.userStories.summary || {},
        comments_count: latestAnalysis.analysis.userStories.comments_count || 0
      }];
      
      dispatch(setCurrentProjectUserStories(userStoriesData));
      
      // Also set deepAnalysis state for compatibility with existing logic
      const deepAnalysisData = {
        id: `consolidated_${currentProjectId}`,
        type: 'user_story',
        userId: user?.id || user?.user_id || '',
        projectId: currentProjectId,
        process_template: latestAnalysis.analysis.userStories.process_template || 'Agile',
        platform: latestAnalysis.analysis.userStories.platform || selectedPlatform || 'azure',
        generated_at: latestAnalysis.analysis.userStories.generated_at,
        work_items: workItems,
        work_items_by_feature: latestAnalysis.analysis.userStories.work_items_by_feature || {},
        summary: latestAnalysis.analysis.userStories.summary || {},
        comments_count: latestAnalysis.analysis.userStories.comments_count || 0
      };
      
      console.log('🔍 Dashboard: Setting deepAnalysis from consolidated data:', deepAnalysisData);
      dispatch(setDeepAnalysis(deepAnalysisData));
    } else if (latestAnalysis && (!latestAnalysis.exists || !latestAnalysis.analysis)) {
      // Clear user stories when no analysis data exists for the project
      console.log('🔍 Dashboard: Clearing user stories - no analysis data exists for project');
      dispatch(clearCurrentProjectUserStories());
      dispatch(setDeepAnalysis(null));
    }
  }, [latestAnalysis, currentProjectId, user, dispatch]);

  // Fetch projects and integration accounts on mount (guard against double-invoke in dev)
  useEffect(() => {
    if (skipBootstrapFetches) return;
    if (didInitRef.current) return;
    didInitRef.current = true;
    dispatch(fetchProjects());
    dispatch(fetchIntegrationAccounts());
  }, [dispatch, skipBootstrapFetches]);

  // Handle page refresh - fetch consolidated dashboard data for the current project
  useEffect(() => {
    // Prevent duplicate fetches
    if (hasConsolidatedFetchRef.current) return;
    
    const currentProjectId = typeof window !== 'undefined' ? localStorage.getItem('project_id') : null;
    
    if (currentProjectId) {
      hasConsolidatedFetchRef.current = true;
      // Mark latest fetch as satisfied for this project to avoid a subsequent getLatestAnalysis call
      lastFetchedProjectRef.current = currentProjectId;
      // Fetch consolidated dashboard data (analysis + user stories + comments + submission status)
      console.log('🔍 Dashboard: Fetching consolidated data for project:', currentProjectId);
      dispatch(getConsolidatedDashboardData(currentProjectId));
    }
  }, [dispatch]);

  // Handle project selection
  const handleProjectSelect = (projectId: string) => {
    // If external handler is provided (from route-based component), use it
    if (onProjectSelect) {
      onProjectSelect(projectId);
      return;
    }
    
    // Otherwise, use the original logic for backward compatibility
    setCurrentProjectId(projectId);
    if (typeof window !== 'undefined') {
      localStorage.setItem('project_id', projectId);
    }
    
    // Clear current analysis data when switching projects
    dispatch(clearAnalysisData());
    dispatch(setLoadedComments(null));
    dispatch(clearCurrentProjectUserStories());
    
    // Reset the processed analysis ID ref when switching projects
    lastProcessedAnalysisIdRef.current = null;
    
    // Fetch consolidated dashboard data for the selected project
    if (projectId) {
      console.log('🔍 Dashboard: Fetching consolidated data for selected project:', projectId);
      // Mark latest fetch as satisfied for this project to avoid triggering getLatestAnalysis
      lastFetchedProjectRef.current = projectId;
      dispatch(getConsolidatedDashboardData(projectId));
    }
  };

  // Note: Work items are now generated dynamically and stored in deepAnalysis state
  // No need to load from backend as they're created on-demand

  // Handle deep analysis data when it's included in analysis response
  useEffect(() => {
    if (analysisData && analysisData.deepAnalysis && !deepAnalysis) {
      console.log('Setting deep analysis from analysis data:', analysisData.deepAnalysis);
      dispatch(setDeepAnalysis(analysisData.deepAnalysis));
    }
  }, [analysisData, deepAnalysis, dispatch]);

  // Debug: Monitor deepAnalysis state changes
  useEffect(() => {
    console.log('🔍 deepAnalysis state changed:', {
      deepAnalysis: deepAnalysis,
      workItemsLength: deepAnalysis?.work_items?.length,
      hasWorkItems: deepAnalysis?.work_items && deepAnalysis.work_items.length > 0
    });
  }, [deepAnalysis]);


  // Avoids calling this endpoint for brand new projects without uploads
  useEffect(() => {
    const loadCommentsFromBackend = async () => {
      if (!loadedComments && analysisData) {
        const effectiveProjectId =
          currentProjectId ||
          projectId ||
          personalProjectId ||
          '';
        const queryParam = effectiveProjectId
          ? `project_id=${effectiveProjectId}`
          : 'is_personal=true';
        try {
          console.log('🔄 Loading comments from backend:', queryParam);
          const response = await apiRequest('get', `/insights/comments/?${queryParam}`, undefined, true);
          if (response.data.success && response.data.data.comments) {
            dispatch(setLoadedComments(response.data.data.comments));
            console.log(`✅ Loaded ${response.data.data.comments.length} comments from backend for regeneration`);
            if (!effectiveProjectId && response.data.data.project_id) {
              setPersonalProjectId(response.data.data.project_id);
            }
          } else {
            console.log('⚠️ No comments found in backend for this context');
          }
        } catch (error: any) {
          console.error('❌ Error loading comments from backend:', error);
          console.error('Error details:', {
            status: error?.response?.status || 'Unknown',
            statusText: error?.response?.statusText || 'Unknown',
            data: error?.response?.data || 'No data',
            url: error?.config?.url || 'No URL',
            message: error?.message || 'No message'
          });
        }
      }
    };
    loadCommentsFromBackend();
  }, [loadedComments, projectId, currentProjectId, personalProjectId, analysisData, dispatch]);



  // Set currentProjectId from initialProjectId prop or localStorage when component mounts
  useEffect(() => {
    if (initialProjectId && !currentProjectId) {
      setCurrentProjectId(initialProjectId);
    } else if (projectId && !currentProjectId && !initialProjectId) {
      setCurrentProjectId(projectId);
    }
  }, [projectId, currentProjectId, initialProjectId]);


  function parseDeepAnalysis(value: any): any {
    try {
      if (Array.isArray(value)) {
        const first = value[0];
        return typeof first === 'string' ? JSON.parse(first) : first;
      }
      if (typeof value === 'string') {
        return JSON.parse(value);
      }
      return value;
    } catch {
      return value;
    }
  }

  // When project changes, fetch latest analysis for it
  useEffect(() => {
    if (!currentProjectId) return;
    // Prevent fetching for the same project multiple times
    if (lastFetchedProjectRef.current === currentProjectId) return;
    lastFetchedProjectRef.current = currentProjectId;
    
    (async () => {
      try {
        const result = await dispatch(getLatestAnalysis(currentProjectId)).unwrap();
        console.log('Latest analysis result:', result);
        if (result?.exists && result?.analysis) {
          const a = result.analysis; // Extract the nested analysis data
          console.log('Analysis data from backend:', a);
          
          // The backend now returns data in the new format (analysisData field)
          // Check if data is already in the correct frontend format
          if (a.analysisData) {
            // Data is already in the new format, use it directly
            console.log('Using new format data directly');
            dispatch(setAnalysisData(a));
            dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
          } else if (a.result?.overall && a.result?.counts && a.result?.features !== undefined) {
            // Data is nested under result field - normalize it and merge metadata
            console.log('Using result field data, normalizing');
            const normalized = normalizeAnalysis(a.result);
            // Merge metadata from the analysis object
            if (normalized) {
              normalized.id = a.id || normalized.id;
              normalized.projectId = a.projectId || normalized.projectId;
              normalized.userId = a.userId || normalized.userId;
              normalized.createdAt = a.createdAt || a.analysis_date || normalized.createdAt;
              normalized.analysisType = a.analysis_type || normalized.analysisType;
            }
            dispatch(setAnalysisData(normalized));
            dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
          } else if (a.sentimentsummary && a.counts && a.featureasba !== undefined) {
            // Data is in the old format, normalize it
            console.log('Using old format data, normalizing');
            dispatch(setAnalysisData(normalizeAnalysis(a)));
            dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
          } else if (a.overall && a.counts && a.features !== undefined) {
            // Fallback: data is in the old format, normalize it
            console.log('Using old format data, normalizing');
            dispatch(setAnalysisData(normalizeAnalysis(a)));
            dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
          } else if (a.commentAnalysis) {
            // Fallback: use commentAnalysis if available
            console.log('Using commentAnalysis as fallback');
            const ca = Array.isArray(a.commentAnalysis)
              ? (typeof a.commentAnalysis[0] === 'string' ? JSON.parse(a.commentAnalysis[0]) : a.commentAnalysis[0])
              : a.commentAnalysis;
            dispatch(setAnalysisData(normalizeAnalysis(ca)));
            dispatch(setDeepAnalysis(a.userStories ? parseDeepAnalysis(a.userStories) : null));
          } else {
            console.log('No analysis data found, available keys:', Object.keys(a));
            dispatch(setAnalysisData(null));
            dispatch(setDeepAnalysis(null));
          }
        } else {
          console.log('No analysis exists for project');
          dispatch(setAnalysisData(null));
          dispatch(setDeepAnalysis(null));
        }
      } catch (e) {
        console.error('Error fetching latest analysis:', e);
      }
    })();
  }, [currentProjectId, dispatch]);

  const handleCloudConnect = () => {
    alert('Cloud connect functionality would be implemented here');
  };

  // Analyze loaded comments using the backend analyze endpoint
  async function handleTopAnalyze() {
    if (!topFile) {
      setTopError('Please select a file first');
      return;
    }
    const validation = validateFile(topFile);
    if (!validation.isValid) {
      setTopError(validation.error);
      return;
    }
    try {
      setTopError(null);
      dispatch(clearError());

      // Load file data first
      const text = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(topFile);
      });
      
      let comments: string[] = [];
      const lowerName = topFile.name.toLowerCase();
      if (lowerName.endsWith('.json')) {
        try {
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed)) {
            comments = parsed.map(String).filter(Boolean);
          } else if (Array.isArray(parsed.comments)) {
            comments = parsed.comments.map(String).filter(Boolean);
          }
        } catch {
          // ignore, will error below if empty
        }
      } else if (lowerName.endsWith('.csv')) {
        // Parse CSV properly handling quoted fields (commas inside quotes)
        const parseCSVLine = (line: string): string[] => {
          const fields: string[] = [];
          let current = '';
          let inQuotes = false;
          for (let i = 0; i < line.length; i++) {
            const ch = line[i];
            if (inQuotes) {
              if (ch === '"' && line[i + 1] === '"') {
                current += '"';
                i++; // skip escaped quote
              } else if (ch === '"') {
                inQuotes = false;
              } else {
                current += ch;
              }
            } else {
              if (ch === '"') {
                inQuotes = true;
              } else if (ch === ',') {
                fields.push(current);
                current = '';
              } else {
                current += ch;
              }
            }
          }
          fields.push(current);
          return fields;
        };

        const lines = text.split(/\r?\n/).filter(Boolean);
        if (lines.length > 0) {
          const header = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase());
          const commentIdx = header.indexOf('comment');
          if (commentIdx >= 0) {
            comments = lines.slice(1)
              .map(line => (parseCSVLine(line)[commentIdx] || '').trim())
              .filter(Boolean);
          } else {
            comments = lines.slice(1).map(line => (parseCSVLine(line)[0] || '').trim()).filter(Boolean);
          }
        }
      }
      
      if (!comments.length) {
        setTopError('No comments detected. Ensure JSON has a comments array or CSV has a comment column.');
        return;
      }
      
      // Update loadedComments for display
      dispatch(setLoadedComments(comments));
      
      // Use Redux action to analyze comments
      const effectiveProjectId = currentProjectId || personalProjectId || undefined;
      const result = await dispatch(analyzeComments({ 
        comments, 
        projectId: effectiveProjectId,
        fileName: topFile.name 
      })).unwrap();
      

      // Extract analysis data from the result
      const payload = (result && (result.analysisData || result.sentimentsummary || result.featureasba)) ? result : (result?.data || null);
      
      if (payload) {
        const resolvedProjectId = payload?.context?.project_id || payload?.projectId;
        const isDraft = payload?.context?.is_draft;
        if (resolvedProjectId) {
          if (isDraft) {
            setPersonalProjectId(resolvedProjectId);
          }
          if (!currentProjectId) {
            setCurrentProjectId(resolvedProjectId);
          }
          if (typeof window !== 'undefined') {
            localStorage.setItem('project_id', resolvedProjectId);
          }
        }
        // The result is already in the correct format, just use it directly
        console.log('Using analysis result directly:', payload);
        dispatch(setAnalysisData(payload));
        
        // Set deepAnalysis if available
        if (payload.deepAnalysis) {
          dispatch(setDeepAnalysis(payload.deepAnalysis));
        }
        
        // Generate work items asynchronously in the background (don't await)
        // This allows the dashboard to display analysis results immediately
        generateWorkItemsFromAnalysis(payload).catch(e => {
          console.error('Background work item generation failed:', e);
        });
        
      }
      
    } catch (e: any) {
      const data = e?.response?.data;
      const message =
        (typeof data?.message === 'string' && data.message) ||
        (typeof data?.error === 'string' && data.error) ||
        (typeof data?.detail === 'string' && data.detail) ||
        (Array.isArray(data?.errors) && data.errors[0]) ||
        e?.message ||
        'Analysis failed. Please try again.';
      setTopError(message);
    }
  }

  // Generate work items from analysis data
  async function generateWorkItemsFromAnalysis(analysisData: any) {
    try {
      setIsGeneratingUserStories(true);
      
      // Use platform derived from selected project (default to Azure for personal workspaces)
      const currentPlatform = selectedPlatform ?? 'azure';
      
      // Ensure we have comments available
      let commentsToUse = loadedComments;
      const effectiveProjectId = currentProjectId || personalProjectId || '';
      if (!commentsToUse || commentsToUse.length === 0) {
        console.log('🔄 No comments available, trying to load from backend...');
        try {
          const queryParam = effectiveProjectId
            ? `project_id=${effectiveProjectId}`
            : 'is_personal=true';
          const response = await apiRequest('get', `/insights/comments/?${queryParam}`, undefined, true);
          if (response.data.success && response.data.data.comments) {
            commentsToUse = response.data.data.comments;
            dispatch(setLoadedComments(commentsToUse));
            console.log(`✅ Loaded ${commentsToUse?.length} comments from backend`);
            if (!effectiveProjectId && response.data.data.project_id) {
              setPersonalProjectId(response.data.data.project_id);
            }
          }
        } catch (error) {
          console.error('❌ Error loading comments:', error);
        }
      }
      
      if (!commentsToUse || commentsToUse.length === 0) {
        console.error('❌ No comments available for work item generation');
        setIsGeneratingUserStories(false);
        return;
      }
      
      console.log('🔧 generateWorkItemsFromAnalysis called:', {
        currentPlatform,
        analysisData: !!analysisData,
        loadedCommentsLength: commentsToUse?.length,
        projectContext: effectiveProjectId || null
      });
      
      if (currentPlatform === 'jira') {
        // For Jira, follow the same flow as Azure: general analysis -> work items generation
        console.log('🔧 Generating Jira work items using the correct flow');
        
        if (commentsToUse && commentsToUse.length > 0) {
          // Step 1: Get Jira project metadata for better work item generation
          let jiraProjectMetadata = null;
          const selectedJiraProjectId = typeof window !== 'undefined' ? localStorage.getItem('jira_selected_project') : null;
          
          if (selectedJiraProjectId) {
            try {
              const metadataResponse = await apiRequest('get', `/workitems/jira/project-metadata?projectId=${selectedJiraProjectId}`, {}, true, false);
              jiraProjectMetadata = metadataResponse.data.metadata;
              console.log('✅ Jira project metadata:', jiraProjectMetadata);
            } catch (e) {
              console.warn('⚠️ Failed to fetch Jira project metadata, proceeding without it:', e);
            }
          }
          
          // Step 2: Generate work items using the analysis data and Jira metadata
          console.log('🔧 Step 2: Generating Jira work items from analysis data...');
          const workItemsResult = await dispatch(generateUserStories({
            analysisData,
            comments: commentsToUse, // Use the loaded comments
            platform: 'jira',
            processTemplate: 'Agile', // Default for Jira
            projectId: effectiveProjectId || undefined,
            projectMetadata: jiraProjectMetadata
          })).unwrap();
          
          console.log('✅ Jira work items generated:', workItemsResult);
          console.log('📊 Work items count:', workItemsResult.work_items?.length);
          
          // Fetch the persisted user stories from the backend after successful generation
          if (effectiveProjectId && user?.id) {
            console.log('🔄 Fetching persisted user stories after Jira generation...');
            const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
            
            // Add a small delay to ensure the backend has saved the data
            setTimeout(() => {
              dispatch(fetchUserStoriesByProject({ 
                projectId: formattedProjectId,
                userId: user.id || user.user_id || user.username
              }));
            }, 1000);
          }
          
          // Set the generated work items in the store
          if (workItemsResult.work_items) {
            console.log('🔄 Dispatching setDeepAnalysis with work items...');
            
            // Structure the data properly for the UserStories component
            // The UserStoryList expects an array of user stories, so we need to wrap the response
            const structuredData = {
              ...workItemsResult,
              work_items: workItemsResult.work_items,
              work_items_by_feature: workItemsResult.work_items_by_feature,
              summary: workItemsResult.summary
            };
            
            dispatch(setDeepAnalysis(structuredData));
            
            // Also update the userStories state with the proper format
            // The UserStoryList component expects userStories to be an array
            const userStoryFormat = [{
              id: workItemsResult.id,
              type: workItemsResult.type || 'user_story',
              userId: workItemsResult.userId,
              projectId: workItemsResult.projectId,
              platform: workItemsResult.platform,
              work_items: workItemsResult.work_items,
              summary: workItemsResult.summary,
              generated_at: workItemsResult.generated_at,
              success: workItemsResult.success
            }];
            
            // Store in the userStories slice as well for proper display
            // This ensures the UserStoryList component gets the data in the expected format
            console.log('✅ Structured user story format:', userStoryFormat);
            
            dispatch(setDeepAnalysis(structuredData));
            console.log('✅ setDeepAnalysis dispatched with structured data:', structuredData);
            console.log('🔍 Work items in structured data:', structuredData.work_items?.length);
            console.log('🔍 Structured data keys:', Object.keys(structuredData));
          } else {
            console.warn('⚠️ No work items in result');
          }
        } else {
          console.log('📝 No comments available for Jira work item generation');
        }
      } else {
        // For Azure DevOps, use the existing logic
        const processTemplate = (typeof window !== 'undefined') ? 
          localStorage.getItem('azure_process_template') || 'Agile' : 'Agile';
        
        console.log('🔧 Generating Azure work items with template:', processTemplate);
        
        // Check if we have comments and analysis data available
        if (commentsToUse && commentsToUse.length > 0 && analysisData) {
          console.log('Using existing analysis data with comments:', commentsToUse.length);
          
          // Use existing analysis data instead of calling analyzeComments again
          console.log('Using existing analysis data:', analysisData);
          
          // Generate work items from the existing analysis data
          const workItemsResult = await dispatch(generateUserStories({
            analysisData: analysisData,
            comments: commentsToUse,
            platform: (currentPlatform as 'azure' | 'jira') ?? 'azure',
            processTemplate,
            projectId: effectiveProjectId || undefined
          })).unwrap();
          
          if (workItemsResult?.work_items && workItemsResult.work_items.length > 0) {
            // Structure the data properly for the UserStories component
            const structuredData = {
              ...workItemsResult,
              work_items: workItemsResult.work_items,
              work_items_by_feature: workItemsResult.work_items_by_feature,
              summary: workItemsResult.summary
            };
            
            dispatch(setDeepAnalysis(structuredData));
            console.log('✅ Work items generated and stored:', workItemsResult);
            
            // Fetch the persisted user stories from the backend after successful generation
            if (effectiveProjectId && user?.id) {
              console.log('🔄 Fetching persisted user stories after Azure generation...');
              const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
              
              // Add a small delay to ensure the backend has saved the data
              setTimeout(() => {
                dispatch(fetchUserStoriesByProject({ 
                  projectId: formattedProjectId,
                  userId: user.id || user.user_id || user.username
                }));
              }, 1000);
            }
          } else {
            console.warn('No work items generated from analysis');
          }
        } else {
          console.log('No comments available, using analysis data for work items');
          
          // Fallback to old method using analysis data
          const workItemsResult = await dispatch(generateUserStories({
            analysisData,
            comments: commentsToUse,
            platform: (currentPlatform as 'azure' | 'jira') ?? 'azure',
            processTemplate,
            projectId: effectiveProjectId || undefined
          })).unwrap();
          
          console.log('Work items generated:', workItemsResult);
          
          // Set the generated work items in the store
          if (workItemsResult.work_items) {
            // Structure the data properly for the UserStories component
            const structuredData = {
              ...workItemsResult,
              work_items: workItemsResult.work_items,
              work_items_by_feature: workItemsResult.work_items_by_feature,
              summary: workItemsResult.summary
            };
            dispatch(setDeepAnalysis(structuredData));
            console.log('✅ setDeepAnalysis dispatched (fallback 2):', structuredData);
            
            // Fetch the persisted user stories from the backend after fallback generation
            if (effectiveProjectId && user?.id) {
              console.log('🔄 Fetching persisted user stories after fallback generation...');
              const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
              
              // Add a small delay to ensure the backend has saved the data
              setTimeout(() => {
                dispatch(fetchUserStoriesByProject({ 
                  projectId: formattedProjectId,
                  userId: user.id || user.user_id || user.username
                }));
              }, 1000);
            }
          }
        }
      }
      
    } catch (e: any) {
      console.error('❌ Error generating work items:', e);
      
      // Show error to user for better debugging
      const errorMessage = typeof e === 'string' ? e : e?.message || 'Unknown error occurred';
      console.error('❌ Work item generation failed:', errorMessage);
      
      // You can uncomment this to show errors to users:
      // alert(`Work item generation failed: ${errorMessage}`);
    } finally {
      setIsGeneratingUserStories(false);
      
      // Fetch the persisted user stories from the backend after generation
      const effectiveProjectId = currentProjectId || personalProjectId;
      if (effectiveProjectId && user?.id) {
        console.log('🔄 Fetching persisted user stories after generation...');
        const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
        
        // Add a small delay to ensure the backend has saved the data
        setTimeout(() => {
          dispatch(fetchUserStoriesByProject({ 
            projectId: formattedProjectId,
            userId: user.id || user.user_id || user.username
          }));
        }, 1000);
      }
    }
  }

  // Normalize backend keys to frontend shape
  function normalizeAnalysis(input: any): AnalysisData {
    if (!input) return input as AnalysisData;
    
    console.log('Normalizing analysis data:', input);
    
    // If data is already in the new format (has analysisData field)
    if (input.analysisData) {
      const toNum = (v: any) => (typeof v === 'number' ? v : Number(v ?? 0));
      
      const normalized = {
        id: input.id || `analysis_${Date.now()}`,
        projectId: input.projectId || 'unknown',
        userId: input.userId || 'anonymous',
        createdAt: input.createdAt || new Date().toISOString(),
        analysisType: input.analysisType || 'commentSentiment',
        rawLlm: input.rawLlm || {},
        analysisData: {
          overall: {
            positive: toNum(input.analysisData.overall?.positive),
            negative: toNum(input.analysisData.overall?.negative),
            neutral: toNum(input.analysisData.overall?.neutral),
          },
          counts: {
            total: toNum(input.analysisData.counts?.total),
            positive: toNum(input.analysisData.counts?.positive),
            negative: toNum(input.analysisData.counts?.negative),
            neutral: toNum(input.analysisData.counts?.neutral),
          },
          features: (input.analysisData.features || []).map((f: any) => ({
            featureId: f.featureId || f.id || f.name,
            name: f.name || f.feature,
            description: f.description || '',
            sentiment: {
              positive: toNum(f.sentiment?.positive),
              negative: toNum(f.sentiment?.negative),
              neutral: toNum(f.sentiment?.neutral),
            },
            keywords: f.keywords || [],
            comment_count: toNum(f.comment_count),
          })),
          positive_keywords: input.analysisData.positive_keywords || [],
          negative_keywords: input.analysisData.negative_keywords || [],
        },
        deepAnalysis: input.deepAnalysis,
      } as AnalysisData;
      
      console.log('Normalized data:', normalized);
      return normalized;
    }
    
    // If data is in the old format (has overall, counts, features at top level)
    if (input.overall && input.counts && input.features !== undefined) {
      const toNum = (v: any) => (typeof v === 'number' ? v : Number(v ?? 0));
      
      const normalized = {
        id: `analysis_${Date.now()}`,
        projectId: 'unknown',
        userId: 'anonymous',
        createdAt: new Date().toISOString(),
        analysisType: 'commentSentiment',
        rawLlm: input.raw_llm || {},
        analysisData: {
          overall: {
            positive: toNum(input.overall.positive),
            negative: toNum(input.overall.negative),
            neutral: toNum(input.overall.neutral),
          },
          counts: {
            total: toNum(input.counts.total),
            positive: toNum(input.counts.positive),
            negative: toNum(input.counts.negative),
            neutral: toNum(input.counts.neutral || 0),
          },
          features: (input.features || []).map((f: any) => ({
            featureId: f.featureId || f.id || f.name,
            name: f.name || f.feature,
            description: f.description || '',
            sentiment: {
              positive: toNum(f.sentiment?.positive),
              negative: toNum(f.sentiment?.negative),
              neutral: toNum(f.sentiment?.neutral),
            },
            keywords: f.keywords || [],
            comment_count: toNum(f.comment_count),
          })),
          positive_keywords: input.positive_keywords || [],
          negative_keywords: input.negative_keywords || [],
        },
        deepAnalysis: input.deepAnalysis,
      } as AnalysisData;
      
      console.log('Normalized data:', normalized);
      return normalized;
    }
    
    // Handle old format or commentAnalysis format
    const toNum = (v: any) => (typeof v === 'number' ? v : Number(v ?? 0));
    const sentiments = input.sentimentsummary || input.sentiment_summary || input.overall || {};
    const features = input.featureasba || input.feature_asba || input.features || [];
    const negatives = input.negativesummary || input.negative_summary || [];
    const emojis = input.emojianalysis || input.emoji_analysis || undefined;
    const posKeys = input.positivekeywords || input.positive_keywords || [];
    const negKeys = input.negativekeywords || input.negative_keywords || [];
    const counts = input.counts || input.count || { total: 0, positive: 0, negative: 0 };
    
    // Extract deepAnalysis from raw_llm.deep_chunks if available
    let deepAnalysis = null;
    if (input.raw_llm?.deep_chunks && input.raw_llm.deep_chunks.length > 0) {
      try {
        const deepChunk = input.raw_llm.deep_chunks[0];
        if (typeof deepChunk === 'string') {
          deepAnalysis = JSON.parse(deepChunk);
        } else {
          deepAnalysis = deepChunk;
        }
      } catch (e) {
        console.error('Error parsing deep analysis:', e);
      }
    }
    
    return {
      id: `analysis_${Date.now()}`,
      projectId: 'unknown',
      userId: 'anonymous',
      createdAt: new Date().toISOString(),
      analysisType: 'commentSentiment',
      rawLlm: input.raw_llm || {},
      analysisData: {
        overall: {
          positive: toNum(sentiments.positive),
          negative: toNum(sentiments.negative),
          neutral: toNum(sentiments.neutral),
        },
        counts: {
          total: toNum(counts.total),
          positive: toNum(counts.positive),
          negative: toNum(counts.negative),
          neutral: toNum(counts.neutral || 0),
        },
        features: (features || []).map((f: any) => ({
          featureId: f.featureId || f.id || f.name,
          name: f.feature || f.name,
          description: f.description || '',
          sentiment: {
            positive: toNum(f.sentiment?.positive ?? f.sentiment_positive),
            negative: toNum(f.sentiment?.negative ?? f.sentiment_negative),
            neutral: toNum(f.sentiment?.neutral ?? f.sentiment_neutral),
          },
          keywords: f.keywords || [],
          comment_count: toNum(f.comment_count),
        })),
        positive_keywords: posKeys,
        negative_keywords: negKeys,
      },
      deepAnalysis: deepAnalysis,
    } as AnalysisData;
  }

  // Prepare chart data
  const sentimentData = [
    { name: 'Positive', value: activeAnalysisData?.analysisData?.overall?.positive ?? 0 },
    { name: 'Negative', value: activeAnalysisData?.analysisData?.overall?.negative ?? 0 },
    { name: 'Neutral', value: activeAnalysisData?.analysisData?.overall?.neutral ?? 0 }
  ];

  const featureSentimentData = (activeAnalysisData?.analysisData?.features || []).map((feature: any) => ({
    name: feature.name || feature.feature,
    positive: feature.sentiment.positive,
    negative: feature.sentiment.negative,
    neutral: feature.sentiment.neutral,
    description: feature.description || '',
    keywords: feature.keywords || [],
    comment_count: feature.comment_count
  }));

  console.log('Feature sentiment data:---?', featureSentimentData);
  console.log('Analysis data for features:', activeAnalysisData?.analysisData?.features);
  console.log('Raw features array:', activeAnalysisData?.analysisData?.features);
  console.log('First feature example:', activeAnalysisData?.analysisData?.features?.[0]);

  // Enhanced colorful metrics
  const metrics = [
    {
      title: "Total Comments",
      value: String(activeAnalysisData?.analysisData?.counts?.total ?? 0),
      color: "blue" as const,
      description: "Comments analyzed in current file"
    },
    {
      title: "Positive Comments",
      value: String(activeAnalysisData?.analysisData?.counts?.positive ?? 0),
      color: "green" as const,
      description: "Comments with positive sentiment"
    },
    {
      title: "Negative Comments", 
      value: String(activeAnalysisData?.analysisData?.counts?.negative ?? 0),
      color: "red" as const,
      description: "Comments with negative sentiment"
    }
  ];

  // Show loader while:
  // - projects are still loading (initial load only)
  // Note: We don't show full-screen loader for analysis loading anymore
  // Analysis loading is handled within the dashboard section
  if (projectsLoading && projects.length === 0) {
    return (
      <div className="min-h-screen bg-secondary/40 dark:bg-background">
        {/* Main Content */}
        <main className="p-6">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Project Selector & Navigation */}
            <div className="flex items-center justify-between">
              {/* Unified Project Selector */}
              <div>
                <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
                  Select Project
                </label>
                <AnalysisProjectSelector
                  projects={projects}
                  selectedProjectId={currentProjectId}
                  loading={projectsLoading}
                  error={error}
                  onProjectSelect={handleProjectSelect}
                  onRefreshProjects={() => dispatch(fetchProjects())}
                />
              </div>

              {/* Navigation Tabs - Inlined */}
              <div className="flex bg-secondary/70 rounded-xl p-1">
                <Button
                  onClick={() => setActiveView('dashboard')}
                  variant="ghost"
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeView === 'dashboard' 
                      ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                      : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                  }`}
                >
                  Dashboard
                </Button>
                <Button
                  onClick={() => setActiveView('user-stories')}
                  variant="ghost"
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeView === 'user-stories' 
                      ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                      : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                  }`}
                >
                  User Stories
                </Button>
              </div>
            </div>

            {activeView === 'dashboard' ? (
              <>
                {/* Upload Panel */}
                <UploadPanel
                  dbProjectId={currentProjectId}
                  topFile={topFile}
                  topError={error || topError}
                  loadedComments={loadedComments}
                  topUploading={isProjectAnalyzing}
                  onFileSelect={setTopFile}
                  onAnalyze={handleTopAnalyze}
                  onCloudConnect={handleCloudConnect}
                />
              </>
            ) : activeView === 'user-stories' ? (
              /* User Stories View Loading */
              <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
                <div className="animate-pulse">
                  <div className="h-6 bg-secondary/60 rounded-xl w-1/4 mb-4"></div>
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-16 bg-secondary/60 rounded-xl"></div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* Jira Integration View Loading */
              <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
                <div className="animate-pulse">
                  <div className="h-6 bg-secondary/60 rounded-xl w-1/4 mb-4"></div>
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-16 bg-secondary/60 rounded-xl"></div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-secondary/40 dark:bg-background">
      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Project Selector & Navigation */}
          <div className="flex items-center justify-between">
            {/* Unified Project Selector */}
            <div>
              <label className="block text-sm font-medium text-muted-foreground dark:text-muted-foreground mb-2">
                Select Project
              </label>
              <AnalysisProjectSelector
                projects={projects}
                selectedProjectId={currentProjectId}
                loading={projectsLoading}
                error={error}
                onProjectSelect={handleProjectSelect}
                onRefreshProjects={() => dispatch(fetchProjects())}
              />
            </div>

            {/* Navigation Tabs - Inlined */}
            <div className="flex gap-4 items-center">
              <div className="flex bg-secondary/70 rounded-xl p-1">
                <Button
                  onClick={() => setActiveView('dashboard')}
                  variant="ghost"
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeView === 'dashboard' 
                      ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                      : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                  }`}
                >
                  Dashboard
                </Button>
                <Button
                  onClick={() => {
                    setActiveView('user-stories');
                    // Fetch user stories when switching to the user stories tab
                    const effectiveProjectId = currentProjectId || personalProjectId;
                    if (effectiveProjectId && user?.id) {
                      console.log('🔄 Fetching user stories on tab switch...');
                      const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
                      const userId = user.id || user.user_id || user.username;
                      console.log('🔍 Tab switch fetch params:', { 
                        projectId: formattedProjectId, 
                        userId, 
                        selectedPlatform,
                        userObject: user 
                      });
                      dispatch(fetchUserStoriesByProject({ 
                        projectId: formattedProjectId,
                        userId
                      }));
                    }
                  }}
                  variant="ghost"
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeView === 'user-stories' 
                      ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                      : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                  }`}
                >
                  User Stories
                </Button>
              </div>
              
              {/* Projects Button */}
              <Button
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    window.location.href = '/projects';
                  }
                }}
                variant="saramsa"
                className="px-4 py-2 text-sm font-medium"
              >
                Projects
              </Button>
            </div>
          </div>

          {activeView === 'dashboard' ? (
            <>
              {/* Upload Panel - Always visible */}
              <UploadPanel
                dbProjectId={currentProjectId}
                topFile={topFile}
                topError={error || topError}
                loadedComments={loadedComments}
                topUploading={isProjectAnalyzing}
                onFileSelect={setTopFile}
                onAnalyze={handleTopAnalyze}
                onCloudConnect={handleCloudConnect}
              />

              {/* Dismissible error banner above results */}
              {(error || topError) && (
                <div className="flex items-center justify-between gap-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
                  <p className="text-sm text-red-700 dark:text-red-300 flex-1">
                    {error || topError}
                  </p>
                  <Button
                    type="button"
                    onClick={() => {
                      setTopError(null);
                      dispatch(clearError());
                    }}
                    variant="ghost"
                    size="icon"
                    className="shrink-0 h-9 w-9 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30"
                    aria-label="Dismiss error"
                  >
                    <span className="text-lg leading-none">x</span>
                  </Button>
                </div>
              )}

              {/* Analysis Results Section */}
              {(isProjectAnalyzing || loading) ? (
                <LoaderForDashboard />
              ) : (
                <>
                  {/* Summary Info */}
                  <div className="text-sm text-muted-foreground dark:text-muted-foreground">
                    {hasAnalysisResults ? (
                      <>Current file summary based on the data uploaded as of {
                        (() => {
                          // Try to get the most recent timestamp
                          const analysisDate = activeAnalysisData?.createdAt;
                          const deepAnalysisDate = activeAnalysisData?.deepAnalysis?.generated_at;
                          
                          // Use the most recent date available
                          const timestamp = deepAnalysisDate || analysisDate;
                          
                          if (timestamp) {
                            return new Date(timestamp).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            });
                          } else {
                            return new Date().toLocaleDateString();
                          }
                        })()
                      }
                      </>
                    ) : (
                      <>No analysis data available yet. Upload a file above to get started.</>
                    )}
                  </div>

                  {/* Metrics Cards */}
                  {hasAnalysisResults && <MetricsCards metrics={metrics} />}

                  {hasAnalysisResults && (
                    <>
                      {/* Feature Sentiments Table */}
                      {hasAnalysisResults && (
                        <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
                          <FeatureSentimentsTable
                            features={transformedFeatures}
                            selectedFeatures={selectedFeatures}
                            onFeatureToggle={(featureName) => {
                              setSelectedFeatures(prev => 
                                prev.includes(featureName) 
                                  ? prev.filter(name => name !== featureName)
                                  : [...prev, featureName]
                              );
                            }}
                            onKeywordsUpdate={handleKeywordsUpdate}
                            onRegenerateAnalysis={handleRegenerateAnalysis}
                            hasEditedFeaturesProp={Object.keys(editedKeywords).length > 0}
                            hasComments={!!loadedComments && loadedComments.length > 0}
                          />
                        </div>
                      )}

                      <SentimentCharts
                        featureSentimentData={featureSentimentData}
                        sentimentData={sentimentData}
                        selectedFeatures={selectedFeatures}
                      />
                    </>
                  )}

                  {/* Keywords Analysis */}
                  {hasAnalysisResults && (
                    <div className="space-y-4">
                      {/* Word Cloud View Toggle */}
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
                          Word Cloud Analysis
                        </h3>
                        {/* <div className="flex bg-secondary/70 rounded-xl p-1">
                          <Button
                            onClick={() => setWordCloudView('split')}
                            className={`px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 ${
                              wordCloudView === 'split' 
                                ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                                : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                            }`}
                          >
                            Split View
                          </Button>
                          <Button
                            onClick={() => setWordCloudView('advanced')}
                            className={`px-3 py-1 rounded-md text-sm font-medium transition-all duration-200 ${
                              wordCloudView === 'advanced' 
                                ? 'bg-background/90 text-foreground dark:text-foreground shadow-[0_12px_30px_-24px_rgba(15,23,42,0.5)]' 
                                : 'text-muted-foreground dark:text-muted-foreground hover:text-foreground dark:hover:text-white'
                            }`}
                          >
                            Advanced View
                          </Button>
                        </div> */}
                      </div>

                      {/* Word Cloud Components */}
                      {wordCloudView === 'split' ? (
                        <KeywordCloud
                          positiveKeywords={
                            activeAnalysisData?.analysisData?.positive_keywords?.map((word: any) => 
                              typeof word === 'string' ? word : word.keyword || word.text || String(word)
                            ) || []
                          }
                          negativeKeywords={
                            activeAnalysisData?.analysisData?.negative_keywords?.map((word: any) => 
                              typeof word === 'string' ? word : word.keyword || word.text || String(word)
                            ) || []
                          }
                        />
                      ) : (
                        <AdvancedWordCloud
                          positiveKeywords={
                            activeAnalysisData?.analysisData?.positive_keywords?.map((word: any) => 
                              typeof word === 'string' ? word : word.keyword || word.text || String(word)
                            ) || []
                          }
                          negativeKeywords={
                            activeAnalysisData?.analysisData?.negative_keywords?.map((word: any) => 
                              typeof word === 'string' ? word : word.keyword || word.text || String(word)
                            ) || []
                          }
                        />
                      )}
                    </div>
                  )}
                </>
              )}
            </>
          ) : activeView === 'user-stories' ? (
            /* User Stories View */
            <div className="bg-card/90 dark:bg-card/95 rounded-2xl shadow-xl border border-border/60 dark:border-border/60 p-6">
              {isGeneratingUserStories ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <LoaderForDashboard />
                  <p className="mt-4 text-muted-foreground dark:text-muted-foreground">Generating user stories from analysis...</p>
                </div>
              ) : selectedPlatform === 'jira' ? (
                /* Jira User Stories View */
                (() => {
                  console.log('🔍 Jira Platform Debug:', {
                    selectedPlatform,
                    loadedComments: loadedComments?.length,
                    currentProjectUserStories: currentProjectUserStories?.length,
                    deepAnalysis: deepAnalysis ? 'exists' : 'null',
                    deepAnalysisWorkItems: deepAnalysis?.work_items?.length
                  });
                  return loadedComments && loadedComments.length > 0;
                })() ? (
                  (() => {
                    console.log('🔍 Jira User Stories Debug:', {
                      selectedPlatform,
                      loadedCommentsLength: loadedComments?.length ?? 0,
                      deepAnalysis: deepAnalysis,
                      deepAnalysisWorkItems: deepAnalysis?.work_items,
                      workItemsLength: deepAnalysis?.work_items?.length,
                      jiraAnalysis: jiraAnalysis,
                      jiraAnalysisWorkItems: jiraAnalysis?.work_items,
                      deepAnalysisKeys: deepAnalysis ? Object.keys(deepAnalysis) : 'null',
                      deepAnalysisType: typeof deepAnalysis
                    });
                    
                    // Check if we have work items in deepAnalysis OR in currentProjectUserStories
                    const hasDeepAnalysisWorkItems = deepAnalysis?.work_items && deepAnalysis.work_items.length > 0;
                    const hasCurrentUserStories = currentProjectUserStories && currentProjectUserStories.length > 0;
                    const hasAnyUserStories = hasDeepAnalysisWorkItems || hasCurrentUserStories;
                    
                    console.log('🔍 Jira User Stories Check:', {
                      hasDeepAnalysisWorkItems,
                      hasCurrentUserStories,
                      hasAnyUserStories,
                      deepAnalysisWorkItemsLength: deepAnalysis?.work_items?.length,
                      currentUserStoriesLength: currentProjectUserStories?.length,
                      currentProjectUserStories: currentProjectUserStories,
                      currentUserStoriesPlatform: currentProjectUserStories?.[0]?.platform
                    });
                    
                    return hasAnyUserStories ? (
                      (() => {
                        // Prepare user stories data for display
                        let userStoriesToDisplay = currentProjectUserStories;
                        
                        if (hasDeepAnalysisWorkItems) {
                          // Store Jira user stories in Redux state like Azure does
                          const jiraUserStory = {
                            id: deepAnalysis.id,
                            type: deepAnalysis.type || 'user_story',
                            userId: deepAnalysis.userId,
                            projectId: deepAnalysis.projectId,
                            process_template: deepAnalysis.process_template || 'Agile',
                            platform: deepAnalysis.platform,
                            work_items: deepAnalysis.work_items,
                            summary: deepAnalysis.summary,
                            generated_at: deepAnalysis.generated_at,
                            comments_count: deepAnalysis.comments_count || 0
                          };
                          
                          // Check if we need to store this in Redux (similar to Azure logic)
                          if (!hasCurrentUserStories) {
                            console.log('🔍 Storing Jira user story in Redux state:', jiraUserStory);
                            dispatch(setCurrentProjectUserStories([jiraUserStory]));
                          }
                          
                          userStoriesToDisplay = [jiraUserStory];
                        }
                        
                        console.log('🔍 Jira UserStoryList will receive:', userStoriesToDisplay);
                        
                        return (
                          <UserStoryList 
                            userStories={userStoriesToDisplay}
                            platform="jira"
                            projectId={currentProjectId}
                            onRegenerateAnalysis={async () => {
                              if (loadedComments && loadedComments.length > 0) {
                                try {
                                  // Use existing analysis data instead of calling analyzeComments again
                                  const analysisResult = analysisData;
                                  
                                  if (!analysisResult) {
                                    console.error('No analysis data available for Jira work item generation');
                                    return;
                                  }
                                  
                                  // Step 1: Get Jira project metadata
                                  let jiraProjectMetadata = null;
                                  const selectedJiraProjectId = typeof window !== 'undefined' ? localStorage.getItem('jira_selected_project') : null;
                                  
                                  if (selectedJiraProjectId) {
                                    try {
                                      const metadataResponse = await apiRequest('get', `/workitems/jira/project-metadata?projectId=${selectedJiraProjectId}`, {}, true, false);
                                      jiraProjectMetadata = metadataResponse.data.metadata;
                                    } catch (e) {
                                      console.warn('Failed to fetch Jira project metadata:', e);
                                    }
                                  }
                                  
                                  // Step 3: Generate work items
                                  const workItemsResult = await dispatch(generateUserStories({
                                    analysisData: analysisResult,
                                    comments: loadedComments, // Add the original comments
                                    platform: selectedPlatform === 'jira' ? 'jira' : 'azure',
                                    processTemplate: 'Agile',
                                    projectId: projectId || undefined,
                                    projectMetadata: jiraProjectMetadata
                                  })).unwrap();
                                  
                                  // Structure the data properly for the UserStories component
                                  const structuredData = {
                                    ...workItemsResult,
                                    work_items: workItemsResult.work_items,
                                    work_items_by_feature: workItemsResult.work_items_by_feature,
                                    summary: workItemsResult.summary
                                  };
                                  dispatch(setDeepAnalysis(structuredData));
                                  console.log('✅ setDeepAnalysis dispatched (regenerate):', structuredData);
                                } catch (error) {
                                  console.error('Failed to regenerate Jira analysis:', error);
                                }
                              }
                            }}
                            isAnalyzing={loading}
                          />
                        );
                      })()
                    ) : (
                      <div className="text-center py-8">
                        <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
                          <Sparkles className="w-8 h-8 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 dark:text-foreground mb-2">
                          No User Stories Generated
                        </h3>
                        <p className="text-slate-500 dark:text-slate-400 mb-4">
                          User stories will be automatically generated after you analyze feedback data.
                        </p>
                        <p className="text-sm text-slate-400 dark:text-slate-500">
                          Go to the Dashboard tab, upload feedback data, and click "Analyze" to generate user stories.
                        </p>
                      </div>
                    );
                  })()
                ) : currentProjectUserStories && currentProjectUserStories.length > 0 ? (
                  /* Show user stories even without loaded comments if they exist in Redux */
                  <UserStoryList 
                    userStories={currentProjectUserStories}
                    platform="jira"
                    projectId={currentProjectId}
                    isAnalyzing={loading}
                  />
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
                      <Sparkles className="w-8 h-8 text-slate-400" />
                    </div>
                    <h3 className="text-lg font-medium text-slate-900 dark:text-foreground mb-2">
                      No User Stories Found
                    </h3>
                    <p className="text-slate-500 dark:text-slate-400 mb-4">
                      {loadedComments && loadedComments.length > 0 
                        ? "User stories should have been generated. Try refreshing or check the console for errors."
                        : "No comments available. Please upload feedback data to use Jira integration."
                      }
                    </p>
                    {process.env.NODE_ENV === 'development' && (
                      <Button
                        onClick={() => {
                          const effectiveProjectId = currentProjectId || personalProjectId;
                          if (effectiveProjectId && user?.id) {
                            const formattedProjectId = effectiveProjectId.startsWith('project_') ? effectiveProjectId.replace('project_', '') : effectiveProjectId;
                            const userId = user.id || user.user_id || user.username;
                            dispatch(fetchUserStoriesByProject({
                              projectId: formattedProjectId,
                              userId
                            }));
                          }
                        }}
                        variant="saramsa"
                        className="mt-4 px-4 py-2 text-sm"
                      >
                        Refresh user stories
                      </Button>
                    )}
                  </div>
                )
              ) : (
                /* Azure User Stories View */
                (() => {
                  console.log('🔍 Azure User Stories Debug:', {
                    deepAnalysis: deepAnalysis,
                    deepAnalysisWorkItems: deepAnalysis?.work_items,
                    workItemsLength: deepAnalysis?.work_items?.length,
                    deepAnalysisKeys: deepAnalysis ? Object.keys(deepAnalysis) : 'null',
                    deepAnalysisType: typeof deepAnalysis
                  });
                  
                  // Check if we have work items in the response
                  const hasWorkItems = deepAnalysis?.work_items && deepAnalysis.work_items.length > 0;
                  const hasValidDeepAnalysis = deepAnalysis && (deepAnalysis.work_items || deepAnalysis.work_items_by_feature);
                  const hasUserStories = currentProjectUserStories && currentProjectUserStories.length > 0;
                  console.log('🔍 Final check - hasWorkItems:', hasWorkItems, 'work_items length:', deepAnalysis?.work_items?.length);
                  console.log('🔍 Final check - hasValidDeepAnalysis:', hasValidDeepAnalysis);
                  console.log('🔍 Final check - hasUserStories:', hasUserStories);
                  console.log('🔍 Final check - deepAnalysis.work_items:', deepAnalysis?.work_items);
                  console.log('🔍 Final check - currentProjectUserStories:', currentProjectUserStories);
                  console.log('🔍 Final check - currentProjectUserStories length:', currentProjectUserStories?.length);
                  console.log('🔍 Final check - currentProjectUserStories[0]:', currentProjectUserStories?.[0]);
                  console.log('🔍 Final check - Condition result:', (hasValidDeepAnalysis && hasWorkItems) || hasUserStories);
                  
                  // Simplified condition - show if we have ANY work items from either source
                  const shouldShowUserStories = (hasValidDeepAnalysis && hasWorkItems) || hasUserStories;
                  
                  return shouldShowUserStories ? (
                    <UserStoryList 
                      key={`user-stories-${deepAnalysis?.id || currentProjectUserStories?.[0]?.id || 'default'}`} 
                      userStories={hasWorkItems ? [{
                        id: deepAnalysis.id,
                        type: deepAnalysis.type || 'user_story',
                        userId: deepAnalysis.userId,
                        projectId: deepAnalysis.projectId,
                        process_template: deepAnalysis.process_template || 'Agile',
                        platform: deepAnalysis.platform,
                        work_items: deepAnalysis.work_items,
                        summary: deepAnalysis.summary,
                        generated_at: deepAnalysis.generated_at,
                        comments_count: deepAnalysis.comments_count || 0
                      }] : currentProjectUserStories}
                      platform="azure"
                      projectId={currentProjectId}
                    />
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-muted-foreground dark:text-muted-foreground">
                        No deep analysis data available. Please upload feedback data to generate user stories.
                      </p>
                    </div>
                  );
                })()
              )}
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
