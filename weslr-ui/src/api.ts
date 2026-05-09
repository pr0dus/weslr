/** API client for Weslr App Shell v1
 *
 * Public demo defaults are intentionally conservative:
 * - no operator visibility
 * - no file upload
 * - no memory/write actions
 */

import config from './config';

const API_BASE = '';

export interface ContinuityStatus {
  active: boolean;
  last_snapshot_id?: string;
  last_updated?: string;
  snapshots: Array<{
    id: string;
    created_at: string;
    entity_count: number;
  }>;
  error?: string;
}

export async function fetchContinuityStatus(): Promise<ContinuityStatus> {
  return {
    active: true,
    last_updated: new Date().toISOString(),
    snapshots: [],
  };
}

export interface OperatorVisibility {
  visible: boolean;
  reason: string;
  can_review: boolean;
}

export async function fetchOperatorVisibility(): Promise<OperatorVisibility> {
  if (!config.features.operatorPanel) {
    return {
      visible: false,
      reason: 'Public demo mode — operator panel disabled',
      can_review: false,
    };
  }

  return {
    visible: config.operator.visibility.defaultValue,
    reason: 'Operator panel enabled by configured product mode',
    can_review: config.features.proposalReview,
  };
}

export interface WeslrCandidate {
  id: string;
  title: string;
  domain: string;
  requester_type: string;
  status: string;
  weslr_assessment?: {
    priority: 'high' | 'medium' | 'low';
    fit_score: number;
    implementation_risk: 'low' | 'medium' | 'high';
    recommended_action: string;
    reasoning: string;
  };
}

export interface OperatorSummary {
  active_proposals: Array<{
    id: string;
    title: string;
    state: string;
    created_at: string;
  }>;
  pending_reviews: number;
  last_review?: string;
  total_proposals: number;
  weslr_candidates?: WeslrCandidate[];
  error?: string;
}

export async function fetchOperatorSummary(): Promise<OperatorSummary> {
  return {
    active_proposals: [],
    pending_reviews: 0,
    total_proposals: 0,
    weslr_candidates: [],
  };
}

export interface Conversation {
  id: string;
  title: string;
  entity_id: string;
  entity_type: string;
  participant_count: number;
  last_message_at: string;
  snippet: string;
  unread_count: number;
}

export async function fetchConversations(limit: number = 20): Promise<Conversation[]> {
  void limit;
  return [];
}

export interface FileRouteResult {
  file_type: string;
  category: string;
  content: string;
  content_type: string;
  relevance: string;
  relevance_reason: string;
  labels: string[];
  metadata: {
    source_file: string;
    parsed_successfully: boolean;
    parse_error?: string;
    category: string;
  };
  safety: {
    injection_risk: string;
    content_type: string;
  };
  error?: string;
}

export async function routeFile(
  filepath: string,
): Promise<FileRouteResult> {
  return {
    file_type: '',
    category: 'error',
    content: '',
    content_type: '',
    relevance: 'none',
    relevance_reason: 'File routing is not available in this mode',
    labels: [],
    metadata: {
      source_file: filepath,
      parsed_successfully: false,
      category: 'error',
    },
    safety: { injection_risk: 'low', content_type: 'error' },
    error: 'File routing is not available in this mode',
  };
}

export interface UploadResult {
  success: boolean;
  filepath?: string;
  filename?: string;
  result?: FileRouteResult;
  error?: string;
}

export async function uploadFile(
  filename: string,
  base64Content: string,
): Promise<UploadResult> {
  void base64Content;

  if (!config.features.fileUpload) {
    return {
      success: false,
      filename,
      error: 'File upload is disabled in the read-only public demo.',
      result: {
        file_type: '',
        category: 'error',
        content: '',
        content_type: 'error',
        relevance: 'none',
        relevance_reason: 'File upload disabled by product mode',
        labels: [],
        metadata: {
          source_file: filename,
          parsed_successfully: false,
          category: 'error',
        },
        safety: { injection_risk: 'low', content_type: 'error' },
        error: 'File upload is disabled in the read-only public demo.',
      },
    };
  }

  return {
    success: false,
    filename,
    error: 'File upload backend is not configured yet.',
  };
}

export interface ChatMessage {
  id: string;
  sender: 'weslr' | 'you';
  text: string;
  timestamp: string;
}

export interface ChatResult {
  success: boolean;
  reply?: string;
  intent?: any;
  source?: string;
  error?: string;
}

export async function sendChatMessage(message: string): Promise<ChatResult> {
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    return await response.json();
  } catch (_e) {
    return {
      success: false,
      error:
        'This public demo only supports selected read-only WESLR routes. I can explain WESLR, describe hosted or private deployment, or show safe status information.',
    };
  }
}
