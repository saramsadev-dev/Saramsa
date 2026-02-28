'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Button } from './button';
import { Input } from './input';
import { Alert, AlertDescription } from './alert';
import { Badge } from './badge';
import { Select } from './select';
import { XCircle, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { clearError } from '../../store/features/workItems/workItemsSlice';
import {
  fetchJiraProjects,
  fetchJiraIssueTypes,
  fetchJiraProjectMetadata,
  createJiraIssues,
  createJiraProject,
} from '../../store/features/jira/jiraSlice';
import { analyzeComments } from '../../store/features/analysis/analysisSlice';
import { apiRequest } from '../../lib/apiRequest';
import { useAppDispatch, useAppSelector } from '../../store/hooks';

interface JiraIntegrationProps {
  comments: string[];
  projectId?: string;
}

export default function JiraIntegration({ comments, projectId }: JiraIntegrationProps) {
  const dispatch = useAppDispatch();
  const { projects: jiraProjects, loading, error: jiraError } = useAppSelector((state) => state.jira);
  
  // Local state
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [projectMetadata, setProjectMetadata] = useState<any>(null);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [workItemsResults, setWorkItemsResults] = useState<any>(null);
  const [creationResults, setCreationResults] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState<'project-creation' | 'analysis' | 'work-items' | 'creation'>('project-creation');
  const [error, setError] = useState<string | null>(null);
  
  // Project creation state
  const [projectName, setProjectName] = useState<string>('');
  const [selectedJiraProject, setSelectedJiraProject] = useState<any>(null);
  const [jiraEmail, setJiraEmail] = useState<string>('');
  const [jiraApiToken, setJiraApiToken] = useState<string>('');
  const [jiraDomain, setJiraDomain] = useState<string>('');
  const [createdProjectId, setCreatedProjectId] = useState<string>('');

  useEffect(() => {
    // Load Jira projects on component mount
    dispatch(fetchJiraProjects());
  }, [dispatch]);

  const handleProjectSelect = async (projectId: string) => {
    setSelectedProject(projectId);
    if (projectId) {
      try {
        const metadata = await dispatch(fetchJiraProjectMetadata(projectId)).unwrap();
        setProjectMetadata(metadata);
      } catch (error) {
        console.error('Failed to fetch project metadata:', error);
      }
    }
  };

  // Create Jira project in our database
  const handleCreateProject = async () => {
    if (!selectedJiraProject || !projectName || !jiraEmail || !jiraApiToken || !jiraDomain) {
      setError('Please fill in all required fields');
      return;
    }

    setCurrentStep('project-creation');
    setError(null);

    try {
      console.log('🏗️ Creating Jira project in database...');
      
      const projectData = {
        project_name: projectName,
        jira_project_id: selectedJiraProject.id,
        jira_project_key: selectedJiraProject.key,
        jira_project_name: selectedJiraProject.name,
        jira_domain: jiraDomain,
        jira_email: jiraEmail,
        jira_api_token: jiraApiToken
      };

      const result = await dispatch(createJiraProject(projectData)).unwrap();
      
      if (result.success) {
        setCreatedProjectId(result.project.id);
        console.log('✅ Jira project created:', result.project);
        
        // Store the project ID in localStorage for future use
        if (typeof window !== 'undefined') {
          localStorage.setItem('current_jira_project_id', result.project.id);
        }
        
        // Move to analysis step
        setCurrentStep('analysis');
      } else {
        setError('Failed to create project');
      }
    } catch (error: any) {
      console.error('Failed to create Jira project:', error);
      setError(error || 'Failed to create project');
    }
  };

  // Analyze comments and generate work items
  const handleAnalyze = async () => {
    if (!comments || comments.length === 0) {
      setError('No comments available for analysis');
      return;
    }

    if (!createdProjectId) {
      setError('No project created. Please create a project first.');
      return;
    }

    setCurrentStep('analysis');
    setError(null);

    try {
      console.log('🔄 Starting Jira analysis process...');
      console.log('📊 Comments count:', comments.length);
      console.log('🏗️ Project ID:', createdProjectId);
      
      // Step 1: General Analysis (same as Azure)
      console.log('📈 Step 1: Performing general analysis...');
      const analysisResult = await dispatch(analyzeComments({
        comments,
        projectId: createdProjectId
      })).unwrap();
      
      console.log('✅ General analysis completed:', analysisResult);
      setAnalysisResults(analysisResult);
      
      // Step 2: Use the analysis data directly for Jira issue creation
      console.log('🔧 Step 2: Preparing work items from analysis...');
      const workItemsResult = {
        work_items: analysisResult.work_items || [],
        summary: analysisResult.summary || {}
      };
      
      console.log('✅ Work items generated:', workItemsResult);
      setWorkItemsResults(workItemsResult);
      setCurrentStep('work-items');
      
    } catch (error: any) {
      console.error('❌ Analysis failed:', error);
      setError(error.message || 'Analysis failed');
    }
  };

  const handleCreateIssues = async () => {
    if (!workItemsResults?.work_items || !selectedJiraProject) {
      return;
    }

    setCurrentStep('creation');
    try {
      // Transform work items to match Jira API format
      const transformedItems = workItemsResults.work_items.map((item: any) => ({
        title: item.title,
        description: item.description,
        type: item.type,
        priority: item.priority,
        labels: Array.isArray(item.tags) ? item.tags : (item.tags ? item.tags.split(',').map((tag: string) => tag.trim()) : []),
        acceptance_criteria: item.acceptance_criteria || item.acceptancecriteria || '',
        business_value: item.business_value || item.businessvalue || ''
      }));

      console.log('🔧 Creating Jira issues with:', {
        projectId: createdProjectId,
        projectKey: selectedJiraProject.key,
        itemsCount: transformedItems.length,
        transformedItems
      });

      const result = await dispatch(createJiraIssues({
        items: transformedItems,
        projectId: createdProjectId,
        projectKey: selectedJiraProject.key
      })).unwrap();
      
      setCreationResults(result.results || []);
    } catch (error) {
      console.error('Failed to create Jira issues:', error);
    }
  };

  const clearErrors = () => {
    dispatch(clearError());
    setError(null);
  };

  // Get selected project details
  const selectedProjectDetails = jiraProjects.find((p: any) => p.id === selectedProject);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <img 
              src="https://cdn.worldvectorlogo.com/logos/jira-1.svg" 
              alt="Jira" 
              className="w-6 h-6"
            />
            Jira Integration
          </CardTitle>
          <CardDescription>
            Create a Jira project and generate work items based on your feedback analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Error Display */}
          {(jiraError || error) && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>
                {jiraError || error}
                <Button variant="link" onClick={clearErrors} className="p-0 h-auto">
                  Dismiss
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Step Indicator */}
          <div className="flex items-center justify-center space-x-4 mb-6">
            <div className={`flex items-center space-x-2 ${currentStep === 'project-creation' ? 'text-saramsa-brand' : 'text-muted-foreground'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'project-creation' ? 'bg-saramsa-brand text-white' : 'bg-secondary/60'}`}>
                1
              </div>
              <span className="text-sm font-medium">Create Project</span>
            </div>
            <div className={`flex items-center space-x-2 ${currentStep === 'analysis' ? 'text-saramsa-brand' : currentStep === 'work-items' || currentStep === 'creation' ? 'text-green-600' : 'text-muted-foreground'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'analysis' ? 'bg-saramsa-brand text-white' : currentStep === 'work-items' || currentStep === 'creation' ? 'bg-green-600 text-white' : 'bg-secondary/60'}`}>
                2
              </div>
              <span className="text-sm font-medium">Analyze</span>
            </div>
            <div className={`flex items-center space-x-2 ${currentStep === 'work-items' ? 'text-saramsa-brand' : currentStep === 'creation' ? 'text-green-600' : 'text-muted-foreground'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'work-items' ? 'bg-saramsa-brand text-white' : currentStep === 'creation' ? 'bg-green-600 text-white' : 'bg-secondary/60'}`}>
                3
              </div>
              <span className="text-sm font-medium">Work Items</span>
            </div>
            <div className={`flex items-center space-x-2 ${currentStep === 'creation' ? 'text-saramsa-brand' : 'text-muted-foreground'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${currentStep === 'creation' ? 'bg-saramsa-brand text-white' : 'bg-secondary/60'}`}>
                4
              </div>
              <span className="text-sm font-medium">Create Issues</span>
            </div>
          </div>

          {/* Step 1: Project Creation */}
          {currentStep === 'project-creation' && (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Project Name (in our system)</label>
                <Input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter a name for this project"
                  className="w-full p-2 border border-border/60 rounded-md"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Select Jira Project</label>
                <Select value={selectedProject} onChange={(e) => {
                  const projectId = e.target.value;
                  setSelectedProject(projectId);
                  if (projectId) {
                    const project = jiraProjects.find((p: any) => p.id === projectId);
                    setSelectedJiraProject(project);
                  }
                }}>
                  <option value="">Choose a Jira project...</option>
                  {jiraProjects.map((project: any) => (
                    <option key={project.id} value={project.id}>
                      {project.key} - {project.name} ({project.isCompanyManaged ? 'Company' : 'Team'})
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Jira Domain</label>
                <Input
                  type="text"
                  value={jiraDomain}
                  onChange={(e) => setJiraDomain(e.target.value)}
                  placeholder="your-domain.atlassian.net"
                  className="w-full p-2 border border-border/60 rounded-md"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Jira Email</label>
                <Input
                  type="email"
                  value={jiraEmail}
                  onChange={(e) => setJiraEmail(e.target.value)}
                  placeholder="your-email@company.com"
                  className="w-full p-2 border border-border/60 rounded-md"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Jira API Token</label>
                <Input
                  type="password"
                  value={jiraApiToken}
                  onChange={(e) => setJiraApiToken(e.target.value)}
                  placeholder="Enter your Jira API token"
                  className="w-full p-2 border border-border/60 rounded-md"
                />
              </div>

              <Button 
                onClick={handleCreateProject}
                disabled={!projectName || !selectedProject || !jiraDomain || !jiraEmail || !jiraApiToken || loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Project...
                  </>
                ) : (
                  'Create Jira Project'
                )}
              </Button>
            </div>
          )}

          {/* Step 2: Analysis */}
          {currentStep === 'analysis' && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-800 dark:text-green-200 font-medium">Project Created Successfully!</span>
                </div>
                <p className="text-green-700 dark:text-green-300 text-sm mt-1">
                  Project ID: {createdProjectId}
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Comments to Analyze</label>
                <div className="p-3 bg-secondary/40 dark:bg-card/95 rounded-md">
                  <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                    {comments.length} comments ready for analysis
                  </p>
                </div>
              </div>

              <Button 
                onClick={handleAnalyze}
                disabled={loading || comments.length === 0}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing Comments...
                  </>
                ) : (
                  'Analyze Comments & Generate Work Items'
                )}
              </Button>
            </div>
          )}

          {/* Step 3: Work Items */}
          {currentStep === 'work-items' && workItemsResults && (
            <div className="space-y-4">
              <div className="p-4 bg-saramsa-accent/10 dark:bg-saramsa-accent/20 rounded-xl">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-saramsa-brand" />
                  <span className="text-saramsa-brand dark:text-saramsa-brand font-medium">Analysis Complete!</span>
                </div>
                <p className="text-saramsa-brand/80 dark:text-saramsa-brand/90 text-sm mt-1">
                  Generated {workItemsResults.work_items?.length || 0} work items
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Generated Work Items</label>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {workItemsResults.work_items?.map((item: any, index: number) => (
                    <div key={index} className="p-3 border border-border/60 dark:border-border/60 rounded-md">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-sm">{item.title}</h4>
                        <Badge variant="secondary">{item.type}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground dark:text-muted-foreground mt-1">
                        {item.description}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge variant="outline">{item.priority}</Badge>
                        {item.tags && (
                          <div className="flex space-x-1">
                            {Array.isArray(item.tags) ? item.tags.map((tag: string, tagIndex: number) => (
                              <Badge key={tagIndex} variant="outline" className="text-xs">{tag}</Badge>
                            )) : (
                              <Badge variant="outline" className="text-xs">{item.tags}</Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <Button 
                onClick={handleCreateIssues}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Jira Issues...
                  </>
                ) : (
                  'Create Jira Issues'
                )}
              </Button>
            </div>
          )}

          {/* Step 4: Creation Results */}
          {currentStep === 'creation' && creationResults.length > 0 && (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-xl">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-800 dark:text-green-200 font-medium">Jira Issues Created!</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Creation Results</label>
                <div className="max-h-60 overflow-y-auto space-y-2">
                  {creationResults.map((result: any, index: number) => (
                    <div key={index} className={`p-3 border rounded-md ${result.success ? 'border-green-200 bg-green-50 dark:bg-green-900/20' : 'border-red-200 bg-red-50 dark:bg-red-900/20'}`}>
                      <div className="flex items-center space-x-2">
                        {result.success ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span className={`text-sm font-medium ${result.success ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}`}>
                          {result.success ? 'Success' : 'Failed'}
                        </span>
                      </div>
                      {result.success && result.url && (
                        <a 
                          href={result.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-saramsa-brand hover:underline mt-1 block"
                        >
                          View Issue
                        </a>
                      )}
                      {!result.success && result.error && (
                        <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                          Error: {result.error}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <Button 
                onClick={() => setCurrentStep('project-creation')}
                variant="outline"
                className="w-full"
              >
                Create Another Project
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
