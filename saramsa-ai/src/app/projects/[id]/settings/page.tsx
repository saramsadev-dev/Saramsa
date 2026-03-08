"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiRequest } from "@/lib/apiRequest";
import { decryptProjectId, isValidEncryptedId, encryptProjectId } from "@/lib/encryption";
import { ArrowLeft, Loader2, Shield } from 'lucide-react';

type RoleEntry = {
  user_id: string;
  role: "viewer" | "editor" | "admin";
  is_owner?: boolean;
  updated_at?: string;
};

export default function ProjectSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const [projectId, setProjectId] = useState<string | null>(null);
  const [roles, setRoles] = useState<RoleEntry[]>([]);
  const [currentRole, setCurrentRole] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newUserId, setNewUserId] = useState("");
  const [newRole, setNewRole] = useState<RoleEntry["role"]>("viewer");

  useEffect(() => {
    const encryptedId = params.id as string;
    if (!encryptedId) {
      setError("No project ID provided");
      setLoading(false);
      return;
    }

    try {
      if (isValidEncryptedId(encryptedId)) {
        setProjectId(decryptProjectId(encryptedId));
      } else {
        setProjectId(encryptedId);
      }
    } catch (err) {
      console.error("Failed to decrypt project ID:", err);
      setError("Invalid project ID");
      setLoading(false);
    }
  }, [params.id]);

  const fetchRoles = async (resolvedProjectId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiRequest("get", `/integrations/projects/${resolvedProjectId}/roles/`, undefined, true);
      const payload = response?.data?.data || {};
      setRoles(Array.isArray(payload.roles) ? payload.roles : []);
      setCurrentRole(payload.current_user_role || null);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Failed to load roles.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!projectId) return;
    fetchRoles(projectId);
  }, [projectId]);

  const handleSaveRole = async () => {
    if (!projectId) return;
    if (!newUserId.trim()) {
      setError("User ID is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await apiRequest(
        "post",
        `/integrations/projects/${projectId}/roles/`,
        { user_id: newUserId.trim(), role: newRole },
        true
      );
      setNewUserId("");
      await fetchRoles(projectId);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Failed to update role.";
      setError(detail);
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveRole = async (userId: string) => {
    if (!projectId) return;
    setSaving(true);
    setError(null);
    try {
      await apiRequest(
        "delete",
        `/integrations/projects/${projectId}/roles/`,
        { user_id: userId },
        true
      );
      await fetchRoles(projectId);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Failed to remove role.";
      setError(detail);
    } finally {
      setSaving(false);
    }
  };

  const backToDashboard = () => {
    if (!projectId) {
      router.push("/projects");
      return;
    }
    try {
      const encrypted = encryptProjectId(projectId);
      router.push(`/projects/${encrypted}/dashboard`);
    } catch (err) {
      router.push(`/projects/${projectId}/dashboard`);
    }
  };

  const sortedRoles = useMemo(() => {
    return [...roles].sort((a, b) => {
      if (a.is_owner) return -1;
      if (b.is_owner) return 1;
      return a.user_id.localeCompare(b.user_id);
    });
  }, [roles]);

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to text-white shadow-lg">
                <Shield className="h-6 w-6" />
              </span>
              <div>
                <h1 className="text-3xl font-bold text-foreground">Project Settings</h1>
                <p className="text-sm text-muted-foreground">Manage project roles and permissions</p>
              </div>
            </div>
            {currentRole && (
              <p className="text-xs text-muted-foreground">Your role: {currentRole}</p>
            )}
          </div>
          <Button onClick={backToDashboard} variant="outline" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>

        <div className="bg-card rounded-xl border border-border p-6 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground">Roles</h2>
            <p className="text-sm text-muted-foreground">
              Add team members by user ID and assign a role.
            </p>
          </div>

          {error && (
            <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg border border-red-200/70 dark:border-red-800/60">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-foreground mb-2">User ID</label>
              <Input
                value={newUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                placeholder="user_123 or uuid"
                className="h-10 bg-background text-foreground"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Role</label>
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value as RoleEntry["role"])}
                className="h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground"
              >
                <option value="viewer">Viewer</option>
                <option value="editor">Editor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSaveRole} disabled={saving || loading}>
              {saving ? "Saving..." : "Add / Update Role"}
            </Button>
          </div>

          <div className="border-t border-border pt-4">
            <h3 className="text-sm font-semibold text-foreground mb-3">Current Access</h3>
            {loading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading roles...
              </div>
            ) : sortedRoles.length === 0 ? (
              <p className="text-sm text-muted-foreground">No role assignments found.</p>
            ) : (
              <div className="space-y-2">
                {sortedRoles.map((entry) => (
                  <div
                    key={`${entry.user_id}-${entry.role}`}
                    className="flex items-center justify-between rounded-lg border border-border/60 bg-secondary/40 px-3 py-2"
                  >
                    <div className="text-sm">
                      <div className="font-medium text-foreground">{entry.user_id}</div>
                      <div className="text-xs text-muted-foreground">
                        {entry.is_owner ? "Owner" : entry.role}
                      </div>
                    </div>
                    {!entry.is_owner && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={saving}
                        onClick={() => handleRemoveRole(entry.user_id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

