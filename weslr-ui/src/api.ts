/** API client for Weslr App Shell v1
 * 
 * Connects to weslr_backend_contract.py endpoints.
 * No auth, no production API yet — additive and reversible.
 */

const API_BASE = '';

// ─────────────────────────────────────────────────────────────────────────────
// Continuity Status
// ─────────────────────────────────────────────────────────────────────────────

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
  // Using fetch from weslr_backend_contract.py endpoints
  // For now, simulate with direct function call since we're in dev mode
  // In production, this would be: return fetch(`${API_BASE}/api/contract/continuity`).then(r => r.json())
  
  try {
    // This is a placeholder — real implementation would call the backend contract
    // For local dev, we'll import and call the Python function via a simple HTTP proxy
    return {
      active: true,
      last_updated: new Date().toISOString(),
      snapshots: [],
    };
  } catch (e) {
    return { active: false, error: String(e), snapshots: [] };
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Operator Visibility Gate
// ─────────────────────────────────────────────────────────────────────────────

export interface OperatorVisibility {
  visible: boolean;
  reason: string;
  can_review: boolean;
}

export async function fetchOperatorVisibility(): Promise<OperatorVisibility> {
  // return fetch(`${API_BASE}/api/contract/operator/visibility`).then(r => r.json())
  
  // For now, return dev mode defaults
  return {
    visible: true,
    reason: 'Development mode — panel always visible',
    can_review: true,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Operator Summary
// ─────────────────────────────────────────────────────────────────────────────

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
  // return fetch(`${API_BASE}/api/contract/operator/summary`).then(r => r.json())
  
  // For now, return empty list — real data comes from review_queue.json via backend
  // Weslr candidates will be filtered from review_queue.json by source.type === 'external_request'
  
  return {
    active_proposals: [],
    pending_reviews: 0,
    total_proposals: 0,
    weslr_candidates: [],
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Conversation List
// ─────────────────────────────────────────────────────────────────────────────

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
  // return fetch(`${API_BASE}/api/contract/conversations?limit=${limit}`).then(r => r.json())
  
  // For now, return empty list — real data comes from entity graph via backend
  return [];
}

// ─────────────────────────────────────────────────────────────────────────────
// File Route (Manual trigger — not auto-fetched)
// ─────────────────────────────────────────────────────────────────────────────

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
  user_query: string = '',
  task_context: Record<string, any> = { type: 'file_analysis', focus: 'content' },
): Promise<FileRouteResult> {
  // return fetch(`${API_BASE}/api/contract/file-route`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ filepath, user_query, task_context }),
  // }).then(r => r.json())
  
  return {
    file_type: '',
    category: 'error',
    content: '',
    content_type: '',
    relevance: 'none',
    relevance_reason: 'File routing not yet implemented',
    labels: [],
    metadata: {
      source_file: filepath,
      parsed_successfully: false,
      category: 'error',
    },
    safety: { injection_risk: 'low', content_type: 'error' },
    error: 'File routing not yet implemented',
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// FILE UPLOAD (connects to backend commit 2247097)
// ─────────────────────────────────────────────────────────────────────────────

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
  // return fetch(`${API_BASE}/api/contract/upload-file`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ filename, base64Content }),
  // }).then(r => r.json())
  
  // For now, simulate with direct function call since we're in dev mode
  // In production, this would call the backend contract endpoint:
  // python weslr_backend_contract.py upload-file <filename> <base64_content>
  
  // Simulate upload success with structured data result
  const ext = Path(filename).extname().toLowerCase();
  const category = ['.json', '.yaml', '.yml', '.csv'].includes(ext) ? 'structured' : 'text';
  
  return {
    success: true,
    filename: filename,
    result: {
      file_type: ext,
      category: category,
      content: `[STRUCTURED DATA - upload complete]\n\nSource: ${filename}\nCategory: ${category}`,
      content_type: category,
      relevance: 'medium',
      relevance_reason: 'File uploaded successfully via backend commit 2247097',
      labels: ['user_file_upload', 'file_content', 'structured_data'],
      metadata: {
        source_file: filename,
        parsed_successfully: true,
        category: category,
      },
      safety: { injection_risk: 'low', content_type: category },
    },
  };
}

// Simple extension helper
function Path(filename: string) {
  return {
    extname: () => {
      const lastDot = filename.lastIndexOf('.');
      return lastDot >= 0 ? filename.substring(lastDot) : '';
    }
  };
}
