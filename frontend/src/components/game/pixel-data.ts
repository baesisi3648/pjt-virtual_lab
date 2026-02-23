/**
 * 16x16 Pixel Art Data for Characters
 * Each grid is a 2D array of color indices.
 * 0 = transparent, other numbers map to palette colors.
 */

import type { CharacterRole } from './game-types';

export interface PixelPalette {
  [key: number]: string;
}

// PI: Purple lab coat researcher
const PI_PALETTE: PixelPalette = {
  0: 'transparent',
  1: '#1a1a2e', // dark outline
  2: '#8b5cf6', // purple coat
  3: '#a78bfa', // light purple
  4: '#f5d0a9', // skin
  5: '#2d1b69', // dark purple
  6: '#e8d5b7', // light skin
  7: '#1e1b4b', // hair
  8: '#c4b5fd', // highlight
  9: '#ffffff', // white (eyes/details)
};

const PI_GRID: number[][] = [
  [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
  [0,0,0,0,1,7,7,7,7,7,7,1,0,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,1,4,4,6,6,6,6,6,6,4,4,1,0,0],
  [0,0,1,4,9,1,4,4,4,1,9,4,4,1,0,0],
  [0,0,1,4,4,4,4,4,4,4,4,4,4,1,0,0],
  [0,0,0,1,4,4,1,1,1,4,4,1,0,0,0,0],
  [0,0,0,0,1,2,2,2,2,2,2,1,0,0,0,0],
  [0,0,0,1,2,2,3,2,2,3,2,2,1,0,0,0],
  [0,0,1,5,2,2,2,2,2,2,2,2,5,1,0,0],
  [0,0,1,5,2,8,2,2,2,2,8,2,5,1,0,0],
  [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
  [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
  [0,0,0,1,5,5,1,1,1,5,5,1,0,0,0,0],
  [0,0,0,1,5,5,1,0,1,5,5,1,0,0,0,0],
];

// Critic: Cyan glasses + clipboard
const CRITIC_PALETTE: PixelPalette = {
  0: 'transparent',
  1: '#1a1a2e', // dark outline
  2: '#06b6d4', // cyan body
  3: '#22d3ee', // light cyan
  4: '#f5d0a9', // skin
  5: '#0e7490', // dark cyan
  6: '#e8d5b7', // light skin
  7: '#374151', // hair (gray)
  8: '#67e8f9', // highlight/glasses
  9: '#ffffff', // white
};

const CRITIC_GRID: number[][] = [
  [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
  [0,0,0,0,1,7,7,7,7,7,7,1,0,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,1,4,4,6,6,6,6,6,6,4,4,1,0,0],
  [0,0,1,8,8,1,4,4,4,1,8,8,4,1,0,0],
  [0,0,1,4,4,4,4,4,4,4,4,4,4,1,0,0],
  [0,0,0,1,4,4,1,1,1,4,4,1,0,0,0,0],
  [0,0,0,0,1,2,2,2,2,2,2,1,0,0,0,0],
  [0,0,0,1,2,2,3,2,2,3,2,2,1,0,0,0],
  [0,0,1,5,2,2,2,2,2,2,2,2,5,1,0,0],
  [0,0,1,5,2,3,2,2,2,2,3,2,5,1,0,0],
  [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
  [0,0,0,1,1,2,2,2,2,2,2,1,1,9,0,0],
  [0,0,0,1,5,5,1,1,1,5,5,1,9,9,0,0],
  [0,0,0,1,5,5,1,0,1,5,5,1,0,0,0,0],
];

// Specialist: Green lab coat
const SPECIALIST_PALETTE: PixelPalette = {
  0: 'transparent',
  1: '#1a1a2e', // dark outline
  2: '#10b981', // emerald body
  3: '#34d399', // light green
  4: '#f5d0a9', // skin
  5: '#065f46', // dark green
  6: '#e8d5b7', // light skin
  7: '#44403c', // hair (brown)
  8: '#6ee7b7', // highlight
  9: '#ffffff', // white
};

const SPECIALIST_GRID: number[][] = [
  [0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0],
  [0,0,0,0,1,7,7,7,7,7,7,1,0,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,0,1,7,7,7,7,7,7,7,7,1,0,0,0],
  [0,0,1,4,4,6,6,6,6,6,6,4,4,1,0,0],
  [0,0,1,4,9,1,4,4,4,1,9,4,4,1,0,0],
  [0,0,1,4,4,4,4,4,4,4,4,4,4,1,0,0],
  [0,0,0,1,4,4,1,1,1,4,4,1,0,0,0,0],
  [0,0,0,0,1,2,2,2,2,2,2,1,0,0,0,0],
  [0,0,0,1,2,2,3,9,9,3,2,2,1,0,0,0],
  [0,0,1,5,2,2,2,2,2,2,2,2,5,1,0,0],
  [0,0,1,5,2,8,2,2,2,2,8,2,5,1,0,0],
  [0,0,0,1,2,2,2,2,2,2,2,2,1,0,0,0],
  [0,0,0,1,1,2,2,2,2,2,2,1,1,0,0,0],
  [0,0,0,1,5,5,1,1,1,5,5,1,0,0,0,0],
  [0,0,0,1,5,5,1,0,1,5,5,1,0,0,0,0],
];

export interface PixelCharacterData {
  grid: number[][];
  palette: PixelPalette;
}

const CHARACTER_DATA: Record<CharacterRole, PixelCharacterData> = {
  pi: { grid: PI_GRID, palette: PI_PALETTE },
  critic: { grid: CRITIC_GRID, palette: CRITIC_PALETTE },
  specialist: { grid: SPECIALIST_GRID, palette: SPECIALIST_PALETTE },
};

export function getCharacterData(role: CharacterRole): PixelCharacterData {
  return CHARACTER_DATA[role];
}

/** Role-specific accent colors for UI highlights */
export const ROLE_COLORS: Record<CharacterRole, {
  primary: string;
  light: string;
  dark: string;
  glow: string;
  bg: string;
  text: string;
}> = {
  pi: {
    primary: '#8b5cf6',
    light: '#a78bfa',
    dark: '#5b21b6',
    glow: 'rgba(139, 92, 246, 0.5)',
    bg: 'rgba(139, 92, 246, 0.15)',
    text: 'text-purple-400',
  },
  critic: {
    primary: '#06b6d4',
    light: '#22d3ee',
    dark: '#0e7490',
    glow: 'rgba(6, 182, 212, 0.5)',
    bg: 'rgba(6, 182, 212, 0.15)',
    text: 'text-cyan-400',
  },
  specialist: {
    primary: '#10b981',
    light: '#34d399',
    dark: '#065f46',
    glow: 'rgba(16, 185, 129, 0.5)',
    bg: 'rgba(16, 185, 129, 0.15)',
    text: 'text-emerald-400',
  },
};
