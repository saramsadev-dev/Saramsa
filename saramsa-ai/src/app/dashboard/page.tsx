'use client';

import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { ProjectDashboard } from '@/components/ui/dashboard';
import { DashboardComponent } from '@/components/ui/dashboard';
import { setCurrentProject } from '@/store/features/projects/projectsSlice';
import type { AppDispatch } from '@/store/store';
import type { Project } from '@/store/features/projects/projectsSlice';

export default function DashboardPage() {
  const dispatch = useDispatch<AppDispatch>();
  const [view, setView] = useState<'projects' | 'analysis'>('analysis');
  
  const handleGoToProject = (project: Project) => {
    // Persist selection so analysis view resolves the project immediately
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('project_id', project.id);
        if (project.name) localStorage.setItem('selected_project_name', project.name);
      } catch {}
    }
    dispatch(setCurrentProject(project));
    setView('analysis');
  };
  
  // Show analysis dashboard by default, with option to switch to projects view
  if (view === 'projects') {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Projects Management</h1>
              <button
                onClick={() => setView('analysis')}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Back to Analysis
              </button>
            </div>
            <ProjectDashboard 
              onNavigateToAnalysis={() => setView('analysis')}
              onGoToProject={handleGoToProject}
            />
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analysis Dashboard</h1>
            <button
              onClick={() => setView('projects')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Manage Projects
            </button>
          </div>
          <DashboardComponent />
        </div>
      </div>
    </div>
  );
}