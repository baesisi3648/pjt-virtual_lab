'use client';

import type { CharacterState } from './game-types';
import { ROLE_COLORS } from './pixel-data';
import PixelCharacter from './PixelCharacter';
import SpeechBubble from './SpeechBubble';

interface LabSceneProps {
  characters: CharacterState[];
  onCharacterClick: (id: string) => void;
}

export default function LabScene({ characters, onCharacterClick }: LabSceneProps) {
  const pi = characters.find(c => c.role === 'pi');
  const specialists = characters.filter(c => c.role === 'specialist');
  const cols = Math.max(specialists.length, 3);
  const gridCols = cols <= 3 ? 'grid-cols-3' : cols <= 4 ? 'grid-cols-4' : 'grid-cols-5';

  return (
    <div className="animate-scene-fade-in">
      {/* PI monitoring from top */}
      {pi && (
        <div className="flex items-center justify-center gap-4 mb-4 py-3 glass-panel rounded-lg">
          <div className="relative">
            <PixelCharacter
              role="pi"
              status={pi.status}
              size={2}
              onClick={() => onCharacterClick(pi.id)}
              label="PI"
            />
            {pi.message && pi.status === 'speaking' && (
              <SpeechBubble message={pi.message} direction="down" maxWidth={250} />
            )}
          </div>
          <div className="text-sm text-purple-400 font-mono">
            <span className="material-symbols-outlined text-sm align-middle mr-1">monitoring</span>
            Monitoring...
          </div>
        </div>
      )}

      {/* Lab Cubicles Grid */}
      <div className={`grid ${gridCols} gap-3`}>
        {specialists.map((spec, idx) => {
          const colors = ROLE_COLORS.specialist;
          const isActive = spec.status === 'speaking' || spec.status === 'active';
          const isDone = spec.status === 'done';

          return (
            <div
              key={spec.id}
              className={`relative glass-panel rounded-lg p-4 flex flex-col items-center overflow-hidden transition-all duration-500 ${
                isActive
                  ? 'border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                  : isDone
                    ? 'border-emerald-500/30'
                    : 'border-white/10'
              }`}
              style={{
                animationDelay: `${idx * 100}ms`,
              }}
            >
              {/* Lab background decoration */}
              <div className="absolute inset-0 rounded-lg overflow-hidden pointer-events-none">
                <div className="absolute top-1 right-2 text-[10px] text-white/10 font-mono">
                  LAB-{String(idx + 1).padStart(2, '0')}
                </div>
                {/* Desk line */}
                <div className="absolute bottom-12 left-2 right-2 h-[1px] bg-white/5" />
                {/* Monitor */}
                <div className="absolute top-2 left-2 w-4 h-3 rounded-sm border border-white/5 bg-white/3" />
              </div>

              {/* Speech Bubble */}
              <div className="relative w-full flex justify-center mb-2 min-h-[20px]">
                {spec.message && spec.status === 'speaking' && (
                  <SpeechBubble message={spec.message} direction="down" maxWidth={180} autoHide={10000} />
                )}
              </div>

              {/* Character */}
              <div className="relative my-2">
                <PixelCharacter
                  role="specialist"
                  status={spec.status}
                  size={3}
                  onClick={() => onCharacterClick(spec.id)}
                />
              </div>

              {/* Name + Focus */}
              <div className="text-center mt-2 w-full overflow-hidden px-1">
                <div className="text-xs font-bold text-emerald-400 font-mono truncate">
                  {spec.name}
                </div>
                {spec.focus && (
                  <div className="text-[10px] text-white/40 mt-0.5 line-clamp-2 leading-tight">
                    {spec.focus.length > 30 ? spec.focus.slice(0, 30) + '...' : spec.focus}
                  </div>
                )}
              </div>

              {/* Status indicator */}
              <div className="mt-2 flex items-center gap-1">
                {isActive && (
                  <>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[10px] text-emerald-400 font-mono">
                      {spec.status === 'speaking' ? 'Analyzing...' : 'Active'}
                    </span>
                  </>
                )}
                {isDone && (
                  <>
                    <span className="text-[10px] text-emerald-400 font-mono">Done ✓</span>
                  </>
                )}
                {!isActive && !isDone && (
                  <span className="text-[10px] text-white/20 font-mono">Standby</span>
                )}
              </div>
            </div>
          );
        })}

        {/* Empty lab slots if less than 3 specialists */}
        {specialists.length < 3 &&
          Array.from({ length: 3 - specialists.length }, (_, i) => (
            <div
              key={`empty-${i}`}
              className="glass-panel rounded-lg p-4 flex flex-col items-center justify-center border-dashed border-white/5 min-h-[180px]"
            >
              <span className="text-white/10 text-xs font-mono">EMPTY</span>
            </div>
          ))}
      </div>
    </div>
  );
}
