'use client';

import { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from './game-types';
import { ROLE_COLORS } from './pixel-data';

interface ChatLogProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export default function ChatLog({ messages, isStreaming }: ChatLogProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const formatTime = (ts: number) => {
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="glass-panel rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-mono text-white/60">
          <span className="material-symbols-outlined text-sm text-cyan-400">chat</span>
          Chat Log
        </div>
        <span className="text-xs text-white/30 font-mono">{messages.length} messages</span>
      </div>

      {/* Messages */}
      <div className="max-h-[250px] overflow-y-auto px-4 py-2 space-y-1.5">
        {messages.length === 0 && (
          <div className="text-center py-4 text-white/20 text-xs font-mono">
            Waiting for agents...
          </div>
        )}

        {messages.map((msg) => {
          const colors = ROLE_COLORS[msg.role] || ROLE_COLORS.pi;
          const isSystem = msg.type === 'system' || msg.type === 'phase';
          const hasContent = msg.content && msg.content.length > 0;
          const isExpanded = expandedId === msg.id;

          if (isSystem) {
            return (
              <div key={msg.id} className="text-center">
                <span className="text-[10px] text-white/25 font-mono px-2 py-0.5 rounded-full bg-white/3">
                  {msg.message}
                </span>
              </div>
            );
          }

          const isDecision = msg.type === 'decision';
          const hasScores = isDecision && msg.scores && Object.keys(msg.scores).length > 0;
          const hasFeedback = isDecision && msg.specialist_feedback && Object.keys(msg.specialist_feedback).length > 0;

          return (
            <div
              key={msg.id}
              className={`py-1 hover:bg-white/2 rounded px-1 transition-colors ${isDecision ? 'pb-2' : ''}`}
            >
              <div className="flex items-start gap-2">
                <span className="text-[10px] text-white/20 font-mono mt-0.5 shrink-0">
                  {formatTime(msg.timestamp)}
                </span>
                <span
                  className="text-xs font-bold shrink-0 font-mono"
                  style={{ color: colors.primary }}
                >
                  {msg.name}:
                </span>
                <div className="flex-1 min-w-0">
                  <span className="text-xs text-white/70">{msg.message}</span>
                  {hasContent && !isDecision && (
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : msg.id)}
                      className="ml-1 text-[10px] text-cyan-400/60 hover:text-cyan-400 font-mono"
                    >
                      [{isExpanded ? 'hide' : 'more'}]
                    </button>
                  )}
                  {isExpanded && msg.content && !isDecision && (
                    <div className="mt-1 text-[11px] text-white/40 whitespace-pre-wrap max-h-[120px] overflow-y-auto glass-panel-light rounded p-2 border border-white/5 font-mono">
                      {msg.content.slice(0, 500)}
                      {msg.content.length > 500 && '...'}
                    </div>
                  )}
                </div>
              </div>

              {/* Critic Scores */}
              {hasScores && (
                <div className="ml-[72px] mt-1.5 flex flex-wrap gap-1.5">
                  {Object.entries(msg.scores!).map(([role, score]) => {
                    const color =
                      score >= 5 ? 'text-blue-400 bg-blue-500/10 border-blue-500/30' :
                      score >= 4 ? 'text-green-400 bg-green-500/10 border-green-500/30' :
                      score >= 3 ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30' :
                                   'text-red-400 bg-red-500/10 border-red-500/30';
                    return (
                      <span key={role} className={`text-[10px] px-2 py-0.5 rounded border font-mono ${color}`}>
                        {role}: <strong>{score}/5</strong>
                      </span>
                    );
                  })}
                </div>
              )}

              {/* Specialist Feedback Toggle + Detail */}
              {hasFeedback && (
                <div className="ml-[72px] mt-1.5">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : msg.id)}
                    className="text-[10px] text-cyan-400/60 hover:text-cyan-400 font-mono"
                  >
                    [{isExpanded ? 'hide feedback' : 'show feedback'}]
                  </button>
                  {isExpanded && (
                    <div className="mt-1.5 space-y-1.5">
                      {Object.entries(msg.specialist_feedback!).map(([role, feedback]) => {
                        const score = msg.scores?.[role];
                        const scoreColor =
                          !score ? '' :
                          score >= 4 ? 'text-green-400' :
                          score >= 3 ? 'text-yellow-400' :
                                       'text-red-400';
                        return (
                          <div key={role} className="glass-panel-light rounded p-2 border border-white/5">
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className="text-[10px] font-bold text-emerald-400 font-mono">{role}</span>
                              {score != null && (
                                <span className={`text-[10px] font-mono ${scoreColor}`}>{score}/5</span>
                              )}
                            </div>
                            <p className="text-[10px] text-white/50 whitespace-pre-wrap leading-relaxed">{feedback}</p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {isStreaming && messages.length > 0 && (
          <div className="flex items-center gap-1 px-1 py-1">
            <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
