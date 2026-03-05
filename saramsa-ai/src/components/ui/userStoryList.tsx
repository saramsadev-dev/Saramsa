"use client";

import { useEffect, useMemo, useState, CSSProperties } from "react";
import { motion } from "framer-motion";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  toggleActionSelection,
  clearSelectedActions,
  clearActionItems,
  addActionItem,
  updateActionItem,
  removeActionItem,
} from "@/store/features/workItems/workItemsSlice";
import { submitUserStories, setDeepAnalysis } from "@/store/features/analysis/analysisSlice";
import type { UserStory } from "@/store/features/userStories/userStoriesSlice";
import { deleteWorkItems, fetchUserStoriesByProject, setCurrentProjectUserStories } from "@/store/features/userStories/userStoriesSlice";
import { DeleteWorkItemsModal } from './DeleteWorkItemsModal';
import { DashboardIntegrationModal } from './dashboard/DashboardIntegrationModal';
import { WorkItemReviewModal } from './WorkItemReviewModal';
import { WorkItemQualityGateModal } from './WorkItemQualityGateModal';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import type {
  ActionItem,
  Feature,
} from "@/store/features/workItems/workItemsSlice";
import {
  Edit,
  Trash2,
  Send,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Bug,
  RefreshCw,
  CheckCircle,
} from "lucide-react";
import { Badge } from "./badge";
import { Card, CardContent } from "./card";
import { Checkbox } from "./checkbox";
import { EditActionDrawer } from "./edit-action-drawer";
import apiRequest from "@/lib/apiRequest";
import { getRelatedInsightsForWorkItem } from "@/lib/insightTraceability";
import { DEFAULT_QUALITY_RULES, evaluateWorkItems, type QualityReport, type QualityRules } from "@/lib/workItemQuality";

interface WorkItem {
  id: string;
  type: string;
  title: string;
  description: string;
  priority: string;
  tags?: string[];
  labels?: string[];
  acceptance_criteria?: string;
  acceptance?: string;
  business_value?: string;
  effort_estimate?: string;
  feature_area: string;
  created_at?: string;
}

interface UserStoryListProps {
  userStories?: UserStory[];
  platform?: 'azure' | 'jira';
  projectId?: string;
  projectKey?: string;
  onRegenerateAnalysis?: () => void;
  isAnalyzing?: boolean;
}

export const UserStoryList = ({ 
  userStories, 
  platform = 'azure',
  projectId,
  projectKey,
  onRegenerateAnalysis,
  isAnalyzing 
}: UserStoryListProps) => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { selectedActions, actionItems, features, loading, error } = useAppSelector((state) => state.workItems);
  const { loading: analysisLoading, projectContext, analysisData } = useAppSelector((state) => state.analysis);
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const { currentProjectUserStories } = useAppSelector((state) => state.userStories);
  const { projects } = useAppSelector((state) => state.projects);
  
  const isPushing = analysisLoading;
  
  // Check if project is draft - check both projectContext and actual project from projects list
  const currentProject = projectId ? projects.find((p: any) => p.id === projectId) : null;
  const hasIntegrations = currentProject?.externalLinks && currentProject.externalLinks.length > 0;
  // Check if the specific platform integration exists
  const hasPlatformIntegration = currentProject?.externalLinks?.some(
    (link: any) => link.provider === platform
  ) || false;
  const isDraftFromContext = projectContext?.is_draft === true || projectContext?.config_state === 'unconfigured';
  const isDraftProject = isDraftFromContext || (!hasIntegrations && projectId) || (!hasPlatformIntegration && projectId);
  const currentProjectUserStoryIds = currentProjectUserStories.map(story => story.id);
  const currentProjectUserStoryWorkItems = currentProjectUserStories.flatMap(story => story.work_items || []);
  const currentProjectUserStoryWorkItemIds = currentProjectUserStoryWorkItems.map(item => item.id);
  const currentProjectUserStoryWorkItemIdsSet = new Set(currentProjectUserStoryWorkItemIds);

  const [editingAction, setEditingAction] = useState<ActionItem | null>(null);
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);
  const [collapsedFeatures, setCollapsedFeatures] = useState<Set<string>>(
    new Set()
  );
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showIntegrationModal, setShowIntegrationModal] = useState(false);
  const [expandedDescriptionIds, setExpandedDescriptionIds] = useState<Record<string, boolean>>({});
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showQualityModal, setShowQualityModal] = useState(false);
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [qualityRules, setQualityRules] = useState<QualityRules>(DEFAULT_QUALITY_RULES);
  const [qualityLoading, setQualityLoading] = useState(false);

  const insightsList = useMemo(() => {
    const rawInsights =
      analysisData?.insights ||
      analysisData?.analysisData?.insights ||
      analysisData?.analysisData?.pipeline_insights ||
      analysisData?.analysisData?.pipelineInsights ||
      [];
    return Array.isArray(rawInsights)
      ? rawInsights.map((insight) => String(insight)).filter(Boolean)
      : [];
  }, [analysisData]);

  const relatedInsightsByActionId = useMemo(() => {
    if (!insightsList.length || actionItems.length === 0) return new Map<string, string[]>();
    const map = new Map<string, string[]>();
    actionItems.forEach((action) => {
      const matches = getRelatedInsightsForWorkItem(insightsList, {
        id: action.id,
        title: action.title,
        description: action.description,
        tags: action.tags,
        featureArea: action.featureArea,
      });
      map.set(action.id, matches.map((match) => match.item));
    });
    return map;
  }, [actionItems, insightsList]);

  const toggleDescription = (id: string) => {
    setExpandedDescriptionIds((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const truncateStyle: CSSProperties = useMemo(
    () => ({
      display: "-webkit-box",
      WebkitLineClamp: 1,
      WebkitBoxOrient: "vertical",
      overflow: "hidden",
    }),
    []
  );

  const renderDescription = (text: string | undefined | null, id: string) => {
    if (!text) return null;
    const isExpanded = expandedDescriptionIds[id] === true;
    const shouldShowToggle = text.length > 180;

    return (
      <div className="space-y-1">
        <p
          className="text-sm text-muted-foreground dark:text-muted-foreground leading-relaxed"
          style={!isExpanded ? truncateStyle : undefined}
        >
          {text}
        </p>
        {shouldShowToggle && (
          <Button
            type="button"
            onClick={() => toggleDescription(id)}
            variant="link"
            size="sm"
            className="text-xs font-medium text-saramsa-brand hover:text-saramsa-brand-hover dark:text-saramsa-brand dark:hover:text-saramsa-brand-hover focus:outline-none"
          >
            {isExpanded ? "See less" : "See more"}
          </Button>
        )}
      </div>
    );
  };

  const renderRelatedInsights = (actionId: string) => {
    const related = relatedInsightsByActionId.get(actionId) || [];
    if (related.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-1">
        {related.slice(0, 2).map((insight, idx) => (
          <Badge key={`${actionId}-insight-${idx}`} variant="outline" className="text-xs">
            Insight: {insight}
          </Badge>
        ))}
      </div>
    );
  };

  const recalculateSummary = (existingSummary: UserStory['summary'] | undefined, updatedWorkItems: UserStory['work_items'] = []) => {
    const summary = existingSummary
      ? { ...existingSummary }
      : {
          totalitems: 0,
          bytype: {} as Record<string, number>,
          bypriority: {} as Record<string, number>,
        };

    summary.totalitems = updatedWorkItems.length;
    summary.bytype = {};
    summary.bypriority = {};

    updatedWorkItems.forEach((item) => {
      const typeKey = (item.type || 'Unknown').toLowerCase();
      const priorityKey = (item.priority || 'Unknown').toLowerCase();

      summary.bytype[typeKey] = (summary.bytype[typeKey] || 0) + 1;
      summary.bypriority[priorityKey] = (summary.bypriority[priorityKey] || 0) + 1;
    });

    return summary;
  };


  // Set user stories or deep analysis data when component mounts or data changes
  useEffect(() => {
    console.log('🔍 UserStoryList useEffect - userStories:', userStories);
    console.log('🔍 UserStoryList useEffect - currentProjectUserStories:', currentProjectUserStories);
    console.log('🔍 UserStoryList useEffect - features:', features);
    console.log('🔍 UserStoryList useEffect - actionItems:', actionItems);
    
    // Use userStories work items (prioritize prop over Redux state)
    const workItemsToProcess = userStories && userStories.length > 0 
      ? userStories[0]?.work_items // Use the first (most recent) user story from props
      : currentProjectUserStories && currentProjectUserStories.length > 0
      ? currentProjectUserStories[0]?.work_items // Fallback to Redux state
      : [];
    
    console.log('🔍 UserStoryList useEffect - work_items:', workItemsToProcess);
    console.log('🔍 UserStoryList useEffect - work_items length:', workItemsToProcess?.length);
    
    if (workItemsToProcess && workItemsToProcess.length > 0) {
      console.log('🔍 UserStoryList - Converting work items to action items:', workItemsToProcess.length);
      
      // Clear existing action items first to prevent duplicates
      dispatch(clearActionItems());
      dispatch(clearSelectedActions());
      
      // Convert work items to action items and add them
      workItemsToProcess.forEach((item, index) => {
        console.log(`🔍 UserStoryList - Converting item ${index}:`, item);
        const actionItem: ActionItem = {
          id: item.id,
          title: item.title,
          description: item.description,
          priority: item.priority as "low" | "medium" | "high" | "critical",
          type: item.type as "feature" | "bug" | "change",
          status: "todo",
          createdAt: 'created_at' in item ? item.created_at : new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          tags: item.tags || item.labels || [],
          acceptance: item.acceptancecriteria || item.acceptance_criteria || item.acceptance || '',
          featureArea: item.feature_area || item.featureArea || item.feature || item.feature_name || '',
        };
        console.log(`🔍 UserStoryList - Dispatching action item ${index}:`, actionItem);
        dispatch(addActionItem(actionItem));
      });
      
      console.log('🔍 UserStoryList - Finished converting work items to action items');
    } else {
      console.log('🔍 UserStoryList - No work items to process');
    }
  }, [userStories, currentProjectUserStories, dispatch, platform]);

  const handleActionSelect = (actionId: string) => {
    // Check if this work item has already been submitted
    const workItem = currentProjectUserStoryWorkItems.find(item => item.id === actionId);
    if (workItem?.submitted) {
      alert('This work item has already been submitted and cannot be selected again.');
      return;
    }
    dispatch(toggleActionSelection(actionId));
  };

  const handleEditAction = (action: ActionItem) => {
    setEditingAction(action);
    setIsEditDrawerOpen(true);
  };

  const handleSaveAction = async (updatedAction: ActionItem) => {
    try {
      // First update the local state immediately for better UX
      dispatch(updateActionItem(updatedAction));

      // Then make API call to persist changes to backend
      const response = await apiRequest(
        "put",
        `/insights/work-items/${updatedAction.id}/update/`,
        {
          title: updatedAction.title,
          description: updatedAction.description,
          acceptance: updatedAction.acceptance,
          priority: updatedAction.priority,
          type: updatedAction.type,
          tags: updatedAction.tags,
          status: updatedAction.status,
          project_id: projectId,
        },
        true
      );

      if (response.status !== 200) {
        throw new Error("Failed to update work item on server");
      }

      const result = response.data;
      console.log("User story updated on server:", result);

      setIsEditDrawerOpen(false);
      setEditingAction(null);
    } catch (error) {
      console.error("Error updating user story:", error);
      // Revert the local state change if server update failed
      if (editingAction) {
        dispatch(updateActionItem(editingAction));
      }
      alert("Failed to update user story. Please try again.");
    }
  };

  const handlePushActionItems = async () => {
    if (selectedActions.length === 0) {
      alert("Please select user stories to push");
      return;
    }

    if (!projectId) {
      alert("Project ID is required for submission");
      return;
    }

    // Check if project is a draft (no integrations configured)
    // Also check if projectId starts with "proj_draft" which indicates a draft project
    const isDraftProjectId = projectId && (projectId.startsWith('proj_draft') || projectId.includes('draft'));
    
    console.log('🔍 Push check - projectId:', projectId);
    console.log('🔍 Push check - platform:', platform);
    console.log('🔍 Push check - isDraftFromContext:', isDraftFromContext);
    console.log('🔍 Push check - hasIntegrations:', hasIntegrations);
    console.log('🔍 Push check - hasPlatformIntegration:', hasPlatformIntegration);
    console.log('🔍 Push check - isDraftProjectId:', isDraftProjectId);
    console.log('🔍 Push check - currentProject:', currentProject);
    console.log('🔍 Push check - final isDraftProject:', isDraftProject || isDraftProjectId);
    
    // Block push if: draft project, draft project ID, no integrations at all, or no platform-specific integration
    // Also block if currentProject is null (project not in list yet, likely a draft)
    const shouldBlockPush = 
      isDraftProject || 
      isDraftProjectId || 
      (projectId && !currentProject) ||  // Project not found in list - likely draft
      (currentProject && !hasIntegrations) || 
      (currentProject && !hasPlatformIntegration);
    
    if (shouldBlockPush) {
      console.log('🚫 Blocking push - project needs integration configuration for', platform);
      setShowIntegrationModal(true);
      return;
    }

    // The backend expects the project ID without the project_ prefix
    // It will add the prefix internally when querying Cosmos DB
    const formattedProjectId = projectId.startsWith('project_') ? projectId.replace('project_', '') : projectId;
    console.log('🔍 Original projectId:', projectId);
    console.log('🔍 Formatted projectId (without project_ prefix):', formattedProjectId);

    // Debug user authentication
    console.log('🔍 Auth state - isAuthenticated:', isAuthenticated);
    console.log('🔍 User object:', user);
    console.log('🔍 User user_id:', user?.user_id);
    console.log('🔍 User username:', user?.username);
    console.log('🔍 User object keys:', user ? Object.keys(user) : 'No user object');
    console.log('🔍 User object full:', JSON.stringify(user, null, 2));

    if (!isAuthenticated || !user) {
      alert("User authentication is required. Please login again.");
      return;
    }

    if (!user.user_id && !user.username) {
      alert("User ID not found. Please logout and login again.");
      return;
    }

    // Use the id field (which contains the proper user_xxxxx format) instead of user_id
    const userId = user.id || user.user_id || user.username || '';
    
    // Check if user_id is in the correct format
    if (userId && !userId.startsWith('user_')) {
      console.warn('⚠️ User ID is not in expected format. Forcing session refresh...');
      alert("User session needs to be refreshed. Please logout and login again to get the correct user ID.");
      return;
    }
    
    if (!userId) {
      alert("User ID could not be determined. Please logout and login again.");
      return;
    }

    console.log('🔍 Final userId being sent:', userId);

    const selectedItems = getSelectedItems();

    if (selectedItems.length === 0) {
      alert("No selected items found");
      return;
    }

    // Transform action items to user story format
    const userStoriesToSubmit = selectedItems.map((item: ActionItem) => ({
      id: item.id,
      title: item.title,
      description: item.description,
      type: item.type === 'feature' ? 'Feature' : item.type === 'bug' ? 'Bug' : 'Task',
      priority: item.priority,
      acceptance_criteria: item.acceptance || '',
      business_value: '', // Could be added to ActionItem interface if needed
      tags: item.tags || [],
      created: false // Always false for new submissions
    }));

    try {
      console.log('🔍 Submitting user stories with userId:', userId);
      
      const result = await dispatch(
        submitUserStories({
          userId: userId,
          projectId: formattedProjectId,
          userStories: userStoriesToSubmit,
          platform: platform,
          processTemplate: 'Agile',
          time: new Date().toISOString()
        })
      ).unwrap();

      // Check if the submission was actually successful
      if (result.success) {
        // Clear selection after successful submission
        dispatch(clearSelectedActions());
        
        // Update Redux state with the updated user stories from the response
        if (result.updated_user_stories && Array.isArray(result.updated_user_stories)) {
          console.log('🔍 Updating Redux state with submitted user stories from response');
          dispatch(setCurrentProjectUserStories(result.updated_user_stories));
          
          // Also update deepAnalysis to sync the top section
          if (userStories && userStories.length > 0) {
            const updatedDeepAnalysis = {
              ...userStories[0],
              work_items: result.updated_user_stories[0]?.work_items || userStories[0].work_items
            };
            console.log('🔍 Updating deepAnalysis to sync top section');
            dispatch(setDeepAnalysis(updatedDeepAnalysis));
          }
        } else {
          // Fallback: Refresh user stories to get updated submission status
          if (projectId && user) {
            console.log('🔍 Refreshing user stories after successful submission (fallback)');
            dispatch(fetchUserStoriesByProject({ 
              projectId: projectId.startsWith('project_') ? projectId.replace('project_', '') : projectId,
              userId: user.id || user.user_id || user.username
            }));
          }
        }
        
        const summary = result.summary || {};
        const created = summary.created || 0;
        const skipped = summary.skipped || 0;
        const failed = summary.failed || 0;
      const submissionResults = (result.results || []).filter((r: any) => r.success);
      const submissionTimestamp = result.submitted_at || new Date().toISOString();

      if (submissionResults.length > 0) {
        const submittedIdSet = new Set(submissionResults.map((r: any) => r.story_id));

        const baseUserStory =
          currentProjectUserStories.find((story) => story.work_items?.some((item) => submittedIdSet.has(item.id))) ||
          userStories?.find((story) => story.work_items?.some((item) => submittedIdSet.has(item.id)));

        if (baseUserStory) {
          const updatedWorkItems =
            baseUserStory.work_items?.map((item) => {
              if (submittedIdSet.has(item.id)) {
                const match = submissionResults.find((res: any) => res.story_id === item.id);
                return {
                  ...item,
                  submitted: true,
                  submittedAt: submissionTimestamp,
                  submittedTo: platform,
                  external_work_item_id: match?.work_item_id ?? item.external_work_item_id,
                  external_url: match?.url ?? item.external_url,
                };
              }
              return item;
            }) || [];

          const updatedSummary = recalculateSummary(baseUserStory.summary, updatedWorkItems);
          const updatedStory: UserStory = {
            ...baseUserStory,
            work_items: updatedWorkItems,
            summary: updatedSummary,
            generated_at: baseUserStory.generated_at,
          };

          const nextStories = currentProjectUserStories.length
            ? currentProjectUserStories.map((story) => (story.id === updatedStory.id ? updatedStory : story))
            : [updatedStory];

          dispatch(setCurrentProjectUserStories(nextStories));
          dispatch(setDeepAnalysis({
            ...(userStories?.[0] || updatedStory),
            work_items: updatedWorkItems,
            summary: updatedSummary,
          }));

          submissionResults.forEach((res: any) => {
            const targetAction = actionItems.find((action) => action.id === res.story_id);
            if (targetAction) {
              dispatch(
                updateActionItem({
                  ...targetAction,
                  status: 'done',
                  submitted: true,
                  submittedAt: submissionTimestamp,
                  externalWorkItemId: res.work_item_id?.toString?.() || String(res.work_item_id ?? ''),
                  externalUrl: res.url,
                })
              );
            }
          });
        }
      }
        
        if (created > 0) {
          alert(`Successfully submitted ${created} user stories to ${platform === 'azure' ? 'Azure DevOps' : 'Jira'}${skipped > 0 ? ` (${skipped} already existed)` : ''}`);
        } else if (skipped > 0 && failed === 0) {
          alert(`All ${skipped} user stories were already created in ${platform === 'azure' ? 'Azure DevOps' : 'Jira'}`);
        }
      } else {
        // Handle case where submission failed
        const summary = result.summary || {};
        const failed = summary.failed || 0;
        const results = result.results || [];
        
        // Get error messages from failed results
        const errorMessages = results
          .filter((r: any) => !r.success)
          .map((r: any) => r.error)
          .filter(Boolean);
        
        const errorMessage = errorMessages.length > 0 
          ? errorMessages[0] 
          : 'Unknown error occurred';
        
        alert(`Failed to submit user stories: ${errorMessage}`);
      }
    } catch (error) {
      console.error('Failed to submit user stories:', error);
      alert(`Failed to submit user stories: ${error}`);
    }
  };

  const fetchQualityRules = async () => {
    if (!projectId) return DEFAULT_QUALITY_RULES;
    try {
      const response = await apiRequest('get', `/work-items/quality-rules/?project_id=${projectId}`, undefined, true);
      const rules = response?.data?.data?.rules;
      if (rules) {
        setQualityRules(rules);
        return rules as QualityRules;
      }
    } catch (error) {
      // Fall back to default rules if API fails
    }
    setQualityRules(DEFAULT_QUALITY_RULES);
    return DEFAULT_QUALITY_RULES;
  };

  const handleReviewClick = async () => {
    if (selectedActions.length === 0) {
      alert("Please select user stories to push");
      return;
    }

    setQualityLoading(true);
    const rules = await fetchQualityRules();
    const selectedItems = getSelectedItems();
    const report = evaluateWorkItems(selectedItems, rules);
    report.allow_push_with_warnings = rules.allow_push_with_warnings;

    setQualityReport(report);
    setQualityLoading(false);

    if (report.items_with_issues > 0) {
      setShowQualityModal(true);
      if (!rules.allow_push_with_warnings) {
        return;
      }
    }

    setShowReviewModal(true);
  };

  const getSelectedItems = () => {
    const selectedFromFeatures = features
      .flatMap((feature: Feature) => feature.actions)
      .filter((action: ActionItem) => selectedActions.includes(action.id));

    const selectedFromActionItems = actionItems
      .filter((action: ActionItem) => selectedActions.includes(action.id));

    return [...selectedFromFeatures, ...selectedFromActionItems];
  };

  const handleDeleteSelected = () => {
    if (selectedActions.length === 0) {
      alert("Please select work items to delete");
      return;
    }
    
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    const toDelete = [...selectedActions];
    
    try {
      setDeleteLoading(true);
      
      // We need to identify which user story these work items belong to
      // Use the Redux state to find the matching user story
      const matchingUserStories = currentProjectUserStories.filter(story => 
        story.work_items?.some(item => toDelete.includes(item.id))
      );
      
      if (matchingUserStories.length === 0) {
        alert('Could not find user story containing these work items');
        return;
      }
      
      // Use the first matching user story
      const userStoryId = matchingUserStories[0].id;
      
      // Use the proper Redux action for deleting work items
      await dispatch(deleteWorkItems({ 
        workItemIds: toDelete,
        userStoryId: userStoryId,
        projectId: projectId
      })).unwrap();

      // Remove deleted items from action items list to reflect immediately
      toDelete.forEach((id) => dispatch(removeActionItem(id)));

      const baseStory =
        currentProjectUserStories.find((story) => story.id === userStoryId) ||
        userStories?.find((story) => story.id === userStoryId);

      const updatedWorkItems =
        (baseStory?.work_items || []).filter((item) => !toDelete.includes(item.id));
      const updatedSummary = recalculateSummary(baseStory?.summary, updatedWorkItems);

      if (baseStory) {
        const updatedStory: UserStory = {
          ...baseStory,
          work_items: updatedWorkItems,
          summary: updatedSummary,
        };

        const nextStories = currentProjectUserStories.length
          ? currentProjectUserStories.map((story) => (story.id === userStoryId ? updatedStory : story))
          : [updatedStory];

        dispatch(setCurrentProjectUserStories(nextStories));
        dispatch(
          setDeepAnalysis({
            ...(userStories?.[0] || updatedStory),
            work_items: updatedWorkItems,
            summary: updatedSummary,
          })
        );
      }
      
      // Clear selection after successful deletion
      dispatch(clearSelectedActions());
      
      // Close modal
      setShowDeleteModal(false);
      
      console.log(`Successfully deleted ${toDelete.length} work items`);
    } catch (err) {
      console.error('Failed to delete work items:', err);
      alert('Failed to delete work items. Please try again.');
    } finally {
      setDeleteLoading(false);
    }
  };

  const toggleFeatureCollapse = (featureName: string) => {
    const newCollapsed = new Set(collapsedFeatures);
    if (newCollapsed.has(featureName)) {
      newCollapsed.delete(featureName);
    } else {
      newCollapsed.add(featureName);
    }
    setCollapsedFeatures(newCollapsed);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "critical":
        return "bg-red-500 text-white";
      case "high":
        return "bg-orange-500 text-white";
      case "medium":
        return "bg-yellow-500 text-black";
      case "low":
        return "bg-green-500 text-white";
      default:
        return "bg-secondary text-secondary-foreground border border-border";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "feature":
      case "user story":
      case "product backlog item":
      case "requirement":
      case "story":
      case "epic":
        return <Sparkles className="w-4 h-4" />;
      case "bug":
        return <Bug className="w-4 h-4" />;
      case "task":
      case "issue":
        return <RefreshCw className="w-4 h-4" />;
      default:
        return <Sparkles className="w-4 h-4" />;
    }
  };

  const getPlatformDisplayName = () => {
    return platform === 'azure' ? 'Azure DevOps' : 'Jira';
  };

  // Get submitted work items for the "Pushed to" section
  const getSubmittedWorkItems = () => {
    console.log('🔍 currentProjectUserStories:', currentProjectUserStories);
    console.log('🔍 currentProjectUserStoryWorkItems:', currentProjectUserStoryWorkItems);
    
    const submitted = currentProjectUserStoryWorkItems.filter(item => item.submitted === true);
    console.log('🔍 Submitted work items:', submitted);
    console.log('🔍 All work items:', currentProjectUserStoryWorkItems.map(item => ({ id: item.id, submitted: item.submitted })));
    return submitted;
  };

  console.log('🔍 UserStoryList render - features.length:', features.length, 'actionItems.length:', actionItems.length);
  console.log('🔍 UserStoryList render - userStories:', userStories);
  console.log('🔍 UserStoryList render - currentProjectUserStories:', currentProjectUserStories);
  console.log('🔍 UserStoryList render - features:', features);
  console.log('🔍 UserStoryList render - actionItems:', actionItems);
  
  // Check if there are any user stories available (from props, Redux state, features, or action items)
  const hasUserStories = (userStories && userStories.length > 0) || 
                        (currentProjectUserStories && currentProjectUserStories.length > 0);
  const hasWorkItems = features.length > 0 || actionItems.length > 0;
  
  // Also check if we have work_items directly in the user stories data
  const hasWorkItemsInData = userStories?.some(story => story.work_items && story.work_items.length > 0) ||
                            currentProjectUserStories?.some(story => story.work_items && story.work_items.length > 0);
  
  console.log('🔍 UserStoryList render - hasUserStories:', hasUserStories);
  console.log('🔍 UserStoryList render - hasWorkItems:', hasWorkItems);
  console.log('🔍 UserStoryList render - hasWorkItemsInData:', hasWorkItemsInData);
  console.log('🔍 UserStoryList render - userStories length:', userStories?.length);
  console.log('🔍 UserStoryList render - currentProjectUserStories length:', currentProjectUserStories?.length);
  console.log('🔍 UserStoryList render - features length:', features.length);
  console.log('🔍 UserStoryList render - actionItems length:', actionItems.length);
  
  // Show content if we have user stories OR work items OR work items in data
  const shouldShowContent = hasUserStories || hasWorkItems || hasWorkItemsInData;
  
  if (!shouldShowContent) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-lg font-medium text-slate-900 dark:text-foreground mb-2">
          No User Stories Generated
        </h3>
        <p className="text-slate-500 dark:text-slate-400 mb-4">
          User stories will be automatically generated after you analyze
          feedback data.
        </p>
        <p className="text-sm text-slate-400 dark:text-slate-500">
          Go to the Dashboard tab, upload feedback data, and click "Analyze" to
          generate user stories.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="text-sm text-muted-foreground dark:text-muted-foreground">
        User story generation based on the uploaded feedback analysis for {getPlatformDisplayName()}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
          <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Action Items (from deep analysis) - Filter out submitted items */}
      {actionItems.filter(actionItem => {
        const submittedItem = currentProjectUserStoryWorkItems.find(item => item.id === actionItem.id);
        return !submittedItem?.submitted;
      }).length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
            Generated Work Items ({actionItems.filter(actionItem => {
              const submittedItem = currentProjectUserStoryWorkItems.find(item => item.id === actionItem.id);
              return !submittedItem?.submitted;
            }).length})
          </h3>
          {actionItems.filter(actionItem => {
            const submittedItem = currentProjectUserStoryWorkItems.find(item => item.id === actionItem.id);
            return !submittedItem?.submitted;
          }).map((actionItem: ActionItem, index: number) => (
            <motion.div
              key={actionItem.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="bg-card/90 dark:bg-card/95 border border-border/60 dark:border-border/60 rounded-xl p-4"
            >
              <div className="flex items-start gap-3">
                <Checkbox
                  checked={selectedActions.includes(actionItem.id)}
                  onCheckedChange={() => handleActionSelect(actionItem.id)}
                  className="mt-1"
                  disabled={currentProjectUserStoryWorkItems.find(item => item.id === actionItem.id)?.submitted === true}
                />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-foreground dark:text-foreground">
                      {actionItem.title}
                    </h4>
                    <Badge
                      variant={
                        actionItem.priority === "high" || actionItem.priority === "critical"
                          ? "destructive"
                          : actionItem.priority === "medium"
                          ? "default"
                          : "secondary"
                      }
                    >
                      {actionItem.priority}
                    </Badge>
                    <Badge variant="outline">{actionItem.type}</Badge>
                  </div>
                  {renderDescription(actionItem.description, `draft-${actionItem.id}`)}
                  {actionItem.acceptance && (
                    <div className="text-xs text-muted-foreground dark:text-muted-foreground">
                      <strong>Acceptance Criteria:</strong> {actionItem.acceptance}
                    </div>
                  )}
                  {actionItem.tags && actionItem.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {actionItem.tags.map((tag, tagIndex) => (
                        <Badge key={tagIndex} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                  {renderRelatedInsights(actionItem.id)}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleEditAction(actionItem)}
                  className="text-muted-foreground hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground"
                >
                  <Edit className="w-4 h-4" />
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Features and Actions */}
      {features.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
            Features ({features.length})
          </h3>
          {features.map((feature: Feature, featureIndex: number) => (
          <motion.div
            key={feature.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: featureIndex * 0.1 }}
            className="space-y-4"
          >
            {/* Feature Header with Collapse */}
            <div className="flex items-center gap-3">
              <Button
                onClick={() => toggleFeatureCollapse(feature.name)}
                variant="ghost"
                size="icon"
                className="h-7 w-7 hover:bg-accent/60 dark:hover:bg-accent/60"
              >
                {collapsedFeatures.has(feature.name) ? (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </Button>
              <Badge className={`px-3 py-1 ${feature.color || 'bg-saramsa-brand/10 text-saramsa-brand dark:bg-saramsa-brand/20 dark:text-saramsa-brand'}`}>
                {feature.name}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {feature.actions.length} items
              </span>
            </div>

            {/* Action Items - Collapsible */}
            {!collapsedFeatures.has(feature.name) && (
              <div className="space-y-4 ml-6">
                {feature.actions.map(
                  (action: ActionItem, actionIndex: number) => (
                    <motion.div
                      key={action.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{
                        duration: 0.4,
                        delay: featureIndex * 0.1 + actionIndex * 0.05,
                      }}
                    >
                      <Card className="bg-card/90 dark:bg-card/95 border border-border/60 dark:border-border/60 hover:shadow-md transition-all duration-300">
                        <CardContent className="p-6">
                          <div className="space-y-4">
                            {/* Action Header */}
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex items-start gap-3 flex-1">
                                <Checkbox
                                  checked={selectedActions.includes(action.id)}
                                  onCheckedChange={() =>
                                    handleActionSelect(action.id)
                                  }
                                  className="mt-1"
                                  disabled={currentProjectUserStoryWorkItems.find(item => item.id === action.id)?.submitted === true}
                                />
                                <div className="space-y-1 flex-1">
                                  <div className="flex items-center gap-2">
                                    {getTypeIcon(action.type || "feature")}
                                    <h4 className="font-medium text-foreground dark:text-foreground">
                                      {action.title}
                                    </h4>
                                    <Badge
                                      className={`px-2 py-1 text-xs ${getPriorityColor(
                                        action.priority || "medium"
                                      )}`}
                                    >
                                      {action.priority}
                                    </Badge>
                                  </div>
                                </div>
                              </div>

                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditAction(action)}
                                className="text-saramsa-brand hover:text-saramsa-brand/80 hover:bg-saramsa-brand/10"
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                Edit
                              </Button>
                            </div>

                            {/* Action Details Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                              {/* Description */}
                              <div className="space-y-2">
                                <h5 className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                                  Description
                                </h5>
                                {renderDescription(action.description, `feature-${action.id}`)}
                              </div>

                              {/* Acceptance Criteria */}
                              <div className="space-y-2">
                                <h5 className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                                  Acceptance Criteria
                                </h5>
                                <p className="text-sm text-muted-foreground dark:text-muted-foreground leading-relaxed">
                                  {action.acceptance ||
                                    "Define acceptance criteria for this user story."}
                                </p>
                              </div>
                            </div>

                            {/* Tags */}
                            {action.tags && action.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {action.tags.map(
                                  (tag: string, index: number) => (
                                    <Badge
                                      key={index}
                                      variant="outline"
                                      className="text-xs bg-secondary/40 dark:bg-secondary/40"
                                    >
                                      {tag}
                                    </Badge>
                                  )
                                )}
                              </div>
                            )}
                            {renderRelatedInsights(action.id)}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  )
                )}
              </div>
            )}
          </motion.div>
        ))}
        </div>
      )}

      {/* Pushed to Jira/Azure Section */}
      {getSubmittedWorkItems().length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
            Pushed to {getPlatformDisplayName()} ({getSubmittedWorkItems().length})
          </h3>
          <div className="space-y-3">
            {getSubmittedWorkItems().map((workItem: any, index: number) => (
              <motion.div
                key={workItem.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <h4 className="font-medium text-foreground dark:text-foreground">
                        {workItem.title}
                      </h4>
                      <Badge className="bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200">
                        Submitted
                      </Badge>
                      <Badge variant="outline">{workItem.type}</Badge>
                    </div>
                    {renderDescription(workItem.description, `submitted-${workItem.id}`)}
                    {renderRelatedInsights(workItem.id)}
                    <div className="flex items-center gap-4 text-xs text-muted-foreground dark:text-muted-foreground">
                      <span>
                        <strong>Submitted:</strong> {new Date(workItem.submittedAt).toLocaleDateString()} at {new Date(workItem.submittedAt).toLocaleTimeString()}
                      </span>
                      {workItem.external_work_item_id && (
                        <span>
                          <strong>ID:</strong> {workItem.external_work_item_id}
                        </span>
                      )}
                    </div>
                  </div>
                  {workItem.external_url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(workItem.external_url, '_blank')}
                      className="text-green-600 border-green-200 hover:bg-green-50 dark:text-green-400 dark:border-green-800 dark:hover:bg-green-900/20"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      View in {getPlatformDisplayName()}
                    </Button>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-4 pt-6 border-t border-border/60 dark:border-border/60">
        {onRegenerateAnalysis && (
          <Button
            onClick={onRegenerateAnalysis}
            disabled={isAnalyzing}
            variant="outline"
            className="text-saramsa-brand border-saramsa-brand/20 hover:bg-saramsa-brand/10 dark:text-saramsa-brand dark:border-saramsa-brand/30 dark:hover:bg-saramsa-brand/20"
          >
            {isAnalyzing ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-saramsa-brand/30 border-t-blue-600 rounded-full animate-spin" />
                <span>Generating...</span>
              </div>
            ) : (
              <span>Regenerate Analysis</span>
            )}
          </Button>
        )}

        <Button
          onClick={handleReviewClick}
          disabled={selectedActions.length === 0 || isPushing || qualityLoading}
          className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to hover:from-saramsa-brand-hover hover:to-saramsa-gradient-to text-white px-6"
        >
          {isPushing || qualityLoading ? (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>{qualityLoading ? "Checking..." : "Pushing..."}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Send className="w-4 h-4" />
              <span>
                {isDraftProject 
                  ? "Configure Integration to Push" 
                  : `Review & Push`
                }
              </span>
            </div>
          )}
        </Button>

        <Button
          variant="outline"
          onClick={handleDeleteSelected}
          disabled={selectedActions.length === 0}
          className="text-red-600 border-red-200 hover:bg-red-50 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-900/20"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete Selected
        </Button>

        <div className="text-sm text-muted-foreground dark:text-muted-foreground">
          {selectedActions.length} items selected
        </div>
      </div>

      {/* Edit Drawer */}
      <EditActionDrawer
        action={editingAction}
        isOpen={isEditDrawerOpen}
        onClose={() => {
          setIsEditDrawerOpen(false);
          setEditingAction(null);
        }}
        onSave={handleSaveAction}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <DeleteWorkItemsModal
          workItemCount={selectedActions.length}
          onConfirm={handleConfirmDelete}
          onCancel={() => setShowDeleteModal(false)}
          loading={deleteLoading}
        />
      )}

      {/* Integration Setup Modal */}
      <DashboardIntegrationModal
        isOpen={showIntegrationModal}
        onClose={() => setShowIntegrationModal(false)}
        projectId={projectId || ''}
      />

      <WorkItemReviewModal
        isOpen={showReviewModal}
        onClose={() => setShowReviewModal(false)}
        onConfirm={() => {
          setShowReviewModal(false);
          handlePushActionItems();
        }}
        items={getSelectedItems()}
        platformLabel={getPlatformDisplayName()}
        isSubmitting={isPushing}
      />

      <WorkItemQualityGateModal
        isOpen={showQualityModal}
        onClose={() => setShowQualityModal(false)}
        onProceed={() => {
          setShowQualityModal(false);
          setShowReviewModal(true);
        }}
        report={qualityReport}
        allowProceed={!!qualityReport?.allow_push_with_warnings}
      />
    </div>
  );
};
