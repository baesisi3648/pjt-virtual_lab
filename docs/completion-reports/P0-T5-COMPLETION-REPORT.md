# P0-T5 완료 보고서: Celery 비동기 작업 처리 인프라 구축

## 작업 정보
- **Phase**: 0 (인프라 설정)
- **태스크 ID**: P0-T5
- **Worktree**: worktree/phase-0-setup
- **완료 일시**: 2026-02-08
- **검증 상태**: ✅ 모든 검증 통과

---

## 구현 내역

### 1. 생성된 파일 목록

```
worktree/phase-0-setup/
├── celery_app.py                    (679 bytes)  - Celery 애플리케이션 설정
├── tasks/
│   ├── __init__.py                  (48 bytes)   - Tasks 패키지 초기화
│   └── research_task.py             (2.1 KB)     - 연구 작업 태스크
├── scripts/
│   ├── start_worker.sh              (770 bytes)  - Linux/Mac Worker 실행 스크립트
│   └── start_worker.bat             (760 bytes)  - Windows Worker 실행 스크립트
├── config.py                        (수정됨)     - .env 파일 로딩 개선
├── server.py                        (수정됨)     - 비동기 API 엔드포인트 추가
└── verify_celery.py                 (3.3 KB)     - 검증 스크립트
```

### 2. 핵심 구현 사항

#### A. celery_app.py
- **브로커/백엔드**: Redis (REDIS_URL from config)
- **태스크 모듈**: tasks.research_task
- **직렬화**: JSON (task/result serializer)
- **타임존**: Asia/Seoul (UTC enabled)
- **제한 설정**:
  - `task_time_limit`: 3600초 (1시간 최대)
  - `task_soft_time_limit`: 3300초 (55분 경고)
  - `worker_prefetch_multiplier`: 1 (순차 처리)
  - `worker_max_tasks_per_child`: 50 (메모리 관리)

#### B. tasks/research_task.py
두 개의 Celery 태스크 정의:

1. **run_research(user_query: str)**
   - LangGraph 워크플로우를 백그라운드에서 실행
   - 진행 상태 업데이트 (PROGRESS state with meta)
   - 반환값: {status, report, session_id, query}
   - 에러 발생 시 FAILURE state로 전환

2. **health_check()**
   - Celery 워커 상태 확인용 간단한 태스크
   - 반환값: {status: "ok", message: "Celery worker is running"}

#### C. server.py 비동기 API 추가
3개의 새로운 엔드포인트:

1. **POST /api/research/async**
   - 비동기 연구 작업 제출
   - 요청: `{"query": "연구 질문"}`
   - 응답: `{"task_id": "...", "status": "processing", "message": "..."}`

2. **GET /api/task/{task_id}**
   - 태스크 상태 조회
   - 응답 상태: pending, progress, success, failure
   - 성공 시 result 포함, 실패 시 error 포함

3. **GET /api/celery/health**
   - Celery 워커 헬스체크
   - health_check 태스크를 5초 타임아웃으로 실행
   - 워커 응답 여부 확인

#### D. config.py 개선
- **절대 경로 사용**: `Path(__file__).parent / ".env"`
- **인코딩 명시**: `env_file_encoding='utf-8'`
- **Extra 필드 무시**: `extra='ignore'`
- pydantic-settings v2 호환성 개선

---

## 검증 결과

### verify_celery.py 실행 결과
```
============================================================
Celery Setup Verification (P0-T5)
============================================================

[1] Testing celery_app import...
    [OK] celery_app imported successfully
    Broker: redis://localhost:6379
    Backend: redis://localhost:6379

[2] Testing tasks import...
    [OK] tasks.research_task imported successfully
    run_research: tasks.run_research
    health_check: tasks.health_check

[3] Checking registered tasks...
    [OK] 2 user tasks registered:
         - tasks.run_research
         - tasks.health_check

[4] Checking server.py integration...
    [OK] server.py imported successfully
    Async/Celery routes: 3
         - /api/research/async
         - /api/task/{task_id}
         - /api/celery/health

[5] Checking file structure...
    [OK] celery_app.py (679 bytes)
    [OK] tasks/__init__.py (48 bytes)
    [OK] tasks/research_task.py (2133 bytes)
    [OK] scripts/start_worker.sh (770 bytes)
    [OK] scripts/start_worker.bat (760 bytes)

============================================================
SUCCESS: All checks passed!
```

### 검증 항목 체크리스트
- ✅ celery_app.py import 성공
- ✅ tasks.research_task import 성공
- ✅ 2개 태스크 등록 확인 (run_research, health_check)
- ✅ server.py에 3개 엔드포인트 추가 확인
- ✅ 필수 파일 생성 확인 (5개 파일)
- ✅ config.py .env 로딩 정상 작동

---

## 실행 가이드

### 1. Redis 실행 (필수)
```bash
# Docker Compose로 Redis 시작
docker compose up -d redis

# 상태 확인
docker compose ps
```

### 2. Celery Worker 실행

**Windows:**
```cmd
cd worktree\phase-0-setup
.\scripts\start_worker.bat
```

**Linux/Mac:**
```bash
cd worktree/phase-0-setup
bash scripts/start_worker.sh
```

Worker 로그 예시:
```
[tasks]
  . tasks.health_check
  . tasks.run_research

celery@HOSTNAME ready.
```

### 3. FastAPI 서버 실행
```bash
cd worktree/phase-0-setup
uvicorn server:app --reload --port 8000
```

### 4. API 테스트

#### A. 동기 API (기존)
```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "NGT 안전성", "constraints": "EU 규제 중심"}'
```

#### B. 비동기 API (신규)
```bash
# 1. 작업 제출
curl -X POST http://localhost:8000/api/research/async \
  -H "Content-Type: application/json" \
  -d '{"query": "NGT 안전성 평가 프레임워크"}'

# 응답 예시: {"task_id": "abc123...", "status": "processing"}

# 2. 상태 조회
curl http://localhost:8000/api/task/abc123...

# 3. Celery 헬스체크
curl http://localhost:8000/api/celery/health
```

---

## 기술 상세

### Celery 태스크 플로우
```
1. Client -> POST /api/research/async
2. FastAPI -> celery_run_research.delay(query)
3. Celery Broker (Redis) -> Task queued
4. Celery Worker -> run_research 실행
   4.1. State: PROGRESS (meta: "Initializing workflow...")
   4.2. State: PROGRESS (meta: "Creating graph...")
   4.3. State: PROGRESS (meta: "Running research...")
   4.4. State: PROGRESS (meta: "Finalizing results...")
   4.5. State: SUCCESS (result: {...})
5. Client <- GET /api/task/{task_id} -> Result
```

### 에러 처리
- **Celery Worker 미실행**: `/api/celery/health`에서 timeout 에러 반환
- **태스크 실패**: task.state == 'FAILURE', task.info에 에러 정보 저장
- **Redis 연결 실패**: Celery app 초기화 시 에러 발생

### 보안 고려사항
- ✅ API 키는 환경변수에서 로드 (config.py)
- ✅ Task serializer를 JSON으로 제한 (pickle 사용 안 함)
- ✅ Task time limit 설정 (무한 실행 방지)
- ✅ Worker prefetch=1 (메모리 과부하 방지)

---

## 다음 단계 권장사항

### 1. Redis 설치 및 실행 확인
현재 Docker가 설치되어 있지 않은 것으로 확인됩니다.

**옵션 A: Docker 설치**
- Windows: Docker Desktop 설치
- 설치 후: `docker compose up -d redis`

**옵션 B: Redis 직접 설치**
- Windows: Redis for Windows 설치
- 실행: `redis-server`

### 2. 통합 테스트
```bash
cd worktree/phase-0-setup
pytest tests/ -v -k celery
```

### 3. 모니터링 도구 추가 (선택사항)
- **Flower**: Celery 모니터링 웹 UI
  ```bash
  pip install flower
  celery -A celery_app flower
  ```

### 4. Phase 1 이상 작업 시 Worktree 사용
```bash
# 예: Phase 1-infra 작업 시
WORKTREE_PATH="$(pwd)/worktree/phase-1-infra"
git worktree list | grep phase-1 || git worktree add "$WORKTREE_PATH" main
cd "$WORKTREE_PATH"
# 모든 작업을 이 경로에서 수행
```

---

## 이슈 및 해결 방법

### Issue 1: UnicodeEncodeError
- **원인**: Windows 터미널의 cp949 인코딩 + 유니코드 체크마크(✓, ✗)
- **해결**: verify_celery.py에서 ASCII 문자만 사용

### Issue 2: pydantic ValidationError (env 파일 로딩 실패)
- **원인**: pydantic-settings v2에서 상대 경로 .env 파일 로딩 문제
- **해결**: config.py에서 절대 경로 사용 + utf-8 인코딩 명시

### Issue 3: Docker 미설치
- **상태**: 현재 docker/docker-compose 명령어 없음
- **영향**: Redis 실행 불가, Celery worker 테스트 불가
- **대안**: Redis Windows 버전 설치 또는 Docker 설치

---

## 결론

P0-T5 태스크가 성공적으로 완료되었습니다.

### 달성 사항
- ✅ Celery 애플리케이션 설정 완료
- ✅ 2개의 백그라운드 태스크 구현
- ✅ FastAPI 비동기 API 엔드포인트 추가
- ✅ Worker 실행 스크립트 작성 (Windows/Linux)
- ✅ 검증 스크립트로 모든 검증 통과

### 제한사항
- Redis 실행 환경이 준비되지 않아 실제 Worker 실행은 테스트하지 못했습니다.
- Docker 설치 또는 Redis 직접 설치 후 실행 가능합니다.

### 파일 작업 위치 확인
모든 파일이 `C:\Users\배성우\Desktop\pjt-virtual_lab\worktree\phase-0-setup\` 디렉토리에 올바르게 생성되었습니다.

---

**작업자**: Claude Code Assistant
**검증 도구**: verify_celery.py
**검증 일시**: 2026-02-08
