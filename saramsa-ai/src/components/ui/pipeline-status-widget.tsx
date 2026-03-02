"use client";

import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";
import type { RootState } from "@/store/rootReducer";
import { apiRequest } from "@/lib/apiRequest";
import { getValidAccessToken } from "@/lib/auth";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Loader2,
} from "lucide-react";
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
  updatedAt: number;
};

const statusCopy: Record<StageStatus, { label: string; tone: string }> = {
  idle: { label: "Idle", tone: "text-muted-foreground" },
  pending: { label: "Queued", tone: "text-amber-600" },
  running: { label: "Processing", tone: "text-sky-600" },
  success: { label: "Completed", tone: "text-emerald-600" },
  error: { label: "Failed", tone: "text-rose-600" },
};

const iconForStatus = (status: StageStatus) => {
  switch (status) {
    case "running":
      return <Loader2 className="h-4 w-4 animate-spin text-sky-600" />;
    case "success":
      return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
    case "error":
      return <AlertCircle className="h-4 w-4 text-rose-600" />;
    case "pending":
      return <Clock className="h-4 w-4 text-amber-600" />;
    default:
      return <Activity className="h-4 w-4 text-muted-foreground" />;
  }
};

export function PipelineStatusWidget() {
  const [open, setOpen] = useState(false);
  const analysisStatus = useSelector(
    (state: RootState) => state.analysis.analysisStatus
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
      ? `Analysis • ${projectContext.project_id.slice(0, 8)}`
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
    let eventSource: EventSource | null = null;
    const mapApiStatus = (raw: string): StageStatus => {
      if (raw === "RUNNING") return "running";
      if (raw === "SUCCESS") return "success";
      if (raw === "FAILED") return "error";
      return "pending";
    };

    const toLabel = (projectId?: string, fileName?: string) => {
      if (fileName) return fileName;
      if (projectId) return `Analysis • ${projectId.slice(0, 8)}`;
      return "Feedback analysis";
    };

    const fetchTasks = async () => {
      try {
        const response = await apiRequest("get", "/insights/tasks/", undefined, true);
        const list = response.data?.data?.tasks ?? [];
        if (!isMounted || !Array.isArray(list)) {
          return;
        }
        const mapped = list.slice(0, 15).map((task: any) => ({
          id: task.task_id,
          label: toLabel(task.project_id, task.file_name),
          detail: "Sentiment + synthesis pipeline",
          status: mapApiStatus(task.status),
          updatedAt: Date.now(),
        }));
        setApiTasks(mapped);
      } catch {
        // Keep local fallback
      }
    };

    const startStream = () => {
      if (typeof window === "undefined") return;
      try {
        const token = getValidAccessToken();
        const url = token
          ? `/api/insights/tasks/stream/?token=${encodeURIComponent(token)}`
          : "/api/insights/tasks/stream/";
        eventSource = new EventSource(url);
        eventSource.addEventListener("tasks", (event) => {
          try {
            const payload = JSON.parse((event as MessageEvent).data);
            const list = payload?.tasks ?? [];
            if (!isMounted || !Array.isArray(list)) return;
            const mapped = list.slice(0, 15).map((task: any) => ({
              id: task.task_id,
              label: toLabel(task.project_id, task.file_name),
              detail: "Sentiment + synthesis pipeline",
              status: mapApiStatus(task.status),
              updatedAt: Date.now(),
            }));
            setApiTasks(mapped);
          } catch {
            // ignore
          }
        });
        eventSource.onerror = () => {
          eventSource?.close();
          eventSource = null;
          fetchTasks();
        };
      } catch {
        fetchTasks();
      }
    };

    startStream();
    const interval = setInterval(fetchTasks, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
      eventSource?.close();
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

  const overallCopy = statusCopy[overall];
  const taskSource = apiTasks.length > 0 ? apiTasks : tasks;
  const activeTasks = taskSource
    .filter((task) => task.status === "pending" || task.status === "running")
    .slice(0, 3);
  const historyTasks = taskSource
    .filter((task) => task.status !== "pending" && task.status !== "running")
    .slice(0, 15);

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {open && (
        <div className="mb-4 w-[320px] rounded-2xl border border-border/70 bg-background/95 p-4 shadow-[0_24px_60px_-30px_rgba(15,23,42,0.6)] backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                Pipeline Status
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className={cn("text-sm font-semibold", overallCopy.tone)}>
                  {overallCopy.label}
                </span>
                <span className="text-xs text-muted-foreground">
                  · Live view
                </span>
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

          <div className="mt-4 space-y-3">
            {stages.map((stage) => (
              <div
                key={stage.label}
                className="flex items-center gap-3 rounded-xl border border-border/50 bg-card/60 px-3 py-2"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/60">
                  {iconForStatus(stage.status)}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-foreground">
                    {stage.label}
                  </p>
                  <p className="text-xs text-muted-foreground">{stage.detail}</p>
                </div>
                <span className={cn("text-xs font-medium", statusCopy[stage.status].tone)}>
                  {statusCopy[stage.status].label}
                </span>
              </div>
            ))}
          </div>

          <div className="mt-5">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
              <span>Active Tasks</span>
              <span>{activeTasks.length}/3</span>
            </div>
            <div className="mt-3 space-y-2">
              {activeTasks.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/60 px-3 py-3 text-xs text-muted-foreground">
                  No active tasks right now.
                </div>
              ) : (
                activeTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-xl border border-border/50 bg-muted/30 px-3 py-2"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/60">
                      {iconForStatus(task.status)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {task.label}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {task.detail}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "text-xs font-medium",
                        statusCopy[task.status].tone
                      )}
                    >
                      {statusCopy[task.status].label}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="mt-5">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
              <span>History</span>
              <span>Max 15</span>
            </div>
            <div className="mt-3 max-h-48 space-y-2 overflow-y-auto pr-1">
              {historyTasks.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/60 px-3 py-3 text-xs text-muted-foreground">
                  No completed tasks yet.
                </div>
              ) : (
                historyTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 rounded-xl border border-border/50 bg-card/60 px-3 py-2"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/60">
                      {iconForStatus(task.status)}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground">
                        {task.label}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {task.detail}
                      </p>
                    </div>
                    <span
                      className={cn(
                        "text-xs font-medium",
                        statusCopy[task.status].tone
                      )}
                    >
                      {statusCopy[task.status].label}
                    </span>
                  </div>
                ))
              )}
            </div>
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
        <Activity className="h-6 w-6" />
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
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Pipeline
          </span>
        </div>
      )}
    </div>
  );
}
