"use client";

import { useEffect, useMemo, useState } from "react";
import { Settings, UserRound, PlugZap, Building2, Bot } from 'lucide-react';
import { apiRequest } from "@/lib/apiRequest";
import { IntegrationsPage } from "@/components/ui/settings/IntegrationsPage";
import { WorkspacePage } from "@/components/ui/settings/WorkspacePage";
import { PromptSettingsPage } from "@/components/ui/settings/PromptSettingsPage";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/useAuth";
import {
  createStripeBillingPortalSession,
  createStripeCheckoutSession,
  getStripeSubscriptionStatus,
  type SubscriptionStatus,
} from "@/lib/billingService";

type Profile = { email?: string };

export default function SettingsPage() {
  const { user } = useAuth();
  const isSuperadmin = !!user?.is_staff;
  const [activeTab, setActiveTab] = useState<"profile" | "workspace" | "integrations" | "prompts">("profile");
  const [profile, setProfile] = useState<Profile>({});
  const [billing, setBilling] = useState<SubscriptionStatus | null>(null);
  const [billingLoading, setBillingLoading] = useState<boolean>(true);
  const [billingError, setBillingError] = useState<string | null>(null);
  const [billingActionLoading, setBillingActionLoading] = useState<"checkout" | "portal" | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const tab = new URLSearchParams(window.location.search).get("tab");
      if (tab === "integrations") {
        setActiveTab("integrations");
      } else if (tab === "workspace") {
        setActiveTab("workspace");
      } else if (tab === "prompts" && isSuperadmin) {
        setActiveTab("prompts");
      }
    }
  }, [isSuperadmin]);

  const tabs = useMemo(
    () => {
      const list: Array<{ key: "profile" | "workspace" | "integrations" | "prompts"; label: string; Icon: typeof UserRound }> = [
        { key: "profile", label: "Profile", Icon: UserRound },
        { key: "workspace", label: "Workspace", Icon: Building2 },
        { key: "integrations", label: "Integrations", Icon: PlugZap },
      ];
      if (isSuperadmin) {
        list.push({ key: "prompts", label: "Prompts", Icon: Bot });
      }
      return list;
    },
    [isSuperadmin],
  );

  useEffect(() => {
    (async () => {
      try {
        const me = await apiRequest("get", "/auth/me/", undefined, true);
        const payload = me.data?.data || me.data || {};
        setProfile({
          email: payload.email || "",
        });
      } catch {
        setProfile({});
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        setBillingLoading(true);
        setBillingError(null);
        const status = await getStripeSubscriptionStatus();
        setBilling(status);
      } catch (e: any) {
        setBillingError(e?.message || "Failed to load billing status.");
      } finally {
        setBillingLoading(false);
      }
    })();
  }, []);

  const handleStartSubscription = async () => {
    try {
      setBillingActionLoading("checkout");
      const data = await createStripeCheckoutSession();
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (e: any) {
      setBillingError(e?.message || "Failed to start checkout.");
    } finally {
      setBillingActionLoading(null);
    }
  };

  const handleOpenBillingPortal = async () => {
    try {
      setBillingActionLoading("portal");
      const data = await createStripeBillingPortalSession();
      if (data?.portal_url) {
        window.location.href = data.portal_url;
      }
    } catch (e: any) {
      setBillingError(e?.message || "Failed to open billing portal.");
    } finally {
      setBillingActionLoading(null);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-background text-foreground">
      <div className="min-h-full max-w-4xl mx-auto space-y-6 p-6">
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
          <div className={`grid gap-2 ${tabs.length === 4 ? "grid-cols-4" : "grid-cols-3"}`}>
            {tabs.map(({ key, label, Icon }) => (
              <Button
                key={key}
                variant="ghost"
                className={`h-10 text-sm font-medium transition-colors ${
                  activeTab === key
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                }`}
                onClick={() => setActiveTab(key)}
              >
                <span className="flex items-center gap-2">
                  <span
                    className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to text-white transition-opacity ${
                      activeTab === key ? "opacity-100" : "opacity-60"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </span>
                  {label}
                </span>
              </Button>
            ))}
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
                  <p className="text-muted-foreground mb-1">Email</p>
                  <p className="font-medium text-foreground">{profile.email || "-"}</p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-border bg-secondary/80 dark:border-border/60 dark:bg-background/60 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-foreground">Subscription Billing</p>
                  <p className="text-xs text-muted-foreground">
                    {billingLoading
                      ? "Loading billing status..."
                      : billing?.is_subscribed
                      ? `Active (${billing.subscription_status ?? "subscribed"})`
                      : `Not active (${billing?.subscription_status || "inactive"})`}
                  </p>
                </div>
                <div className="flex gap-2">
                  {!billing?.is_subscribed && (
                    <Button
                      variant="saramsa"
                      size="sm"
                      onClick={handleStartSubscription}
                      disabled={billingActionLoading !== null}
                    >
                      {billingActionLoading === "checkout" ? "Starting..." : "Start Subscription"}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleOpenBillingPortal}
                    disabled={billingActionLoading !== null}
                  >
                    {billingActionLoading === "portal" ? "Opening..." : "Manage Billing"}
                  </Button>
                </div>
              </div>
              {billingError && (
                <p className="text-xs text-red-600 dark:text-red-400">{billingError}</p>
              )}
            </div>
          </div>
        )}

        {activeTab === "workspace" && <WorkspacePage />}
        {activeTab === "integrations" && <IntegrationsPage />}
        {activeTab === "prompts" && isSuperadmin && <PromptSettingsPage />}
      </div>
    </div>
  );
}
