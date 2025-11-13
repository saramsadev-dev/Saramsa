"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Eye,
  EyeOff,
  Loader2,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Shield,
  Zap,
  Download,
  ArrowRight,
  ArrowLeft,
  Folder,
} from "lucide-react";

interface AzureDevOpsProject {
  id: string;
  name: string;
  description?: string;
  url?: string;
  templateName?: string;
}

interface DevOpsFormPanelProps {
  orgName: string;
  onOrgNameChange: (value: string) => void;
  pat: string;
  onPatChange: (value: string) => void;
  onFetchProjects: () => void;
  isLoading: boolean;
  error: string;
  projects: AzureDevOpsProject[];
  selectedProject: string;
  onProjectSelect: (projectId: string) => void;
  onContinue: () => void;
  onBack: () => void;
  isExistingIntegration?: boolean;
}

export const DevOpsFormPanel = ({
  orgName,
  onOrgNameChange,
  pat,
  onPatChange,
  onFetchProjects,
  isLoading,
  error,
  projects,
  selectedProject,
  onProjectSelect,
  onContinue,
  onBack,
  isExistingIntegration = false,
}: DevOpsFormPanelProps) => {
  const [showPat, setShowPat] = useState(false);
  const [isPatGuideOpen, setIsPatGuideOpen] = useState(false);

  const togglePatVisibility = () => setShowPat(!showPat);

  const patSteps = [
    {
      step: 1,
      title: "Go to Azure DevOps → User Settings → Personal Access Tokens",
      description:
        "Navigate to your Azure DevOps organization and access your user settings.",
    },
    {
      step: 2,
      title: "Click 'New Token' and select scopes: vso.work_write",
      description:
        "Create a new token with work item read/write permissions for feedback analysis.",
    },
    {
      step: 3,
      title: "Copy the token and paste it here",
      description:
        "Save the generated token securely and enter it in the field above.",
    },
  ];

  return (
    <div className="relative w-full max-w-2xl space-y-8 mx-auto">
      {/* Header */}
      {/* <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="space-y-4 text-center sm:text-left"
      >
        <div className="flex justify-center sm:justify-start">
          <div className="w-16 h-16 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-2xl flex items-center justify-center shadow-lg">
            <Download className="w-8 h-8 text-white" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Connect Your Azure DevOps
          </h1>
          <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
            To begin analyzing feedback, please link your Azure DevOps organization and select project access.
          </p>
        </div>
      </motion.div> */}

      {/* Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="space-y-6"
      >
        {/* Back Button */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex justify-center sm:justify-start"
        >
          <button
            onClick={onBack}
            className="w-full sm:w-auto px-6 h-12 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 font-semibold shadow-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-all duration-300 rounded-md flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Platform Selection
          </button>
        </motion.div>
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-2 border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/30 transition-all duration-300 rounded-lg p-6">
          {/* Show form fields only for new integrations */}
          {!isExistingIntegration && (
            <>
              {/* Organization Name */}
              <div className="space-y-2 mb-6">
                <label
                  htmlFor="orgName"
                  className="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Organization Name
                </label>
                <input
                  id="orgName"
                  type="text"
                  value={orgName}
                  onChange={(e) => onOrgNameChange(e.target.value)}
                  placeholder="e.g., mycompany"
                  className="w-full h-12 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:border-[#E603EB]/50 focus:border-[#E603EB] focus:ring-2 focus:ring-[#E603EB]/20 transition-all duration-300 rounded-md px-3"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Your Azure DevOps organization name (found in your URL:
                  https://dev.azure.com/[orgname])
                </p>
              </div>

              {/* Personal Access Token */}
              <div className="space-y-2 mb-6">
                <label
                  htmlFor="pat"
                  className="text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Personal Access Token (PAT)
                </label>
                <div className="relative">
                  <input
                    id="pat"
                    type={showPat ? "text" : "password"}
                    value={pat}
                    onChange={(e) => onPatChange(e.target.value)}
                    placeholder="Enter your Azure DevOps PAT"
                    className="w-full h-12 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:border-[#E603EB]/50 focus:border-[#E603EB] focus:ring-2 focus:ring-[#E603EB]/20 transition-all duration-300 rounded-md px-3 pr-12"
                  />
                  <button
                    type="button"
                    onClick={togglePatVisibility}
                    className="absolute right-1 top-1 h-10 w-10 text-gray-400 hover:text-[#E603EB] flex items-center justify-center"
                  >
                    {showPat ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* PAT Generation Guide */}
              <div className="mb-6">
                <button
                  onClick={() => setIsPatGuideOpen(!isPatGuideOpen)}
                  className="w-full justify-between p-3 h-auto text-left border border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 transition-all duration-300 rounded-md flex items-center"
                >
                  <div className="flex items-center gap-2">
                    <ExternalLink className="w-4 h-4 text-[#E603EB]" />
                    <span className="font-medium text-gray-900 dark:text-white">
                      How to generate a PAT
                    </span>
                  </div>
                  {isPatGuideOpen ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  )}
                </button>

                <AnimatePresence>
                  {isPatGuideOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="space-y-4 mt-4"
                    >
                      {patSteps.map((step, index) => (
                        <motion.div
                          key={step.step}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.1 }}
                          className="flex gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                        >
                          <div className="flex-shrink-0 w-6 h-6 bg-[#E603EB] text-white rounded-full flex items-center justify-center text-xs font-bold">
                            {step.step}
                          </div>
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {step.title}
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {step.description}
                            </p>
                          </div>
                        </motion.div>
                      ))}

                      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <div className="flex items-start gap-2">
                          <ExternalLink className="w-4 h-4 text-blue-600 mt-0.5" />
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-blue-700 dark:text-blue-400">
                              Quick Access
                            </p>
                            <p className="text-xs text-blue-600 dark:text-blue-300">
                              Go directly to:
                              https://dev.azure.com/[your-org]/_usersSettings/tokens
                            </p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </>
          )}

          {/* Show organization info for existing integrations */}
          {isExistingIntegration && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-700 dark:text-green-400">
                    Azure DevOps Integration Connected
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-300">
                    Organization: {orgName}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 mb-6"
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <p className="text-sm text-red-700 dark:text-red-400">
                    {error}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Success Message & Project Selection */}
          <AnimatePresence>
            {projects.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <p className="text-sm font-medium text-green-700 dark:text-green-400">
                      Successfully connected! Found {projects.length} projects
                    </p>
                  </div>
                </div>

                {/* Project Selection with Folder Icons */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Select Azure DevOps Project
                  </label>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {projects.map((project) => (
                      <div
                        key={project.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-all ${
                          selectedProject === project.id
                            ? "border-[#E603EB] bg-[#E603EB]/10 dark:bg-[#E603EB]/20"
                            : "border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/50"
                        }`}
                        onClick={() => onProjectSelect(project.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="flex-shrink-0">
                              <Folder className="w-5 h-5 text-[#E603EB]" />
                            </div>
                            <div>
                              <div className="font-medium text-gray-900 dark:text-white">
                                {project.name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {project.templateName &&
                                  `Template: ${project.templateName}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {project.templateName && (
                              <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                                {project.templateName}
                              </span>
                            )}
                            {selectedProject === project.id && (
                              <CheckCircle className="w-4 h-4 text-[#E603EB]" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    This project will be used to create work items from analyzed
                    feedback
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          {projects.length === 0 ? (
            /* Fetch Projects Button */
            <button
              onClick={onFetchProjects}
              disabled={
                (!isExistingIntegration && (!orgName.trim() || !pat.trim())) ||
                isLoading
              }
              className="w-full h-12 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 group rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#E603EB]"
            >
              {isLoading ? (
                <div className="flex items-center gap-3 justify-center">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>
                    {isExistingIntegration
                      ? "Fetching Projects..."
                      : "Connecting..."}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-3 justify-center">
                  <Zap className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span>
                    {isExistingIntegration
                      ? "Fetch Projects"
                      : "Fetch Projects"}
                  </span>
                </div>
              )}
            </button>
          ) : (
            /* Continue to Dashboard Button */
            <button
              onClick={onContinue}
              disabled={!selectedProject}
              className="w-full h-12 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 group rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#E603EB]"
            >
              <div className="flex items-center gap-3 justify-center">
                <span>Continue to Dashboard</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>
          )}

          {/* Project selection hint */}
          {projects.length > 0 && !selectedProject && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center text-xs text-gray-500 dark:text-gray-400 mt-2"
            >
              Please select a project to continue
            </motion.p>
          )}
        </div>
      </motion.div>

      {/* Security Footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="space-y-2 text-center sm:text-left"
      >
        <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent" />
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <Shield className="w-4 h-4 text-gray-500" />
            <span>
              Your token is encrypted and never stored without your permission.
            </span>
          </div>
          <div className="flex items-center justify-center sm:justify-end gap-2">
            <ExternalLink className="w-4 h-4 text-[#E603EB]" />
            <a
              href="https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"
              target="_blank"
              rel="noreferrer"
              className="font-medium text-[#E603EB] hover:text-[#8B5FBF]"
            >
              Azure PAT security guidance
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
