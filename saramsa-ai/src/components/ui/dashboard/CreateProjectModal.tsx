'use client';

import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import { fetchExternalProjects, clearExternalProjects } from '@/store/features/integrations/integrationsSlice';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FolderPlus, Cloud, Loader2, Search, ExternalLink, Link2 } from 'lucide-react';
import type { IntegrationAccount } from '@/store/features/integrations/integrationsSlice';

interface CreateProjectModalProps {
  onClose: () => void;
  onCreate: (name: string, description?: string, externalLink?: { provider: 'azure' | 'jira', accountId: string, projectId: string, projectName: string, projectUrl?: string, projectKey?: string }) => void;
  onImport: (provider: 'azure' | 'jira') => void;
  integrations: IntegrationAccount[];
  loading?: boolean;
}

export function CreateProjectModal({ onClose, onCreate, onImport, integrations, loading = false }: CreateProjectModalProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { externalProjects, fetchingProjects } = useSelector((state: RootState) => state.integrations);
  const { projects } = useSelector((state: RootState) => state.projects);
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<'none' | 'azure' | 'jira'>('none');
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [selectedExternalProject, setSelectedExternalProject] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const maxDescriptionLength = 100;

  const azureIntegrations = integrations.filter(acc => acc.provider === 'azure' && acc.status === 'active');
  const jiraIntegrations = integrations.filter(acc => acc.provider === 'jira' && acc.status === 'active');

  // Helper function to check if an external project is already linked
  const getLinkedProject = (externalProjectId: string) => {
    return projects.find(p => 
      p.externalLinks?.some(link => 
        link.provider === selectedProvider && 
        link.externalId === externalProjectId
      )
    );
  };

  // Fetch external projects when provider is selected
  useEffect(() => {
    if (selectedProvider !== 'none' && selectedAccount) {
      dispatch(clearExternalProjects());
      dispatch(fetchExternalProjects({ provider: selectedProvider, accountId: selectedAccount }));
    }
  }, [dispatch, selectedProvider, selectedAccount]);

  // Auto-select first account when provider changes
  useEffect(() => {
    if (selectedProvider === 'azure' && azureIntegrations.length > 0) {
      setSelectedAccount(azureIntegrations[0].id);
    } else if (selectedProvider === 'jira' && jiraIntegrations.length > 0) {
      setSelectedAccount(jiraIntegrations[0].id);
    } else if (selectedProvider === 'none') {
      setSelectedAccount('');
      setSelectedExternalProject(null);
    }
  }, [selectedProvider, azureIntegrations, jiraIntegrations]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      let externalLink = undefined;
      if (selectedProvider !== 'none' && selectedExternalProject && selectedAccount) {
        externalLink = {
          provider: selectedProvider,
          accountId: selectedAccount,
          projectId: selectedExternalProject.id,
          projectName: selectedExternalProject.name,
          projectUrl: selectedExternalProject.url,
          projectKey: selectedExternalProject.key
        };
      }
      onCreate(name.trim(), description.trim() || undefined, externalLink);
    }
  };

  const filteredProjects = externalProjects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (project.description && project.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const isFetchingProjects = selectedProvider !== 'none' && fetchingProjects[selectedProvider];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Create New Project
            </h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              disabled={loading}
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label htmlFor="project-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project Name *
              </label>
              <input
                id="project-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#E603EB] focus:border-transparent"
                placeholder="Enter project name"
                required
                disabled={loading}
                autoFocus
              />
            </div>

            <div>
              <label htmlFor="project-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                id="project-description"
                value={description}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value.length <= maxDescriptionLength) {
                    setDescription(value);
                  }
                }}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#E603EB] focus:border-transparent resize-none"
                placeholder="Enter project description (optional)"
                disabled={loading}
              />
              <div className="flex justify-end items-center mt-1">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {description.length}/{maxDescriptionLength}
                </p>
              </div>
            </div>

            {/* Link to External Project */}
            {(azureIntegrations.length > 0 || jiraIntegrations.length > 0) && (
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Link to External Project (Optional)
                </label>
                
                {/* Provider Selection */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <button
                    type="button"
                    onClick={() => setSelectedProvider('none')}
                    className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                      selectedProvider === 'none'
                        ? 'border-[#E603EB] bg-[#E603EB]/10 text-[#E603EB] dark:text-[#E603EB]'
                        : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                    disabled={loading}
                  >
                    None
                  </button>
                  {azureIntegrations.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setSelectedProvider('azure')}
                      className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                        selectedProvider === 'azure'
                          ? 'border-[#E603EB] bg-[#E603EB]/10 text-[#E603EB] dark:text-[#E603EB]'
                          : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                      disabled={loading}
                    >
                      Azure
                    </button>
                  )}
                  {jiraIntegrations.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setSelectedProvider('jira')}
                      className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                        selectedProvider === 'jira'
                          ? 'border-[#E603EB] bg-[#E603EB]/10 text-[#E603EB] dark:text-[#E603EB]'
                          : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                      disabled={loading}
                    >
                      Jira
                    </button>
                  )}
                </div>

                {/* Account Selection (if multiple accounts) */}
                {selectedProvider !== 'none' && (
                  <>
                    {((selectedProvider === 'azure' && azureIntegrations.length > 1) ||
                      (selectedProvider === 'jira' && jiraIntegrations.length > 1)) && (
                      <div className="mb-3">
                        <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                          Select Account
                        </label>
                        <select
                          value={selectedAccount}
                          onChange={(e) => setSelectedAccount(e.target.value)}
                          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                          disabled={loading}
                        >
                          {(selectedProvider === 'azure' ? azureIntegrations : jiraIntegrations).map((account) => (
                            <option key={account.id} value={account.id}>
                              {account.displayName}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* Search Projects */}
                    <div className="mb-3">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="text"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          placeholder="Search projects..."
                          className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500"
                          disabled={loading}
                        />
                      </div>
                    </div>

                    {/* Info Banner */}
                    {!isFetchingProjects && filteredProjects.length > 0 && (
                      <div className="mb-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <p className="text-xs text-blue-700 dark:text-blue-300">
                          {filteredProjects.filter(p => getLinkedProject(p.id)).length > 0 ? (
                            <>
                              <strong>{filteredProjects.filter(p => getLinkedProject(p.id)).length}</strong> project(s) already linked. 
                              They are disabled and show which Saramsa project they're connected to.
                            </>
                          ) : (
                            'All projects are available to link.'
                          )}
                        </p>
                      </div>
                    )}

                    {/* Projects List */}
                    <div className="max-h-48 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg">
                      {isFetchingProjects ? (
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                          <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Loading projects...</span>
                        </div>
                      ) : filteredProjects.length === 0 ? (
                        <div className="text-center py-8">
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {searchTerm ? 'No projects found' : 'No projects available'}
                          </p>
                        </div>
                      ) : (
                        <div className="divide-y divide-gray-200 dark:divide-gray-700">
                          {filteredProjects.map((project) => {
                            const linkedProject = getLinkedProject(project.id);
                            const isAlreadyLinked = !!linkedProject;
                            
                            return (
                              <button
                                key={project.id}
                                type="button"
                                onClick={() => !isAlreadyLinked && setSelectedExternalProject(project)}
                                className={`w-full px-3 py-2 text-left transition-colors ${
                                  isAlreadyLinked
                                    ? 'opacity-60 cursor-not-allowed bg-gray-100 dark:bg-gray-800'
                                    : selectedExternalProject?.id === project.id
                                    ? 'bg-[#E603EB]/10 dark:bg-[#E603EB]/20'
                                    : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                                disabled={loading || isAlreadyLinked}
                              >
                                <div className="flex items-center justify-between gap-2">
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                      {project.name}
                                    </p>
                                    {project.key && (
                                      <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {project.key}
                                      </p>
                                    )}
                                    {isAlreadyLinked && (
                                      <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                                        Already linked to "{linkedProject.name}"
                                      </p>
                                    )}
                                  </div>
                                  {selectedExternalProject?.id === project.id && !isAlreadyLinked && (
                                    <div className="w-2 h-2 bg-[#E603EB] rounded-full ml-2 flex-shrink-0"></div>
                                  )}
                                  {isAlreadyLinked && (
                                    <span className="flex items-center gap-1 text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded flex-shrink-0">
                                      <Link2 className="w-3 h-3" />
                                      Linked
                                    </span>
                                  )}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {selectedExternalProject && (
                      <div className="mt-2 p-2 bg-[#E603EB]/10 dark:bg-[#E603EB]/20 rounded-lg">
                        <p className="text-xs text-gray-700 dark:text-gray-300">
                          <strong>Selected:</strong> {selectedExternalProject.name}
                        </p>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white rounded-lg hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading || !name.trim()}
              >
                <FolderPlus className="w-4 h-4" />
                {loading ? 'Creating...' : 'Create Project'}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
