/**
 * @TASK P4-T2 - Live Process Timeline
 * @SPEC TASKS.md#P4-T2
 *
 * 에이전트 상태를 실시간으로 시각화하는 타임라인 컴포넌트
 * Server-Sent Events (SSE)를 사용하여 백엔드로부터 이벤트를 스트리밍
 */

'use client';

import { useEffect, useState, useRef } from 'react';

// 타임라인 이벤트 타입
interface TimelineEvent {
  type: 'start' | 'phase' | 'agent' | 'decision' | 'iteration' | 'complete' | 'error';
  timestamp: number;
  message: string;
  agent?: 'scientist' | 'critic' | 'pi';
  phase?: 'drafting' | 'critique' | 'finalizing';
  decision?: 'approve' | 'revise';
  iteration?: number;
  report?: string;
  error?: string;
}

// Props 타입
interface ProcessTimelineProps {
  topic: string;
  constraints?: string;
  onComplete?: (report: string) => void;
  onError?: (error: string) => void;
}

// 에이전트별 아이콘 및 색상
const AGENT_CONFIG = {
  scientist: {
    icon: '🔬',
    name: 'Scientist',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  critic: {
    icon: '🔍',
    name: 'Critic',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
  },
  pi: {
    icon: '👔',
    name: 'PI',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
};

export default function ProcessTimeline({
  topic,
  constraints = '',
  onComplete,
  onError,
}: ProcessTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentReport, setCurrentReport] = useState<string>('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const timelineEndRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  // SSE 연결
  useEffect(() => {
    if (!topic) return;

    const startStreaming = async () => {
      setIsStreaming(true);
      setEvents([]);
      setCurrentReport('');

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // SSE 연결 (POST 요청은 직접 지원하지 않으므로 먼저 POST로 시작하고 GET으로 스트리밍)
      // 간단하게 하기 위해 query params로 전달
      const params = new URLSearchParams({
        topic,
        constraints: constraints || '',
      });

      // EventSource는 GET만 지원하므로 POST를 위해서는 fetch를 사용해야 함
      // 하지만 여기서는 간단하게 구현하기 위해 서버에서 POST를 받는 대신
      // 프론트에서 직접 fetch를 사용하여 ReadableStream을 처리

      try {
        const response = await fetch(`${API_BASE_URL}/api/research/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            topic,
            constraints: constraints || '',
          }),
        });

        if (!response.ok) {
          throw new Error(`Stream failed: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body');
        }

        // 스트림 읽기
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setIsStreaming(false);
            break;
          }

          // SSE 데이터 파싱
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // 'data: ' 제거
              try {
                const event: TimelineEvent = JSON.parse(data);

                // 이벤트 추가
                setEvents((prev) => [...prev, event]);

                // 완료 이벤트 처리
                if (event.type === 'complete' && event.report) {
                  setCurrentReport(event.report);
                  onComplete?.(event.report);
                }

                // 에러 이벤트 처리
                if (event.type === 'error' && event.error) {
                  onError?.(event.error);
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', e);
              }
            }
          }
        }
      } catch (error) {
        console.error('SSE connection error:', error);
        setIsStreaming(false);
        onError?.(error instanceof Error ? error.message : 'Unknown error');
      }
    };

    startStreaming();

    // Cleanup
    return () => {
      eventSourceRef.current?.close();
      setIsStreaming(false);
    };
  }, [topic, constraints, onComplete, onError]);

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">연구 진행 상황</h2>

      {/* 타임라인 */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {events.map((event, index) => (
          <TimelineItem key={index} event={event} />
        ))}

        {/* 스트리밍 중 인디케이터 */}
        {isStreaming && events.length === 0 && (
          <div className="flex items-center gap-2 text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>연결 중...</span>
          </div>
        )}

        <div ref={timelineEndRef} />
      </div>

      {/* 최종 보고서 미리보기 */}
      {currentReport && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="font-semibold text-green-800 mb-2">✅ 연구 완료</h3>
          <p className="text-sm text-gray-600">
            최종 보고서가 생성되었습니다. (길이: {currentReport.length}자)
          </p>
        </div>
      )}
    </div>
  );
}

// 개별 타임라인 아이템 컴포넌트
function TimelineItem({ event }: { event: TimelineEvent }) {
  // 에이전트 정보 가져오기
  const agentConfig = event.agent ? AGENT_CONFIG[event.agent] : null;

  // 타임스탬프 포맷팅
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // 이벤트 타입별 스타일링
  let itemClasses = 'p-4 rounded-lg border';
  let iconClasses = 'text-2xl';

  if (event.type === 'start') {
    itemClasses += ' bg-blue-50 border-blue-200';
  } else if (event.type === 'complete') {
    itemClasses += ' bg-green-50 border-green-200';
  } else if (event.type === 'error') {
    itemClasses += ' bg-red-50 border-red-200';
  } else if (agentConfig) {
    itemClasses += ` ${agentConfig.bgColor} border-${agentConfig.color.split('-')[1]}-200`;
  } else {
    itemClasses += ' bg-gray-50 border-gray-200';
  }

  return (
    <div className={itemClasses}>
      <div className="flex items-start gap-3">
        {/* 아이콘 */}
        <div className={iconClasses}>
          {agentConfig?.icon || (event.type === 'complete' ? '✅' : event.type === 'error' ? '❌' : '🔄')}
        </div>

        {/* 내용 */}
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {agentConfig && (
                <span className={`font-semibold ${agentConfig.color}`}>
                  {agentConfig.name}
                </span>
              )}
              {event.iteration && (
                <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                  반복 {event.iteration}회
                </span>
              )}
            </div>
            <span className="text-xs text-gray-500">{formatTime(event.timestamp)}</span>
          </div>

          <p className="mt-1 text-gray-700">{event.message}</p>

          {/* Decision 뱃지 */}
          {event.decision && (
            <div className="mt-2">
              <span
                className={`inline-block px-2 py-1 text-xs rounded ${
                  event.decision === 'approve'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {event.decision === 'approve' ? '승인' : '수정 필요'}
              </span>
            </div>
          )}

          {/* 에러 상세 */}
          {event.error && (
            <div className="mt-2 text-sm text-red-600 bg-red-100 p-2 rounded">
              {event.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
