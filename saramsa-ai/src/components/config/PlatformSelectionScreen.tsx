"use client";

import { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { motion } from "framer-motion";
import {
  Download,
  Globe,
  Zap,
  Shield,
  ArrowRight,
  CheckCircle,
} from "lucide-react";
import type { AppDispatch, RootState } from "@/store/store";
import { fetchIntegrationAccounts } from "@/store/features/integrations/integrationsSlice";

interface PlatformSelectionScreenProps {
  onPlatformSelect: (platform: "azure" | "jira") => void;
  onSkipConfig?: () => void;
}

export function PlatformSelectionScreen({
  onPlatformSelect,
  onSkipConfig,
}: PlatformSelectionScreenProps) {
  const dispatch = useDispatch<AppDispatch>();
  const { accounts } = useSelector((state: RootState) => state.integrations);
  const [selectedPlatform, setSelectedPlatform] = useState<
    "azure" | "jira" | null
  >(null);

  useEffect(() => {
    // Integration accounts are now fetched at the parent level
    // This component just reads from Redux state
  }, []);

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
        ? "Azure DevOps integration is already configured"
        : "Connect your Azure DevOps organization for seamless work item creation",
      icon: <Download className="w-8 h-8" />,
      color: "from-[#E603EB] to-[#8B5FBF]",
      features: [
        "AI-Powered Analysis",
        "Auto Work Item Creation",
        "Real-time Sync",
        "Team Assignment",
      ],
      status: hasAzureIntegration ? "configured" : "available",
      comingSoon: false,
    },
    {
      id: "jira",
      name: "Jira",
      description: hasJiraIntegration
        ? "Jira integration is already configured"
        : "Integrate with Jira for comprehensive project management",
      icon: <Globe className="w-8 h-8" />,
      color: "from-saramsa-gradient-from to-saramsa-gradient-to",
      features: [
        "Dynamic Project Detection",
        "AI-Powered Issue Classification",
        "Automatic Priority Assignment",
        "Rich Issue Details",
      ],
      status: hasJiraIntegration ? "configured" : "available",
      comingSoon: false,
    },
  ];

  const handlePlatformSelect = (platform: "azure" | "jira") => {
    setSelectedPlatform(platform);
    // Add a small delay for animation
    setTimeout(() => {
      onPlatformSelect(platform);
    }, 300);
  };

  return (
    <div className="h-full bg-background overflow-hidden">
      <div className="h-[calc(100vh-65px)] flex flex-col">
        {/* Left Panel - Platform Selection (60% on desktop, full width on mobile) */}
        <motion.div
          className="flex-1 w-full flex items-center justify-center bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm order-2 lg:order-1"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <div className="max-w-md space-y-8">
            {/* Header */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center space-y-4"
            >
              <div className="flex items-center gap-4 justify-center">
                <div className="w-10 h-10 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-xl flex items-center justify-center shadow-lg">
                  <Zap className="w-4 h-4 text-white" />
                </div>
                <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  Choose Your Platform
                </h1>
              </div>

              <div className="space-y-2">
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                  Integrate with Azure DevOps or Jira to unlock automated work
                  item creation and project management.
                </p>
              </div>
            </motion.div>

            {/* Platform Options */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 gap-3">
                {platforms.map((platform, index) => (
                  <motion.div
                    key={platform.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: 0.2 + index * 0.1 }}
                  >
                    <div
                      className={`relative bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border-2 rounded-xl p-6 transition-all duration-300 ${
                        selectedPlatform === platform.id
                          ? "border-[#E603EB] shadow-lg"
                          : platform.status === "configured"
                          ? "border-green-300 dark:border-green-600 bg-green-50/50 dark:bg-green-900/20"
                          : platform.comingSoon
                          ? "border-gray-300 dark:border-gray-600 opacity-50"
                          : "border-gray-200 dark:border-gray-700 hover:border-[#E603EB]/50 hover:shadow-lg cursor-pointer"
                      }`}
                      onClick={() =>
                        !platform.comingSoon &&
                        handlePlatformSelect(platform.id as "azure" | "jira")
                      }
                    >
                      {platform.status === "configured" && (
                        <div className="absolute top-3 right-3">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Configured
                          </span>
                        </div>
                      )}
                      {platform.comingSoon && (
                        <div className="absolute top-3 right-3">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400">
                            Coming Soon
                          </span>
                        </div>
                      )}

                      <div className="flex items-start gap-4">
                        <div
                          className={`w-12 h-12 bg-gradient-to-br ${platform.color} rounded-lg flex items-center justify-center text-white`}
                        >
                          {platform.icon}
                        </div>

                        <div className="flex-1 space-y-3">
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              {platform.name}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm">
                              {platform.description}
                            </p>
                          </div>
                        </div>

                        {!platform.comingSoon &&
                          platform.status !== "configured" && (
                            <ArrowRight className="w-5 h-5 text-gray-400" />
                          )}
                        {platform.status === "configured" && (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Skip Configuration Option */}
            {onSkipConfig && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="text-center"
              >
                <button
                  onClick={onSkipConfig}
                  className="text-sm text-muted-foreground hover:text-saramsa-brand transition-colors underline"
                >
                  Skip configuration and go to dashboard
                </button>
              </motion.div>
            )}

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
                  Your credentials are encrypted and stored for future use.
                </p>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
