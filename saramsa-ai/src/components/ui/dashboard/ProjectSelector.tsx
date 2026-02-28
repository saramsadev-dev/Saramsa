'use client';

import { ChevronDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

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
        <span className="text-sm font-medium text-muted-foreground">Select Project</span>
        <ChevronDown className="w-4 h-4 text-muted-foreground" />
      </div>
      
      {/* Azure Config Missing */}
      {needsAzureConfig && (
        <div className="flex items-center gap-3 text-xs text-amber-600 dark:text-amber-400">
          <span>Azure DevOps is not configured. Please configure it first.</span>
          <Button
            onClick={() => router.push('/config')}
            variant="outline"
            size="sm"
            className="px-3 py-1 border-amber-300/60 text-amber-700 dark:text-amber-300 hover:bg-amber-50/70 dark:hover:bg-amber-900/20"
          >
            Go to Config
          </Button>
        </div>
      )}
      
      {/* No Projects Found */}
      {!needsAzureConfig && azureProjects.length === 0 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>No Azure DevOps projects found.</span>
          <Button
            onClick={onFetchAzureProjects}
            disabled={isFetchingAzure}
            variant="outline"
            size="sm"
            className="px-3 py-1"
          >
            {isFetchingAzure ? 'Fetching...' : 'Retry'}
          </Button>
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
        className="w-64 px-3 py-2 border border-border/70 rounded-xl bg-background/80 text-foreground focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40 transition-all"
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
