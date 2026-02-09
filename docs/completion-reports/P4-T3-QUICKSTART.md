# P4-T3 Quick Start: Interactive Report Editor

## 실행 방법

### 1. FastAPI 서버 시작
```bash
cd worktree/phase-4-nextjs
uvicorn server:app --reload --port 8000
```

### 2. Next.js 개발 서버 시작
```bash
cd worktree/phase-4-nextjs/frontend
npm run dev
```

### 3. 브라우저에서 데모 페이지 접속
```
http://localhost:3000/report-demo
```

## 기능 테스트

### 1. 섹션 재검토 요청
1. "알레르기 위험" 섹션 옆의 "재검토 요청" 버튼 클릭
2. 피드백 입력: "알레르기 더 자세히"
3. "제출" 버튼 클릭
4. 업데이트된 섹션 확인

### 2. 편집 모드
1. 우측 상단 "편집" 버튼 클릭
2. 보고서 내용 수정
3. "저장" 버튼 클릭
4. 변경사항 확인

## 구현 내용

### Frontend
- **ReportEditor.tsx**: 마크다운 보고서 편집 컴포넌트
- **report-demo/page.tsx**: 데모 페이지
- **api.ts**: regenerateSection API 클라이언트

### Backend
- **POST /api/report/regenerate**: 섹션 재생성 API
- **RegenerateRequest/Response**: 요청/응답 스키마

### Tests
- **ReportEditor.test.tsx**: 8개 테스트 케이스
- 모든 테스트 통과 확인

## 검증

```bash
# 테스트 실행
cd frontend
npm test

# 검증 스크립트
cd ..
python verify_p4_t3.py
```

## 주요 파일

```
frontend/
├── src/
│   ├── components/
│   │   ├── ReportEditor.tsx           # 메인 컴포넌트
│   │   └── __tests__/
│   │       └── ReportEditor.test.tsx  # 테스트
│   ├── app/
│   │   └── report-demo/
│   │       └── page.tsx               # 데모 페이지
│   └── lib/
│       └── api.ts                     # API 클라이언트
server.py                              # FastAPI 백엔드
```

## API 예제

```typescript
// 섹션 재생성 요청
const response = await regenerateSection({
  section: "알레르기 위험",
  feedback: "알레르기 더 자세히",
  current_report: report,
});

console.log(response.updated_report);
```

## 완료 기준

- [x] ReportEditor 컴포넌트 구현
- [x] 마크다운 렌더링
- [x] 편집 모드
- [x] 섹션별 재검토 요청
- [x] FastAPI 재검토 API
- [x] 테스트 8개 통과
- [x] 데모 페이지 작성
- [x] 검증 스크립트 통과
