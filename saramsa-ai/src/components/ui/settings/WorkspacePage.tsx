"use client";

import { useEffect, useState } from "react";
import { Building2, Loader2, Plus, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/apiRequest";
import { useAuth } from "@/lib/useAuth";

type WorkspaceMember = {
  membership_id: string;
  user_id: string;
  email?: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: string;
  status: string;
  is_current_user: boolean;
};

type WorkspacePayload = {
  organization?: {
    id: string;
    name: string;
    slug: string;
    description?: string;
  };
  current_membership?: {
    role?: string;
  };
  members: WorkspaceMember[];
};

export function WorkspacePage() {
  const { user } = useAuth();
  const [data, setData] = useState<WorkspacePayload>({ members: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");

  const loadMembers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiRequest("get", "/auth/organizations/members/", undefined, true);
      const payload = res.data?.data || { members: [] };
      setData(payload);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load workspace members.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.active_organization_id) {
      loadMembers();
    } else {
      setLoading(false);
    }
  }, [user?.active_organization_id]);

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      setError("Email is required.");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const res = await apiRequest(
        "post",
        "/auth/organizations/members/",
        { email: inviteEmail.trim(), role: inviteRole },
        true,
      );
      setData(res.data?.data || { members: [] });
      setInviteEmail("");
      setInviteRole("member");
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to add member.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (memberUserId: string) => {
    try {
      setSaving(true);
      setError(null);
      const res = await apiRequest(
        "delete",
        `/auth/organizations/members/?user_id=${encodeURIComponent(memberUserId)}`,
        undefined,
        true,
      );
      setData(res.data?.data || { members: [] });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to remove member.");
    } finally {
      setSaving(false);
    }
  };

  const canManageMembers = ["owner", "admin"].includes(data.current_membership?.role || "");

  return (
    <div className="bg-card rounded-xl border border-border p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Workspace</h2>
          <p className="text-muted-foreground text-sm">Manage the active organization and its members.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-xl bg-secondary px-3 py-2 text-sm text-foreground">
          <Building2 className="h-4 w-4" />
          <span>{user?.active_organization?.name || "No workspace selected"}</span>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      {canManageMembers && (
        <div className="rounded-lg border border-border bg-secondary/80 dark:border-border/60 dark:bg-background/60 p-4 space-y-4">
          <div>
            <p className="text-sm font-medium text-foreground">Add member</p>
            <p className="text-xs text-muted-foreground">Add an existing Saramsa user to this workspace by email.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_auto] gap-3">
            <input
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="member@example.com"
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="viewer">Viewer</option>
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <Button onClick={handleInvite} disabled={saving} variant="saramsa" className="h-10 flex items-center gap-2">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Add
            </Button>
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border bg-secondary/80 dark:border-border/60 dark:bg-background/60">
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <Users className="h-4 w-4 text-muted-foreground" />
          <p className="text-sm font-medium text-foreground">Members</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="divide-y divide-border">
            {data.members.map((member) => {
              const displayName =
                `${member.first_name || ""} ${member.last_name || ""}`.trim() ||
                member.username ||
                member.email ||
                member.user_id;
              return (
                <div key={member.membership_id} className="flex items-center justify-between gap-4 px-4 py-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground">{displayName}</p>
                    <p className="text-xs text-muted-foreground">{member.email || member.user_id}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-background px-3 py-1 text-xs font-medium capitalize text-foreground border border-border">
                      {member.role}
                    </span>
                    {member.is_current_user && (
                      <span className="text-xs text-muted-foreground">You</span>
                    )}
                    {canManageMembers && member.role !== "owner" && !member.is_current_user && (
                      <Button
                        onClick={() => handleRemove(member.user_id)}
                        disabled={saving}
                        variant="ghost"
                        className="h-8 px-2 text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
            {!data.members.length && (
              <div className="px-4 py-8 text-sm text-muted-foreground">No members found for this workspace.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
