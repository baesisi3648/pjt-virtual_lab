# Virtual Lab 빠른 시작 가이드 (5분)

> 5분 안에 Virtual Lab을 실행하는 가장 빠른 방법

---

## 🚀 MVP 모드 (Docker 없이) - 권장

### 1단계: Python 패키지 설치 (2분)

```bash
# 프로젝트 디렉토리로 이동
cd C:\Users\배성우\Desktop\pjt-virtual_lab

# 가상환경 생성 및 활성화 (Windows)
python -m venv venv
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 프론트엔드 설치 (2분)

```bash
cd frontend
npm install
cd ..
```

### 3단계: 환경 변수 확인

`.env` 파일 확인 (이미 설정되어 있음):
```env
OPENAI_API_KEY=sk-proj-...  ✅
TAVILY_API_KEY=tvly-...     ✅
```

### 4단계: 서버 시작 (1분)

**터미널 1 - 백엔드**:
```bash
uvicorn server:app --reload --port 8000
```

**터미널 2 - 프론트엔드**:
```bash
cd frontend
npm run dev
```

### 5단계: 브라우저 접속

```
http://localhost:3000/timeline
```

---

## 🎯 테스트 시나리오

### 연구 주제 입력 예시

```
CRISPR-Cas9 유전자편집 토마토 안전성 평가
```

### 예상 결과

1. **실시간 타임라인**:
   - 🚀 연구 시작
   - 🔬 Scientist: 초안 작성
   - 🔍 Critic: 검토
   - 👔 PI: 최종 보고서

2. **최종 보고서**: Markdown 형식으로 표시

3. **실행 시간**: 약 20-30초

---

## 🐳 Production 모드 (Docker 사용)

### 추가 단계: Docker 컨테이너 시작

```bash
# PostgreSQL, ChromaDB, Redis 시작
docker-compose up -d

# 컨테이너 확인
docker-compose ps
```

### .env 파일 수정

주석 제거:
```env
POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/virtual_lab
CHROMA_HOST=localhost
CHROMA_PORT=8001
REDIS_URL=redis://localhost:6379
```

### 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

### 서버 재시작

백엔드/프론트엔드를 다시 시작하면 완료!

---

## ❌ 문제 해결

### 백엔드 서버 시작 실패

**에러**:
```
pydantic_core._pydantic_core.ValidationError
```

**해결**:
```bash
# .env 파일 확인
cat .env

# OPENAI_API_KEY, TAVILY_API_KEY가 올바른지 확인
# 없으면 추가
```

### 프론트엔드 연결 실패

**에러**:
```
Failed to fetch
```

**해결**:
```bash
# 백엔드 서버 확인
curl http://localhost:8000/health

# 출력: {"status":"ok","version":"1.0.0"}
```

### Docker 컨테이너 시작 실패

**해결**:
```bash
# Docker Desktop 실행 확인
# 기존 컨테이너 정리
docker-compose down
docker-compose up -d
```

---

## 📚 자세한 가이드

더 자세한 내용은 `SETUP_GUIDE.md`를 참조하세요:
- 시스템 요구사항
- 상세 설치 방법
- 문제 해결
- API 엔드포인트
- 추가 설정

---

**완료!** 🎉

이제 Virtual Lab을 사용할 수 있습니다.
