"use client";

import { useEffect, useState } from "react";
import { Settings, UserRound, PlugZap } from "lucide-react";
import { apiRequest } from "@/lib/apiRequest";
import { IntegrationsPage } from "@/components/ui/settings/IntegrationsPage";

type Profile = { first_name?: string; last_name?: string; email?: string; username?: string };

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"profile" | "integrations">("profile");
  const [profile, setProfile] = useState<Profile>({});
  const [saving, setSaving] = useState(false);
  const [azureStatus, setAzureStatus] = useState<string>("");

  useEffect(() => {
    (async () => {
      try {
        const me = await apiRequest("get", "/auth/me/", undefined, true);
        setProfile(me.data || {});
      } catch {}
      try {
        const integrations = await apiRequest("get", "/integrations/", undefined, true);
        const hasAzure = integrations.data?.accounts?.some((acc: any) => acc.provider === 'azure');
        setAzureStatus(hasAzure ? "Connected" : "Not Connected");
      } catch {
        setAzureStatus("Not Connected");
      }
    })();
  }, []);

  const saveProfile = async () => {
    setSaving(true);
    try {
      await apiRequest(
        "patch",
        "/auth/me/",
        { first_name: profile.first_name, last_name: profile.last_name, email: profile.email },
        true
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="mb-8 space-y-2">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] text-white shadow-lg">
              <Settings className="h-6 w-6" />
            </span>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          </div>
          <p className="text-muted-foreground">Manage your account and integrations</p>
        </div>
        
        <div className="flex gap-2 border-b border-border">
          <button
            className={`px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "profile" 
                ? "border-b-2 border-primary text-foreground" 
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setActiveTab("profile")}
          >
            <span className="flex items-center gap-2">
              <span
                className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] text-white transition-opacity ${
                  activeTab === "profile" ? "opacity-100" : "opacity-60"
                }`}
              >
                <UserRound className="h-4 w-4" />
              </span>
              Profile
            </span>
          </button>
          <button
            className={`px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "integrations" 
                ? "border-b-2 border-primary text-foreground" 
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setActiveTab("integrations")}
          >
            <span className="flex items-center gap-2">
              <span
                className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] text-white transition-opacity ${
                  activeTab === "integrations" ? "opacity-100" : "opacity-60"
                }`}
              >
                <PlugZap className="h-4 w-4" />
              </span>
              Integrations
            </span>
          </button>
        </div>

        {activeTab === "profile" && (
          <div className="bg-card rounded-xl border border-border p-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-2">Profile Information</h2>
              <p className="text-muted-foreground text-sm">Update your personal information</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">First Name</label>
                <input
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  value={profile.first_name || ""}
                  onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                  placeholder="Enter your first name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Last Name</label>
                <input
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  value={profile.last_name || ""}
                  onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                  placeholder="Enter your last name"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-foreground mb-2">Email</label>
                <input
                  type="email"
                  className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                  value={profile.email || ""}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  placeholder="Enter your email address"
                />
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <button
                onClick={saveProfile}
                disabled={saving}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        )}

        {activeTab === "integrations" && <IntegrationsPage />}
      </div>
    </div>
  );
}


