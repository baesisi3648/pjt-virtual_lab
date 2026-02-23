'use client';

import type { CharacterState } from './game-types';
import { ROLE_COLORS } from './pixel-data';
import PixelCharacter from './PixelCharacter';

interface CharacterDetailModalProps {
  character: CharacterState | null;
  onClose: () => void;
}

export default function CharacterDetailModal({ character, onClose }: CharacterDetailModalProps) {
  if (!character) return null;

  const colors = ROLE_COLORS[character.role];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative glass-panel rounded-xl p-6 max-w-md w-full animate-speech-appear"
        style={{ border: `1px solid ${colors.primary}33` }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
        >
          <span className="material-symbols-outlined text-white/40 text-sm">close</span>
        </button>

        {/* Character display */}
        <div className="flex flex-col items-center mb-4">
          <div
            className="p-4 rounded-full mb-3"
            style={{ background: colors.bg }}
          >
            <PixelCharacter role={character.role} status={character.status} size={4} />
          </div>
          <h3 className="text-lg font-bold" style={{ color: colors.primary }}>
            {character.name}
          </h3>
          {character.focus && (
            <p className="text-xs text-white/40 mt-1">{character.focus}</p>
          )}
          <div className="flex items-center gap-2 mt-2">
            <span
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: character.status === 'done' ? '#10b981'
                  : character.status === 'speaking' ? colors.primary
                  : character.status === 'active' ? colors.light
                  : '#ffffff33',
              }}
            />
            <span className="text-xs text-white/50 capitalize font-mono">
              {character.status}
            </span>
          </div>
        </div>

        {/* Role info */}
        <div className="space-y-3">
          <div className="glass-panel-light rounded-lg p-3">
            <div className="text-[10px] text-white/30 font-mono mb-1">ROLE</div>
            <div className="text-sm text-white/80 capitalize">{character.role}</div>
          </div>

          {character.message && (
            <div className="glass-panel-light rounded-lg p-3">
              <div className="text-[10px] text-white/30 font-mono mb-1">LAST MESSAGE</div>
              <div className="text-sm text-white/70">{character.message}</div>
            </div>
          )}

          {character.content && (
            <div className="glass-panel-light rounded-lg p-3">
              <div className="text-[10px] text-white/30 font-mono mb-1">DETAILED OUTPUT</div>
              <div className="text-xs text-white/50 whitespace-pre-wrap max-h-[200px] overflow-y-auto font-mono leading-relaxed">
                {character.content}
              </div>
            </div>
          )}

          {character.scores && Object.keys(character.scores).length > 0 && (
            <div className="glass-panel-light rounded-lg p-3">
              <div className="text-[10px] text-white/30 font-mono mb-2">SCORES</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(character.scores).map(([k, v]) => (
                  <span
                    key={k}
                    className={`text-xs px-2 py-1 rounded font-mono ${
                      v >= 4 ? 'text-green-400 bg-green-500/10 border border-green-500/30'
                      : v >= 3 ? 'text-yellow-400 bg-yellow-500/10 border border-yellow-500/30'
                      : 'text-red-400 bg-red-500/10 border border-red-500/30'
                    }`}
                  >
                    {k}: {v}/5
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
