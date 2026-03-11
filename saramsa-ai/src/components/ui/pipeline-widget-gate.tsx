"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { PipelineStatusWidget } from "@/components/ui/pipeline-status-widget";
import { getValidAccessToken } from "@/lib/auth";

export function PipelineWidgetGate() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const hasToken = Boolean(getValidAccessToken());

  if (!pathname || !pathname.startsWith("/projects/")) {
    return null;
  }

  if (!hasToken) {
    return null;
  }

  return <PipelineStatusWidget />;
}
