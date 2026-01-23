'use client';

import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "@/store/store";
import { fetchIntegrationAccounts } from "@/store/features/integrations/integrationsSlice";
import { fetchProjects, createProject } from "@/store/features/projects/projectsSlice";
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
  const [isCreatingProject, setIsCreatingProject] = useState(false);
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
    // Integration accounts are now fetched at the parent level
    // Just fetch projects here
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
      fetchProjectsForExistingIntegration(jiraAccount);
    }
  }, [accounts]);

  const fetchProjectsForExistingIntegration = async (jiraAccount: any) => {
    setIsLoading(true);
    setErrorMessage('');
    setValidationStatus('loading');

    try {
      const projectsResponse = await apiRequest('get', `/integrations/external/projects/?provider=jira&accountId=${jiraAccount.id}`, undefined, true);
      
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

  const handleConfigChange = (field: string, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
    setValidationStatus('idle');
    setErrorMessage('');
  };

  const handleValidateConfig = async () => {
    // Only for new integrations - existing integrations are handled separately
    if (!config.email || !config.apiToken || !config.domain) {
      setErrorMessage('Please fill in all required fields');
      setValidationStatus('error');
      return;
    }

    setIsLoading(true);
    setErrorMessage('');
    setValidationStatus('loading');

    try {
      // For new integration, use the direct API endpoint with user credentials
      const projectsResponse = await apiRequest('get', `/integrations/jira/projects/?domain=${encodeURIComponent(config.domain)}&email=${encodeURIComponent(config.email)}&api_token=${encodeURIComponent(config.apiToken)}`);
      
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

    setIsCreatingProject(true);
    setErrorMessage(""); // Clear any previous errors

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
        integrationAccountId = integrationResponse.data.data.account.id;
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
      const projectData = {
        name: selectedProjectData?.name || 'Jira Project',
        description: `Imported from Jira: ${config.domain}`,
        externalLinks: [{
          provider: 'jira',
          integrationAccountId: integrationAccountId,
          externalId: selectedProject, // This is the Jira project ID
          externalKey: selectedProjectData?.key,
          url: `https://${config.domain}/browse/${selectedProjectData?.key}`,
          status: 'ok',
          lastSyncedAt: null,
          syncMetadata: {}
        }]
      };

      const result = await dispatch(createProject(projectData)).unwrap();
      
      // Store project info in localStorage for compatibility
      localStorage.setItem('project_id', result.id);
      localStorage.setItem('selected_project_name', selectedProjectData?.name || '');
      
      console.log('New Saramsa project created and linked to Jira project:', result.id);
      
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
    } finally {
      setIsCreatingProject(false);
    }

    onContinue();
  };

  return (
    <div className="min-h-screen bg-background py-12 lg:py-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="space-y-4 text-center lg:text-left"
        >
          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            Jira Integration
          </p>
          <h1 className="text-3xl sm:text-4xl font-semibold text-foreground">
            Connect your Jira workspace and bring projects into Saramsa.ai
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl lg:max-w-3xl mx-auto lg:mx-0">
            Link your Jira account once, then choose the project you would like Saramsa.ai to use when generating issues from customer feedback. We handle the secure connection and remember your configuration for future sessions.
          </p>
        </motion.div>

        <div className="grid gap-10 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)] items-start">
          <motion.aside
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="rounded-3xl bg-gradient-to-br from-[#E603EB]/25 via-[#8B5FBF]/15 to-transparent p-6 sm:p-8 shadow-lg ring-1 ring-[#E603EB]/10 backdrop-blur-sm"
          >
            <div className="space-y-6">
              <div className="space-y-2">
                <h2 className="text-xl font-semibold text-white drop-shadow">
                  Why link Jira?
                </h2>
                <p className="text-sm text-white/80">
                  Create issues directly from feedback, synchronize updates, and keep teams aligned without switching tools.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  {
                    title: "Secure authentication",
                    description: "API tokens stay encrypted in storage and never leave your browser without consent."
                  },
                  {
                    title: "Synced project context",
                    description: "Choose the project where Saramsa.ai should publish triaged feedback as issues."
                  },
                  {
                    title: "Reusable integration",
                    description: "We detect existing connections and let you manage multiple Jira accounts with ease."
                  }
                ].map((item) => (
                  <div key={item.title} className="rounded-2xl border border-white/20 bg-white/10 p-4">
                    <p className="text-sm font-medium text-white/90">{item.title}</p>
                    <p className="mt-1 text-xs text-white/70">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>
              <div className="rounded-2xl border border-white/20 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-white/70">
                  Need help?
                </p>
                <p className="mt-2 text-sm text-white/85">
                  Reach out to your Saramsa.ai admin to enable Jira integrations for your workspace.
                </p>
              </div>
            </div>
          </motion.aside>

          <motion.section
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className="w-full"
          >
            <JiraFormPanel
              config={config}
              onConfigChange={handleConfigChange}
              onValidateConfiguration={handleValidateConfig}
              isLoading={isLoading}
              isCreatingProject={isCreatingProject}
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
          </motion.section>
        </div>
      </div>
    </div>
  );
};
