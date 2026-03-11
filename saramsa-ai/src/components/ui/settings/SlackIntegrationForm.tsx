"use client";

import { useState } from "react";
import { Loader2, MessageSquare } from "lucide-react";
import { apiRequest } from "@/lib/apiRequest";
import { BaseModal } from "@/components/ui/modals/BaseModal";
import { Button } from "@/components/ui/button";

interface SlackIntegrationFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function SlackIntegrationForm({ onClose, onSuccess }: SlackIntegrationFormProps) {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    try {
      const res = await apiRequest("get", "/integrations/slack/oauth/start/", undefined, true);
      const oauthUrl = res.data?.data?.oauth_url;
      if (!oauthUrl) {
        throw new Error("Failed to get OAuth URL from server");
      }
      // Redirect to Slack OAuth page
      window.location.href = oauthUrl;
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to start Slack connection");
      setConnecting(false);
    }
  };

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      size="sm"
      icon={
        <div className="w-12 h-12 rounded-2xl bg-saramsa-brand/10 flex items-center justify-center">
          <MessageSquare className="w-6 h-6 text-saramsa-brand" />
        </div>
      }
      title="Connect Slack"
      description="Install the Saramsa bot to your Slack workspace to import feedback from channels."
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={connecting}>
            Cancel
          </Button>
          <Button onClick={handleConnect} disabled={connecting} variant="saramsa">
            {connecting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Connecting...
              </>
            ) : (
              "Connect to Slack"
            )}
          </Button>
        </div>
      }
    >
      <div className="space-y-3 text-sm text-muted-foreground">
        <p>This will redirect you to Slack to authorize the bot. The bot will request these permissions:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Read messages from public and private channels</li>
          <li>List channels in your workspace</li>
          <li>Read user profile information</li>
        </ul>
        {error && (
          <p className="text-red-600 dark:text-red-400 font-medium">{error}</p>
        )}
      </div>
    </BaseModal>
  );
}
