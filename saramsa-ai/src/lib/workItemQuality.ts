export interface QualityRules {
  require_acceptance_criteria: boolean;
  require_priority: boolean;
  require_tags: boolean;
  min_description_length: number;
  min_acceptance_criteria_length: number;
  allow_push_with_warnings: boolean;
}

export interface QualityIssue {
  code: string;
  message: string;
}

export interface QualityItemIssue {
  id: string;
  title: string;
  issues: QualityIssue[];
}

export interface QualityReport {
  total_items: number;
  items_with_issues: number;
  issues: QualityItemIssue[];
  allow_push_with_warnings?: boolean;
}

export const DEFAULT_QUALITY_RULES: QualityRules = {
  require_acceptance_criteria: true,
  require_priority: true,
  require_tags: false,
  min_description_length: 30,
  min_acceptance_criteria_length: 20,
  allow_push_with_warnings: false,
};

type WorkItemLike = {
  id?: string;
  work_item_id?: string;
  title?: string;
  description?: string;
  acceptance_criteria?: string;
  acceptancecriteria?: string;
  acceptance?: string;
  priority?: string;
  tags?: string[];
  labels?: string[];
};

export function evaluateWorkItems(
  workItems: WorkItemLike[],
  rules: QualityRules
): QualityReport {
  const issues: QualityItemIssue[] = [];
  const safeRules = { ...DEFAULT_QUALITY_RULES, ...(rules || {}) };

  for (const item of workItems || []) {
    const itemId = item.id || item.work_item_id || item.title || "unknown";
    const title = item.title || "Untitled";
    const description = item.description || "";
    const acceptance =
      item.acceptance_criteria || item.acceptancecriteria || item.acceptance || "";
    const priority = item.priority;
    const tags = item.tags || item.labels || [];

    const itemIssues: QualityIssue[] = [];

    if (safeRules.require_acceptance_criteria) {
      const acceptanceLen = String(acceptance || "").trim().length;
      if (acceptanceLen < safeRules.min_acceptance_criteria_length) {
        itemIssues.push({
          code: "missing_acceptance_criteria",
          message: "Acceptance criteria is missing or too short.",
        });
      }
    }

    if (safeRules.require_priority && !priority) {
      itemIssues.push({
        code: "missing_priority",
        message: "Priority is required.",
      });
    }

    if (safeRules.require_tags && (!tags || tags.length === 0)) {
      itemIssues.push({
        code: "missing_tags",
        message: "Tags/labels are required.",
      });
    }

    const descLen = String(description || "").trim().length;
    if (descLen < safeRules.min_description_length) {
      itemIssues.push({
        code: "description_too_short",
        message: "Description is too short.",
      });
    }

    if (itemIssues.length > 0) {
      issues.push({
        id: String(itemId),
        title,
        issues: itemIssues,
      });
    }
  }

  return {
    total_items: workItems?.length || 0,
    items_with_issues: issues.length,
    issues,
  };
}
