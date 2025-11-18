'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { useEffect, useRef, useState, useCallback } from 'react';
import { ProjectDashboard } from '@/components/ui/dashboard/ProjectDashboard';
import { encryptProjectId } from '@/lib/encryption';
import type { Project } from '@/store/features/projects/projectsSlice';

export default function HomePage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();
  const hasRedirectedRef = useRef(false);
  const [isRedirecting, setIsRedirecting] = useState(false);

  useEffect(() => {
    // Prevent multiple redirects
    if (hasRedirectedRef.current || isRedirecting) return;
    
    // Wait for auth to be determined
    if (loading) return;
    
    // Only redirect to login if not authenticated
    if (!isAuthenticated) {
      console.log("Redirecting to login");
      hasRedirectedRef.current = true;
      setIsRedirecting(true);
      
      const timer = setTimeout(() => {
        router.replace('/login');
      }, 100);
      
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, loading, router, isRedirecting]);

  const handleGoToProject = useCallback((project: Project) => {
    try {
      const encryptedId = encryptProjectId(project.id);
      router.push(`/projects/${encryptedId}/dashboard`);
    } catch (error) {
      console.error('Failed to navigate to project:', error);
      // Fallback to unencrypted ID if encryption fails
      router.push(`/projects/${project.id}/dashboard`);
    }
  }, [router]);

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show loading while redirecting to login
  if (!isAuthenticated && isRedirecting) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Redirecting...</p>
        </div>
      </div>
    );
  }

  // Show projects dashboard if authenticated
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <ProjectDashboard 
        onGoToProject={handleGoToProject}
      />
    </div>
  );
}
