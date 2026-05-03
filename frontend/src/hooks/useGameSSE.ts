'use client';

import { useEffect, useReducer, useRef, useCallback } from 'react';
import {
  GameState,
  INITIAL_GAME_STATE,
  getSceneForPhase,
  parsePhase,
  type CharacterState,
} from '@/components/game/game-types';

// SSE event from backend (same as ProcessTimeline)
interface SSEEvent {
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

type GameAction =
  | { type: 'SSE_EVENT'; event: SSEEvent }
  | { type: 'RESET' }
  | { type: 'START_STREAM' };

let msgIdCounter = 0;

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'RESET':
      msgIdCounter = 0;
      return { ...INITIAL_GAME_STATE };

    case 'START_STREAM':
      return { ...state, isStreaming: true, phase: 'idle', chatLog: [], error: undefined };

    case 'SSE_EVENT': {
      const { event } = action;
      const newState = { ...state };
      newState.characters = state.characters.map(c => ({ ...c }));
      newState.chatLog = [...state.chatLog];

      switch (event.type) {
        case 'start': {
          newState.phase = 'planning';
          newState.scene = 'meeting';
          newState.characters = newState.characters.map(c =>
            c.role === 'pi' ? { ...c, status: 'active' as const } : c
          );
          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'pi',
            name: 'System',
            message: event.message,
            type: 'system',
          });
          break;
        }

        case 'phase': {
          const phase = parsePhase(event.phase || '');
          newState.phase = phase;
          newState.scene = getSceneForPhase(phase);

          newState.characters = newState.characters.map(c => ({
            ...c,
            status: 'idle' as const,
            message: undefined,
          }));

          if (phase === 'researching' || phase === 'round_revision') {
            newState.characters = newState.characters.map(c =>
              c.role === 'specialist' ? { ...c, status: 'active' as const } : c
            );
          } else if (phase === 'critique') {
            newState.characters = newState.characters.map(c =>
              c.role === 'critic' ? { ...c, status: 'active' as const } : c
            );
          } else if (phase === 'pi_summary' || phase === 'final_synthesis') {
            newState.characters = newState.characters.map(c =>
              c.role === 'pi' ? { ...c, status: 'active' as const } : c
            );
          }

          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'pi',
            name: 'System',
            message: event.message,
            type: 'phase',
          });
          break;
        }

        case 'agent': {
          const agentRole = event.agent === 'scientist' ? 'specialist' as const : (event.agent || 'pi') as 'pi' | 'critic' | 'specialist';

          if (agentRole === 'specialist' && event.specialist_name) {
            const specId = event.specialist_name.toLowerCase().replace(/\s+/g, '_');
            const exists = newState.characters.find(c => c.id === specId);
            if (!exists) {
              newState.characters.push({
                id: specId,
                role: 'specialist',
                name: event.specialist_name,
                focus: event.specialist_focus,
                status: 'speaking',
                message: event.message,
                content: event.content,
              });
            } else {
              newState.characters = newState.characters.map(c =>
                c.id === specId
                  ? { ...c, status: 'speaking' as const, message: event.message, content: event.content, focus: event.specialist_focus || c.focus }
                  : c
              );
            }
          } else {
            newState.characters = newState.characters.map(c => {
              if (c.role === agentRole && (agentRole !== 'specialist' || !event.specialist_name)) {
                return { ...c, status: 'speaking' as const, message: event.message, content: event.content };
              }
              return c;
            });
          }

          if (event.agent === 'pi' && (state.phase === 'planning' || state.phase === 'idle')) {
            const nameMatches = event.message.match(/팀 구성|Team|specialist/i);
            if (nameMatches && event.content) {
              const specRegex = /[-*]\s*\*?\*?(.+?)\*?\*?\s*[:\-–]\s*(.+?)(?:\n|$)/g;
              let match;
              while ((match = specRegex.exec(event.content)) !== null) {
                const specName = match[1].trim();
                const specFocus = match[2].trim();
                const specId = specName.toLowerCase().replace(/\s+/g, '_');
                if (!newState.characters.find(c => c.id === specId) && specName.length < 40) {
                  newState.characters.push({
                    id: specId,
                    role: 'specialist',
                    name: specName,
                    focus: specFocus,
                    status: 'idle',
                  });
                }
              }
            }
          }

          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: agentRole,
            name: event.specialist_name || (agentRole === 'pi' ? 'PI' : agentRole === 'critic' ? 'Critic' : 'Specialist'),
            message: event.message,
            content: event.content,
            type: 'agent',
          });
          break;
        }

        case 'decision': {
          newState.phase = 'critique';
          newState.scene = 'meeting';
          newState.characters = newState.characters.map(c =>
            c.role === 'critic'
              ? { ...c, status: 'speaking' as const, message: event.message, scores: event.scores }
              : { ...c, status: 'idle' as const }
          );
          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'critic',
            name: 'Critic',
            message: event.message,
            content: event.content,
            type: 'decision',
            scores: event.scores,
            specialist_feedback: event.specialist_feedback,
          });
          break;
        }

        case 'iteration': {
          newState.currentRound = event.round || (state.currentRound + 1);
          newState.characters = newState.characters.map(c => ({
            ...c, status: 'idle' as const, message: undefined,
          }));
          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'pi',
            name: 'System',
            message: event.message,
            type: 'system',
          });
          break;
        }

        case 'complete': {
          newState.phase = 'complete';
          newState.scene = 'meeting';
          newState.isStreaming = false;
          newState.finalReport = event.report;
          newState.savedFilename = event.saved_filename;
          newState.characters = newState.characters.map(c => ({
            ...c, status: 'done' as const,
          }));
          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'pi',
            name: 'System',
            message: event.message,
            type: 'system',
          });
          break;
        }

        case 'error': {
          newState.isStreaming = false;
          newState.error = event.error || event.message;
          newState.chatLog.push({
            id: ++msgIdCounter,
            timestamp: event.timestamp,
            role: 'pi',
            name: 'System',
            message: event.error || event.message,
            type: 'system',
          });
          break;
        }
      }

      return newState;
    }

    default:
      return state;
  }
}

export interface UseGameSSEOptions {
  topic: string;
  constraints?: string;
  onComplete?: (report: string, filename?: string) => void;
  onError?: (error: string) => void;
}

/**
 * SSE hook for Game Board - uses ProcessTimeline's proven auto-start pattern.
 * Auto-starts streaming when topic is non-empty.
 * Pass topic='' to keep idle.
 */
export function useGameSSE({ topic, constraints, onComplete, onError }: UseGameSSEOptions) {
  const [state, dispatch] = useReducer(gameReducer, INITIAL_GAME_STATE);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isStreamingRef = useRef(false);

  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  // Auto-start SSE when topic is provided (ProcessTimeline pattern)
  useEffect(() => {
    if (!topic) return;
    if (isStreamingRef.current) return;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    dispatch({ type: 'RESET' });
    dispatch({ type: 'START_STREAM' });

    const startStreaming = async () => {
      isStreamingRef.current = true;

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
            isStreamingRef.current = false;
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event: SSEEvent = JSON.parse(line.slice(6));
                dispatch({ type: 'SSE_EVENT', event });

                if (event.type === 'complete' && event.report) {
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
        isStreamingRef.current = false;
        onErrorRef.current?.(error instanceof Error ? error.message : 'Unknown error');
      }
    };

    startStreaming();

    return () => {
      abortController.abort();
      isStreamingRef.current = false;
    };
  }, [topic, constraints]);

  const reset = useCallback(() => {
    abortControllerRef.current?.abort();
    isStreamingRef.current = false;
    dispatch({ type: 'RESET' });
  }, []);

  return { state, reset };
}
