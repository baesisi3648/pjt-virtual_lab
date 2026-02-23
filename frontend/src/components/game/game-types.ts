/** Game Board Type Definitions */

export type SceneType = 'lab' | 'meeting';

export type GamePhase =
  | 'idle'
  | 'planning'
  | 'researching'
  | 'critique'
  | 'pi_summary'
  | 'round_revision'
  | 'final_synthesis'
  | 'complete';

export type CharacterRole = 'pi' | 'critic' | 'specialist';

export type CharacterStatus = 'idle' | 'active' | 'speaking' | 'done';

export interface CharacterState {
  id: string;
  role: CharacterRole;
  name: string;
  focus?: string;
  status: CharacterStatus;
  message?: string;
  content?: string;
  scores?: Record<string, number>;
}

export interface ChatMessage {
  id: number;
  timestamp: number;
  role: CharacterRole;
  name: string;
  message: string;
  content?: string;
  type: 'system' | 'agent' | 'decision' | 'phase';
}

export interface GameState {
  phase: GamePhase;
  scene: SceneType;
  currentRound: number;
  maxRounds: number;
  characters: CharacterState[];
  chatLog: ChatMessage[];
  isStreaming: boolean;
  finalReport?: string;
  savedFilename?: string;
  error?: string;
}

export const INITIAL_GAME_STATE: GameState = {
  phase: 'idle',
  scene: 'meeting',
  currentRound: 1,
  maxRounds: 3,
  characters: [
    { id: 'pi', role: 'pi', name: 'PI', status: 'idle' },
    { id: 'critic', role: 'critic', name: 'Critic', status: 'idle' },
  ],
  chatLog: [],
  isStreaming: false,
};

/** Map SSE phase string to GamePhase */
export function parsePhase(phase: string): GamePhase {
  const map: Record<string, GamePhase> = {
    planning: 'planning',
    researching: 'researching',
    critique: 'critique',
    pi_summary: 'pi_summary',
    round_revision: 'round_revision',
    final_synthesis: 'final_synthesis',
  };
  return map[phase] || 'idle';
}

/** Get scene type for a given phase */
export function getSceneForPhase(phase: GamePhase): SceneType {
  switch (phase) {
    case 'researching':
    case 'round_revision':
      return 'lab';
    case 'planning':
    case 'critique':
    case 'pi_summary':
    case 'final_synthesis':
    default:
      return 'meeting';
  }
}
