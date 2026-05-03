# Virtual Lab - 설치 및 실행 가이드

## 사전 준비

### 1. Python 설치 (3.11 이상)
- https://www.python.org/downloads/
- **설치 시 "Add Python to PATH" 반드시 체크!**
- 설치 확인: `python --version`

### 2. Node.js 설치 (20 이상)
- https://nodejs.org/ (LTS 버전 선택)
- 설치 확인: `node --version`

---

## 프로젝트 세팅

### 1. 프로젝트 가져오기

**방법 A: Git Clone (추천)**
```bash
git clone <repo-url>
cd pjt-virtual_lab
```

**방법 B: USB 복사**

폴더 통째로 복사하되, 아래 폴더는 **제외**:

| 제외 대상 | 이유 |
|-----------|------|
| `venv/` | 새로 만들면 됨 |
| `frontend/node_modules/` | `npm install`로 재설치 |
| `__pycache__/` | 자동 생성됨 |
| `.env` | API 키 포함, 직접 생성 |
| `.claude/` | Claude Code 로컬 설정 |

### 2. 환경 변수 설정 (.env)

프로젝트 루트에서 `.env.example`을 복사하여 `.env` 파일 생성:
```bash
cp .env.example .env
```

`.env` 파일을 열고 아래 3개 API 키를 입력:
```env
OPENAI_API_KEY=sk-proj-...     # OpenAI API 키
TAVILY_API_KEY=tvly-...        # Tavily API 키
PINECONE_API_KEY=pcsk_...      # Pinecone API 키
```

> API 키 발급처:
> - OpenAI: https://platform.openai.com/api-keys
> - Tavily: https://app.tavily.com/
> - Pinecone: https://app.pinecone.io/

### 3. 백엔드 설치

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 프론트엔드 설치

```bash
cd frontend
npm install
cd ..
```

---

## 실행

터미널 2개를 열고 각각 실행:

**터미널 1 - 백엔드**
```bash
venv\Scripts\activate
python -B -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**터미널 2 - 프론트엔드**
```bash
cd frontend
npm run dev
```

---

## 확인

| 서비스 | URL |
|--------|-----|
| 백엔드 헬스체크 | http://localhost:8000/health |
| 프론트엔드 | http://localhost:3000 |

---

## 문제 해결

### 백엔드가 새 코드를 안 불러올 때
```bash
./restart_server.bat
```

### 프론트엔드에서 API 연결이 안 될 때
```bash
curl http://localhost:8000/health
```
백엔드가 정상 응답하는지 먼저 확인.

### Pinecone 연결 오류
`.env` 파일에 `PINECONE_API_KEY`, `PINECONE_HOST` 값이 올바른지 확인.
