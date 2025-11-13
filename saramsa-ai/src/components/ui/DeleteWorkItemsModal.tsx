'use client';

import type { ReactNode } from 'react';
import { AlertTriangle, Trash2 } from 'lucide-react';
import { BaseModal } from './modals/BaseModal';

interface DeleteWorkItemsModalProps {
  workItemCount: number;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  isOpen?: boolean;
  title?: ReactNode;
  description?: ReactNode;
  warningTitle?: ReactNode;
  warningDescription?: ReactNode;
  confirmLabel?: ReactNode;
}

export function DeleteWorkItemsModal({
  workItemCount,
  onConfirm,
  onCancel,
  loading = false,
  isOpen = true,
  title,
  description,
  warningTitle,
  warningDescription,
  confirmLabel,
}: DeleteWorkItemsModalProps) {
  const defaultTitle = title ?? 'Delete Work Items';
  const defaultDescription =
    description ??
    (
      <>
        Are you sure you want to delete <strong>{workItemCount}</strong> work item{workItemCount !== 1 ? 's' : ''}?
      </>
    );
  const defaultWarningTitle = warningTitle ?? 'This action cannot be undone';
  const defaultWarningDescription =
    warningDescription ?? 'The selected work items will be permanently removed from your project.';
  const defaultConfirmLabel =
    confirmLabel ?? `Delete ${workItemCount} Work Item${workItemCount !== 1 ? 's' : ''}`;

  const footer = (
    <div className="flex items-center justify-end gap-3">
      <button
        type="button"
        onClick={onCancel}
        disabled={loading}
        className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
      >
        Cancel
      </button>
      <button
        type="button"
        onClick={onConfirm}
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
            {defaultConfirmLabel}
          </>
        )}
      </button>
    </div>
  );

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onCancel}
      title={defaultTitle}
      description={defaultDescription}
      size="sm"
      icon={
        <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
        </div>
      }
      footer={footer}
    >
      <div className="space-y-4">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm space-y-1">
              <p className="text-red-800 dark:text-red-200 font-medium">{defaultWarningTitle}</p>
              <p className="text-red-700 dark:text-red-300">{defaultWarningDescription}</p>
            </div>
          </div>
        </div>
      </div>
    </BaseModal>
  );
}
