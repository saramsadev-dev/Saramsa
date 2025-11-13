"use client";

import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import type { AppDispatch, RootState } from "@/store/store";
import {
  fetchIntegrationAccounts,
  createAzureIntegration,
  createJiraIntegration,
  deleteIntegrationAccount,
  testIntegrationConnection,
  clearError,
  fetchExternalProjects,
  clearExternalProjects,
} from "@/store/features/integrations/integrationsSlice";
import { apiRequest } from "@/lib/apiRequest";
import { motion } from "framer-motion";
import {
  Plus,
  Settings,
  Trash2,
  TestTube,
  CheckCircle,
  XCircle,
  AlertCircle,
  AlertTriangle,
  ExternalLink,
  Loader2,
  Shield,
  Cloud,
  Download,
  Folder,
  Users,
} from "lucide-react";
import { AzureIntegrationForm } from "@/components/ui/settings/AzureIntegrationForm";
import { JiraIntegrationForm } from "@/components/ui/settings/JiraIntegrationForm";
import { BaseModal } from "@/components/ui/modals/BaseModal";
import type { IntegrationAccount } from "@/store/features/integrations/integrationsSlice";

export function IntegrationsPage() {
  const dispatch = useDispatch<AppDispatch>();
  const router = useRouter();
  const {
    accounts,
    loading,
    error,
    testingConnection,
    externalProjects,
    fetchingProjects,
  } = useSelector((state: RootState) => state.integrations);

  const [showAzureForm, setShowAzureForm] = useState(false);
  const [showJiraForm, setShowJiraForm] = useState(false);
  const [creatingProject, setCreatingProject] = useState<string | null>(null);
  const [accountPendingDeletion, setAccountPendingDeletion] = useState<IntegrationAccount | null>(null);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);

  // Check if integrations already exist
  const hasAzureIntegration = accounts.some(
    (account) => account.provider === "azure"
  );
  const hasJiraIntegration = accounts.some(
    (account) => account.provider === "jira"
  );

  useEffect(() => {
    // Fetch integration accounts from the new API
    dispatch(fetchIntegrationAccounts());
  }, [dispatch]);

  const handleTestConnection = async (accountId: string) => {
    await dispatch(testIntegrationConnection(accountId));
  };

  const handleDeleteAccount = (account: IntegrationAccount) => {
    setAccountPendingDeletion(account);
  };

  const closeDeleteModal = () => {
    if (deletingAccountId) return;
    setAccountPendingDeletion(null);
  };

  const handleConfirmDeleteAccount = async () => {
    if (!accountPendingDeletion) return;
    setDeletingAccountId(accountPendingDeletion.id);
    try {
      await dispatch(deleteIntegrationAccount(accountPendingDeletion.id)).unwrap();
      dispatch(clearExternalProjects());
    } catch (error: any) {
      console.error("Failed to delete integration account:", error);
      alert(error?.message || "Failed to delete integration. Please try again.");
    } finally {
      setDeletingAccountId(null);
      setAccountPendingDeletion(null);
    }
  };

  const handleFetchProjects = async (provider: "azure" | "jira") => {
    const account = accounts.find((acc) => acc.provider === provider);
    if (account) {
      await dispatch(
        fetchExternalProjects({ provider, accountId: account.id })
      );
    }
  };

  const handleCreateOrNavigateToProject = async (project: any) => {
    setCreatingProject(project.id);

    try {
      const account = accounts.find((acc) => acc.provider === project.provider);
      if (!account) {
        throw new Error("Integration account not found");
      }

      // Create the project using the same endpoint as config pages
      const res = await apiRequest(
        "post",
        "/integrations/projects/create/",
        {
          project_name: project.name,
          description: `Imported from ${
            project.provider === "azure" ? "Azure DevOps" : "Jira"
          }`,
          platform: project.provider,
          external_project_id: project.id,
          external_url: project.url || "",
          integration_account_id: account.id,
          ...(project.provider === "jira" &&
            project.key && { jira_project_key: project.key }),
          ...(project.provider === "azure" &&
            project.templateName && {
              azure_process_template: project.templateName,
            }),
        },
        true
      );

      if (!res.data.success) {
        throw new Error(res.data.error || "Failed to create project");
      }

      const createdProject = res.data.project;

      // Store project info in localStorage for dashboard navigation
      localStorage.setItem("project_id", createdProject.id);
      localStorage.setItem("selected_project_name", project.name);

      // Handle both new project creation and existing project navigation
      if (res.data.already_exists) {
        console.log("Project already exists, navigating to existing project");
      } else {
        console.log("Project created successfully, navigating to dashboard");
      }

      // Navigate to dashboard
      router.push("/dashboard");
    } catch (error: any) {
      console.error("Failed to create/navigate to project:", error);
      alert(
        `Failed to create/navigate to project: ${
          error.message || "Unknown error"
        }`
      );
    } finally {
      setCreatingProject(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "expired":
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case "azure":
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center shadow-lg">
            <Cloud className="w-4 h-4 text-white" />
          </div>
        );
      case "jira":
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white text-sm font-bold">J</span>
          </div>
        );
      default:
        return (
          <div className="w-8 h-8 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-lg flex items-center justify-center shadow-lg">
            <Settings className="w-4 h-4 text-white" />
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Integrations</h2>
          <p className="text-muted-foreground mt-1">
            Connect your DevOps platforms to import projects and sync work items
          </p>
        </div>
        {accounts.length > 0 && (
          <div className="flex gap-3">
            {!hasAzureIntegration && (
              <button
                onClick={() => setShowAzureForm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white rounded-md transition-all duration-300 font-medium shadow-lg hover:shadow-xl"
              >
                <Plus className="w-4 h-4" />
                Add Azure DevOps
              </button>
            )}
            {!hasJiraIntegration && (
              <button
                onClick={() => setShowJiraForm(true)}
                className="flex items-center gap-2 px-4 py-2 border-2 border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 text-gray-900 dark:text-white rounded-md transition-all duration-300 font-medium"
              >
                <Plus className="w-4 h-4" />
                Add Jira
              </button>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-destructive/10 border border-destructive/20 rounded-lg p-4"
        >
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-destructive" />
            <span className="text-destructive">{error}</span>
            <button
              onClick={() => dispatch(clearError())}
              className="ml-auto text-destructive hover:text-destructive/80"
            >
              ×
            </button>
          </div>
        </motion.div>
      )}

      {/* Integration Accounts */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : accounts.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12 bg-muted/50 rounded-xl border-2 border-dashed border-border"
          >
            <Shield className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No integrations configured
            </h3>
            <p className="text-muted-foreground mb-6">
              Connect your Azure DevOps or Jira accounts to start importing
              projects
            </p>
            <div className="flex gap-3 justify-center">
              {!hasAzureIntegration && (
                <button
                  onClick={() => setShowAzureForm(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white rounded-md transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  <Plus className="w-4 h-4" />
                  Connect Azure DevOps
                </button>
              )}
              {!hasJiraIntegration && (
                <button
                  onClick={() => setShowJiraForm(true)}
                  className="flex items-center gap-2 px-4 py-2 border-2 border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 text-gray-900 dark:text-white rounded-md transition-all duration-300"
                >
                  <Plus className="w-4 h-4" />
                  Connect Jira
                </button>
              )}
            </div>
          </motion.div>
        ) : (
          <div className="grid gap-4">
            {accounts.map((account, index) => (
              <motion.div
                key={account.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-2 border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/30 transition-all duration-300 rounded-xl p-6"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getProviderIcon(account.provider)}
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {account.displayName}
                        </h3>
                        {getStatusIcon(account.status)}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                        <span>
                          {account.provider === "azure"
                            ? "Azure DevOps"
                            : "Jira Cloud"}
                        </span>
                        <span>•</span>
                        <span>
                          Connected{" "}
                          {new Date(account.savedAt).toLocaleDateString()}
                        </span>
                        {account.metadata.organization && (
                          <>
                            <span>•</span>
                            <span>{account.metadata.organization}</span>
                          </>
                        )}
                        {account.metadata.domain && (
                          <>
                            <span>•</span>
                            <span>{account.metadata.domain}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleFetchProjects(account.provider)}
                      disabled={fetchingProjects[account.provider]}
                      className="flex items-center gap-2 px-3 py-2 text-sm bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] hover:from-[#E603EB]/90 hover:to-[#8B5FBF]/90 text-white rounded-md transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {fetchingProjects[account.provider] ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Download className="w-4 h-4" />
                      )}
                      Fetch Projects
                    </button>

                    <button
                      onClick={() => handleTestConnection(account.id)}
                      disabled={testingConnection[account.id]}
                      className="flex items-center gap-2 px-3 py-2 text-sm border-2 border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 transition-all duration-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {testingConnection[account.id] ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <TestTube className="w-4 h-4" />
                      )}
                      Test
                    </button>

                    {account.metadata.baseUrl && (
                      <a
                        href={account.metadata.baseUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-3 py-2 text-sm border-2 border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 transition-all duration-300 rounded-md"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Open
                      </a>
                    )}

                    <button
                      onClick={() => handleDeleteAccount(account)}
                      className="flex items-center gap-2 px-3 py-2 text-sm text-destructive border border-destructive/20 rounded-md hover:bg-destructive/10 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>

                {/* Scopes */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-medium">Permissions:</span>
                    <div className="flex gap-2">
                      {account.scopes.map((scope) => (
                        <span
                          key={scope}
                          className="px-2 py-1 bg-[#E603EB]/10 text-[#E603EB] rounded text-xs font-medium"
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Projects Section */}
      {externalProjects.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-foreground">
                Available Projects
              </h3>
              <p className="text-muted-foreground text-sm mt-1">
                Click on any project to create or navigate to it
              </p>
            </div>
            <button
              onClick={() => dispatch(clearExternalProjects())}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear
            </button>
          </div>

          {/* Success Message */}
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <p className="text-sm font-medium text-green-700 dark:text-green-400">
                Successfully connected! Found {externalProjects.length} projects
              </p>
            </div>
          </div>

          {/* Project Selection with Folder Icons */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Select Project to Import
            </label>
            <div className="grid gap-3 max-h-96 overflow-y-auto">
              {externalProjects.map((project, index) => (
                <motion.div
                  key={project.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-300 ${
                    creatingProject === project.id
                      ? "border-[#E603EB] bg-[#E603EB]/10 dark:bg-[#E603EB]/20"
                      : "border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/50 hover:bg-[#E603EB]/5"
                  }`}
                  onClick={() => handleCreateOrNavigateToProject(project)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <Folder className="w-6 h-6 text-[#E603EB]" />
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-gray-900 dark:text-white text-base">
                          {project.name}
                        </div>
                        {project.description && (
                          <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            {project.description}
                          </div>
                        )}

                        {/* Project metadata */}
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          {project.key && (
                            <div className="flex items-center gap-1">
                              <span className="font-medium">Key:</span>
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                                {project.key}
                              </span>
                            </div>
                          )}
                          {project.templateName && (
                            <div className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              <span className="px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 rounded">
                                {project.templateName}
                              </span>
                            </div>
                          )}
                          <div className="flex items-center gap-1">
                            <Cloud className="w-3 h-3" />
                            <span className="capitalize">
                              {(project as any).provider}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {project.url && (
                        <a
                          href={project.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="flex items-center gap-1 px-3 py-2 text-sm border-2 border-[#E603EB]/20 hover:border-[#E603EB]/40 hover:bg-[#E603EB]/5 transition-all duration-300 rounded-md"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Open
                        </a>
                      )}

                      <div className="flex items-center gap-2">
                        {creatingProject === project.id && (
                          <Loader2 className="w-4 h-4 animate-spin text-[#E603EB]" />
                        )}
                        {creatingProject !== project.id && (
                          <CheckCircle className="w-5 h-5 text-[#E603EB]" />
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Click on any project to create or navigate to it in your dashboard
            </p>
          </div>
        </motion.div>
      )}

      {/* Integration Forms */}
      {showAzureForm && (
        <AzureIntegrationForm
          onClose={() => setShowAzureForm(false)}
          onSuccess={() => {
            setShowAzureForm(false);
            dispatch(fetchIntegrationAccounts());
          }}
        />
      )}

      {showJiraForm && (
        <JiraIntegrationForm
          onClose={() => setShowJiraForm(false)}
          onSuccess={() => {
            setShowJiraForm(false);
            dispatch(fetchIntegrationAccounts());
          }}
        />
      )}

      {accountPendingDeletion && (
        <BaseModal
          isOpen={!!accountPendingDeletion}
          onClose={closeDeleteModal}
          size="sm"
          icon={
            <div className="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
          }
          title="Delete integration"
          description={
            <>
              Deleting <strong>{accountPendingDeletion.displayName}</strong> will remove the{" "}
              {accountPendingDeletion.provider === "azure" ? "Azure DevOps" : "Jira"} connection and all related data.
            </>
          }
          footer={
            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={closeDeleteModal}
                disabled={!!deletingAccountId}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDeleteAccount}
                disabled={!!deletingAccountId}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {deletingAccountId ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete integration
                  </>
                )}
              </button>
            </div>
          }
        >
          <div className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
            <p>
              This action will also delete every project created through this integration along with their analysis history and AI-generated work items.
            </p>
            <ul className="list-disc list-inside space-y-1 text-gray-500 dark:text-gray-400">
              <li>Associated Saramsa projects</li>
              <li>Stored analysis results</li>
              <li>Work items generated from those projects</li>
            </ul>
            <p className="text-red-600 dark:text-red-400 font-medium">This cannot be undone.</p>
          </div>
        </BaseModal>
      )}
    </div>
  );
}
