# P4-T4 Demo: Real-time Research Streaming

## Quick Start

### Terminal 1: Backend
```bash
cd worktree/phase-4-nextjs
uvicorn server:app --reload --port 8000
```

### Terminal 2: Frontend
```bash
cd worktree/phase-4-nextjs/frontend
npm run dev
```

### Browser
```
http://localhost:3000/timeline
```

## Expected Output

### 1. SSE Event Stream (Backend)
```
data: {"type":"start","timestamp":1707360000.0,"message":"연구 프로세스를 시작합니다...","topic":"CRISPR-Cas9 토마토"}

data: {"type":"phase","timestamp":1707360000.1,"phase":"drafting","agent":"scientist","message":"🔬 Scientist: 위험 요소 분석 중..."}

data: {"type":"agent","timestamp":1707360005.2,"agent":"scientist","phase":"drafting","message":"🔬 Scientist: 초안 작성 완료","iteration":1}

data: {"type":"agent","timestamp":1707360006.0,"agent":"critic","phase":"critique","message":"🔍 Critic: 초안 검토 중...","iteration":1}

data: {"type":"decision","timestamp":1707360010.5,"agent":"critic","decision":"revise","message":"❌ Critic: 수정 필요","feedback":"알레르기 유발 가능성 추가 분석 필요..."}

data: {"type":"iteration","timestamp":1707360010.6,"iteration":1,"message":"🔄 반복 1회차 시작"}

data: {"type":"agent","timestamp":1707360015.2,"agent":"scientist","phase":"drafting","message":"🔬 Scientist: 초안 작성 완료","iteration":2}

data: {"type":"agent","timestamp":1707360016.0,"agent":"critic","phase":"critique","message":"🔍 Critic: 초안 검토 중...","iteration":2}

data: {"type":"decision","timestamp":1707360020.0,"agent":"critic","decision":"approve","message":"✅ Critic: 승인"}

data: {"type":"agent","timestamp":1707360020.5,"agent":"pi","phase":"finalizing","message":"👔 PI: 최종 보고서 작성 중..."}

data: {"type":"complete","timestamp":1707360025.0,"message":"✅ 연구 프로세스 완료","report":"# NGT 안전성 평가 프레임워크\n\n## 서론\n...","iterations":2,"messages":[...]}
```

### 2. Frontend Timeline UI

```
┌─────────────────────────────────────────────────────────────┐
│  Virtual Lab - Process Timeline                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  연구 진행 상황                                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔄  연구 프로세스를 시작합니다...                      14:30:00  │
│      연구 주제: CRISPR-Cas9 토마토                           │
│                                                              │
│  🔬  Scientist                                        14:30:05  │
│      🔬 Scientist: 초안 작성 완료            [반복 1회]        │
│                                                              │
│  🔍  Critic                                          14:30:10  │
│      🔍 Critic: 초안 검토 중...               [반복 1회]        │
│      [수정 필요]                                              │
│                                                              │
│  🔄                                                   14:30:10  │
│      🔄 반복 1회차 시작                                       │
│                                                              │
│  🔬  Scientist                                        14:30:15  │
│      🔬 Scientist: 초안 작성 완료            [반복 2회]        │
│                                                              │
│  🔍  Critic                                          14:30:20  │
│      🔍 Critic: 초안 검토 중...               [반복 2회]        │
│      [승인]                                                  │
│                                                              │
│  👔  PI                                              14:30:20  │
│      👔 PI: 최종 보고서 작성 중...                            │
│                                                              │
│  ✅  연구 프로세스 완료                               14:30:25  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ✅ 연구 완료                                                  │
│  최종 보고서가 생성되었습니다. (길이: 5,432자)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  최종 보고서                                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  # NGT 안전성 평가 프레임워크                                 │
│                                                              │
│  ## 서론                                                     │
│  CRISPR-Cas9 기술을 이용한 유전자편집 토마토는...             │
│                                                              │
│  ## 위험 요소 분석                                           │
│  1. 알레르기 유발 가능성                                      │
│     - 신규 단백질 발현 검증                                   │
│  ...                                                         │
│                                                              │
│  [📋 복사] [💾 다운로드]                                      │
└─────────────────────────────────────────────────────────────┘

[새 연구 시작]
```

## Key Features Demonstrated

### ✅ Real-time Streaming
- Events appear instantly as they're generated
- No page refresh needed
- Smooth auto-scroll to latest event

### ✅ Progressive Timeline
- Start event → shows research begins
- Agent events → shows each agent's work in real-time
- Decision events → shows Critic's approval/revision
- Iteration events → shows revision cycles
- Complete event → shows final report

### ✅ Visual Feedback
- 🔬 Scientist: Blue background, blue text
- 🔍 Critic: Red background, red text
- 👔 PI: Green background, green text
- ✅ Complete: Green badge
- ❌ Error: Red badge

### ✅ Report Delivery
- Full report delivered in `complete` event
- Preview shows character count
- Copy to clipboard button
- Download as .txt file

## Testing the Stream

### Test Case 1: Simple Research
```bash
# Input
Topic: "CRISPR wheat safety"
Constraints: ""

# Expected: ~10-15 events in 20-30 seconds
```

### Test Case 2: Complex Research
```bash
# Input
Topic: "Multi-gene edited salmon regulatory framework"
Constraints: "Include FDA, EU, and Japan regulations"

# Expected: ~15-25 events in 30-60 seconds (may have revisions)
```

### Test Case 3: Error Handling
```bash
# Input
Topic: ""
Constraints: ""

# Expected: Validation error (422)
```

## Performance Metrics

### Expected Timings
- Connection establishment: <1s
- First event (start): <1s
- Scientist draft: 5-10s
- Critic review: 3-5s
- PI finalization: 5-10s
- Total (1 iteration): 15-30s
- Total (2 iterations): 30-60s

### Network
- SSE overhead: ~100-200 bytes per event
- Total stream size: ~10-50 KB
- Compression: gzip supported

## Troubleshooting

### Backend not streaming
```bash
# Check if server is running
curl http://localhost:8000/health

# Check stream endpoint (should hang and stream)
curl -N -X POST http://localhost:8000/api/research/stream \
  -H "Content-Type: application/json" \
  -d '{"topic":"test","constraints":""}'
```

### Frontend not receiving events
```bash
# Check browser console for errors
# Common issues:
# - CORS error → check server CORS config
# - Network error → check backend is running
# - Parse error → check SSE format (data: {...}\n\n)
```

### Events received but not displayed
```typescript
// Check React DevTools
// - events state should be growing
// - isStreaming should be true during stream
// - currentReport should be set on complete
```

## Architecture Flow

```
┌─────────────┐                              ┌─────────────┐
│             │  POST /api/research/stream   │             │
│  Next.js    │ ────────────────────────────>│   FastAPI   │
│  Frontend   │                              │   Backend   │
│             │<────────────────────────────>│             │
│             │  SSE: data: {...}\n\n        │             │
└─────────────┘                              └─────────────┘
      │                                             │
      │ fetch ReadableStream                        │ StreamingResponse
      │ decoder.decode(chunk)                       │ yield send_event()
      │ parse SSE events                            │
      │ setEvents([...prev, event])                 │
      │                                             │
      v                                             v
┌─────────────┐                              ┌─────────────┐
│  Timeline   │                              │  LangGraph  │
│  Component  │                              │  Workflow   │
└─────────────┘                              └─────────────┘
- Real-time render                           - stream() API
- Auto-scroll                                - Node-by-node execution
- Agent icons                                - State updates
```

## Success Criteria

✅ **Events stream in real-time** (not batched at the end)
✅ **Timeline updates progressively** (not all at once)
✅ **Auto-scroll works** (latest event visible)
✅ **Final report appears** (in complete event)
✅ **No errors in console** (network, parsing, React)
✅ **All 7 event types received** (start, phase, agent, decision, iteration, complete, error)

## Conclusion

P4-T4 successfully demonstrates:
- FastAPI SSE streaming with `StreamingResponse`
- LangGraph workflow streaming with `stream()` API
- Next.js real-time UI updates with ReadableStream
- Progressive report generation visualization

The system provides a smooth, real-time research experience where users can observe the AI agents collaborating to produce the final safety framework report.
