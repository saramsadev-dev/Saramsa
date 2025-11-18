"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BaseModal } from '../modals/BaseModal';
import { DashboardPlatformSelection } from './DashboardPlatformSelection';
import { AzureDevOpsConfigScreen } from '@/components/config/azure/AzureDevOpsConfigScreen';
import { JiraConfigScreen } from '@/components/config/jira/JiraConfigScreen';

interface DashboardIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export function DashboardIntegrationModal({
  isOpen,
  onClose,
  projectId,
}: DashboardIntegrationModalProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<'azure' | 'jira' | null>(null);

  const handlePlatformSelect = (platform: 'azure' | 'jira') => {
    setSelectedPlatform(platform);
    if (typeof window !== 'undefined') {
      localStorage.setItem('selected_platform', platform);
    }
  };

  const handleBack = () => {
    setSelectedPlatform(null);
  };

  const handleConfigComplete = () => {
    // Configuration is complete, close the modal and stay on dashboard
    setSelectedPlatform(null);
    onClose();
  };

  const handleClose = () => {
    setSelectedPlatform(null);
    onClose();
  };

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title={selectedPlatform ? `Configure ${selectedPlatform === 'azure' ? 'Azure DevOps' : 'Jira'} Integration` : "Configure Integration"}
      description={selectedPlatform ? undefined : "Connect your project to Azure DevOps or Jira to push work items"}
      size="xl"
      className="max-h-[90vh] overflow-hidden"
    >
      <div className="max-h-[75vh] overflow-y-auto -mx-6 -mt-6">
        <AnimatePresence mode="wait">
          {!selectedPlatform ? (
            <motion.div
              key="platform-selection"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <DashboardPlatformSelection
                onPlatformSelect={handlePlatformSelect}
                projectId={projectId}
              />
            </motion.div>
          ) : selectedPlatform === 'azure' ? (
            <motion.div
              key="azure-config"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <AzureDevOpsConfigScreen
                onContinue={handleConfigComplete}
                onBack={handleBack}
              />
            </motion.div>
          ) : (
            <motion.div
              key="jira-config"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <JiraConfigScreen
                onContinue={handleConfigComplete}
                onBack={handleBack}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </BaseModal>
  );
}
