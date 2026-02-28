'use client';

import { useEffect, useRef, useState } from 'react';
import type { ChatMessage, GamePhase } from './game-types';

interface ChatLogProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  phase?: GamePhase;
  currentRound?: number;
}

/** Agent icon/color config by role */
const AGENT_CONFIG: Record<string, { icon: string; label: string; color: string; bgColor: string; badgeBg: string }> = {
  pi: {
    icon: 'psychology',
    label: 'PI Agent',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    badgeBg: 'bg-blue-100 text-blue-700',
  },
  critic: {
    icon: 'gavel',
    label: 'Critic Agent',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50 border-amber-200',
    badgeBg: 'bg-amber-100 text-amber-700',
  },
  specialist: {
    icon: 'biotech',
    label: 'Specialist',
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 border-emerald-200',
    badgeBg: 'bg-emerald-100 text-emerald-700',
  },
};

/** Phase display labels */
const PHASE_LABELS: Record<string, string> = {
  planning: 'PLANNING',
  researching: 'RESEARCHING',
  critique: 'REVIEWING',
  pi_summary: 'SUMMARIZING',
  round_revision: 'REVISING',
  final_synthesis: 'SYNTHESIZING',
  complete: 'COMPLETED',
};

function StatusDot({ status }: { status: 'completed' | 'active' | 'pending' }) {
  if (status === 'completed') {
    return (
      <div className="w-8 h-8 rounded-full bg-[#1b7440] flex items-center justify-center shadow-sm">
        <span className="material-symbols-outlined text-white text-sm">check</span>
      </div>
    );
  }
  if (status === 'active') {
    return (
      <div className="relative w-8 h-8 rounded-full border-2 border-[#1b7440] bg-white flex items-center justify-center">
        <span className="w-3 h-3 rounded-full bg-[#1b7440] animate-pulse" />
      </div>
    );
  }
  return (
    <div className="w-8 h-8 rounded-full border-2 border-[#dde4e0] bg-white flex items-center justify-center">
      <span className="w-2.5 h-2.5 rounded-full bg-[#dde4e0]" />
    </div>
  );
}

function StatusBadge({ status, phase }: { status: 'completed' | 'active' | 'pending'; phase?: string }) {
  if (status === 'completed') {
    return (
      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#e8f5ed] text-[#1b7440]">
        Completed
      </span>
    );
  }
  if (status === 'active') {
    const label = phase ? PHASE_LABELS[phase] || phase.toUpperCase() : 'PROCESSING';
    return (
      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-700 animate-pulse">
        {label}...
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-100 text-gray-400">
      Pending
    </span>
  );
}

function ScoreBadge({ role, score }: { role: string; score: number }) {
  const color =
    score >= 5 ? 'bg-blue-100 text-blue-700 border-blue-200' :
    score >= 4 ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
    score >= 3 ? 'bg-amber-100 text-amber-700 border-amber-200' :
                 'bg-red-100 text-red-700 border-red-200';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-semibold ${color}`}>
      {role}: {score}/5
    </span>
  );
}

function formatTime(ts: number) {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function ChatLog({ messages, isStreaming, phase, currentRound }: ChatLogProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const getMessageStatus = (msg: ChatMessage, idx: number): 'completed' | 'active' | 'pending' => {
    if (msg.type === 'system' || msg.type === 'phase') return 'completed';
    // Last non-system message while streaming is active
    const isLastAgent = isStreaming && idx === messages.length - 1;
    if (isLastAgent) return 'active';
    return 'completed';
  };

  return (
    <div className="bg-white border border-[#dde4e0] rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#dde4e0] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[#1b7440]">timeline</span>
          <h3 className="text-sm font-bold text-[#121714] uppercase tracking-wider">Agent Activity</h3>
        </div>
        <div className="flex items-center gap-3">
          {currentRound != null && currentRound > 0 && (
            <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-[#e8f5ed] text-[#1b7440]">
              Round {currentRound}
            </span>
          )}
          <span className="text-xs text-[#678373]">{messages.filter(m => m.type === 'agent' || m.type === 'decision').length} activities</span>
        </div>
      </div>

      {/* Timeline */}
      <div className="max-h-[600px] overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="text-center py-12 text-[#678373]">
            <span className="material-symbols-outlined text-4xl mb-2 block opacity-40">hourglass_empty</span>
            <p className="text-sm">Waiting for agents to start...</p>
          </div>
        )}

        <div className="relative">
          {/* Vertical line */}
          {messages.length > 0 && (
            <div className="absolute left-[15px] top-4 bottom-4 w-0.5 bg-gradient-to-b from-[#1b7440]/30 via-[#dde4e0] to-[#dde4e0]/50" />
          )}

          {messages.map((msg, idx) => {
            const isSystem = msg.type === 'system' || msg.type === 'phase';
            const isDecision = msg.type === 'decision';
            const status = getMessageStatus(msg, idx);
            const config = AGENT_CONFIG[msg.role] || AGENT_CONFIG.specialist;
            const isExpanded = expandedIds.has(msg.id);
            const hasContent = msg.content && msg.content.length > 0;
            const hasScores = isDecision && msg.scores && Object.keys(msg.scores).length > 0;
            const hasFeedback = isDecision && msg.specialist_feedback && Object.keys(msg.specialist_feedback).length > 0;

            // System/phase messages: divider style
            if (isSystem) {
              return (
                <div key={msg.id} className="relative flex items-center gap-4 py-3">
                  <StatusDot status="completed" />
                  <div className="flex-1 flex items-center gap-3">
                    <span className="text-xs font-semibold text-[#678373] uppercase tracking-wider">
                      {msg.message}
                    </span>
                    <div className="flex-1 h-px bg-[#dde4e0]" />
                    <span className="text-[10px] text-[#678373]/60">{formatTime(msg.timestamp)}</span>
                  </div>
                </div>
              );
            }

            // Agent/Decision messages: card style
            return (
              <div key={msg.id} className="relative flex items-start gap-4 py-2">
                {/* Status dot */}
                <div className="flex-shrink-0 z-10 mt-3">
                  <StatusDot status={status} />
                </div>

                {/* Card */}
                <div className={`flex-1 rounded-xl border p-4 transition-all ${
                  status === 'active'
                    ? 'bg-white border-[#1b7440]/30 shadow-md ring-1 ring-[#1b7440]/10'
                    : 'bg-[#f6f8f7] border-[#dde4e0] hover:border-[#c5d0c9]'
                }`}>
                  {/* Card header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                        msg.role === 'pi' ? 'bg-blue-100' :
                        msg.role === 'critic' ? 'bg-amber-100' :
                        'bg-emerald-100'
                      }`}>
                        <span className={`material-symbols-outlined text-sm ${config.color}`}>
                          {config.icon}
                        </span>
                      </div>
                      <div>
                        <span className="text-sm font-bold text-[#121714]">
                          {msg.name !== 'PI' && msg.name !== 'Critic' && msg.name !== 'Specialist'
                            ? msg.name
                            : config.label}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={status} phase={phase} />
                      <span className="text-[10px] text-[#678373]/60">{formatTime(msg.timestamp)}</span>
                    </div>
                  </div>

                  {/* Message summary */}
                  <p className="text-sm text-[#3a4d42] leading-relaxed">{msg.message}</p>

                  {/* Scores (for decision messages) */}
                  {hasScores && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {Object.entries(msg.scores!).map(([role, score]) => (
                        <ScoreBadge key={role} role={role} score={score} />
                      ))}
                    </div>
                  )}

                  {/* Expand/Collapse for content */}
                  {(hasContent || hasFeedback) && (
                    <div className="mt-3">
                      <button
                        onClick={() => toggleExpand(msg.id)}
                        className="inline-flex items-center gap-1 text-xs font-medium text-[#1b7440] hover:text-[#13542e] transition-colors"
                      >
                        <span className="material-symbols-outlined text-sm">
                          {isExpanded ? 'expand_less' : 'expand_more'}
                        </span>
                        {isExpanded ? '접기' : '자세히 보기'}
                      </button>

                      {isExpanded && (
                        <div className="mt-2 space-y-3">
                          {/* Full content */}
                          {hasContent && (
                            <div className="bg-white rounded-lg border border-[#dde4e0] p-4">
                              <p className="text-xs text-[#3a4d42] whitespace-pre-wrap leading-relaxed">
                                {msg.content}
                              </p>
                            </div>
                          )}

                          {/* Specialist feedback */}
                          {hasFeedback && (
                            <div className="space-y-2">
                              <p className="text-[11px] font-bold text-[#678373] uppercase tracking-wider">
                                Specialist Feedback
                              </p>
                              {Object.entries(msg.specialist_feedback!).map(([role, feedback]) => {
                                const score = msg.scores?.[role];
                                return (
                                  <div key={role} className="bg-white rounded-lg border border-[#dde4e0] p-3">
                                    <div className="flex items-center gap-2 mb-1.5">
                                      <span className="text-xs font-bold text-emerald-700">{role}</span>
                                      {score != null && <ScoreBadge role="" score={score} />}
                                    </div>
                                    <p className="text-xs text-[#3a4d42] whitespace-pre-wrap leading-relaxed">
                                      {feedback}
                                    </p>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Streaming indicator */}
          {isStreaming && messages.length > 0 && (
            <div className="relative flex items-center gap-4 py-3">
              <div className="flex-shrink-0 z-10">
                <div className="relative w-8 h-8 rounded-full border-2 border-[#1b7440]/40 bg-white flex items-center justify-center">
                  <span className="w-2 h-2 rounded-full bg-[#1b7440] animate-ping" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-[#1b7440] rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-[#1b7440] rounded-full animate-bounce [animation-delay:150ms]" />
                  <div className="w-1.5 h-1.5 bg-[#1b7440] rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-xs text-[#678373]">Processing...</span>
              </div>
            </div>
          )}
        </div>

        <div ref={endRef} />
      </div>
    </div>
  );
}
