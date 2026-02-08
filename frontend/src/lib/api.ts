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
