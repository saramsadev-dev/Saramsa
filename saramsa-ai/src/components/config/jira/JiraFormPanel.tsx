'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
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
  Globe,
  ArrowRight,
  ArrowLeft,
  Folder
} from 'lucide-react';

interface JiraProject {
  id: string;
  key: string;
  name: string;
  isCompanyManaged?: boolean;
  isTeamManaged?: boolean;
  projectCategory?: string;
}

interface JiraFormPanelProps {
  config: {
    email: string;
    apiToken: string;
    domain: string;
    projectKey: string;
  };
  onConfigChange: (field: string, value: string) => void;
  onValidateConfiguration: () => void;
  isLoading: boolean;
  isCreatingProject?: boolean;
  error: string;
  projects: JiraProject[];
  selectedProject: string;
  onProjectSelect: (projectId: string) => void;
  onContinue: () => void;
  onBack: () => void;
  validationStatus: 'idle' | 'loading' | 'success' | 'error';
  isExistingIntegration?: boolean;
  linkedProjects?: { [key: string]: { id: string; name: string } };
}

export const JiraFormPanel = ({
  config,
  onConfigChange,
  onValidateConfiguration,
  isLoading,
  isCreatingProject = false,
  error,
  projects,
  selectedProject,
  onProjectSelect,
  onContinue,
  onBack,
  validationStatus,
  isExistingIntegration = false,
  linkedProjects = {},
}: JiraFormPanelProps) => {
  const router = useRouter();
  const [showApiToken, setShowApiToken] = useState(false);
  const [isTokenGuideOpen, setIsTokenGuideOpen] = useState(false);

  const toggleApiTokenVisibility = () => setShowApiToken(!showApiToken);

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

  const tokenSteps = [
    {
      step: 1,
      title: "Go to Atlassian Account Settings → Security → API tokens",
      description: "Navigate to your Atlassian account security settings to manage API tokens."
    },
    {
      step: 2,
      title: "Click 'Create API token' and give it a label",
      description: "Create a new token with a descriptive name like 'Saramsa Integration'."
    },
    {
      step: 3,
      title: "Copy the token and paste it here",
      description: "Save the generated token securely and enter it in the field above."
    }
  ];

  return (
    <div className="relative w-full max-w-2xl space-y-8 mx-auto pb-16">
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
              {/* Email */}
              <div className="space-y-2 mb-6">
            <label htmlFor="email" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Jira Email Address
            </label>
            <input
              id="email"
              type="email"
              value={config.email}
              onChange={(e) => onConfigChange('email', e.target.value)}
              placeholder="your-email@company.com"
              className="w-full h-12 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:border-[#E603EB]/50 focus:border-[#E603EB] focus:ring-2 focus:ring-[#E603EB]/20 transition-all duration-300 rounded-md px-3"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              The email address associated with your Jira account
            </p>
          </div>

          {/* API Token */}
          <div className="space-y-2 mb-6">
            <label htmlFor="apiToken" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              API Token
            </label>
            <div className="relative">
              <input
                id="apiToken"
                type={showApiToken ? "text" : "password"}
                value={config.apiToken}
                onChange={(e) => onConfigChange('apiToken', e.target.value)}
                placeholder="Enter your Jira API token"
                className="w-full h-12 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:border-[#E603EB]/50 focus:border-[#E603EB] focus:ring-2 focus:ring-[#E603EB]/20 transition-all duration-300 rounded-md px-3 pr-12"
              />
              <button
                type="button"
                onClick={toggleApiTokenVisibility}
                className="absolute right-1 top-1 h-10 w-10 text-gray-400 hover:text-[#E603EB] flex items-center justify-center"
              >
                {showApiToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Domain */}
          <div className="space-y-2 mb-6">
            <label htmlFor="domain" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Jira Domain
            </label>
            <input
              id="domain"
              type="text"
              value={config.domain}
              onChange={(e) => onConfigChange('domain', e.target.value)}
              placeholder="your-domain.atlassian.net"
              className="w-full h-12 bg-white dark:bg-gray-700 border-2 border-gray-300 dark:border-gray-600 hover:border-[#E603EB]/50 focus:border-[#E603EB] focus:ring-2 focus:ring-[#E603EB]/20 transition-all duration-300 rounded-md px-3"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Your Jira cloud domain (e.g., company.atlassian.net)
            </p>
          </div>

          {/* API Token Generation Guide */}
          <div className="mb-6">
            <button
              onClick={() => setIsTokenGuideOpen(!isTokenGuideOpen)}
              className="w-full justify-between p-3 h-auto text-left border border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 transition-all duration-300 rounded-md flex items-center"
            >
              <div className="flex items-center gap-2">
                <ExternalLink className="w-4 h-4 text-[#E603EB]" />
                <span className="font-medium text-gray-900 dark:text-white">
                  How to generate an API token
                </span>
              </div>
              {isTokenGuideOpen ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </button>
            
            <AnimatePresence>
              {isTokenGuideOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4 mt-4"
                >
                  {tokenSteps.map((step, index) => (
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
                        <a 
                          href="https://id.atlassian.com/manage-profile/security/api-tokens" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-blue-600 dark:text-blue-300 hover:underline"
                        >
                          Go directly to: https://id.atlassian.com/manage-profile/security/api-tokens
                        </a>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
            </>
          )}

          {/* Show connection info for existing integrations */}
          {isExistingIntegration && (
            <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div>
                  <p className="text-sm font-medium text-green-700 dark:text-green-400">
                    Jira Integration Connected
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-300">
                    Domain: {config.domain} | Email: {config.email}
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
            {projects && projects.length > 0 && (
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
                      Successfully connected! Found {projects?.length || 0} projects
                    </p>
                  </div>
                </div>

                {/* Project Selection with Folder Icons */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Select Jira Project
                  </label>
                  
                  {Object.keys(linkedProjects).length > 0 && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-xs text-blue-700 dark:text-blue-300">
                        <strong>{Object.keys(linkedProjects).length}</strong> project(s) already linked. 
                        Click on a linked project to go to its dashboard.
                      </p>
                    </div>
                  )}
                  
                  <div className="max-h-48 overflow-y-auto scrollbar-thin">
                    <div className="space-y-2 p-1">
                      {projects?.map((project) => {
                        const linkedProject = linkedProjects[project.id];
                        const isAlreadyLinked = !!linkedProject;
                        
                        return (
                          <div
                            key={project.id}
                            className={`p-3 border rounded-lg transition-all ${
                              isAlreadyLinked
                                ? "cursor-pointer border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20 hover:border-orange-300 dark:hover:border-orange-700"
                                : selectedProject === project.id
                                ? "border-[#E603EB] bg-[#E603EB]/10 dark:bg-[#E603EB]/20 cursor-pointer"
                                : "border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/50 cursor-pointer"
                            }`}
                            onClick={() => isAlreadyLinked ? handleLinkedProjectClick(linkedProject.id) : onProjectSelect(project.id)}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3 flex-1">
                                <div className="flex-shrink-0">
                                  <Folder className="w-5 h-5 text-[#E603EB]" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium text-gray-900 dark:text-white">
                                    {project.name}
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    Key: {project.key}
                                  </div>
                                  {isAlreadyLinked && (
                                    <div className="text-xs text-orange-600 dark:text-orange-400 mt-1 flex items-center gap-1">
                                      Already linked to "{linkedProject.name}"
                                      <ArrowRight className="w-3 h-3" />
                                    </div>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {project.isCompanyManaged && (
                                  <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                                    Company
                                  </span>
                                )}
                                {project.isTeamManaged && (
                                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded">
                                    Team
                                  </span>
                                )}
                                {selectedProject === project.id && !isAlreadyLinked && (
                                  <CheckCircle className="w-4 h-4 text-[#E603EB]" />
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
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    This project will be used to create issues from analyzed feedback
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          {!projects || projects.length === 0 ? (
            /* Validate Configuration Button */
            <button
              onClick={onValidateConfiguration}
              disabled={(!isExistingIntegration && (!config.email || !config.apiToken || !config.domain)) || isLoading}
              className="w-full h-12 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 group rounded-md"
            >
              {isLoading ? (
                <div className="flex items-center gap-3 justify-center">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>{isExistingIntegration ? 'Fetching Projects...' : 'Validating...'}</span>
                </div>
              ) : (
                <div className="flex items-center gap-3 justify-center">
                  <Shield className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span>{isExistingIntegration ? 'Fetch Projects' : 'Validate Configuration'}</span>
                </div>
              )}
            </button>
          ) : (
            /* Continue to Dashboard Button */
            <button
              onClick={onContinue}
              disabled={!selectedProject || isCreatingProject}
              className="w-full h-12 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 group rounded-md"
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
            </button>
          )}

          {/* Project selection hint */}
          {projects && projects.length > 0 && !selectedProject && (
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
        className="text-center space-y-2"
      >
        <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent" />
        <div className="flex items-center justify-center gap-2">
          <Shield className="w-4 h-4 text-gray-500" />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Your credentials are encrypted and never stored without your permission.
          </p>
        </div>
      </motion.div>

      {/* Floating Elements */}
      <div className="absolute -top-10 -right-10 w-20 h-20 bg-gradient-to-br from-[#E603EB]/20 to-[#8B5FBF]/20 rounded-full blur-xl animate-float" />
      <div className="absolute -bottom-10 -left-10 w-16 h-16 bg-gradient-to-br from-[#8B5FBF]/20 to-[#E603EB]/20 rounded-full blur-xl animate-float" style={{ animationDelay: '2s' }} />
    </div>
  );
};
