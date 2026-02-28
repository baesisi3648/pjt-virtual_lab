'use client';

import type { CharacterState } from './game-types';
import { ROLE_COLORS } from './pixel-data';
import PixelCharacter from './PixelCharacter';
import SpeechBubble from './SpeechBubble';

interface MeetingSceneProps {
  characters: CharacterState[];
  onCharacterClick: (id: string) => void;
}

/** Position characters around an elliptical meeting table */
function getPositions(count: number): Array<{ top: string; left: string }> {
  // PI at 12 o'clock (index 0), Critic at 6 o'clock (index 1),
  // rest distributed evenly
  const positions: Array<{ top: string; left: string }> = [];

  if (count <= 0) return positions;

  // Fixed: PI = top center (well below container top to avoid clipping)
  positions.push({ top: '8%', left: '50%' });

  if (count === 1) return positions;

  // Fixed: Critic = bottom center
  positions.push({ top: '70%', left: '50%' });

  if (count === 2) return positions;

  // Remaining characters distributed along sides
  const remaining = count - 2;
  const leftCount = Math.ceil(remaining / 2);
  const rightCount = remaining - leftCount;

  // Left side (from top to bottom)
  for (let i = 0; i < leftCount; i++) {
    const t = (i + 1) / (leftCount + 1);
    positions.push({
      top: `${18 + t * 55}%`,
      left: `${10 + Math.sin(t * Math.PI) * 5}%`,
    });
  }

  // Right side (from top to bottom)
  for (let i = 0; i < rightCount; i++) {
    const t = (i + 1) / (rightCount + 1);
    positions.push({
      top: `${18 + t * 55}%`,
      left: `${90 - Math.sin(t * Math.PI) * 5}%`,
    });
  }

  return positions;
}

export default function MeetingScene({ characters, onCharacterClick }: MeetingSceneProps) {
  const pi = characters.find(c => c.role === 'pi');
  const critic = characters.find(c => c.role === 'critic');
  const specialists = characters.filter(c => c.role === 'specialist');

  // Order: PI first, then critic, then specialists
  const orderedChars = [
    pi,
    critic,
    ...specialists,
  ].filter(Boolean) as CharacterState[];

  const positions = getPositions(orderedChars.length);

  return (
    <div className="animate-scene-fade-in relative" style={{ minHeight: 500 }}>
      {/* Meeting Table (elliptical) */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[55%] h-[55%]">
        <div
          className="w-full h-full rounded-[50%] border-2 border-white/10"
          style={{
            background: 'radial-gradient(ellipse at center, rgba(26,35,46,0.9) 0%, rgba(16,24,32,0.7) 70%, transparent 100%)',
            boxShadow: '0 0 40px rgba(19, 127, 236, 0.1), inset 0 0 30px rgba(255,255,255,0.02)',
          }}
        >
          {/* Table label */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-white/20 text-xs font-mono tracking-widest">MEETING TABLE</span>
          </div>
        </div>
      </div>

      {/* Characters around the table */}
      {orderedChars.map((char, idx) => {
        const pos = positions[idx];
        if (!pos) return null;
        const colors = ROLE_COLORS[char.role];
        const isSpeaking = char.status === 'speaking';

        return (
          <div
            key={char.id}
            className="absolute transition-all duration-700"
            style={{
              top: pos.top,
              left: pos.left,
              transform: `translate(-50%, 0) ${isSpeaking ? 'scale(1.15)' : 'scale(1)'}`,
              zIndex: isSpeaking ? 20 : 10,
            }}
          >
            <div className="relative flex flex-col items-center">
              {/* Speech bubble above */}
              {char.message && isSpeaking && (
                <div className="mb-1">
                  <SpeechBubble message={char.message} direction="down" maxWidth={220} autoHide={10000} />
                </div>
              )}

              {/* Glow ring for speaker */}
              {isSpeaking && (
                <div
                  className="absolute inset-[-8px] rounded-full animate-pulse"
                  style={{
                    background: `radial-gradient(circle, ${colors.glow} 0%, transparent 70%)`,
                  }}
                />
              )}

              <PixelCharacter
                role={char.role}
                status={char.status}
                size={idx === 0 ? 3 : 3} // PI slightly larger could be done here
                onClick={() => onCharacterClick(char.id)}
              />

              {/* Name tag */}
              <div
                className="mt-1 px-2 py-0.5 rounded text-xs font-mono text-center"
                style={{
                  background: colors.bg,
                  color: colors.primary,
                  border: `1px solid ${colors.primary}33`,
                }}
              >
                {char.name}
              </div>
              {char.focus && (
                <div className="text-[9px] text-gray-400 text-center mt-0.5 max-w-[90px] truncate">
                  {char.focus}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
