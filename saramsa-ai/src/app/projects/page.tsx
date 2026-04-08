'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { type Project } from '@/store/features/projects/projectsSlice';
import { ProjectDashboard } from '@/components/ui/dashboard/ProjectDashboard';
import { encryptProjectId } from '@/lib/encryption';

function ProjectsPage() {
  const router = useRouter();

  const handleGoToProject = useCallback((project: Project) => {
    try {
      const encryptedId = encryptProjectId(project.id);
      router.push(`/projects/${encryptedId}/dashboard/`);
    } catch (error) {
      console.error('Failed to navigate to project:', error);
      router.push(`/projects/${project.id}/dashboard/`);
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      <ProjectDashboard
        onGoToProject={handleGoToProject}
      />
    </div>
  );
}

export default ProjectsPage;
