'use client';

import type { GamePhase } from './game-types';

interface RoundProgressBarProps {
  currentRound: number;
  maxRounds: number;
  phase: GamePhase;
  isStreaming: boolean;
}

const PHASE_LABELS: Record<GamePhase, string> = {
  idle: 'Idle',
  planning: 'Planning',
  researching: 'Researching',
  critique: 'Critique Review',
  pi_summary: 'PI Summary',
  round_revision: 'Round Revision',
  final_synthesis: 'Final Synthesis',
  complete: 'Complete',
};

export default function RoundProgressBar({
  currentRound,
  maxRounds,
  phase,
  isStreaming,
}: RoundProgressBarProps) {
  const progress = phase === 'complete' ? 100 : ((currentRound - 1) / maxRounds) * 100 +
    (phase === 'researching' ? 10 : phase === 'critique' ? 20 : phase === 'pi_summary' ? 25 : phase === 'round_revision' ? 15 : phase === 'final_synthesis' ? 30 : 5) / maxRounds * 100;

  return (
    <div className="glass-panel rounded-lg px-4 py-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          {/* Round indicators */}
          {Array.from({ length: maxRounds }, (_, i) => {
            const roundNum = i + 1;
            const isActive = roundNum === currentRound;
            const isDone = roundNum < currentRound || phase === 'complete';
            return (
              <div
                key={roundNum}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold font-mono transition-all duration-500 ${
                  isDone
                    ? 'bg-emerald-500/30 text-emerald-400 border border-emerald-500/50'
                    : isActive
                      ? 'bg-[#137fec]/30 text-[#137fec] border border-[#137fec]/50 animate-pulse'
                      : 'bg-gray-100 text-gray-400 border border-gray-200'
                }`}
              >
                {isDone ? '✓' : `R${roundNum}`}
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-2">
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-xs text-cyan-300">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
              </span>
              LIVE
            </span>
          )}
          <span className="text-xs font-mono text-gray-500">
            {PHASE_LABELS[phase]}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${Math.min(progress, 100)}%`,
            background: phase === 'complete'
              ? 'linear-gradient(90deg, #10b981, #34d399)'
              : 'linear-gradient(90deg, #137fec, #8b5cf6, #06b6d4)',
          }}
        />
      </div>
    </div>
  );
}
