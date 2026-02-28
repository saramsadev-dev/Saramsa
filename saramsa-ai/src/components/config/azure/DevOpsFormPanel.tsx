"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

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
  isCreatingProject?: boolean;
  error: string;
  projects: AzureDevOpsProject[];
  selectedProject: string;
  onProjectSelect: (projectId: string) => void;
  onContinue: () => void;
  onBack: () => void;
  isExistingIntegration?: boolean;
  linkedProjects?: { [key: string]: { id: string; name: string } }; // Map of external project ID to Saramsa project
}

export const DevOpsFormPanel = ({
  orgName,
  onOrgNameChange,
  pat,
  onPatChange,
  onFetchProjects,
  isLoading,
  isCreatingProject = false,
  error,
  projects,
  selectedProject,
  onProjectSelect,
  onContinue,
  onBack,
  isExistingIntegration = false,
  linkedProjects = {},
}: DevOpsFormPanelProps) => {
  const router = useRouter();
  const [showPat, setShowPat] = useState(false);
  const [isPatGuideOpen, setIsPatGuideOpen] = useState(false);

  const togglePatVisibility = () => setShowPat(!showPat);

  const handleLinkedProjectClick = async (projectId: string) => {
    try {
      const { encryptProjectId } = await import('@/lib/encryption');
      const encryptedId = encryptProjectId(projectId);
      router.push(`/projects/${encryptedId}/dashboard`);
    } catch (error) {
      console.error('Navigation error:', error);
      // Fallback to unencrypted ID if encryption fails
      router.push(`/projects/${projectId}/dashboard`);
    }
  };

  const patSteps = [
    {
      step: 1,
      title: "Go to Azure DevOps > User Settings > Personal Access Tokens",
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
    <div className="relative w-full max-w-2xl space-y-8 mx-auto pb-16">
      {/* Header */}
      {/* <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="space-y-4 text-center sm:text-left"
      >
        <div className="flex justify-center sm:justify-start">
          <div className="w-16 h-16 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-2xl flex items-center justify-center shadow-lg">
            <Download className="w-8 h-8 text-white" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-foreground dark:text-foreground">
            Connect Your Azure DevOps
          </h1>
          <p className="text-muted-foreground dark:text-muted-foreground leading-relaxed">
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
          <Button
            onClick={onBack}
            variant="outline"
            className="w-full sm:w-auto h-12 gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Platform Selection
          </Button>
        </motion.div>
        <div className="bg-card/80 dark:bg-card/90 backdrop-blur-sm border-2 border-border/60 dark:border-border/60 hover:border-saramsa-brand/30 transition-all duration-300 rounded-xl p-6">
          {/* Show form fields only for new integrations */}
          {!isExistingIntegration && (
            <>
              {/* Organization Name */}
              <div className="space-y-2 mb-6">
                <label
                  htmlFor="orgName"
                  className="text-sm font-medium text-muted-foreground dark:text-muted-foreground"
                >
                  Organization Name
                </label>
                <Input
                  id="orgName"
                  type="text"
                  value={orgName}
                  onChange={(e) => onOrgNameChange(e.target.value)}
                  placeholder="e.g., mycompany"
                  className="w-full h-12 bg-background/80 border-2 border-border/60 dark:border-border/60 hover:border-saramsa-brand/40 focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 transition-all duration-300 rounded-xl px-3"
                />
                <p className="text-xs text-muted-foreground dark:text-muted-foreground">
                  Your Azure DevOps organization name (found in your URL:
                  https://dev.azure.com/[orgname])
                </p>
              </div>

              {/* Personal Access Token */}
              <div className="space-y-2 mb-6">
                <label
                  htmlFor="pat"
                  className="text-sm font-medium text-muted-foreground dark:text-muted-foreground"
                >
                  Personal Access Token (PAT)
                </label>
                <div className="relative">
                  <Input
                    id="pat"
                    type={showPat ? "text" : "password"}
                    value={pat}
                    onChange={(e) => onPatChange(e.target.value)}
                    placeholder="Enter your Azure DevOps PAT"
                    className="w-full h-12 bg-background/80 border-2 border-border/60 dark:border-border/60 hover:border-saramsa-brand/40 focus:border-saramsa-brand/50 focus:ring-2 focus:ring-saramsa-brand/20 transition-all duration-300 rounded-xl px-3 pr-12"
                  />
                  <Button
                    type="button"
                    onClick={togglePatVisibility}
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1 h-10 w-10 text-muted-foreground hover:text-saramsa-brand"
                  >
                    {showPat ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* PAT Generation Guide */}
              <div className="mb-6">
                <Button
                  onClick={() => setIsPatGuideOpen(!isPatGuideOpen)}
                  variant="outline"
                  className="w-full h-auto text-left justify-between px-3 py-3 border border-saramsa-brand/20 hover:border-saramsa-brand/40 hover:bg-saramsa-brand/5"
                >
                  <div className="flex items-center gap-2">
                    <ExternalLink className="w-4 h-4 text-saramsa-brand" />
                    <span className="font-medium text-foreground dark:text-foreground">
                      How to generate a PAT
                    </span>
                  </div>
                  {isPatGuideOpen ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </Button>

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
                          className="flex gap-3 p-3 bg-secondary/40 dark:bg-secondary/40 rounded-xl"
                        >
                          <div className="flex-shrink-0 w-6 h-6 bg-saramsa-brand text-white rounded-full flex items-center justify-center text-xs font-bold">
                            {step.step}
                          </div>
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-foreground dark:text-foreground">
                              {step.title}
                            </p>
                            <p className="text-xs text-muted-foreground dark:text-muted-foreground">
                              {step.description}
                            </p>
                          </div>
                        </motion.div>
                      ))}

                      <div className="mt-4 p-3 bg-secondary/60 rounded-xl border border-border/60">
                        <div className="flex items-start gap-2">
                          <ExternalLink className="w-4 h-4 text-muted-foreground mt-0.5" />
                          <div className="space-y-1">
                            <p className="text-sm font-medium text-foreground dark:text-foreground">
                              Quick Access
                            </p>
                            <p className="text-xs text-muted-foreground dark:text-muted-foreground">
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
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
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
                className="p-3 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800 mb-6"
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
            {projects && projects.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                transition={{ duration: 0.3 }}
                className="space-y-4"
              >
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <p className="text-sm font-medium text-green-700 dark:text-green-400">
                      Successfully connected! Found {projects.length || 0} projects
                    </p>
                  </div>
                </div>

                {/* Project Selection with Folder Icons */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground dark:text-muted-foreground">
                    Select Azure DevOps Project
                  </label>
                  
                  {/* Info Banner */}
                  {Object.keys(linkedProjects).length > 0 && (
                    <div className="p-3 bg-secondary/60 rounded-xl border border-border/60">
                      <p className="text-xs text-foreground dark:text-muted-foreground">
                        <strong>{Object.keys(linkedProjects).length}</strong> project(s) already linked. 
                        Click on a linked project to go to its dashboard.
                      </p>
                    </div>
                  )}
                  
                  <div className="max-h-48 overflow-y-auto scrollbar-thin">
                    <div className="space-y-2 p-1">
                      {projects.map((project) => {
                        const linkedProject = linkedProjects[project.id];
                        const isAlreadyLinked = !!linkedProject;
                        
                        return (
                          <div
                            key={project.id}
                            className={`p-3 border rounded-xl transition-all ${
                              isAlreadyLinked
                                ? "cursor-pointer border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20 hover:border-orange-300 dark:hover:border-orange-700"
                                : selectedProject === project.id
                                ? "border-saramsa-brand/60 bg-saramsa-brand/10 dark:bg-saramsa-brand/20 cursor-pointer"
                                : "border-border/60 dark:border-border/60 hover:border-saramsa-brand/40 cursor-pointer"
                            }`}
                            onClick={() =>
                              isAlreadyLinked
                                ? handleLinkedProjectClick(linkedProject.id)
                                : onProjectSelect(project.id)
                            }
                          >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 flex-1">
                              <div className="flex-shrink-0">
                                <Folder className="w-5 h-5 text-saramsa-brand" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-foreground dark:text-foreground">
                                  {project.name}
                                </div>
                                {project.templateName && (
                                  <div className="text-sm text-muted-foreground">
                                    Template: {project.templateName}
                                  </div>
                                )}
                                {isAlreadyLinked && (
                                  <div className="text-xs text-orange-600 dark:text-orange-400 mt-1 flex items-center gap-1">
                                    Already linked to "{linkedProject.name}"
                                    <ArrowRight className="w-3 h-3" />
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {selectedProject === project.id && !isAlreadyLinked && (
                                <CheckCircle className="w-4 h-4 text-saramsa-brand" />
                              )}
                              {isAlreadyLinked && (
                                <span className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 rounded whitespace-nowrap">
                                  Linked
                                </span>
                              )}
                            </div>
                          </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground dark:text-muted-foreground">
                    This project will be used to create work items from analyzed
                    feedback
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          {!projects || projects.length === 0 ? (
            /* Fetch Projects Button */
            <Button
              variant="saramsa"
              onClick={onFetchProjects}
              disabled={
                (!isExistingIntegration && (!orgName.trim() || !pat.trim())) ||
                isLoading
              }
              className="w-full h-12 group"
            >
              {isLoading ? (
                <div className="flex items-center gap-3 justify-center">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>
                    {isExistingIntegration ? "Fetching Projects..." : "Connecting..."}
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-3 justify-center">
                  <Zap className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span>
                    {isExistingIntegration ? "Fetch Projects" : "Fetch Projects"}
                  </span>
                </div>
              )}
            </Button>
          ) : (
            /* Continue to Dashboard Button */
            <Button
              variant="saramsa"
              onClick={onContinue}
              disabled={!selectedProject || isCreatingProject}
              className="w-full h-12 group"
            >
              <div className="flex items-center gap-3 justify-center">
                {isCreatingProject ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Creating Project...</span>
                  </>
                ) : (
                  <>
                    <span>Continue to Dashboard</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </div>
            </Button>
          )}

          {/* Project selection hint */}
          {projects && projects.length > 0 && !selectedProject && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center text-xs text-muted-foreground dark:text-muted-foreground mt-2"
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
        <div className="w-full h-px bg-gradient-to-r from-transparent via-border/70 to-transparent" />
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-muted-foreground dark:text-muted-foreground">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <Shield className="w-4 h-4 text-muted-foreground" />
            <span>
              Your token is encrypted and never stored without your permission.
            </span>
          </div>
          <div className="flex items-center justify-center sm:justify-end gap-2">
            <ExternalLink className="w-4 h-4 text-saramsa-brand" />
            <a
              href="https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"
              target="_blank"
              rel="noreferrer"
              className="font-medium text-saramsa-brand hover:text-saramsa-gradient-to"
            >
              Azure PAT security guidance
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
