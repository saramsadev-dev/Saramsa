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
      color: "from-saramsa-gradient-from to-saramsa-gradient-to",
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
          <h2 className="text-xl font-semibold text-foreground dark:text-foreground">
            Choose Your Integration Platform
          </h2>
          <p className="text-sm text-muted-foreground dark:text-muted-foreground">
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
                className={`relative bg-card/90 dark:bg-card/95 border-2 rounded-xl p-5 transition-all duration-300 cursor-pointer hover:border-saramsa-brand/40 hover:shadow-lg ${
                  platform.status === "configured"
                    ? "border-green-300 dark:border-green-600 bg-green-50/30 dark:bg-green-900/10"
                    : "border-border/60 dark:border-border/60"
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
                    className={`w-12 h-12 bg-gradient-to-br ${platform.color} rounded-xl flex items-center justify-center text-white flex-shrink-0`}
                  >
                    {platform.icon}
                  </div>

                  <div className="flex-1 space-y-2">
                    <div>
                      <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
                        {platform.name}
                      </h3>
                      <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                        {platform.description}
                      </p>
                    </div>

                    {/* Features */}
                    <div className="flex flex-wrap gap-2">
                      {platform.features.map((feature) => (
                        <span
                          key={feature}
                          className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-secondary/40 text-muted-foreground dark:bg-secondary/40 dark:text-muted-foreground"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>

                  <ArrowRight className="w-5 h-5 text-muted-foreground flex-shrink-0 mt-1" />
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
          <div className="w-full h-px bg-gradient-to-r from-transparent via-border/70 to-transparent" />
          <div className="flex items-center justify-center gap-2">
            <Shield className="w-4 h-4 text-muted-foreground" />
            <p className="text-xs text-muted-foreground dark:text-muted-foreground">
              Your credentials are encrypted and securely stored
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
