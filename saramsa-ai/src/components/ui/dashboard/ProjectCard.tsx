'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar, 
  BarChart3, 
  ExternalLink, 
  MoreVertical, 
  Trash2,
  Cloud,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  Edit,
  RefreshCw
} from 'lucide-react';
import type { Project } from '@/store/features/projects/projectsSlice';
import { DeleteProjectModal } from './DeleteProjectModal';

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
  onDelete: (projectId: string) => void;
  onEdit?: (project: Project) => void;
  onSync?: (project: Project, provider: 'azure' | 'jira') => void;
  onGoToProject?: (project: Project) => void;
  isSelected?: boolean;
  deleteLoading?: boolean;
  syncLoading?: boolean;
}

export function ProjectCard({ project, onClick, onDelete, onEdit, onSync, onGoToProject, isSelected = false, deleteLoading = false, syncLoading = false }: ProjectCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  const hasExternalLinks = project.externalLinks && project.externalLinks.length > 0;
  
  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    
    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showMenu]);

  const getProviderIcon = (provider: 'azure' | 'jira') => {
    switch (provider) {
      case 'azure':
        return <Cloud className="w-3 h-3" />;
      case 'jira':
        return <span className="text-xs font-bold">J</span>;
      default:
        return null;
    }
  };

  const getProviderColor = (provider: 'azure' | 'jira') => {
    switch (provider) {
      case 'azure':
        return 'bg-blue-500';
      case 'jira':
        return 'bg-blue-600';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`relative bg-white dark:bg-gray-800 rounded-xl border-2 transition-all duration-200 cursor-pointer group flex flex-col ${
        isSelected 
          ? 'border-[#E603EB] shadow-lg shadow-[#E603EB]/20' 
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-lg'
      }`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="p-6 pb-3">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {project.name}
            </h3>
            <div className="h-5 mt-1">
              {project.description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
                  {project.description}
                </p>
              )}
            </div>
          </div>
          
          {/* Menu Button */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-opacity"
            >
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
            
            {showMenu && (
              <div className="absolute right-0 top-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10 min-w-[150px] py-1">
                {onEdit && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(false);
                      onEdit(project);
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                )}
                {hasExternalLinks && onSync && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMenu(false);
                      const provider = project.externalLinks[0].provider;
                      onSync(project, provider);
                    }}
                    disabled={syncLoading}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className={`w-4 h-4 ${syncLoading ? 'animate-spin' : ''}`} />
                    Sync with {project.externalLinks[0].provider === 'azure' ? 'Azure' : 'Jira'}
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowMenu(false);
                    setShowDeleteModal(true);
                  }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Provider Badges */}
        <div className="flex gap-2">
          {project.externalLinks && project.externalLinks.length > 0 ? (
            project.externalLinks.map((link, index) => (
              <span
                key={index}
                className={`inline-flex items-center gap-1 px-2 py-0.5 ${getProviderColor(link.provider)} text-white text-xs rounded-full h-5`}
              >
                {getProviderIcon(link.provider)}
                <span>{link.provider === 'azure' ? 'Azure DevOps' : 'Jira'}</span>
              </span>
            ))
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 bg-gray-500 text-white text-xs rounded-full h-5">
              Basic
            </span>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 py-3">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-gray-400" />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {project.metadata?.totalComments || 0}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Comments</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {getStatusIcon(project.metadata?.analysisStatus)}
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                {project.metadata?.analysisStatus || 'Not started'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Analysis</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 rounded-b-xl mt-auto">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            Created {formatDate(project.createdAt)}
          </div>
          
          {project.externalLinks && project.externalLinks.length > 0 && (
            <div className="flex items-center gap-1">
              <ExternalLink className="w-3 h-3" />
              {project.externalLinks.length} integration{project.externalLinks.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
        
        {project.metadata?.lastAnalysisAt && (
          <div className="flex items-center gap-1 mb-2 text-xs text-gray-500 dark:text-gray-400">
            <BarChart3 className="w-3 h-3" />
            Last analyzed {formatDate(project.metadata.lastAnalysisAt)}
          </div>
        )}
        
        {/* Go to Project Button */}
        {onGoToProject && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onGoToProject(project);
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white text-sm rounded-lg hover:shadow-lg transition-all duration-200"
          >
            <ArrowRight className="w-4 h-4" />
            Go to Analysis
          </button>
        )}
      </div>

      {/* Selection Indicator */}
      {isSelected && (
        <div className="absolute top-4 right-4">
          <div className="w-3 h-3 bg-[#E603EB] rounded-full"></div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <DeleteProjectModal
          project={project}
          onConfirm={() => {
            onDelete(project.id);
            setShowDeleteModal(false);
          }}
          onCancel={() => setShowDeleteModal(false)}
          loading={deleteLoading}
        />
      )}
    </motion.div>
  );
}
