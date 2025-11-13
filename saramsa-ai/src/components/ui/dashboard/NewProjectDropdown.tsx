'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FolderPlus, 
  Download, 
  Cloud, 
  Settings,
  AlertCircle,
  ExternalLink
} from 'lucide-react';
import type { IntegrationAccount } from '@/store/features/integrations/integrationsSlice';

interface NewProjectDropdownProps {
  onClose: () => void;
  onCreateProject: (name: string, description?: string) => void;
  onImportProject: (provider: 'azure' | 'jira') => void;
  integrations: IntegrationAccount[];
}

export function NewProjectDropdown({ 
  onClose, 
  onCreateProject, 
  onImportProject, 
  integrations 
}: NewProjectDropdownProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const azureIntegrations = integrations.filter(acc => acc.provider === 'azure' && acc.status === 'active');
  const jiraIntegrations = integrations.filter(acc => acc.provider === 'jira' && acc.status === 'active');

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const handleCreateProject = () => {
    if (projectName.trim()) {
      onCreateProject(projectName.trim(), projectDescription.trim() || undefined);
      onClose();
    }
  };

  const handleImportClick = (provider: 'azure' | 'jira') => {
    onImportProject(provider);
  };

  if (showCreateForm) {
    return (
      <motion.div
        ref={dropdownRef}
        initial={{ opacity: 0, scale: 0.95, y: -10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: -10 }}
        className="absolute top-12 right-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 w-80 p-4"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <FolderPlus className="w-5 h-5 text-[#E603EB]" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Create New Project</h3>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="e.g., Mobile App Feedback"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-[#E603EB] focus:border-transparent"
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description (optional)
            </label>
            <textarea
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="Brief description of your project..."
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-[#E603EB] focus:border-transparent resize-none"
            />
          </div>
          
          <div className="flex gap-2 pt-2">
            <button
              onClick={() => setShowCreateForm(false)}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm"
            >
              Back
            </button>
            <button
              onClick={handleCreateProject}
              disabled={!projectName.trim()}
              className="flex-1 px-3 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white rounded-lg hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              Create
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      ref={dropdownRef}
      initial={{ opacity: 0, scale: 0.95, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -10 }}
      className="absolute top-12 right-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 w-72"
    >
      <div className="p-2">
        {/* Create Project */}
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-3 w-full px-3 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          <div className="w-8 h-8 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center">
            <FolderPlus className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">Create Project</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">Start with a blank project</p>
          </div>
        </button>

        <div className="my-2 border-t border-gray-200 dark:border-gray-700"></div>

        {/* Import from Azure DevOps */}
        <button
          onClick={() => handleImportClick('azure')}
          disabled={azureIntegrations.length === 0}
          className="flex items-center gap-3 w-full px-3 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <Cloud className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <p className="font-medium text-gray-900 dark:text-white">Import from Azure DevOps</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {azureIntegrations.length > 0 
                ? `${azureIntegrations.length} account${azureIntegrations.length !== 1 ? 's' : ''} connected`
                : 'No accounts connected'
              }
            </p>
          </div>
          {azureIntegrations.length === 0 && (
            <AlertCircle className="w-4 h-4 text-yellow-500" />
          )}
        </button>

        {/* Import from Jira */}
        <button
          onClick={() => handleImportClick('jira')}
          disabled={jiraIntegrations.length === 0}
          className="flex items-center gap-3 w-full px-3 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-sm font-bold">J</span>
          </div>
          <div className="flex-1">
            <p className="font-medium text-gray-900 dark:text-white">Import from Jira</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {jiraIntegrations.length > 0 
                ? `${jiraIntegrations.length} account${jiraIntegrations.length !== 1 ? 's' : ''} connected`
                : 'No accounts connected'
              }
            </p>
          </div>
          {jiraIntegrations.length === 0 && (
            <AlertCircle className="w-4 h-4 text-yellow-500" />
          )}
        </button>

        {/* No integrations message */}
        {integrations.length === 0 && (
          <>
            <div className="my-2 border-t border-gray-200 dark:border-gray-700"></div>
            <div className="px-3 py-3">
              <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    Connect your DevOps platforms
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    Go to Settings → Integrations to connect Azure DevOps or Jira
                  </p>
                  <a
                    href="/settings"
                    className="inline-flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 hover:underline mt-2"
                  >
                    Open Settings
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}
