# Redis 설정 가이드

> 캐싱 및 성능 향상을 위한 Redis 설정

---

## 🚀 Redis란?

**In-Memory 데이터 저장소** - 초고속 캐싱

### 역할

1. **웹 검색 결과 캐싱**
   ```
   첫 검색: Tavily API 호출 (5초)
   같은 검색: Redis 캐시 (0.01초) ⚡
   ```

2. **API 비용 절감**
   - 중복 검색 방지
   - Tavily API 호출 감소

3. **성능 향상**
   - 메모리 기반 (디스크보다 100배 빠름)
   - 1시간 TTL (자동 삭제)

---

## 📥 Windows 설치 방법

### 방법 1: Docker (권장) ⭐

**장점**:
- ✅ 가장 쉬움
- ✅ 공식 Redis 이미지
- ✅ 자동 업데이트

**설치**:

1. **Docker Desktop 설치**:
   - https://www.docker.com/products/docker-desktop/

2. **Redis 컨테이너 실행**:
   ```bash
   docker run -d \
     --name virtual-lab-redis \
     -p 6379:6379 \
     redis:7-alpine
   ```

3. **확인**:
   ```bash
   docker ps
   # NAME: virtual-lab-redis  STATUS: Up
   ```

4. **접속 테스트**:
   ```bash
   docker exec -it virtual-lab-redis redis-cli ping
   # 출력: PONG ✅
   ```

---

### 방법 2: WSL2 (리눅스 환경)

**설치**:

1. **WSL2 활성화** (관리자 권한 PowerShell):
   ```powershell
   wsl --install
   ```

2. **Ubuntu 설치** (Microsoft Store)

3. **Ubuntu에서 Redis 설치**:
   ```bash
   sudo apt update
   sudo apt install redis-server -y
   ```

4. **Redis 시작**:
   ```bash
   sudo service redis-server start
   ```

5. **확인**:
   ```bash
   redis-cli ping
   # 출력: PONG ✅
   ```

---

### 방법 3: Windows Native (비공식)

⚠️ **주의**: 공식 지원 종료 (Windows용 Redis는 5.0까지만 지원)

**설치**:

1. **Redis for Windows 다운로드**:
   - https://github.com/tporadowski/redis/releases
   - `Redis-x64-5.0.14.1.msi` 다운로드

2. **설치 실행**:
   - Next → Next → Install

3. **서비스 자동 시작 확인**:
   ```cmd
   services.msc
   # "Redis" 서비스 찾기 → 시작됨 확인
   ```

4. **확인**:
   ```cmd
   redis-cli ping
   # 출력: PONG ✅
   ```

---

## 🍎 macOS 설치 방법

### Homebrew 사용

```bash
# Redis 설치
brew install redis

# 백그라운드 실행
brew services start redis

# 확인
redis-cli ping
# 출력: PONG ✅
```

---

## 🐧 Linux 설치 방법

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server -y

# 시작
sudo systemctl start redis-server

# 자동 시작 설정
sudo systemctl enable redis-server

# 확인
redis-cli ping
```

---

## 🔧 Python Redis 클라이언트 설정

### 1. 패키지 설치

```bash
pip install redis>=5.0.0
```

또는 requirements.txt에 추가:
```
redis>=5.0.0
```

### 2. utils/cache.py 생성

```python
"""Redis Cache Client"""
import redis
from config import settings
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 캐시 클라이언트"""

    def __init__(self):
        if settings.REDIS_URL:
            try:
                self.client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True
                )
                # 연결 테스트
                self.client.ping()
                logger.info("✅ Redis 연결 성공")
            except Exception as e:
                logger.warning(f"⚠️ Redis 연결 실패: {e}")
                self.client = None
        else:
            logger.info("ℹ️ Redis 비활성화 (REDIS_URL 없음)")
            self.client = None

    def get(self, key: str) -> Optional[str]:
        """캐시에서 값 가져오기"""
        if not self.client:
            return None

        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 에러: {e}")
            return None

    def set(self, key: str, value: str, ex: int = 3600):
        """캐시에 값 저장 (기본 1시간 TTL)"""
        if not self.client:
            return False

        try:
            self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis SET 에러: {e}")
            return False

    def delete(self, key: str):
        """캐시에서 삭제"""
        if not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 에러: {e}")
            return False


# 싱글톤 인스턴스
_cache = None

def get_cache() -> RedisCache:
    """Redis 캐시 싱글톤"""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache
```

### 3. 웹 검색에 캐싱 적용

```python
# tools/web_search.py 수정
from utils.cache import get_cache
import hashlib

@tool
def web_search(query: str) -> str:
    """웹 검색 with Redis 캐싱"""

    # 캐시 키 생성
    cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"

    # 캐시 확인
    cache = get_cache()
    cached_result = cache.get(cache_key)

    if cached_result:
        logger.info(f"✅ 캐시 히트: {query}")
        return cached_result

    # 캐시 미스 - Tavily API 호출
    logger.info(f"⏳ Tavily API 호출: {query}")
    results = tavily_client.search(query)
    formatted = format_results(results)

    # 캐시 저장 (1시간)
    cache.set(cache_key, formatted, ex=3600)

    return formatted
```

---

## ✅ 테스트

### 1. Redis 연결 테스트

```python
# test_redis.py
from utils.cache import get_cache

cache = get_cache()

# 저장
cache.set("test_key", "Hello Redis!")

# 조회
value = cache.get("test_key")
print(f"✅ 값: {value}")

# 삭제
cache.delete("test_key")
```

실행:
```bash
python test_redis.py
```

### 2. 캐싱 성능 테스트

```python
# test_cache_performance.py
import time
from tools.web_search import web_search

query = "CRISPR safety 2025"

# 첫 검색 (캐시 미스)
start = time.time()
result1 = web_search.invoke({"query": query})
time1 = time.time() - start
print(f"첫 검색: {time1:.2f}초")

# 두 번째 검색 (캐시 히트)
start = time.time()
result2 = web_search.invoke({"query": query})
time2 = time.time() - start
print(f"캐시 검색: {time2:.2f}초")

print(f"\n⚡ 성능 향상: {time1/time2:.0f}배 빠름")
```

출력 예:
```
⏳ Tavily API 호출: CRISPR safety 2025
첫 검색: 5.32초

✅ 캐시 히트: CRISPR safety 2025
캐시 검색: 0.01초

⚡ 성능 향상: 532배 빠름
```

---

## 📊 Redis 모니터링

### 1. Redis CLI

```bash
# Redis 접속
redis-cli

# 통계 확인
127.0.0.1:6379> INFO stats
# 히트율, 메모리 사용량 등

# 모든 키 확인
127.0.0.1:6379> KEYS *

# 특정 키 조회
127.0.0.1:6379> GET search:abc123...

# TTL 확인
127.0.0.1:6379> TTL search:abc123...
# 출력: 3456 (남은 초)

# 종료
127.0.0.1:6379> EXIT
```

### 2. Python으로 통계 확인

```python
# redis_stats.py
from utils.cache import get_cache

cache = get_cache()

if cache.client:
    info = cache.client.info("stats")
    print(f"✅ Redis 통계:")
    print(f"  - Total Commands: {info['total_commands_processed']}")
    print(f"  - Cache Hits: {info.get('keyspace_hits', 0)}")
    print(f"  - Cache Misses: {info.get('keyspace_misses', 0)}")

    # 히트율 계산
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    if total > 0:
        hit_rate = (hits / total) * 100
        print(f"  - Hit Rate: {hit_rate:.1f}%")
```

---

## 🎯 .env 설정

```env
# Redis 활성화
REDIS_URL=redis://localhost:6379

# Redis 비밀번호 사용 시
# REDIS_URL=redis://:password@localhost:6379

# Redis DB 선택 (0-15)
# REDIS_URL=redis://localhost:6379/1
```

---

## ⚠️ 문제 해결

### 연결 실패

**에러**:
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**해결**:

1. **Redis 실행 확인**:
   ```bash
   # Docker
   docker ps | grep redis

   # WSL/Linux
   sudo service redis-server status

   # Windows (서비스)
   services.msc → Redis 확인
   ```

2. **포트 확인**:
   ```bash
   netstat -ano | findstr :6379
   ```

3. **Redis 재시작**:
   ```bash
   # Docker
   docker restart virtual-lab-redis

   # WSL/Linux
   sudo service redis-server restart
   ```

### 메모리 부족

**에러**:
```
OOM command not allowed when used memory > 'maxmemory'
```

**해결**:

Redis 메모리 제한 늘리기:
```bash
# redis.conf 수정
maxmemory 256mb
maxmemory-policy allkeys-lru  # LRU 삭제 정책
```

---

## 📈 성능 비교

| 시나리오 | Redis 없음 | Redis 있음 |
|---------|-----------|-----------|
| 첫 검색 | 5초 | 5초 |
| 같은 검색 (10회) | 50초 | **5.1초** ⚡ |
| API 비용 | $0.01 | **$0.001** 💰 |
| 사용자 경험 | ⚠️ 느림 | ✅ **빠름** |

---

## 🎯 완료 체크리스트

- [ ] Redis 설치 (Docker / WSL / Native)
- [ ] Redis 시작 및 실행 확인
- [ ] `redis` 패키지 설치 (`pip install redis`)
- [ ] `utils/cache.py` 작성
- [ ] `tools/web_search.py`에 캐싱 적용
- [ ] `.env`에 `REDIS_URL` 설정
- [ ] 연결 테스트 성공
- [ ] 캐싱 성능 테스트 확인

---

**Redis 설정 완료!** 🎉

이제 웹 검색이 초고속으로 작동합니다.

**다음**: `PINECONE_SETUP.md`로 RAG 검색 설정
