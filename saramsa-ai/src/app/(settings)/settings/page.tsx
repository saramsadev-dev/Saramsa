"use client";

import { useEffect, useState } from "react";
import { Settings, UserRound, PlugZap } from 'lucide-react';
import { apiRequest } from "@/lib/apiRequest";
import { IntegrationsPage } from "@/components/ui/settings/IntegrationsPage";
import { Button } from "@/components/ui/button";

type Profile = { email?: string; username?: string };

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"profile" | "integrations">("profile");
  const [profile, setProfile] = useState<Profile>({});

  useEffect(() => {
    (async () => {
      try {
        const me = await apiRequest("get", "/auth/me/", undefined, true);
        const payload = me.data?.data || me.data || {};
        setProfile({
          email: payload.email || "",
          username: payload.username || "",
        });
      } catch {
        setProfile({});
      }
    })();
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to text-white shadow-lg">
              <Settings className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Settings</h1>
              <p className="text-sm text-muted-foreground">Manage your account and integrations</p>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-xl border border-border p-2">
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="ghost"
              className={`h-10 text-sm font-medium transition-colors ${
                activeTab === "profile"
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
              }`}
              onClick={() => setActiveTab("profile")}
            >
              <span className="flex items-center gap-2">
                <span
                  className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to text-white transition-opacity ${
                    activeTab === "profile" ? "opacity-100" : "opacity-60"
                  }`}
                >
                  <UserRound className="h-4 w-4" />
                </span>
                Profile
              </span>
            </Button>
            <Button
              variant="ghost"
              className={`h-10 text-sm font-medium transition-colors ${
                activeTab === "integrations"
                  ? "bg-secondary text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
              }`}
              onClick={() => setActiveTab("integrations")}
            >
              <span className="flex items-center gap-2">
                <span
                  className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to text-white transition-opacity ${
                    activeTab === "integrations" ? "opacity-100" : "opacity-60"
                  }`}
                >
                  <PlugZap className="h-4 w-4" />
                </span>
                Integrations
              </span>
            </Button>
          </div>
        </div>

        {activeTab === "profile" && (
          <div className="bg-card rounded-xl border border-border p-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-2">Profile Information</h2>
              <p className="text-muted-foreground text-sm">Your account details</p>
            </div>

            <div className="rounded-lg border border-border bg-secondary/80 dark:border-border/60 dark:bg-background/60 p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground mb-1">Username</p>
                  <p className="font-medium text-foreground">{profile.username || "-"}</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">Email</p>
                  <p className="font-medium text-foreground">{profile.email || "-"}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "integrations" && <IntegrationsPage />}
      </div>
    </div>
  );
}
