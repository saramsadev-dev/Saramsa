export interface TraceableWorkItem {
  id: string;
  title: string;
  description?: string;
  tags?: string[];
  featureArea?: string;
}

export interface TraceMatch<T> {
  item: T;
  score: number;
  matched: string[];
}

const MIN_TOKEN_LEN = 3;

function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(text: string): string[] {
  if (!text) return [];
  return normalize(text)
    .split(" ")
    .filter((token) => token.length >= MIN_TOKEN_LEN);
}

function uniqueTokens(tokens: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const token of tokens) {
    if (!seen.has(token)) {
      seen.add(token);
      out.push(token);
    }
  }
  return out;
}

function scoreMatch(haystackTokens: string[], needleTokens: string[]): TraceMatch<string> {
  const haystack = new Set(haystackTokens);
  const matched = needleTokens.filter((token) => haystack.has(token));
  const score = matched.length;
  return { item: "", score, matched };
}

function buildItemTokens(item: TraceableWorkItem): string[] {
  const parts = [
    item.title || "",
    item.description || "",
    item.featureArea || "",
    ...(item.tags || []),
  ];
  return uniqueTokens(parts.flatMap((part) => tokenize(part)));
}

export function getRelatedWorkItemsForInsight(
  items: TraceableWorkItem[],
  insightText: string,
  limit = 3
): TraceMatch<TraceableWorkItem>[] {
  if (!insightText || !Array.isArray(items) || items.length === 0) return [];

  const insightTokens = uniqueTokens(tokenize(insightText));
  if (insightTokens.length === 0) return [];

  const matches: TraceMatch<TraceableWorkItem>[] = items
    .map((item) => {
      const itemTokens = buildItemTokens(item);
      const { score, matched } = scoreMatch(itemTokens, insightTokens);
      return { item, score, matched };
    })
    .filter((match) => match.score > 0)
    .sort((a, b) => b.score - a.score);

  return matches.slice(0, Math.max(0, limit));
}

export function getRelatedInsightsForWorkItem(
  insights: string[],
  workItem: TraceableWorkItem,
  limit = 3
): TraceMatch<string>[] {
  if (!Array.isArray(insights) || insights.length === 0) return [];

  const itemTokens = buildItemTokens(workItem);
  if (itemTokens.length === 0) return [];

  const matches: TraceMatch<string>[] = insights
    .map((insight) => {
      const insightTokens = uniqueTokens(tokenize(insight));
      const { score, matched } = scoreMatch(itemTokens, insightTokens);
      return { item: insight, score, matched };
    })
    .filter((match) => match.score > 0)
    .sort((a, b) => b.score - a.score);

  return matches.slice(0, Math.max(0, limit));
}
