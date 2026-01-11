'use client';

import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "@/store/store";
import { fetchIntegrationAccounts } from "@/store/features/integrations/integrationsSlice";
import { fetchProjects } from "@/store/features/projects/projectsSlice";
import { motion } from 'framer-motion';
import { JiraFormPanel } from './JiraFormPanel';
import { apiRequest } from '@/lib/apiRequest';

interface JiraConfigScreenProps {
  onContinue: () => void;
  onBack: () => void;
}

export function JiraConfigScreen({ onContinue, onBack }: JiraConfigScreenProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { accounts } = useSelector((state: RootState) => state.integrations);
  const { projects: saramsaProjects } = useSelector((state: RootState) => state.projects);
  
  const [config, setConfig] = useState({
    email: '',
    apiToken: '',
    domain: '',
    projectKey: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [isExistingIntegration, setIsExistingIntegration] = useState(false);

  // Build a map of external project IDs to Saramsa projects
  const linkedProjects: { [key: string]: { id: string; name: string } } = {};
  saramsaProjects?.forEach(project => {
    project.externalLinks?.forEach(link => {
      if (link.provider === 'jira') {
        linkedProjects[link.externalId] = { id: project.id, name: project.name };
      }
    });
  });

  useEffect(() => {
    // Check if Jira integration already exists and fetch existing projects
    dispatch(fetchIntegrationAccounts());
    dispatch(fetchProjects());
  }, [dispatch]);

  useEffect(() => {
    const jiraAccount = accounts.find(acc => acc.provider === 'jira');
    if (jiraAccount) {
      setIsExistingIntegration(true);
      setConfig(prev => ({
        ...prev,
        domain: jiraAccount.metadata.domain || '',
        email: jiraAccount.metadata.email || ''
      }));
      // Automatically fetch projects for existing integration
      handleValidateConfig();
    }
  }, [accounts]);

  const handleConfigChange = (field: string, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setValidationStatus('idle');
    setErrorMessage('');
  };

  const handleValidateConfig = async () => {
    // For existing integration, we don't need API token from user
    if (!isExistingIntegration && (!config.email || !config.apiToken || !config.domain)) {
      setErrorMessage('Please fill in all required fields');
      setValidationStatus('error');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setValidationStatus('loading');

    try {
      let projectsResponse;
      
      if (isExistingIntegration) {
        // For existing integration, use the external projects endpoint
        const jiraAccount = accounts.find(acc => acc.provider === 'jira');
        if (!jiraAccount) {
          throw new Error('Jira integration not found');
        }
        
        projectsResponse = await apiRequest('get', `/integrations/external/projects/?provider=jira&accountId=${jiraAccount.id}`, undefined, true);
      } else {
        // For new integration, use the direct API endpoint with user credentials
        projectsResponse = await apiRequest('get', `/integrations/jira/projects/?domain=${encodeURIComponent(config.domain)}&email=${encodeURIComponent(config.email)}&api_token=${encodeURIComponent(config.apiToken)}`);
      }
      
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.data.projects || []);
        setValidationStatus('success');
        setErrorMessage('');
      } else {
        setErrorMessage(projectsResponse.data.error || 'Failed to fetch projects');
        setValidationStatus('error');
      }
    } catch (error: any) {
      console.error('Jira config validation error:', error);
      if (error.response?.data?.error) {
        setErrorMessage(error.response.data.error);
      } else {
        setErrorMessage('Failed to connect to Jira. Please check your credentials.');
      }
      setValidationStatus('error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProjectSelect = (projectId: string) => {
    setSelectedProject(projectId);
    const selectedProjectData = projects.find(p => p.id === projectId);
    if (selectedProjectData) {
      setConfig(prev => ({ ...prev, projectKey: selectedProjectData.key }));
    }
  };

  const handleContinue = async () => {
    if (!selectedProject) {
      setErrorMessage('Please select a project to continue');
      return;
    }

    const selectedProjectData = projects.find(p => p.id === selectedProject);
    if (selectedProjectData) {
      // Store the configuration
      localStorage.setItem('jira_email', config.email);
      localStorage.setItem('jira_api_token', config.apiToken);
      localStorage.setItem('jira_domain', config.domain);
      localStorage.setItem('jira_project_key', selectedProjectData.key);
      localStorage.setItem('jira_project_id', selectedProject);
      localStorage.setItem('jira_project_name', selectedProjectData.name);
    }

    // Persist project to backend using new integrations API
    try {
      let integrationAccountId;
      
      if (isExistingIntegration) {
        // Use existing integration account
        const jiraAccount = accounts.find(acc => acc.provider === 'jira');
        if (!jiraAccount) {
          throw new Error('Jira integration not found');
        }
        integrationAccountId = jiraAccount.id;
      } else {
        // Create new integration account
        const integrationResponse = await apiRequest('post', '/integrations/jira/', {
          domain: config.domain,
          email: config.email,
          api_token: config.apiToken
        }, true);

        if (!integrationResponse.data.success) {
          throw new Error(integrationResponse.data.error || 'Failed to create Jira integration');
        }
        integrationAccountId = integrationResponse.data.account.id;
      }

      // CHECK IF SARAMSA PROJECT ALREADY EXISTS FOR THIS JIRA PROJECT
      // selectedProject is the Jira project ID (external ID)
      try {
        const checkResponse = await apiRequest('get', 
          `/integrations/external/projects/check/?provider=jira&externalId=${selectedProject}`, 
          undefined, 
          true
        );
        
        if (checkResponse.data.data.exists && checkResponse.data.data.project) {
          // A Saramsa project already exists for this Jira project - use it!
          const existingSaramsaProject = checkResponse.data.data.project;
          console.log('Saramsa project already exists for this Jira project, using existing project:', existingSaramsaProject.id);
          
          localStorage.setItem('project_id', existingSaramsaProject.id);
          localStorage.setItem('selected_project_name', existingSaramsaProject.name || selectedProjectData?.name || '');
          
          onContinue();
          return; // Don't try to create, just use the existing one
        }
      } catch (checkError) {
        // If check fails, log but proceed with creation attempt
        console.warn('Failed to check existing project, proceeding with creation:', checkError);
      }

      // No existing Saramsa project found, create a new one and link it to the Jira project
      const res = await apiRequest('post', '/integrations/projects/create/', {
        project_name: selectedProjectData?.name || 'Jira Project',
        description: `Imported from Jira: ${config.domain}`,
        platform: 'jira',
        external_project_id: selectedProject, // This is the Jira project ID
        external_url: `https://${config.domain}/browse/${selectedProjectData?.key}`,
        integration_account_id: integrationAccountId,
        jira_project_key: selectedProjectData?.key
      }, true);
      
      if (!res.data.success) {
        throw new Error(res.data.error || 'Failed to create project');
      }
      
      const project = res.data.data.project;
      localStorage.setItem('project_id', project.id);
      localStorage.setItem('selected_project_name', selectedProjectData?.name || '');
      
      console.log('New Saramsa project created and linked to Jira project');
      
    } catch (e: any) {
      console.error('persist project error', e);
      
      // Handle 409 conflict error as a fallback (in case check didn't work)
      if (e.response?.status === 409) {
        try {
          const checkResponse = await apiRequest('get', 
            `/integrations/external/projects/check/?provider=jira&externalId=${selectedProject}`, 
            undefined, 
            true
          );
          if (checkResponse.data.data.exists && checkResponse.data.data.project) {
            const existingProject = checkResponse.data.data.project;
            localStorage.setItem('project_id', existingProject.id);
            localStorage.setItem('selected_project_name', existingProject.name || selectedProjectData?.name || '');
            onContinue();
            return;
          }
        } catch (checkError) {
          console.error('Failed to get existing project after 409 error:', checkError);
        }
      }
      
      setErrorMessage(e instanceof Error ? e.message : 'Failed to create project');
      setValidationStatus('error');
      // Don't navigate to dashboard on error
      return;
    }

    onContinue();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="flex flex-col lg:flex-row min-h-screen">
        <motion.div 
          className="w-full flex items-start justify-center p-6 lg:p-8 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm overflow-y-auto"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <JiraFormPanel
            config={config}
            onConfigChange={handleConfigChange}
            onValidateConfiguration={handleValidateConfig}
            isLoading={isLoading}
            error={errorMessage}
            projects={projects}
            selectedProject={selectedProject}
            onProjectSelect={handleProjectSelect}
            onContinue={handleContinue}
            onBack={onBack}
            validationStatus={validationStatus}
            isExistingIntegration={isExistingIntegration}
            linkedProjects={linkedProjects}
          />
        </motion.div>
      </div>
    </div>
  );
};
