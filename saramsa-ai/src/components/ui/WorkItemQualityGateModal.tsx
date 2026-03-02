"use client";

import { BaseModal } from "./modals/BaseModal";
import { Button } from "./button";
import { Badge } from "./badge";
import type { QualityReport } from "@/lib/workItemQuality";

interface WorkItemQualityGateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProceed: () => void;
  report: QualityReport | null;
  allowProceed: boolean;
}

export function WorkItemQualityGateModal({
  isOpen,
  onClose,
  onProceed,
  report,
  allowProceed,
}: WorkItemQualityGateModalProps) {
  const issues = report?.issues || [];

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title="Quality Gate Checks"
      description="Some work items need fixes before pushing."
      size="lg"
    >
      <div className="space-y-4">
        <div className="text-sm text-muted-foreground">
          {issues.length} item{issues.length === 1 ? "" : "s"} have quality issues.
        </div>

        <div className="max-h-[420px] space-y-3 overflow-y-auto pr-2">
          {issues.map((item) => (
            <div key={item.id} className="rounded-2xl border border-border/60 bg-card/80 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="text-sm font-semibold text-foreground">{item.title}</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {item.issues.map((issue) => (
                      <Badge key={`${item.id}-${issue.code}`} variant="outline" className="text-xs">
                        {issue.message}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Badge variant="destructive" className="text-xs">
                  Needs fixes
                </Badge>
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <Button variant="outline" onClick={onClose}>
            Back
          </Button>
          {allowProceed && (
            <Button
              onClick={onProceed}
              className="bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to text-white"
            >
              Proceed Anyway
            </Button>
          )}
        </div>
      </div>
    </BaseModal>
  );
}
