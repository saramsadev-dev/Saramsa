"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { motion } from "framer-motion";
import {
  Download,
  Globe,
  ArrowRight,
  CheckCircle,
  Shield,
} from "lucide-react";
import type { AppDispatch, RootState } from "@/store/store";
import { fetchIntegrationAccounts } from "@/store/features/integrations/integrationsSlice";

interface DashboardPlatformSelectionProps {
  onPlatformSelect: (platform: "azure" | "jira") => void;
  projectId: string;
}

export function DashboardPlatformSelection({
  onPlatformSelect,
  projectId,
}: DashboardPlatformSelectionProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { accounts } = useSelector((state: RootState) => state.integrations);

  useEffect(() => {
    // Fetch existing integrations to check status
    dispatch(fetchIntegrationAccounts());
  }, [dispatch]);

  // Check if integrations already exist
  const hasAzureIntegration = accounts.some(
    (account) => account.provider === "azure"
  );
  const hasJiraIntegration = accounts.some(
    (account) => account.provider === "jira"
  );

  const platforms = [
    {
      id: "azure",
      name: "Azure DevOps",
      description: hasAzureIntegration
        ? "Azure DevOps integration is already configured. You can reconfigure or link to a different organization."
        : "Connect your project to Azure DevOps for seamless work item creation",
      icon: <Download className="w-8 h-8" />,
      color: "from-[#E603EB] to-[#8B5FBF]",
      features: [
        "AI-Powered Analysis",
        "Auto Work Item Creation",
        "Real-time Sync",
        "Team Assignment",
      ],
      status: hasAzureIntegration ? "configured" : "available",
    },
    {
      id: "jira",
      name: "Jira",
      description: hasJiraIntegration
        ? "Jira integration is already configured. You can reconfigure or link to a different workspace."
        : "Integrate your project with Jira for comprehensive project management",
      icon: <Globe className="w-8 h-8" />,
      color: "from-saramsa-gradient-from to-saramsa-gradient-to",
      features: [
        "Dynamic Project Detection",
        "AI-Powered Issue Classification",
        "Automatic Priority Assignment",
        "Rich Issue Details",
      ],
      status: hasJiraIntegration ? "configured" : "available",
    },
  ];

  return (
    <div className="p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-3"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Choose Your Integration Platform
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Connect this project to Azure DevOps or Jira to enable automated work item creation and synchronization.
          </p>
        </motion.div>

        {/* Platform Options */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="space-y-3"
        >
          {platforms.map((platform, index) => (
            <motion.div
              key={platform.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
            >
              <div
                className={`relative bg-white dark:bg-gray-800 border-2 rounded-xl p-5 transition-all duration-300 cursor-pointer hover:border-[#E603EB]/50 hover:shadow-lg ${
                  platform.status === "configured"
                    ? "border-green-300 dark:border-green-600 bg-green-50/30 dark:bg-green-900/10"
                    : "border-gray-200 dark:border-gray-700"
                }`}
                onClick={() => onPlatformSelect(platform.id as "azure" | "jira")}
              >
                {platform.status === "configured" && (
                  <div className="absolute top-3 right-3">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Configured
                    </span>
                  </div>
                )}

                <div className="flex items-start gap-4">
                  <div
                    className={`w-12 h-12 bg-gradient-to-br ${platform.color} rounded-lg flex items-center justify-center text-white flex-shrink-0`}
                  >
                    {platform.icon}
                  </div>

                  <div className="flex-1 space-y-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {platform.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {platform.description}
                      </p>
                    </div>

                    {/* Features */}
                    <div className="flex flex-wrap gap-2">
                      {platform.features.map((feature) => (
                        <span
                          key={feature}
                          className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>

                  <ArrowRight className="w-5 h-5 text-gray-400 flex-shrink-0 mt-1" />
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Security Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-center space-y-2 pt-4"
        >
          <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent" />
          <div className="flex items-center justify-center gap-2">
            <Shield className="w-4 h-4 text-gray-500" />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Your credentials are encrypted and securely stored
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
