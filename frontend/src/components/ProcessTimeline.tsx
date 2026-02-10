/**
 * @TASK P4-T2 - Live Process Timeline (Chat-style)
 *
 * 에이전트 간 대화를 채팅 형태로 실시간 표시하는 컴포넌트
 * Server-Sent Events (SSE)를 사용하여 백엔드로부터 이벤트를 스트리밍
 *
 * REDESIGN: 3라운드 팀 회의 워크플로우 UI
 * - 라운드 구분선 표시
 * - 전문가별 점수/피드백 표시
 * - 모든 라운드 내용 누적 표시
 */

'use client';

import { useEffect, useState, useRef } from 'react';

// 타임라인 이벤트 타입
interface TimelineEvent {
  type: 'start' | 'phase' | 'agent' | 'decision' | 'iteration' | 'complete' | 'error';
  timestamp: number;
  message: string;
  agent?: 'scientist' | 'critic' | 'pi' | 'specialist';
  phase?: string;
  decision?: string;
  round?: number;
  report?: string;
  content?: string;
  scores?: Record<string, number>;
  specialist_feedback?: Record<string, string>;
  error?: string;
  saved_filename?: string;
  specialist_name?: string;
  specialist_focus?: string;
}

// Props 타입
interface ProcessTimelineProps {
  topic: string;
  constraints?: string;
  onComplete?: (report: string, filename?: string) => void;
  onError?: (error: string) => void;
}

// 에이전트별 설정 (Material Symbols 아이콘)
const AGENT_CONFIG: Record<string, {
  icon: string;
  name: string;
  role: string;
  color: string;
  borderColor: string;
  iconBg: string;
}> = {
  scientist: {
    icon: 'science',
    name: 'Scientist',
    role: '과학 전문가',
    color: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    iconBg: 'bg-blue-500/20',
  },
  critic: {
    icon: 'fact_check',
    name: 'Critic',
    role: '검증 비평가',
    color: 'text-cyan-400',
    borderColor: 'border-cyan-500/30',
    iconBg: 'bg-cyan-500/20',
  },
  pi: {
    icon: 'psychology',
    name: 'PI',
    role: '총괄 책임자',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/30',
    iconBg: 'bg-purple-500/20',
  },
  specialist: {
    icon: 'biotech',
    name: 'Specialist',
    role: '전문가',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
    iconBg: 'bg-emerald-500/20',
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
                  onCompleteRef.current?.(event.report, event.saved_filename);
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
      {/* 헤더 - glass-panel with terminal icon */}
      <div className="glass-panel rounded-t-lg px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-cyan-400 text-2xl">terminal</span>
            <h2 className="text-xl font-bold text-white neon-text">System Log</h2>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-xs glass-panel-light text-cyan-300 px-3 py-1.5 rounded-full border border-cyan-500/30">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
                STREAMING
              </span>
            )}
          </div>
          <span className="glass-panel-light px-3 py-1 rounded-full text-xs text-gray-400 font-mono border border-white/5">
            {events.filter(e => e.type === 'agent' || e.type === 'decision').length} messages
          </span>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="glass-panel border-x-0 rounded-none px-6 py-4 space-y-4 max-h-[600px] overflow-y-auto bg-grid">
        {events.length === 0 && isStreaming && (
          <div className="flex items-center justify-center py-12 text-gray-500">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto mb-3"></div>
              <p className="font-mono text-sm">Connecting to agents...</p>
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
              <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm text-gray-400 font-mono">에이전트가 작업 중입니다...</span>
          </div>
        )}

        <div ref={timelineEndRef} />
      </div>

      {/* 하단 상태바 - glass-panel */}
      <div className="glass-panel rounded-b-lg px-6 py-3">
        {currentReport ? (
          <div className="flex items-center gap-2 text-green-400 text-sm font-mono">
            <span className="material-symbols-outlined text-lg">check_circle</span>
            <span>연구 완료 - 보고서 {currentReport.length.toLocaleString()}자 생성됨</span>
          </div>
        ) : isStreaming ? (
          <div className="flex items-center gap-2 text-gray-400 text-sm font-mono">
            <div className="animate-pulse h-2 w-2 rounded-full bg-cyan-400"></div>
            <span>3라운드 팀 회의 진행 중...</span>
          </div>
        ) : (
          <div className="text-gray-500 text-sm font-mono">IDLE</div>
        )}
      </div>
    </div>
  );
}

// 전문가별 피드백 패널
function SpecialistFeedbackPanel({ specialistFeedback, scores }: { specialistFeedback: Record<string, string>; scores?: Record<string, number> }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mt-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center gap-1 transition-colors"
      >
        <span className={`material-symbols-outlined text-sm transition-transform ${isOpen ? 'rotate-90' : ''}`}>
          play_arrow
        </span>
        전문가별 상세 피드백 ({Object.keys(specialistFeedback).length}건)
      </button>
      {isOpen && (
        <div className="mt-2 space-y-2">
          {Object.entries(specialistFeedback).map(([role, feedback]) => {
            const score = scores?.[role];
            return (
              <div key={role} className="glass-panel-light rounded p-3 border border-white/5">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold text-emerald-400 font-mono">{role}</span>
                  {score != null && (
                    <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                      score >= 4 ? 'text-green-400 bg-green-500/10 border border-green-500/30' :
                      score >= 3 ? 'text-yellow-400 bg-yellow-500/10 border border-yellow-500/30' :
                      'text-red-400 bg-red-500/10 border border-red-500/30'
                    }`}>
                      {score}/5
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-300 whitespace-pre-wrap">{feedback}</p>
              </div>
            );
          })}
        </div>
      )}
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
          <div className="glass-panel-light text-gray-400 text-xs px-4 py-2 rounded-full border border-white/10 font-mono">
            <span className="material-symbols-outlined text-sm align-middle mr-1">rocket_launch</span>
            {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'iteration') {
      return (
        <div className="flex justify-center my-2">
          <div className="glass-panel text-amber-400 text-sm px-6 py-2.5 rounded-full border border-amber-500/30 font-mono font-bold">
            <span className="material-symbols-outlined text-base align-middle mr-1">groups</span>
            {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'complete') {
      return (
        <div className="flex justify-center">
          <div className="glass-panel text-green-400 text-xs px-4 py-2 rounded-full border border-green-500/30 font-mono">
            <span className="material-symbols-outlined text-sm align-middle mr-1">check_circle</span>
            {event.message}
          </div>
        </div>
      );
    }
    if (event.type === 'error') {
      return (
        <div className="glass-panel border-l-4 border-red-500 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="material-symbols-outlined text-red-400">error</span>
            <p className="text-red-400 font-bold font-mono">ERROR</p>
          </div>
          <p className="text-red-300 text-sm">{event.message}</p>
          {event.error && (
            <pre className="text-red-300/70 text-xs mt-2 overflow-x-auto font-mono bg-black/20 p-2 rounded">{event.error}</pre>
          )}
        </div>
      );
    }
    // phase 이벤트
    return (
      <div className="flex justify-center">
        <div className="glass-panel-light text-gray-400 text-xs px-4 py-2 rounded-full border border-white/5 font-mono">
          {event.message}
        </div>
      </div>
    );
  }

  // 에이전트 메시지 (채팅 버블 with glass-panel)
  const hasContent = event.content && event.content.length > 0;
  const contentPreview = event.content
    ? event.content.length > 300
      ? event.content.slice(0, 300) + '...'
      : event.content
    : '';

  // 전문가(specialist)의 경우 동적 이름 표시
  const displayName = event.specialist_name || agentConfig.name;
  const displayRole = event.specialist_focus || agentConfig.role;

  return (
    <div className={`glass-panel rounded-lg border-l-4 ${agentConfig.borderColor} overflow-hidden glass-panel-hover transition-all duration-200`}>
      {/* 메시지 헤더 */}
      <div className="flex items-center gap-3 px-4 py-3">
        {/* 에이전트 아이콘 (Material Symbols in colored circle) */}
        <div className={`flex items-center justify-center w-10 h-10 rounded-full ${agentConfig.iconBg} border ${agentConfig.borderColor}`}>
          <span className={`material-symbols-outlined ${agentConfig.color} text-xl`}>
            {agentConfig.icon}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-bold ${agentConfig.color} font-mono text-sm`}>{displayName}</span>
            <span className="text-xs text-gray-500">{displayRole}</span>
            {event.round != null && (
              <span className="text-xs glass-panel-light text-gray-400 px-2 py-0.5 rounded border border-white/5 font-mono">
                R{event.round}
              </span>
            )}
          </div>
          <p className="text-gray-200 text-sm mt-1">{event.message}</p>
        </div>
        <span className="text-xs text-gray-500 font-mono shrink-0">{formatTime(event.timestamp)}</span>
      </div>

      {/* Critic 점수 표시 (전문가별 동적 표시) */}
      {event.scores && Object.keys(event.scores).length > 0 && (
        <div className="px-4 pb-3">
          <div className="flex flex-wrap gap-2">
            {Object.entries(event.scores).map(([key, value]) => {
              const scoreClass = value >= 5
                ? 'glass-panel text-blue-400 border-blue-500/40'
                : value >= 4
                  ? 'glass-panel text-green-400 border-green-500/40'
                  : value >= 3
                    ? 'glass-panel text-yellow-400 border-yellow-500/40'
                    : 'glass-panel text-red-400 border-red-500/40';
              return (
                <span key={key} className={`text-xs px-3 py-1.5 rounded font-mono ${scoreClass}`}>
                  {key}: <strong>{value}/5</strong>
                </span>
              );
            })}
          </div>
          {/* 전문가별 피드백 (접기/펼치기) */}
          {event.specialist_feedback && Object.keys(event.specialist_feedback).length > 0 && (
            <SpecialistFeedbackPanel specialistFeedback={event.specialist_feedback} scores={event.scores} />
          )}
        </div>
      )}

      {/* 상세 내용 (접기/펼치기) */}
      {hasContent && !event.scores && (
        <div className="border-t border-white/5">
          <button
            onClick={onToggle}
            className="w-full px-4 py-2.5 text-left text-xs text-gray-400 hover:text-cyan-300 hover:bg-white/5 transition-all flex items-center gap-2 font-mono"
          >
            <span className={`material-symbols-outlined text-sm transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
              play_arrow
            </span>
            {isExpanded ? '내용 접기' : '상세 내용 보기'}
            <span className="text-gray-600 ml-1">({event.content!.length.toLocaleString()}자)</span>
          </button>
          {isExpanded && (
            <div className="px-4 pb-4">
              <div className="glass-panel-light rounded-lg p-4 text-sm text-gray-300 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed border border-white/5 font-mono">
                {event.content}
              </div>
            </div>
          )}
          {!isExpanded && contentPreview && (
            <div className="px-4 pb-3">
              <p className="text-xs text-gray-500 line-clamp-2 font-mono">{contentPreview}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
