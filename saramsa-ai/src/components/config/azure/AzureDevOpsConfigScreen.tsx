'use client';

import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from "@/store/store";
import { fetchIntegrationAccounts } from "@/store/features/integrations/integrationsSlice";

type AzureDevOpsProject = {
  id: string;
  name: string;
  description?: string;
  url?: string;
  templateName?: string;
};
import { motion } from 'framer-motion';
import { DevOpsFormPanel } from './DevOpsFormPanel';
import { apiRequest } from '@/lib/apiRequest';

interface AzureDevOpsConfigScreenProps {
  onContinue: () => void;
  onBack: () => void;
}

export function AzureDevOpsConfigScreen({ onContinue, onBack }: AzureDevOpsConfigScreenProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { accounts } = useSelector((state: RootState) => state.integrations);
  
  const [orgName, setOrgName] = useState("");
  const [pat, setPat] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [projects, setProjects] = useState<AzureDevOpsProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [isExistingIntegration, setIsExistingIntegration] = useState(false);

  useEffect(() => {
    // Check if Azure integration already exists
    dispatch(fetchIntegrationAccounts());
  }, [dispatch]);

  useEffect(() => {
    const azureAccount = accounts.find(acc => acc.provider === 'azure');
    if (azureAccount) {
      setIsExistingIntegration(true);
      setOrgName(azureAccount.metadata.organization || '');
      handleFetchProjects();
    }
  }, [accounts]);

  const handleProjectSelect = (projectId: string) => {
    setSelectedProject(projectId);
  };

  const handleContinue = async () => {
    if (!selectedProject) {
      setError("Please select a project to continue");
      return;
    }

    const selectedProjectData = projects.find(p => p.id === selectedProject);
    if (selectedProjectData) {
      // Store the configuration in localStorage for later use
      localStorage.setItem('azure_pat_token', pat);
      localStorage.setItem('azure_organization', orgName);
      localStorage.setItem('azure_selected_project', selectedProject);
      localStorage.setItem('azure_project_name', selectedProjectData.name);
      if (selectedProjectData.templateName) {
        localStorage.setItem('azure_process_template', selectedProjectData.templateName);
      }
    }
    await handlePersistProject();
    onContinue();
  };

  const handleFetchProjects = async () => {
    if (!isExistingIntegration && (!orgName.trim() || !pat.trim())) {
      setError("Please provide both organization name and personal access token");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      let projectsResponse;
      
      if (isExistingIntegration) {
        // For existing integration, use the external projects endpoint
        const azureAccount = accounts.find(acc => acc.provider === 'azure');
        if (!azureAccount) {
          throw new Error('Azure integration not found');
        }
        
        projectsResponse = await apiRequest('get', `/integrations/external/projects/?provider=azure&accountId=${azureAccount.id}`, undefined, true);
      } else {
        // For new integration, use the direct API endpoint with user credentials
        projectsResponse = await apiRequest('get', `/integrations/azure/projects/?organization=${encodeURIComponent(orgName)}&pat_token=${encodeURIComponent(pat)}`);
      }
      
      if (projectsResponse.data.success) {
        setProjects(projectsResponse.data.projects);
        setError('');
      } else {
        setError(projectsResponse.data.error || 'Failed to fetch projects');
      }
    } catch (error: any) {
      console.error('Azure DevOps config error:', error);
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Failed to connect to Azure DevOps. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handlePersistProject = async () => {
    if (!selectedProject) return;
    const selectedProjectData = projects.find(p => p.id === selectedProject);
    try {
      let integrationAccountId;
      
      if (isExistingIntegration) {
        // Use existing integration account
        const azureAccount = accounts.find(acc => acc.provider === 'azure');
        if (!azureAccount) {
          throw new Error('Azure integration not found');
        }
        integrationAccountId = azureAccount.id;
      } else {
        // Create new integration account
        const integrationResponse = await apiRequest('post', '/integrations/azure/', {
          organization: orgName,
          pat_token: pat
        }, true);

        if (!integrationResponse.data.success) {
          throw new Error(integrationResponse.data.error || 'Failed to create Azure integration');
        }
        integrationAccountId = integrationResponse.data.account.id;
      }

      // Create the project
      const res = await apiRequest('post', '/integrations/projects/create/', {
        project_name: selectedProjectData?.name || 'Azure DevOps Project',
        description: `Imported from Azure DevOps: ${orgName}`,
        platform: 'azure_devops',
        external_project_id: selectedProject,
        external_url: `https://dev.azure.com/${orgName}/${selectedProjectData?.name}`,
        integration_account_id: integrationAccountId, // Link to the integration account
        jira_project_key: null // Not applicable for Azure
      }, true);
      
      if (!res.data.success) {
        throw new Error(res.data.error || 'Failed to create project');
      }
      
      const project = res.data.project;
      localStorage.setItem('project_id', project.id);
      localStorage.setItem('selected_project_name', selectedProjectData?.name || '');
      
      // Handle both new project creation and existing project navigation
      if (res.data.already_exists) {
        console.log('Project already exists, navigating to existing project');
      } else {
        console.log('Project created successfully, navigating to dashboard');
      }
      
    } catch (e) {
      console.error('persist project error', e);
      setError(e instanceof Error ? e.message : 'Failed to create project');
      // Don't navigate to dashboard on error
      return;
    }
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
            Azure DevOps Integration
          </p>
          <h1 className="text-3xl sm:text-4xl font-semibold text-foreground">
            Connect your Azure organization and bring projects into Saramsa.ai
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl lg:max-w-3xl mx-auto lg:mx-0">
            Link your Azure DevOps account once, then choose the project you would like Saramsa.ai to use when generating work items from customer feedback. We handle the secure connection and remember your configuration for future sessions.
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
                  Why link Azure DevOps?
                </h2>
                <p className="text-sm text-white/80">
                  Create work items directly from feedback, synchronize updates, and keep teams aligned without switching tools.
                </p>
              </div>
              <div className="space-y-4">
                {[
                  {
                    title: "Secure authentication",
                    description: "PAT tokens stay encrypted in storage and never leave your browser without consent."
                  },
                  {
                    title: "Synced project context",
                    description: "Choose the project where Saramsa.ai should publish triaged feedback as work items."
                  },
                  {
                    title: "Reusable integration",
                    description: "We detect existing connections and let you manage multiple Azure accounts with ease."
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
                  Reach out to your Saramsa.ai admin to enable Azure DevOps integrations for your workspace.
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
            <DevOpsFormPanel
              orgName={orgName}
              onOrgNameChange={setOrgName}
              pat={pat}
              onPatChange={setPat}
              onFetchProjects={handleFetchProjects}
              isLoading={isLoading}
              error={error}
              projects={projects}
              selectedProject={selectedProject}
              onProjectSelect={handleProjectSelect}
              onContinue={handleContinue}
              onBack={onBack}
              isExistingIntegration={isExistingIntegration}
            />
          </motion.section>
        </div>
      </div>
    </div>
  );
}; 