import { apiRequest } from '@/lib/apiRequest';
import { FileText, Database, Music } from 'lucide-react';
import React from 'react';

export type SentimentBreakdown = {
  positive: number;
  negative: number;
  neutral: number;
};

export type FeatureSentiment = {
  featureId: string;
  name: string;
  description: string;
  sentiment: SentimentBreakdown;
  keywords: string[];
  comment_count: number;
};

export type EmojiAnalysis = {
  overallsentiment: 'Positive' | 'Negative' | 'Neutral';
  topemojis?: string[];
};

export type ActionItems = {
  featurerequests?: Array<{ feature: string; request: string }>;
  bugs?: Array<{ feature: string; issue: string }>;
  changerequests?: Array<{ feature: string; request: string }>;
};

export type AnalysisData = {
  id: string;
  projectId: string;
  userId: string;
  createdAt: string;
  analysisType: string;
  rawLlm: any;
  analysisData: {
    overall: SentimentBreakdown;
    counts: { total: number; positive: number; negative: number; neutral: number };
    features: FeatureSentiment[];
    positive_keywords: Array<{ keyword: string; sentiment: number }>;
    negative_keywords: Array<{ keyword: string; sentiment: number }>;
  };
  deepAnalysis?: {
    work_items?: any[];
    work_items_by_feature?: any;
    summary?: any;
    process_template?: string;
    generated_at?: string;
    comments_count?: number;
  };
  analysis_date?: string;
  total_comments_analyzed?: number;
};

type ValidationResult = { isValid: true } | { isValid: false; error: string };

const MAX_SIZE_BYTES: Record<string, number> = {
  'text/csv': 250 * 1024 * 1024,
  'application/json': 250 * 1024 * 1024,
  'audio/mpeg': 500 * 1024 * 1024,
};

const ACCEPTED_TYPES = new Set(Object.keys(MAX_SIZE_BYTES));

function getMaxSize(type: string): number | undefined {
  return MAX_SIZE_BYTES[type];
}

function isAcceptedType(type: string): boolean {
  return ACCEPTED_TYPES.has(type) || type.includes('csv') || type.includes('json');
}

function acceptedByFileName(name: string): boolean {
  const lower = name.toLowerCase();
  return lower.endsWith('.csv') || lower.endsWith('.json');
}

export const uploadService = {
  validateFile(file: File): ValidationResult {
    const typeOk = isAcceptedType(file.type) || acceptedByFileName(file.name);
    if (!typeOk) {
      return { isValid: false, error: 'Unsupported file type. Use CSV or JSON.' };
    }
    const typeForLimit = file.type && isAcceptedType(file.type) ? file.type : (file.name.toLowerCase().endsWith('.json') ? 'application/json' : 'text/csv');
    const limit = getMaxSize(typeForLimit);
    if (limit && file.size > limit) {
      return { isValid: false, error: 'File is too large. Maximum size is 250 MB for CSV and JSON.' };
    }
    return { isValid: true };
  },

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const projectId = (typeof window !== 'undefined') ? localStorage.getItem('project_id') : null;
    if (projectId) formData.append('project_id', projectId);
    const res = await apiRequest('post', '/upload/a/', formData, true, true);
    return res.data;
  },


  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  },

  getFileIcon(fileType: string): React.ReactNode {
    if (fileType.includes('csv')) return React.createElement(FileText, { className: 'w-6 h-6' });
    if (fileType.includes('json')) return React.createElement(Database, { className: 'w-6 h-6' });
    if (fileType.includes('audio')) return React.createElement(Music, { className: 'w-6 h-6' });
    return React.createElement(FileText, { className: 'w-6 h-6' });
  },
};

export default uploadService;


