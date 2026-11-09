# Virtual Lab 설치 및 실행 가이드

> NGT 안전성 평가 프레임워크를 위한 AI 에이전트 시스템

---

## 📋 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [사전 설치](#2-사전-설치)
3. [프로젝트 설정](#3-프로젝트-설정)
4. [실행 모드 선택](#4-실행-모드-선택)
   - [Option A: MVP 모드 (권장)](#option-a-mvp-모드-권장)
   - [Option B: Production 모드](#option-b-production-모드)
5. [실행 방법](#5-실행-방법)
6. [문제 해결](#6-문제-해결)

---

## 1. 시스템 요구사항

### 최소 사양
- **OS**: Windows 10/11, macOS, Linux
- **CPU**: 2 코어 이상
- **RAM**: 8GB 이상 (16GB 권장)
- **디스크**: 10GB 여유 공간

### 필수 소프트웨어
- Python 3.10 이상
- Node.js 18 이상 (프론트엔드)
- Git

### 선택 소프트웨어 (Production 모드)
- Docker Desktop
- Docker Compose

---

## 2. 사전 설치

### 2.1 Python 설치 확인

```bash
python --version
# 출력 예: Python 3.13.2
```

**설치 필요 시**:
- Windows: https://www.python.org/downloads/
- macOS: `brew install python@3.13`
- Linux: `sudo apt install python3.13`

### 2.2 Node.js 설치 확인

```bash
node --version
npm --version
# 출력 예: v20.x.x, 10.x.x
```

**설치 필요 시**:
- https://nodejs.org/ (LTS 버전 권장)

### 2.3 Docker 설치 (Production 모드만 필요)

```bash
docker --version
docker-compose --version
```

**설치 필요 시**:
- Windows/Mac: https://www.docker.com/products/docker-desktop/
- Linux: https://docs.docker.com/engine/install/

---

## 3. 프로젝트 설정

### 3.1 저장소 이동

```bash
cd <repo>
```

### 3.2 Python 가상환경 생성 및 활성화

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**:
```bash
python -m venv venv
source venv/bin/activate
```

### 3.3 Python 패키지 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**예상 시간**: 3-5분

### 3.4 프론트엔드 패키지 설치

```bash
cd frontend
npm install
cd ..
```

**예상 시간**: 2-3분

### 3.5 환경 변수 확인

`.env` 파일이 이미 존재하고 다음 키들이 설정되어 있는지 확인:

```bash
# .env 파일 내용 확인
cat .env
```

**필수 확인 사항**:
```env
OPENAI_API_KEY=sk-proj-...  # ✅ 이미 설정됨
TAVILY_API_KEY=tvly-...     # ✅ 이미 설정됨
```

---

## 4. 실행 모드 선택

### Option A: MVP 모드 (권장)

**특징**:
- ✅ **빠른 시작**: Docker 없이 바로 실행
- ✅ **간편한 설정**: 환경 변수만 설정
- ⚠️ **제한 사항**:
  - RAG 검색 비활성화 (ChromaDB 없음)
  - 세션 저장 비활성화 (PostgreSQL 없음)
  - 캐싱 비활성화 (Redis 없음)

**사용 케이스**:
- 테스트 및 개발
- 기본 기능 확인
- 빠른 프로토타입

**설정**:
- 추가 설정 불필요 (이미 완료)

---

### Option B: Production 모드

**특징**:
- ✅ **완전한 기능**: 모든 기능 활성화
- ✅ **데이터 영속성**: PostgreSQL로 세션 저장
- ✅ **RAG 검색**: ChromaDB로 규제 문서 검색
- ✅ **캐싱**: Redis로 검색 결과 캐싱
- ⚠️ **설정 필요**: Docker 설치 및 실행

**사용 케이스**:
- 프로덕션 배포
- 완전한 기능 테스트
- 대량 데이터 처리

**설정 방법**:

#### Step 1: Docker Compose 실행

```bash
# PostgreSQL, ChromaDB, Redis 컨테이너 시작
docker-compose up -d
```

**컨테이너 확인**:
```bash
docker-compose ps
```

출력 예:
```
NAME                COMMAND                  SERVICE     STATUS
pjt-virtual_lab-postgres-1   "docker-entrypoint..."   postgres    Up
pjt-virtual_lab-chromadb-1   "uvicorn chromadb.a..."  chromadb    Up
pjt-virtual_lab-redis-1      "redis-server"           redis       Up
```

#### Step 2: 환경 변수 활성화

`.env` 파일에서 다음 줄의 주석 제거:

```env
# 현재 (주석 처리됨)
# POSTGRES_URL=postgresql://user:pass@localhost:5432/virtuallab
# CHROMA_HOST=localhost
# CHROMA_PORT=8001
# REDIS_URL=redis://localhost:6379

# 변경 후 (주석 제거)
POSTGRES_URL=postgresql://virtuallab:password@localhost:5432/virtuallab
CHROMA_HOST=localhost
CHROMA_PORT=8001
REDIS_URL=redis://localhost:6379
```

#### Step 3: 데이터베이스 마이그레이션

```bash
# Alembic 마이그레이션 실행
alembic upgrade head
```

#### Step 4: RAG 문서 로드 (선택)

규제 문서를 ChromaDB에 로드:

```bash
# data/regulatory/ 폴더에 PDF 파일 배치
# 예: codex_guideline.pdf, fda_guideline.pdf

# PDF 처리 및 벡터화 실행
python rag/pdf_processor.py --dir data/regulatory/
```

---

## 5. 실행 방법

### 5.1 백엔드 서버 시작

**터미널 1**:
```bash
# 가상환경 활성화 확인
# venv\Scripts\activate (Windows)
# source venv/bin/activate (macOS/Linux)

uvicorn server:app --reload --port 8000
```

**성공 메시지**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Health Check**:
```bash
# 새 터미널에서
curl http://localhost:8000/health
```

출력:
```json
{"status":"ok","version":"1.0.0"}
```

### 5.2 프론트엔드 서버 시작

**터미널 2**:
```bash
cd frontend
npm run dev
```

**성공 메시지**:
```
  ▲ Next.js 16.1.6
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Starting...
 ✓ Ready in 2.3s
```

### 5.3 브라우저 접속

```
http://localhost:3000/timeline
```

---

## 6. 실행 화면

### 메인 타임라인 페이지

1. **연구 주제 입력**:
   ```
   예: CRISPR-Cas9 유전자편집 토마토 안전성 평가
   ```

2. **"연구 시작" 버튼 클릭**

3. **실시간 타임라인 확인**:
   ```
   [12:00:01] 🚀 연구 프로세스를 시작합니다...
   [12:00:02] 🔬 Scientist: 초안 작성 완료
   [12:00:15] 🔍 Critic: 초안 검토 중...
   [12:00:16] ✅ Critic: 승인
   [12:00:30] 👔 PI: 최종 보고서 작성 중...
   [12:00:35] ✅ 연구 프로세스 완료
   ```

4. **최종 보고서 확인**:
   - Markdown 형식으로 표시
   - 복사 및 다운로드 가능

---

## 7. 문제 해결

### 7.1 백엔드 서버가 시작되지 않음

**증상**:
```
pydantic_core._pydantic_core.ValidationError: X validation errors
```

**해결**:
1. `.env` 파일 확인:
   ```bash
   cat .env
   ```

2. 필수 키 확인:
   - `OPENAI_API_KEY`: 반드시 `sk-`로 시작
   - `TAVILY_API_KEY`: 반드시 `tvly-`로 시작 (또는 주석 처리)

3. MVP 모드 확인:
   ```bash
   # config.py에서 선택적 필드 확인
   grep "Optional" config.py
   ```

### 7.2 프론트엔드가 백엔드에 연결되지 않음

**증상**:
```
Failed to fetch
Network error
```

**해결**:
1. 백엔드 서버 실행 확인:
   ```bash
   curl http://localhost:8000/health
   ```

2. CORS 설정 확인:
   ```python
   # server.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],  # ✅ 확인
   )
   ```

3. Proxy 설정 확인:
   ```typescript
   // frontend/next.config.ts
   rewrites: async () => [
     {
       source: '/api/:path*',
       destination: 'http://localhost:8000/api/:path*',  // ✅ 확인
     },
   ],
   ```

### 7.3 Docker 컨테이너가 시작되지 않음

**증상**:
```
ERROR: for postgres  Cannot start service postgres
```

**해결**:
1. Docker Desktop 실행 확인

2. 포트 충돌 확인:
   ```bash
   # Windows
   netstat -ano | findstr :5432
   netstat -ano | findstr :8001
   netstat -ano | findstr :6379

   # macOS/Linux
   lsof -i :5432
   lsof -i :8001
   lsof -i :6379
   ```

3. 기존 컨테이너 정리:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### 7.4 RAG 검색이 작동하지 않음

**증상**:
```
ChromaDB connection failed
```

**해결** (Production 모드만 해당):
1. ChromaDB 컨테이너 확인:
   ```bash
   docker-compose ps chromadb
   ```

2. ChromaDB Health Check:
   ```bash
   curl http://localhost:8001/api/v1/heartbeat
   ```

3. 환경 변수 확인:
   ```env
   CHROMA_HOST=localhost
   CHROMA_PORT=8001
   ```

**MVP 모드**:
- RAG 검색은 비활성화 상태 (정상)
- 웹 검색 기능만 사용 가능

### 7.5 테스트 실패

**증상**:
```
1 failed, 89 passed
tests/test_llm.py::test_raises_without_api_key
```

**해결**:
- 이것은 정상입니다 (환경에 API 키가 있어서 발생)
- 무시해도 무방

---

## 8. 주요 API 엔드포인트

### 백엔드 (FastAPI)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/health` | GET | Health check |
| `/api/research` | POST | 동기 연구 요청 |
| `/api/research/stream` | POST | SSE 실시간 스트리밍 |
| `/api/report/regenerate` | POST | 보고서 섹션 재생성 |

### 프론트엔드 (Next.js)

| 경로 | 설명 |
|------|------|
| `/` | 홈페이지 |
| `/timeline` | 실시간 연구 타임라인 |
| `/report-demo` | 보고서 에디터 데모 |

---

## 9. 추가 설정 (선택)

### 9.1 LangSmith 트레이싱 활성화

```env
# .env
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=virtual-lab
```

**LangSmith 가입**: https://smith.langchain.com/

### 9.2 LLM 모델 변경

```env
# .env
GPT4O_MODEL=gpt-4o
GPT4O_MINI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### 9.3 프로덕션 배포 (Docker Compose)

```bash
# 전체 스택 배포
docker-compose -f docker-compose.prod.yml up -d

# 접속
http://localhost
```

자세한 내용: `PRODUCTION_DEPLOYMENT.md` 참조

---

## 10. 다음 단계

### ✅ 현재까지 완료
- Phase 0: Project Setup
- Phase 1: Knowledge Injection (RAG System)
- Phase 2: Eyes & Ears (Web Search)
- Phase 3: The Brain (Parallel & Dynamic)
- Phase 4: The Face (Next.js UI)

### 🚀 다음 작업 (선택)
1. 실제 규제 문서 PDF 로드 (RAG 활성화)
2. 프로덕션 배포 (Docker Compose)
3. 추가 에이전트 개발
4. UI/UX 개선

---

## 11. 지원

### 문제 발생 시
1. 이 가이드의 "문제 해결" 섹션 확인
2. `CLAUDE.md`의 "Lessons Learned" 섹션 확인
3. GitHub Issues: (저장소 URL)

### 문서
- `README.md`: 프로젝트 개요
- `TASKS.md`: 전체 태스크 목록
- `PRODUCTION_DEPLOYMENT.md`: 프로덕션 배포 가이드
- `virtual_lab_final.md`: 상세 기획

---

**설치 완료!** 🎉

이제 `http://localhost:3000/timeline`에 접속하여 Virtual Lab을 사용할 수 있습니다.
