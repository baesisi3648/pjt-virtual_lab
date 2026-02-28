'use client';

import { useState, useCallback } from 'react';
import type { GameState, CharacterState } from './game-types';
import RoundProgressBar from './RoundProgressBar';
import LabScene from './LabScene';
import MeetingScene from './MeetingScene';
import ChatLog from './ChatLog';
import CharacterDetailModal from './CharacterDetailModal';

interface GameBoardProps {
  state: GameState;
}

export default function GameBoard({ state }: GameBoardProps) {
  const [selectedChar, setSelectedChar] = useState<CharacterState | null>(null);

  const handleCharClick = useCallback((id: string) => {
    const char = state.characters.find(c => c.id === id);
    if (char) setSelectedChar(char);
  }, [state.characters]);

  const isComplete = state.phase === 'complete';

  return (
    <div className="space-y-4">
      {/* Round Progress */}
      <RoundProgressBar
        currentRound={state.currentRound}
        maxRounds={state.maxRounds}
        phase={state.phase}
        isStreaming={state.isStreaming}
      />

      {/* Scene Container */}
      <div
        className={`glass-panel rounded-lg px-6 pt-8 pb-6 relative overflow-hidden transition-all duration-500 ${
          isComplete ? 'border-emerald-500/30' : ''
        }`}
        style={{ minHeight: state.scene === 'meeting' ? 520 : undefined }}
      >
        {/* Background grid */}
        <div className="absolute inset-0 bg-grid pointer-events-none opacity-50" />

        {/* Scene label */}
        <div className="absolute top-3 right-3 z-20">
          <span className="text-[10px] font-mono text-gray-400 px-2 py-1 rounded bg-gray-100">
            {state.scene === 'lab' ? 'LAB' : 'MEETING'} / R{state.currentRound}
          </span>
        </div>

        {/* Completion overlay */}
        {isComplete && (
          <div className="absolute inset-0 z-30 flex items-center justify-center pointer-events-none">
            <div className="text-center animate-speech-appear">
              <div className="text-4xl mb-2">&#x1F389;</div>
              <div className="text-lg font-bold text-emerald-400 neon-text">Research Complete!</div>
            </div>
          </div>
        )}

        {/* Active Scene */}
        <div className={`relative z-10 ${isComplete ? 'opacity-30' : ''}`}>
          {state.scene === 'lab' ? (
            <LabScene
              characters={state.characters}
              onCharacterClick={handleCharClick}
            />
          ) : (
            <MeetingScene
              characters={state.characters}
              onCharacterClick={handleCharClick}
            />
          )}
        </div>
      </div>

      {/* Chat Log */}
      <ChatLog messages={state.chatLog} isStreaming={state.isStreaming} />

      {/* Error display */}
      {state.error && (
        <div className="glass-panel rounded-lg p-4 border border-red-500/30">
          <div className="flex items-center gap-2 text-red-400 text-sm">
            <span className="material-symbols-outlined text-base">error</span>
            <span className="font-mono">{state.error}</span>
          </div>
        </div>
      )}

      {/* Character Detail Modal */}
      <CharacterDetailModal
        character={selectedChar}
        onClose={() => setSelectedChar(null)}
      />
    </div>
  );
}
