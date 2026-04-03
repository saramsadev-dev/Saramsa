/** Display order: critical first, then high, medium, low; unknown values last. */
const PRIORITY_RANK: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export function workItemPriorityRank(priority: string | undefined): number {
  const key = (priority ?? 'medium').toLowerCase().trim();
  return key in PRIORITY_RANK ? PRIORITY_RANK[key] : 4;
}

export function sortWorkItemsByPriority<T extends { priority?: string }>(items: T[]): T[] {
  return [...items].sort(
    (a, b) => workItemPriorityRank(a.priority) - workItemPriorityRank(b.priority)
  );
}
