'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { useEffect, useCallback } from 'react';
import { ProjectDashboard } from '@/components/ui/dashboard/ProjectDashboard';
import { encryptProjectId } from '@/lib/encryption';
import type { Project } from '@/store/features/projects/projectsSlice';

export default function HomePage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Only redirect to login if auth check is complete and user is not authenticated
    if (!loading && !isAuthenticated) {
      router.replace('/login/');
    }
  }, [isAuthenticated, loading, router]);

  const handleGoToProject = useCallback((project: Project) => {
    try {
      const encryptedId = encryptProjectId(project.id);
      router.push(`/projects/${encryptedId}/dashboard/`);
    } catch (error) {
      console.error('Failed to navigate to project:', error);
      // Fallback to unencrypted ID if encryption fails
      router.push(`/projects/${project.id}/dashboard/`);
    }
  }, [router]);

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-saramsa-brand/20 border-t-saramsa-brand mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // If not authenticated, show nothing (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Show projects dashboard if authenticated
  return (
    <div className="min-h-screen bg-background">
      <ProjectDashboard 
        onGoToProject={handleGoToProject}
      />
    </div>
  );
}
