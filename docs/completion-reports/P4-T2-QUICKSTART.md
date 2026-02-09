# P4-T2 Quick Start Guide

## Task Completed: Live Process Timeline

Real-time agent status visualization with Server-Sent Events (SSE).

## Files Created/Modified

### Backend
- **server.py** - Added `/api/research/stream` SSE endpoint

### Frontend
- **frontend/src/components/ProcessTimeline.tsx** - Timeline component
- **frontend/src/app/timeline/page.tsx** - Demo page

### Testing
- **test_sse_timeline.py** - SSE endpoint validation
- **verify_timeline_setup.py** - Setup verification (18/18 passed)

## Quick Demo

### 1. Start Backend
```bash
cd worktree/phase-4-nextjs
uvicorn server:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd worktree/phase-4-nextjs/frontend
npm run dev
```

### 3. Open Browser
```
http://localhost:3000/timeline
```

### 4. Test Research Flow
1. Enter topic: "CRISPR-Cas9 유전자편집 토마토"
2. Click "연구 시작"
3. Watch real-time timeline:
   - 🔬 Scientist: 초안 작성
   - 🔍 Critic: 검토 중
   - 👔 PI: 최종 보고서

## Event Types

```typescript
// Timeline events streamed via SSE
type EventType =
  | 'start'      // Process started
  | 'phase'      // Phase changed
  | 'agent'      // Agent activity (Scientist/Critic/PI)
  | 'decision'   // Critic decision (approve/revise)
  | 'iteration'  // Iteration count changed
  | 'complete'   // Process completed
  | 'error';     // Error occurred
```

## Agent Colors

- 🔬 **Scientist**: Blue (`text-blue-600`)
- 🔍 **Critic**: Red (`text-red-600`)
- 👔 **PI**: Green (`text-green-600`)

## Testing

### Automated Test
```bash
python test_sse_timeline.py
```

### Verification
```bash
python verify_timeline_setup.py
# Expected: Passed 18/18 (100.0%)
```

## Architecture

```
Client (Next.js)
    ↓ fetch POST /api/research/stream
    ↓
FastAPI Server
    ↓ workflow.stream(initial_state)
    ↓
LangGraph Workflow
    ↓ yield events (drafting, critique, finalizing)
    ↓
SSE Events (data: {...}\n\n)
    ↓
Client Timeline UI
```

## Next Steps

- **P4-T3**: Report Section Editing (inline editing with regenerate)
- **P4-T4**: Full Integration (combine all features)

## Documentation

See `P4-T2-COMPLETION-REPORT.md` for detailed implementation notes.

---

**Status**: ✅ COMPLETED
**Verification**: 18/18 checks passed
**Commit**: feat: P4-T2 - Live Process Timeline (SSE)
