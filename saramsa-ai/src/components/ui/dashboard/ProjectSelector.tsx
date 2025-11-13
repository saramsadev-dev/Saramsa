'use client';

import { ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface ProjectSelectorProps {
  azureProjects: Array<{ id: string; name: string }>;
  selectedAzureProjectId: string;
  needsAzureConfig: boolean;
  isFetchingAzure: boolean;
  fetchAzureError: string | null;
  onProjectChange: (azureId: string, name: string) => Promise<void>;
  onFetchAzureProjects: () => Promise<void>;
}

export function ProjectSelector({
  azureProjects,
  selectedAzureProjectId,
  needsAzureConfig,
  isFetchingAzure,
  fetchAzureError,
  onProjectChange,
  onFetchAzureProjects
}: ProjectSelectorProps) {
  const router = useRouter();

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Select Project</span>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </div>
      
      {/* Azure Config Missing */}
      {needsAzureConfig && (
        <div className="flex items-center gap-3 text-xs text-amber-600 dark:text-amber-400">
          <span>Azure DevOps is not configured. Please configure it first.</span>
          <button
            onClick={() => router.push('/config')}
            className="px-3 py-1 border border-amber-300 dark:border-amber-700 rounded text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
          >
            Go to Config
          </button>
        </div>
      )}
      
      {/* No Projects Found */}
      {!needsAzureConfig && azureProjects.length === 0 && (
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>No Azure DevOps projects found.</span>
          <button
            onClick={onFetchAzureProjects}
            disabled={isFetchingAzure}
            className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors disabled:opacity-50"
          >
            {isFetchingAzure ? 'Fetching...' : 'Retry'}
          </button>
          {fetchAzureError && (
            <span className="text-red-500 text-xs">{fetchAzureError}</span>
          )}
        </div>
      )}
      
      {/* Project Dropdown */}
      <select 
        value={selectedAzureProjectId} 
        onChange={async (e) => {
          const azureId = e.target.value;
          const name = azureProjects.find(p => p.id === azureId)?.name || '';
          await onProjectChange(azureId, name);
        }}
        className="w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-saramsa-brand focus:border-transparent transition-all"
      >
        {azureProjects.length === 0 ? (
          <option value="" disabled>No Azure DevOps projects found</option>
        ) : (
          azureProjects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))
        )}
      </select>
    </div>
  );
}
