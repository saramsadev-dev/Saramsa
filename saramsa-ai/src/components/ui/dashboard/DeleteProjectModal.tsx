'use client';

import { useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, Trash2 } from 'lucide-react';
import type { Project } from '@/store/features/projects/projectsSlice';

interface DeleteProjectModalProps {
  project: Project;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  isOpen?: boolean;
}

export function DeleteProjectModal({
  project,
  onConfirm,
  onCancel,
  loading = false,
  isOpen = true,
}: DeleteProjectModalProps) {
  const modalRoot = typeof document !== 'undefined' ? document.body : null;

  useEffect(() => {
    if (!modalRoot || !isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onCancel();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, modalRoot, onCancel]);

  const content = useMemo(() => {
    if (!modalRoot || !isOpen) return null;

    return createPortal(
      <div
        className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 p-4"
        onClick={loading ? undefined : onCancel}
      >
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.18 }}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-md w-full focus:outline-none"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-project-modal-title"
          >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <h3 id="delete-project-modal-title" className="text-lg font-semibold text-gray-900 dark:text-white">
              Delete Project
            </h3>
          </div>
          <button
            onClick={loading ? undefined : onCancel}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Close"
            type="button"
            disabled={loading}
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Are you sure you want to delete the project <strong>"{project.name}"</strong>?
            This action cannot be undone and will permanently remove:
          </p>

          <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-6">
            <li className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              All project data and files
            </li>
            <li className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              Analysis results and insights
            </li>
            <li className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full" />
              Integration connections
            </li>
          </ul>

          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-sm text-red-700 dark:text-red-300">
              <strong>Warning:</strong> This action is permanent and cannot be reversed.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={loading ? undefined : onCancel}
            type="button"
            disabled={loading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            type="button"
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                Delete Project
              </>
            )}
          </button>
        </div>
          </motion.div>
        </AnimatePresence>
      </div>,
      modalRoot
    );
  }, [isOpen, loading, modalRoot, onCancel, onConfirm, project.name]);

  return content;
}
