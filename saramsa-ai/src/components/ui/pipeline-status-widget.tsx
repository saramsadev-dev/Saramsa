"use client";

import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";
import type { RootState } from "@/store/rootReducer";
import { apiRequest } from "@/lib/apiRequest";
import { getValidAccessToken } from "@/lib/auth";
import { ChevronDown } from 'lucide-react';
import { cn } from "./utils";

type StageStatus = "idle" | "pending" | "running" | "success" | "error";

type Stage = {
  label: string;
  detail: string;
  status: StageStatus;
};

type TaskItem = {
  id: string;
  label: string;
  detail: string;
  status: StageStatus;
  statusLabel?: string;
  statusTone?: string;
  pipelineHealth?: {
    status?: string;
    errors?: Record<string, string>;
  };
  commentCount?: number | null;
  durationSeconds?: number | null;
  updatedAt: number;
};

const statusCopy: Record<StageStatus, { label: string; tone: string }> = {
  idle: { label: "Idle", tone: "text-muted-foreground" },
  pending: { label: "Queued", tone: "text-amber-600" },
  running: { label: "Processing", tone: "text-sky-600" },
  success: { label: "Completed", tone: "text-emerald-600" },
  error: { label: "Failed", tone: "text-rose-600" },
};

export function PipelineStatusWidget() {
  const [open, setOpen] = useState(false);
  const analysisStatus = useSelector(
    (state: RootState) => state.analysis.analysisStatus
  );
  const loadedComments = useSelector(
    (state: RootState) => state.analysis.loadedComments
  );
  const analysisData = useSelector(
    (state: RootState) => state.analysis.analysisData
  );
  const taskId = useSelector((state: RootState) => state.analysis.taskId);
  const projectContext = useSelector(
    (state: RootState) => state.analysis.projectContext
  );
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [apiTasks, setApiTasks] = useState<TaskItem[]>([]);

  useEffect(() => {
    if (!taskId) {
      return;
    }

    const label = projectContext?.project_id
      ? `Analysis - ${projectContext.project_id.slice(0, 8)}`
      : "Feedback analysis";

    const statusMap: Record<string, StageStatus> = {
      pending: "pending",
      processing: "running",
      success: "success",
      failure: "error",
      idle: "idle",
    };

    const mappedStatus = statusMap[analysisStatus] ?? "idle";
    if (mappedStatus === "idle") {
      return;
    }

    setTasks((prev) => {
      const existing = prev.find((task) => task.id === taskId);
      const updated: TaskItem = {
        id: taskId,
        label,
        detail: "Sentiment + synthesis pipeline",
        status: mappedStatus,
        updatedAt: Date.now(),
      };

      const next = existing
        ? prev.map((task) => (task.id === taskId ? updated : task))
        : [updated, ...prev];

      return next.slice(0, 15);
    });
  }, [analysisStatus, taskId, projectContext?.project_id]);

  useEffect(() => {
    let isMounted = true;
    const mapApiTask = (task: any): TaskItem => {
      const raw = String(task?.status || "").toUpperCase();
      if (raw === "PARTIAL") {
        return {
          id: task.task_id,
          label: toLabel(task.project_id, task.file_name),
          detail: "Sentiment + synthesis pipeline",
          status: "error",
          statusLabel: "Partial",
          statusTone: "text-amber-600",
          pipelineHealth: task.pipeline_health,
          commentCount: task.comment_count ?? null,
          durationSeconds: task.duration_seconds ?? null,
          updatedAt: Date.now(),
        };
      }
      const status: StageStatus =
        raw === "RUNNING"
          ? "running"
          : raw === "SUCCESS"
          ? "success"
          : raw === "FAILED"
          ? "error"
          : "pending";
      return {
        id: task.task_id,
        label: toLabel(task.project_id, task.file_name),
        detail: "Sentiment + synthesis pipeline",
        status,
        pipelineHealth: task.pipeline_health,
        commentCount: task.comment_count ?? null,
        durationSeconds: task.duration_seconds ?? null,
        updatedAt: Date.now(),
      };
    };

    const toLabel = (projectId?: string, fileName?: string) => {
      if (fileName) return fileName;
      if (projectId) return `Analysis - ${projectId.slice(0, 8)}`;
      return "Feedback analysis";
    };

    const fetchTasks = async () => {
      try {
        const token = getValidAccessToken();
        if (!token) {
          return;
        }
        const response = await apiRequest("get", "/insights/tasks/", undefined, true);
        const list = response.data?.data?.tasks ?? [];
        if (!isMounted || !Array.isArray(list)) {
          return;
        }
        const mapped = list.slice(0, 15).map((task: any) => mapApiTask(task));
        setApiTasks(mapped);
      } catch {
        // Keep local fallback
      }
    };

    const token = getValidAccessToken();
    if (token) {
      fetchTasks();
    }
    const interval = setInterval(fetchTasks, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const { overall, stages } = useMemo(() => {
    switch (analysisStatus) {
      case "pending":
      case "processing":
        return {
          overall: "running" as StageStatus,
          stages: [
            { label: "Ingestion", detail: "Upload + parsing", status: "success" },
            { label: "Processing", detail: "Sentiment + topics", status: "running" },
            { label: "Synthesis", detail: "Insights + summary", status: "pending" },
            { label: "Work Items", detail: "DevOps/Jira push", status: "pending" },
          ],
        };
      case "success":
        return {
          overall: "success" as StageStatus,
          stages: [
            { label: "Ingestion", detail: "Upload + parsing", status: "success" },
            { label: "Processing", detail: "Sentiment + topics", status: "success" },
            { label: "Synthesis", detail: "Insights + summary", status: "success" },
            { label: "Work Items", detail: "DevOps/Jira push", status: "success" },
          ],
        };
      case "failure":
        return {
          overall: "error" as StageStatus,
          stages: [
            { label: "Ingestion", detail: "Upload + parsing", status: "success" },
            { label: "Processing", detail: "Sentiment + topics", status: "error" },
            { label: "Synthesis", detail: "Insights + summary", status: "idle" },
            { label: "Work Items", detail: "DevOps/Jira push", status: "idle" },
          ],
        };
      default:
        return {
          overall: "idle" as StageStatus,
          stages: [
            { label: "Ingestion", detail: "Upload + parsing", status: "idle" },
            { label: "Processing", detail: "Sentiment + topics", status: "idle" },
            { label: "Synthesis", detail: "Insights + summary", status: "idle" },
            { label: "Work Items", detail: "DevOps/Jira push", status: "idle" },
          ],
        };
    }
  }, [analysisStatus]);

  const commentCount = Array.isArray(loadedComments)
    ? loadedComments.length
    : analysisData?.analysisData?.comments_count ??
      analysisData?.comments_count ??
      analysisData?.analysisData?.counts?.total ??
      analysisData?.counts?.total ??
      null;

  const processingSeconds =
    analysisData?.analysisData?.processing_time ??
    analysisData?.processing_time ??
    null;

  const processingMinutes =
    typeof processingSeconds === "number"
      ? Math.max(1, Math.round(processingSeconds / 60))
      : null;

  const overallCopy = statusCopy[overall];
  const taskSource = apiTasks.length > 0 ? apiTasks : tasks;
  const activeTasks = taskSource.filter(
    (task) => task.status === "pending" || task.status === "running"
  );
  const historyTasks = taskSource.filter(
    (task) => task.status !== "pending" && task.status !== "running"
  );
  const orderedTasks = [...activeTasks, ...historyTasks].slice(0, 15);
  const topTasks = orderedTasks.slice(0, 3);
  const remainingTasks = orderedTasks.slice(3);

  const buildHealthTooltip = (task: TaskItem) => {
    const errors = task.pipelineHealth?.errors;
    if (!errors) return undefined;
    const entries = Object.entries(errors);
    if (!entries.length) return undefined;
    return entries.map(([key, value]) => `${key}: ${value}`).join(" | ");
  };

  const statusLabelForTask = (task: TaskItem) =>
    task.statusLabel ?? statusCopy[task.status].label;
  const statusToneForTask = (task: TaskItem) =>
    task.statusTone ?? statusCopy[task.status].tone;
  const formatTaskMeta = (task: TaskItem) => {
    const parts: string[] = [];
    if (typeof task.commentCount === "number") {
      parts.push(`${task.commentCount} comments`);
    }
    if (typeof task.durationSeconds === "number") {
      const minutes = Math.max(1, Math.round(task.durationSeconds / 60));
      parts.push(`${minutes} min`);
    }
    return parts.join(" · ");
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {open && (
        <div className="mb-4 w-[380px] rounded-2xl border border-border/70 bg-background/95 p-4 shadow-[0_24px_60px_-30px_rgba(15,23,42,0.6)] backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Pipeline Status
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className={cn("text-sm font-semibold", overallCopy.tone)}>
                  {overallCopy.label}
                </span>
                <span className="text-xs text-muted-foreground">- Live view</span>
              </div>
            </div>
            <button
              className="rounded-full border border-border/60 p-1 text-muted-foreground transition hover:text-foreground"
              onClick={() => setOpen(false)}
              aria-label="Collapse pipeline status"
            >
              <ChevronDown className="h-4 w-4" />
            </button>
          </div>

            <div className="mt-4">
              <div className="flex items-center gap-2">
                {stages.map((stage) => (
                  <div key={`${stage.label}-bar`} className="flex-1">
                    <div className="h-2 rounded-full bg-secondary/40 overflow-hidden border border-border/60">
                      <div
                        className={cn(
                          "h-full transition-all duration-500",
                          stage.status === "success"
                            ? "w-full bg-foreground"
                            : stage.status === "running"
                            ? "w-3/4 bg-saramsa-brand/60"
                            : stage.status === "error"
                            ? "w-full bg-muted-foreground/40"
                            : "w-1/5 bg-secondary/60"
                        )}
                      />
                    </div>
                  </div>
                ))}
              </div>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-muted-foreground">
              {stages.map((stage) => (
                <div
                  key={`${stage.label}-status`}
                  className={cn(
                    "inline-flex items-center rounded-md border border-border/60 bg-background/80 px-2 py-1 text-[10px] font-medium text-muted-foreground",
                    stage.status === "success"
                      ? "text-foreground"
                      : stage.status === "running"
                      ? "text-saramsa-brand"
                      : stage.status === "error"
                      ? "text-muted-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {stage.label}: {statusCopy[stage.status].label}
                </div>
              ))}
              {(commentCount || processingMinutes) && (
                <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
                  {commentCount ? (
                    <span>{commentCount} comments</span>
                  ) : null}
                  {commentCount && processingMinutes ? <span>·</span> : null}
                  {processingMinutes ? (
                    <span>{processingMinutes} min</span>
                  ) : null}
                </div>
              )}
            </div>
          </div>

          <div className="mt-5">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
              <span>Tasks</span>
              <span>{orderedTasks.length}/15</span>
            </div>

            <div className="mt-3 space-y-2">
              {topTasks.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/60 px-3 py-3 text-xs text-muted-foreground">
                  No tasks yet.
                </div>
              ) : (
                topTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/30 px-3 py-2"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {task.label}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {task.detail}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={cn("text-[11px] font-medium", statusToneForTask(task))}>
                        {statusLabelForTask(task)}
                      </p>
                      {formatTaskMeta(task) && (
                        <p className="text-[11px] text-muted-foreground" title={buildHealthTooltip(task)}>
                          {formatTaskMeta(task)}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {remainingTasks.length > 0 && (
              <div className="mt-3 max-h-40 space-y-2 overflow-y-auto pr-1">
                {remainingTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-xl border border-border/50 bg-card/60 px-3 py-2"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {task.label}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {task.detail}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={cn("text-[11px] font-medium", statusToneForTask(task))}>
                        {statusLabelForTask(task)}
                      </p>
                      {formatTaskMeta(task) && (
                        <p className="text-[11px] text-muted-foreground" title={buildHealthTooltip(task)}>
                          {formatTaskMeta(task)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen((value) => !value)}
        className={cn(
          "group relative flex h-14 w-14 items-center justify-center rounded-full",
          "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white",
          "shadow-[0_18px_40px_-20px_rgba(15,23,42,0.75)]",
          "transition hover:-translate-y-0.5 hover:shadow-[0_24px_55px_-24px_rgba(15,23,42,0.8)]"
        )}
        aria-label="Toggle pipeline status"
      >
        <span className="text-xs font-semibold">P</span>
        <span
          className={cn(
            "absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full border-2 border-background",
            overall === "running" || overall === "pending"
              ? "bg-amber-400 animate-pulse"
              : overall === "success"
              ? "bg-emerald-400"
              : overall === "error"
              ? "bg-rose-500"
              : "bg-muted-foreground/50"
          )}
        />
      </button>

      {!open && (
        <div className="pointer-events-none mt-2 text-right">
          <span className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-3 py-1 text-xs text-muted-foreground shadow-sm">
            Pipeline
          </span>
        </div>
      )}
    </div>
  );
}

