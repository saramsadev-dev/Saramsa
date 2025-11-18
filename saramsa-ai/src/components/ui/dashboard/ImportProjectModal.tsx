'use client';

import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import { 
  fetchExternalProjects,
  clearExternalProjects 
} from '@/store/features/integrations/integrationsSlice';
import { importProjectFromExternal } from '@/store/features/projects/projectsSlice';
import { motion } from 'framer-motion';
import { 
  X, 
  Search, 
  Cloud, 
  ExternalLink, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  ArrowRight,
  Calendar,
  Users
} from 'lucide-react';

interface ImportProjectModalProps {
  provider: 'azure' | 'jira';
  onClose: () => void;
  onSuccess: () => void;
}

export function ImportProjectModal({ provider, onClose, onSuccess }: ImportProjectModalProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { externalProjects, fetchingProjects, error, accounts } = useSelector((state: RootState) => state.integrations);
  const { projects, importing, importError } = useSelector((state: RootState) => state.projects);
  
  const fetchingProjectsForProvider = fetchingProjects[provider] || false;
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [selectedAccount, setSelectedAccount] = useState<string>('');

  const providerAccounts = accounts.filter(acc => acc.provider === provider && acc.status === 'active');

  // Helper function to check if an external project is already linked
  const getLinkedProject = (externalProjectId: string) => {
    return projects.find(p => 
      p.externalLinks?.some(link => 
        link.provider === provider && 
        link.externalId === externalProjectId
      )
    );
  };

  useEffect(() => {
    if (providerAccounts.length > 0) {
      setSelectedAccount(providerAccounts[0].id);
    }
  }, [providerAccounts]);

  useEffect(() => {
    if (selectedAccount) {
      dispatch(clearExternalProjects());
      dispatch(fetchExternalProjects({ provider, accountId: selectedAccount }));
    }
  }, [dispatch, provider, selectedAccount]);

  const filteredProjects = externalProjects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleImport = async () => {
    if (!selectedProject || !selectedAccount) return;

    try {
      await dispatch(importProjectFromExternal({
        provider,
        integrationAccountId: selectedAccount,
        externalProject: selectedProject,
      })).unwrap();
      
      onSuccess();
    } catch (err) {
      console.error('Failed to import project:', err);
    }
  };

  const getProviderConfig = () => {
    switch (provider) {
      case 'azure':
        return {
          name: 'Azure DevOps',
          color: 'bg-gradient-to-r from-[#E603EB] to-[#8B5FBF]',
          icon: <Cloud className="w-5 h-5 text-white" />,
          baseUrl: 'https://dev.azure.com'
        };
      case 'jira':
        return {
          name: 'Jira',
          color: 'bg-gradient-to-r from-[#E603EB] to-[#8B5FBF]',
          icon: <span className="text-white font-bold">J</span>,
          baseUrl: 'https://atlassian.net'
        };
    }
  };

  const config = getProviderConfig();

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 ${config.color} rounded-lg flex items-center justify-center`}>
              {config.icon}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Import from {config.name}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Select a project to import into Saramsa AI
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Account Selection */}
        {providerAccounts.length > 1 && (
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Account
            </label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            >
              {providerAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.displayName}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Search */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search projects..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-[#E603EB] focus:border-transparent"
            />
          </div>
        </div>

        {/* Error Display */}
        {(error || importError) && (
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-red-700 dark:text-red-300">{error || importError}</span>
              </div>
            </div>
          </div>
        )}

        {/* Info Banner */}
        {!fetchingProjectsForProvider && filteredProjects.length > 0 && (
          <div className="px-6 pb-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-xs text-blue-700 dark:text-blue-300">
                {filteredProjects.filter(p => getLinkedProject(p.id)).length > 0 ? (
                  <>
                    <strong>{filteredProjects.filter(p => getLinkedProject(p.id)).length}</strong> project(s) already linked. 
                    They cannot be imported again.
                  </>
                ) : (
                  'All projects are available to import.'
                )}
              </p>
            </div>
          </div>
        )}

        {/* Projects List */}
        <div className="flex-1 overflow-y-auto max-h-96">
          {fetchingProjectsForProvider ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-600 dark:text-gray-400">Loading projects...</span>
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {searchTerm ? 'No projects found' : 'No projects available'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {searchTerm 
                  ? 'Try adjusting your search terms'
                  : `No projects found in your ${config.name} account`
                }
              </p>
            </div>
          ) : (
            <div className="p-6 space-y-3">
              {filteredProjects.map((project) => {
                const linkedProject = getLinkedProject(project.id);
                const isAlreadyLinked = !!linkedProject;
                
                return (
                  <motion.div
                    key={project.id}
                    whileHover={{ scale: isAlreadyLinked ? 1 : 1.01 }}
                    className={`p-4 border-2 rounded-lg transition-all ${
                      isAlreadyLinked
                        ? 'opacity-60 cursor-not-allowed border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800'
                        : selectedProject?.id === project.id
                        ? 'border-[#E603EB] bg-[#E603EB]/10 dark:bg-[#E603EB]/20 cursor-pointer'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 cursor-pointer'
                    }`}
                    onClick={() => !isAlreadyLinked && setSelectedProject(project)}
                  >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {project.name}
                        </h4>
                        {project.key && (
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded">
                            {project.key}
                          </span>
                        )}
                      </div>
                      {project.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                          {project.description}
                        </p>
                      )}
                      
                      {/* Already linked warning */}
                      {isAlreadyLinked && (
                        <div className="mt-2 p-2 bg-orange-100 dark:bg-orange-900/30 rounded">
                          <p className="text-xs text-orange-700 dark:text-orange-400">
                            Already linked to "{linkedProject.name}"
                          </p>
                        </div>
                      )}
                      
                      {/* Project metadata */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                        {project.templateName && (
                          <div className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {project.templateName}
                          </div>
                        )}
                        {project.url && (
                          <a
                            href={project.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="flex items-center gap-1 hover:text-[#E603EB]"
                          >
                            <ExternalLink className="w-3 h-3" />
                            View in {config.name}
                          </a>
                        )}
                      </div>
                    </div>
                    
                    {selectedProject?.id === project.id && !isAlreadyLinked && (
                      <CheckCircle className="w-5 h-5 text-[#E603EB]" />
                    )}
                    {isAlreadyLinked && (
                      <span className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded">
                        Linked
                      </span>
                    )}
                  </div>
                </motion.div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {selectedProject ? (
                getLinkedProject(selectedProject.id) ? (
                  <span className="text-orange-600 dark:text-orange-400">
                    This project is already linked to "{getLinkedProject(selectedProject.id)?.name}"
                  </span>
                ) : (
                  <span>Selected: <strong>{selectedProject.name}</strong></span>
                )
              ) : (
                'Select a project to import'
              )}
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={!selectedProject || importing || (selectedProject && !!getLinkedProject(selectedProject.id))}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:shadow-lg disabled:opacity-50 text-white rounded-lg transition-all disabled:cursor-not-allowed"
              >
                {importing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    Import Project
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}
