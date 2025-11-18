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
  onCreateProject: () => void;
  onImportProject: (provider: 'azure' | 'jira') => void;
  integrations: IntegrationAccount[];
}

export function NewProjectDropdown({ 
  onClose, 
  onCreateProject, 
  onImportProject, 
  integrations 
}: NewProjectDropdownProps) {
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

  const handleImportClick = (provider: 'azure' | 'jira') => {
    onImportProject(provider);
  };

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
          onClick={onCreateProject}
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
          <div className="w-8 h-8 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center">
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
          <div className="w-8 h-8 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center">
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
