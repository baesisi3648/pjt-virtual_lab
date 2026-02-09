/**
 * @TASK P4-T2 - Live Process Timeline (Chat-style)
 *
 * 에이전트 간 대화를 채팅 형태로 실시간 표시하는 컴포넌트
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
  content?: string;
  scores?: Record<string, number>;
  error?: string;
}

// Props 타입
interface ProcessTimelineProps {
  topic: string;
  constraints?: string;
  onComplete?: (report: string) => void;
  onError?: (error: string) => void;
}

// 에이전트별 설정
const AGENT_CONFIG = {
  scientist: {
    icon: '🔬',
    name: 'Scientist',
    role: '과학 전문가',
    color: 'text-blue-400',
    bgColor: 'bg-blue-950/50',
    borderColor: 'border-blue-800/60',
    accentColor: 'bg-blue-500',
  },
  critic: {
    icon: '🔍',
    name: 'Critic',
    role: '검증 비평가',
    color: 'text-amber-400',
    bgColor: 'bg-amber-950/50',
    borderColor: 'border-amber-800/60',
    accentColor: 'bg-amber-500',
  },
  pi: {
    icon: '👔',
    name: 'PI',
    role: '총괄 책임자',
    color: 'text-green-400',
    bgColor: 'bg-green-950/50',
    borderColor: 'border-green-800/60',
    accentColor: 'bg-green-500',
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
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());
  const timelineEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isStreamingRef = useRef(false);

  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const toggleExpand = (index: number) => {
    setExpandedMessages((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // 자동 스크롤
  useEffect(() => {
    timelineEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  // SSE 연결
  useEffect(() => {
    if (!topic) return;
    if (isStreamingRef.current) return;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const startStreaming = async () => {
      isStreamingRef.current = true;
      setIsStreaming(true);
      setEvents([]);
      setCurrentReport('');
      setExpandedMessages(new Set());

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      try {
        const response = await fetch(`${API_BASE_URL}/api/research/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic, constraints: constraints || '' }),
          signal: abortController.signal,
        });

        if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`);

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) throw new Error('No response body');

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            setIsStreaming(false);
            isStreamingRef.current = false;
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event: TimelineEvent = JSON.parse(line.slice(6));
                setEvents((prev) => [...prev, event]);

                if (event.type === 'complete' && event.report) {
                  setCurrentReport(event.report);
                  onCompleteRef.current?.(event.report);
                }
                if (event.type === 'error' && event.error) {
                  onErrorRef.current?.(event.error);
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', line, e);
              }
            }
          }
        }
      } catch (error) {
        if (abortController.signal.aborted) return;
        console.error('SSE connection error:', error);
        setIsStreaming(false);
        isStreamingRef.current = false;
        onErrorRef.current?.(error instanceof Error ? error.message : 'Unknown error');
      }
    };

    startStreaming();

    return () => {
      abortController.abort();
      isStreamingRef.current = false;
      setIsStreaming(false);
    };
  }, [topic, constraints]);

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* 헤더 */}
      <div className="bg-gray-900 rounded-t-lg border border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">연구 진행 상황</h2>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-xs bg-blue-900/50 text-blue-300 px-2.5 py-1 rounded-full border border-blue-800/50">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                진행 중
              </span>
            )}
          </div>
          <span className="text-xs text-gray-500">
            {events.filter(e => e.type === 'agent' || e.type === 'decision').length}개 메시지
          </span>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="bg-gray-950 border-x border-gray-800 px-6 py-4 space-y-4 max-h-[600px] overflow-y-auto">
        {events.length === 0 && isStreaming && (
          <div className="flex items-center justify-center py-12 text-gray-500">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-3"></div>
              <p>에이전트에 연결 중...</p>
            </div>
          </div>
        )}

        {events.map((event, index) => (
          <MessageItem
            key={index}
            event={event}
            index={index}
            isExpanded={expandedMessages.has(index)}
            onToggle={() => toggleExpand(index)}
          />
        ))}

        {/* 스트리밍 중 타이핑 인디케이터 */}
        {isStreaming && events.length > 0 && events[events.length - 1].type !== 'complete' && (
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm text-gray-500">에이전트가 작업 중입니다...</span>
          </div>
        )}

        <div ref={timelineEndRef} />
      </div>

      {/* 하단 상태바 */}
      <div className="bg-gray-900 rounded-b-lg border border-gray-800 px-6 py-3">
        {currentReport ? (
          <div className="flex items-center gap-2 text-green-400 text-sm">
            <span>✅</span>
            <span>연구 완료 - 보고서 {currentReport.length.toLocaleString()}자 생성됨</span>
          </div>
        ) : isStreaming ? (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="animate-pulse h-2 w-2 rounded-full bg-blue-400"></div>
            <span>워크플로우 실행 중...</span>
          </div>
        ) : (
          <div className="text-gray-500 text-sm">대기 중</div>
        )}
      </div>
    </div>
  );
}

// 개별 메시지 아이템
function MessageItem({
  event,
  index,
  isExpanded,
  onToggle,
}: {
  event: TimelineEvent;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const agentConfig = event.agent ? AGENT_CONFIG[event.agent] : null;

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'Asia/Seoul',
    });
  };

  // 시스템 메시지 (start, iteration, complete, error)
  if (!agentConfig) {
    if (event.type === 'start') {
      return (
        <div className="flex justify-center">
          <div className="bg-gray-800/50 text-gray-400 text-xs px-4 py-1.5 rounded-full border border-gray-700/50">
            🚀 {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'iteration') {
      return (
        <div className="flex justify-center">
          <div className="bg-amber-900/30 text-amber-400 text-xs px-4 py-1.5 rounded-full border border-amber-800/40">
            🔄 {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'complete') {
      return (
        <div className="flex justify-center">
          <div className="bg-green-900/30 text-green-400 text-xs px-4 py-1.5 rounded-full border border-green-800/40">
            ✅ {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'error') {
      return (
        <div className="bg-red-950/50 border border-red-800/60 rounded-lg p-4">
          <p className="text-red-400 font-medium">❌ 오류 발생</p>
          <p className="text-red-300 text-sm mt-1">{event.message}</p>
          {event.error && (
            <pre className="text-red-300/70 text-xs mt-2 overflow-x-auto">{event.error}</pre>
          )}
        </div>
      );
    }
    // phase 이벤트
    return (
      <div className="flex justify-center">
        <div className="bg-gray-800/50 text-gray-400 text-xs px-4 py-1.5 rounded-full border border-gray-700/50">
          {event.message}
        </div>
      </div>
    );
  }

  // 에이전트 메시지 (채팅 버블)
  const hasContent = event.content && event.content.length > 0;
  const contentPreview = event.content
    ? event.content.length > 300
      ? event.content.slice(0, 300) + '...'
      : event.content
    : '';

  return (
    <div className={`rounded-lg border ${agentConfig.borderColor} ${agentConfig.bgColor} overflow-hidden`}>
      {/* 메시지 헤더 */}
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="text-2xl">{agentConfig.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${agentConfig.color}`}>{agentConfig.name}</span>
            <span className="text-xs text-gray-500">{agentConfig.role}</span>
            {event.iteration != null && (
              <span className="text-xs bg-gray-700/50 text-gray-400 px-2 py-0.5 rounded">
                {event.iteration}회차
              </span>
            )}
          </div>
          <p className="text-gray-200 text-sm mt-0.5">{event.message}</p>
        </div>
        <span className="text-xs text-gray-500 font-mono shrink-0">{formatTime(event.timestamp)}</span>
      </div>

      {/* Critic 점수 표시 */}
      {event.scores && Object.keys(event.scores).length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex flex-wrap gap-2">
            {Object.entries(event.scores).map(([key, value]) => {
              const label: Record<string, string> = {
                scientific: '과학적 근거',
                universal: '범용성',
                regulation: '규제 비례성',
                completeness: '구조적 완전성',
              };
              const scoreColor = value >= 4 ? 'text-green-400 bg-green-900/40 border-green-800/50' :
                value >= 3 ? 'text-yellow-400 bg-yellow-900/40 border-yellow-800/50' :
                  'text-red-400 bg-red-900/40 border-red-800/50';
              return (
                <span key={key} className={`text-xs px-2.5 py-1 rounded border ${scoreColor}`}>
                  {label[key] || key}: {value}/5
                </span>
              );
            })}
          </div>
          {/* 승인/수정 뱃지 */}
          {event.decision && (
            <div className="mt-2">
              <span className={`inline-flex items-center gap-1 px-3 py-1 text-sm rounded-full font-medium ${event.decision === 'approve'
                  ? 'bg-green-900/50 text-green-300 border border-green-700/50'
                  : 'bg-red-900/50 text-red-300 border border-red-700/50'
                }`}>
                {event.decision === 'approve' ? '✅ 승인' : '📝 수정 요청'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 상세 내용 (접기/펼치기) */}
      {hasContent && (
        <div className="border-t border-gray-700/30">
          <button
            onClick={onToggle}
            className="w-full px-4 py-2 text-left text-xs text-gray-400 hover:text-gray-300 hover:bg-gray-800/30 transition-colors flex items-center gap-1"
          >
            <span className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}>▶</span>
            {isExpanded ? '내용 접기' : '상세 내용 보기'}
            <span className="text-gray-600 ml-1">({event.content!.length.toLocaleString()}자)</span>
          </button>
          {isExpanded && (
            <div className="px-4 pb-4">
              <div className="bg-gray-900/50 rounded-lg p-4 text-sm text-gray-300 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed border border-gray-700/30">
                {event.content}
              </div>
            </div>
          )}
          {!isExpanded && contentPreview && (
            <div className="px-4 pb-3">
              <p className="text-xs text-gray-500 line-clamp-2">{contentPreview}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
