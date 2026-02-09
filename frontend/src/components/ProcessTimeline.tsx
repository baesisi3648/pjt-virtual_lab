/**
 * @TASK P4-T2 - Live Process Timeline
 * @SPEC TASKS.md#P4-T2
 *
 * 에이전트 상태를 실시간으로 시각화하는 타임라인 컴포넌트
 * Server-Sent Events (SSE)를 사용하여 백엔드로부터 이벤트를 스트리밍
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

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

// 에이전트별 아이콘 및 색상 (다크모드)
const AGENT_CONFIG = {
  scientist: {
    icon: '🔬',
    name: 'Scientist',
    color: 'text-blue-400',
    bgColor: 'bg-blue-950',
    borderColor: 'border-blue-800',
  },
  critic: {
    icon: '🔍',
    name: 'Critic',
    color: 'text-red-400',
    bgColor: 'bg-red-950',
    borderColor: 'border-red-800',
  },
  pi: {
    icon: '👔',
    name: 'PI',
    color: 'text-green-400',
    bgColor: 'bg-green-950',
    borderColor: 'border-green-800',
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
  const timelineEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isStreamingRef = useRef(false);

  // 콜백을 ref로 관리하여 useEffect 재실행 방지
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  // 자동 스크롤
  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  // SSE 연결 - topic/constraints만 의존성으로 사용
  useEffect(() => {
    if (!topic) return;

    // 이미 스트리밍 중이면 중복 실행 방지
    if (isStreamingRef.current) return;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const startStreaming = async () => {
      isStreamingRef.current = true;
      setIsStreaming(true);
      setEvents([]);
      setCurrentReport('');

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`Stream failed: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body');
        }

        let buffer = '';

        // 스트림 읽기
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            setIsStreaming(false);
            isStreamingRef.current = false;
            break;
          }

          // SSE 데이터 파싱 (버퍼링으로 부분 청크 처리)
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 유지

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              try {
                const event: TimelineEvent = JSON.parse(data);

                // 이벤트 추가
                setEvents((prev) => [...prev, event]);

                // 완료 이벤트 처리
                if (event.type === 'complete' && event.report) {
                  setCurrentReport(event.report);
                  onCompleteRef.current?.(event.report);
                }

                // 에러 이벤트 처리
                if (event.type === 'error' && event.error) {
                  onErrorRef.current?.(event.error);
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', data, e);
              }
            }
          }
        }
      } catch (error) {
        if (abortController.signal.aborted) return; // 정상 취소
        console.error('SSE connection error:', error);
        setIsStreaming(false);
        isStreamingRef.current = false;
        onErrorRef.current?.(error instanceof Error ? error.message : 'Unknown error');
      }
    };

    startStreaming();

    // Cleanup
    return () => {
      abortController.abort();
      isStreamingRef.current = false;
      setIsStreaming(false);
    };
  }, [topic, constraints]); // onComplete, onError 제거!

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-gray-900 rounded-lg shadow-lg border border-gray-800">
      <h2 className="text-2xl font-bold mb-6 text-white">연구 진행 상황</h2>

      {/* 타임라인 */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {events.map((event, index) => (
          <TimelineItem key={index} event={event} />
        ))}

        {/* 스트리밍 중 인디케이터 */}
        {isStreaming && events.length === 0 && (
          <div className="flex items-center gap-2 text-gray-400">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
            <span>연결 중...</span>
          </div>
        )}

        {isStreaming && events.length > 0 && (
          <div className="flex items-center gap-2 text-gray-400 p-3">
            <div className="animate-pulse h-2 w-2 rounded-full bg-blue-400"></div>
            <span className="text-sm">처리 중...</span>
          </div>
        )}

        <div ref={timelineEndRef} />
      </div>

      {/* 최종 보고서 미리보기 */}
      {currentReport && (
        <div className="mt-6 p-4 bg-green-950 border border-green-800 rounded">
          <h3 className="font-semibold text-green-400 mb-2">연구 완료</h3>
          <p className="text-sm text-gray-300">
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

  // 타임스탬프 포맷팅 (서울 시간대)
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'Asia/Seoul',
    });
  };

  // 이벤트 타입별 스타일링 (다크모드)
  let bgClass = 'bg-gray-800';
  let borderClass = 'border-gray-700';

  if (event.type === 'start') {
    bgClass = 'bg-blue-950';
    borderClass = 'border-blue-800';
  } else if (event.type === 'complete') {
    bgClass = 'bg-green-950';
    borderClass = 'border-green-800';
  } else if (event.type === 'error') {
    bgClass = 'bg-red-950';
    borderClass = 'border-red-800';
  } else if (agentConfig) {
    bgClass = agentConfig.bgColor;
    borderClass = agentConfig.borderColor;
  }

  return (
    <div className={`p-4 rounded-lg border ${bgClass} ${borderClass}`}>
      <div className="flex items-start gap-3">
        {/* 아이콘 */}
        <div className="text-2xl">
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
              {event.iteration != null && (
                <span className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                  반복 {event.iteration}회
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400 font-mono">{formatTime(event.timestamp)}</span>
          </div>

          <p className="mt-1 text-gray-200">{event.message}</p>

          {/* Decision 뱃지 */}
          {event.decision && (
            <div className="mt-2">
              <span
                className={`inline-block px-2 py-1 text-xs rounded font-medium ${
                  event.decision === 'approve'
                    ? 'bg-green-900 text-green-300 border border-green-700'
                    : 'bg-red-900 text-red-300 border border-red-700'
                }`}
              >
                {event.decision === 'approve' ? '승인' : '수정 필요'}
              </span>
            </div>
          )}

          {/* 에러 상세 */}
          {event.error && (
            <div className="mt-2 text-sm text-red-300 bg-red-950 border border-red-800 p-2 rounded">
              {event.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
