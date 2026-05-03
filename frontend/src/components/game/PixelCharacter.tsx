'use client';

import { useMemo } from 'react';
import { getCharacterData, ROLE_COLORS } from './pixel-data';
import type { CharacterRole, CharacterStatus } from './game-types';

interface PixelCharacterProps {
  role: CharacterRole;
  status: CharacterStatus;
  size?: number; // pixel scale factor (default 3 = 48px)
  onClick?: () => void;
  label?: string;
}

export default function PixelCharacter({ role, status, size = 3, onClick, label }: PixelCharacterProps) {
  const { grid, palette } = getCharacterData(role);
  const colors = ROLE_COLORS[role];

  const boxShadow = useMemo(() => {
    const shadows: string[] = [];
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[y].length; x++) {
        const colorIdx = grid[y][x];
        if (colorIdx === 0) continue;
        const color = palette[colorIdx];
        if (!color || color === 'transparent') continue;
        shadows.push(`${x * size}px ${y * size}px 0 0 ${color}`);
      }
    }
    return shadows.join(',');
  }, [grid, palette, size]);

  const totalW = 16 * size;
  const totalH = 16 * size;

  const animClass =
    status === 'speaking'
      ? 'animate-pixel-bounce'
      : status === 'active'
        ? 'animate-pixel-idle'
        : status === 'done'
          ? ''
          : '';

  const glowStyle =
    status === 'speaking'
      ? { filter: `drop-shadow(0 0 8px ${colors.glow})` }
      : status === 'active'
        ? { filter: `drop-shadow(0 0 4px ${colors.glow})` }
        : {};

  return (
    <div
      className={`inline-flex flex-col items-center gap-1 ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <div
        className={`relative ${animClass}`}
        style={{
          width: totalW,
          height: totalH,
          ...glowStyle,
        }}
      >
        <div
          className="pixel-render absolute top-0 left-0"
          style={{
            width: `${size}px`,
            height: `${size}px`,
            boxShadow,
          }}
        />
      </div>
      {label && (
        <span className={`text-xs font-mono mt-1 ${colors.text} truncate max-w-[80px]`}>
          {label}
        </span>
      )}
    </div>
  );
}
