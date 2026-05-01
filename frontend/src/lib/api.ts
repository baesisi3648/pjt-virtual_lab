/**
 * @TASK P4-T1 - API Client
 * @SPEC TASKS.md#P4-T1
 *
 * FastAPI 백엔드와 통신하는 API 클라이언트
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ResearchRequest {
  topic: string;
  constraints?: string;
}

export interface ResearchResponse {
  report: string;
  messages: Array<{
    role: string;
    content: string;
  }>;
  iterations: number;
}

export interface ReportListItem {
  filename: string;
  topic: string;
  created_at: string;
  size: number;
}

export interface ReportContent {
  filename: string;
  topic: string;
  created_at: string;
  content: string;
  lang?: 'en' | 'ko';
  ko_available?: boolean;
}

export interface RegenerateRequest {
  section: string;
  feedback: string;
  current_report: string;
}

export interface RegenerateResponse {
  updated_report: string;
  section: string;
  message: string;
}

/**
 * 연구 작업 제출
 */
export async function submitResearch(
  request: ResearchRequest
): Promise<ResearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 헬스체크
 */
export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 보고서 섹션 재생성
 */
export async function regenerateSection(
  request: RegenerateRequest
): Promise<RegenerateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/report/regenerate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Regenerate request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 보고서 목록 조회
 */
export async function fetchReports(): Promise<ReportListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/reports`);

  if (!response.ok) {
    throw new Error(`Failed to fetch reports: ${response.statusText}`);
  }

  const data = await response.json();
  return data.reports;
}

/**
 * 보고서 삭제
 */
export async function deleteReport(filename: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error(`Failed to delete report: ${response.statusText}`);
  }
}

/**
 * 보고서 영어 번역
 */
export async function translateReport(
  content: string
): Promise<{ translated: string }> {
  const response = await fetch(`${API_BASE_URL}/api/reports/translate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });

  if (!response.ok) {
    throw new Error(`Translate request failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * 보고서 내용 조회 (메타데이터 + 본문). lang 파라미터로 영/한 선택.
 */
export async function fetchReportContent(
  filename: string,
  lang: 'en' | 'ko' = 'en',
): Promise<ReportContent> {
  const response = await fetch(
    `${API_BASE_URL}/api/reports/${encodeURIComponent(filename)}/content?lang=${lang}`,
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch report content: ${response.statusText}`);
  }

  return response.json();
}

// ── Session History API ──────────────────────────────────

export interface SessionListItem {
  id: string;
  topic: string;
  constraints: string;
  status: string;
  total_rounds: number;
  created_at: string;
  completed_at: string | null;
}

export interface SessionEvent {
  id: number;
  session_id: string;
  event_type: string;
  agent: string;
  agent_name: string;
  round: number;
  content: string;
  scores: Record<string, number> | null;
  timestamp: string;
  metadata: Record<string, unknown> | null;
}

export interface SessionDetail {
  session_id: string;
  topic: string;
  status: string;
  total_rounds: number;
  events: SessionEvent[];
}

export async function fetchSessions(): Promise<SessionListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`);
  if (!response.ok) throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  const data = await response.json();
  return data.sessions;
}

export async function fetchSessionEvents(sessionId: string): Promise<SessionDetail> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/events`);
  if (!response.ok) throw new Error(`Failed to fetch session events: ${response.statusText}`);
  return response.json();
}
