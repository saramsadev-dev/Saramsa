"use client";

import { useEffect, useState } from "react";
import { Bot, Loader2, RotateCcw, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/apiRequest";

type PromptOverride = {
  id: string;
  prompt_type: string;
  scope: string;
  organizationId?: string | null;
  content: string;
};

type OrganizationOption = {
  id: string;
  name: string;
};

type PromptSettingsPayload = {
  available_prompt_types: string[];
  organizations: OrganizationOption[];
  platform_prompts: Record<string, PromptOverride>;
  organization_prompts: Record<string, PromptOverride>;
  selected_organization_id?: string | null;
};

export function PromptSettingsPage() {
  const [loading, setLoading] = useState(true);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PromptSettingsPayload | null>(null);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string>("");
  const [platformDrafts, setPlatformDrafts] = useState<Record<string, string>>({});
  const [organizationDrafts, setOrganizationDrafts] = useState<Record<string, string>>({});

  const loadData = async (organizationId?: string) => {
    try {
      setLoading(true);
      setError(null);
      const query = organizationId ? `?organization_id=${encodeURIComponent(organizationId)}` : "";
      const res = await apiRequest("get", `/auth/admin/prompts/${query}`, undefined, true);
      const payload: PromptSettingsPayload = res.data?.data;
      setData(payload);
      setSelectedOrganizationId(payload.selected_organization_id || organizationId || "");
      setPlatformDrafts(
        Object.fromEntries(
          payload.available_prompt_types.map((type) => [type, payload.platform_prompts?.[type]?.content || ""]),
        ),
      );
      setOrganizationDrafts(
        Object.fromEntries(
          payload.available_prompt_types.map((type) => [type, payload.organization_prompts?.[type]?.content || ""]),
        ),
      );
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load prompt settings.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const savePrompt = async (scope: "platform" | "organization", promptType: string) => {
    const key = `${scope}:${promptType}`;
    const content = scope === "platform" ? platformDrafts[promptType] : organizationDrafts[promptType];

    try {
      setSavingKey(key);
      setError(null);
      await apiRequest(
        "post",
        "/auth/admin/prompts/",
        {
          scope,
          prompt_type: promptType,
          content,
          organization_id: scope === "organization" ? selectedOrganizationId : undefined,
        },
        true,
      );
      await loadData(scope === "organization" ? selectedOrganizationId : selectedOrganizationId || undefined);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to save prompt.");
    } finally {
      setSavingKey(null);
    }
  };

  const resetPrompt = async (scope: "platform" | "organization", promptType: string) => {
    const key = `reset:${scope}:${promptType}`;
    try {
      setSavingKey(key);
      setError(null);
      const suffix =
        `?scope=${encodeURIComponent(scope)}` +
        `&prompt_type=${encodeURIComponent(promptType)}` +
        (scope === "organization" ? `&organization_id=${encodeURIComponent(selectedOrganizationId)}` : "");
      await apiRequest("delete", `/auth/admin/prompts/${suffix}`, undefined, true);
      await loadData(scope === "organization" ? selectedOrganizationId : selectedOrganizationId || undefined);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to reset prompt.");
    } finally {
      setSavingKey(null);
    }
  };

  const renderPromptEditor = (scope: "platform" | "organization", promptType: string) => {
    const drafts = scope === "platform" ? platformDrafts : organizationDrafts;
    const setDrafts = scope === "platform" ? setPlatformDrafts : setOrganizationDrafts;
    const value = drafts[promptType] || "";
    const saveKey = `${scope}:${promptType}`;
    const resetKey = `reset:${scope}:${promptType}`;

    return (
      <div key={`${scope}-${promptType}`} className="rounded-lg border border-border bg-secondary/80 dark:border-border/60 dark:bg-background/60 p-4 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-foreground">{promptType}</p>
            <p className="text-xs text-muted-foreground capitalize">{scope} scope</p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="h-9 px-3"
              disabled={savingKey !== null || (scope === "organization" && !selectedOrganizationId)}
              onClick={() => resetPrompt(scope, promptType)}
            >
              {savingKey === resetKey ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
            </Button>
            <Button
              variant="saramsa"
              className="h-9 px-3 flex items-center gap-2"
              disabled={savingKey !== null || (scope === "organization" && !selectedOrganizationId)}
              onClick={() => savePrompt(scope, promptType)}
            >
              {savingKey === saveKey ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save
            </Button>
          </div>
        </div>
        <textarea
          value={value}
          onChange={(e) => setDrafts((current) => ({ ...current, [promptType]: e.target.value }))}
          rows={10}
          className="w-full rounded-lg border border-border bg-background px-3 py-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
          placeholder={`Override ${promptType} prompt for ${scope} scope`}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="bg-card rounded-xl border border-border p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-2">AI Prompt Settings</h2>
          <p className="text-muted-foreground text-sm">Manage platform-wide and tenant-specific prompt overrides.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-xl bg-secondary px-3 py-2 text-sm text-foreground">
          <Bot className="h-4 w-4" />
          <span>Superadmin only</span>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="space-y-3">
        <p className="text-sm font-medium text-foreground">Tenant-specific target</p>
        <select
          value={selectedOrganizationId}
          onChange={(e) => {
            const value = e.target.value;
            setSelectedOrganizationId(value);
            loadData(value || undefined);
          }}
          className="h-10 min-w-[280px] rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Select tenant workspace</option>
          {data.organizations.map((organization) => (
            <option key={organization.id} value={organization.id}>
              {organization.name}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">Platform-wide prompts</h3>
        {data.available_prompt_types.map((promptType) => renderPromptEditor("platform", promptType))}
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">Tenant-specific prompts</h3>
        {selectedOrganizationId ? (
          data.available_prompt_types.map((promptType) => renderPromptEditor("organization", promptType))
        ) : (
          <div className="rounded-lg border border-dashed border-border px-4 py-8 text-sm text-muted-foreground">
            Select a workspace to manage tenant-specific prompt overrides.
          </div>
        )}
      </div>
    </div>
  );
}
