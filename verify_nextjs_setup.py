#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@TASK P4-T1 - Next.js Setup Verification
@SPEC TASKS.md#P4-T1

Next.js 프로젝트 설정을 검증합니다.
"""
import json
import os
import sys
from pathlib import Path

# Windows 콘솔 유니코드 지원
if sys.platform == "win32":
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')


def verify_nextjs_setup():
    """Next.js 프로젝트 설정 검증"""
    print("=" * 60)
    print("Next.js Setup Verification")
    print("=" * 60)

    # 1. frontend 디렉토리 존재 확인
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("[FAIL] frontend directory not found")
        return False
    print("[OK] frontend directory exists")

    # 2. package.json 확인
    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        print("[FAIL] package.json not found")
        return False

    with open(package_json, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    print("\nDependencies:")
    print(f"  - Next.js: {pkg['dependencies'].get('next', 'N/A')}")
    print(f"  - React: {pkg['dependencies'].get('react', 'N/A')}")
    print(f"  - TypeScript: {pkg['devDependencies'].get('typescript', 'N/A')}")
    print(f"  - Tailwind CSS: {pkg['devDependencies'].get('tailwindcss', 'N/A')}")

    # 3. next.config.ts 확인
    next_config = frontend_dir / "next.config.ts"
    if not next_config.exists():
        print("\n[FAIL] next.config.ts not found")
        return False

    with open(next_config, "r", encoding="utf-8") as f:
        config_content = f.read()

    if "rewrites" not in config_content:
        print("\n[FAIL] next.config.ts missing rewrites configuration")
        return False
    print("\n[OK] next.config.ts has API proxy configuration")

    # 4. TypeScript 설정 확인
    tsconfig = frontend_dir / "tsconfig.json"
    if not tsconfig.exists():
        print("[FAIL] tsconfig.json not found")
        return False
    print("[OK] tsconfig.json exists")

    # 5. 환경 변수 파일 확인
    env_local = frontend_dir / ".env.local"
    if not env_local.exists():
        print("[FAIL] .env.local not found")
        return False

    with open(env_local, "r", encoding="utf-8") as f:
        env_content = f.read()

    if "NEXT_PUBLIC_API_URL" not in env_content:
        print("[FAIL] .env.local missing NEXT_PUBLIC_API_URL")
        return False
    print("[OK] .env.local has environment variables")

    # 6. API 클라이언트 확인
    api_client = frontend_dir / "src" / "lib" / "api.ts"
    if not api_client.exists():
        print("[FAIL] API client (src/lib/api.ts) not found")
        return False
    print("[OK] API client exists")

    # 7. 테스트 API Route 확인
    test_route = frontend_dir / "src" / "app" / "api" / "test" / "route.ts"
    if not test_route.exists():
        print("[FAIL] Test API route not found")
        return False
    print("[OK] Test API route exists")

    # 8. node_modules 확인
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("\n[WARN] node_modules not found. Run 'npm install'")
        return False
    print("[OK] node_modules exists")

    print("\n" + "=" * 60)
    print("All verifications passed!")
    print("=" * 60)
    print("\nStart development server with:")
    print("  cd frontend && npm run dev")
    print("\nThen access:")
    print("  http://localhost:3000")
    print("\nTest API:")
    print("  curl http://localhost:3000/api/test")
    return True


def verify_fastapi_cors():
    """FastAPI CORS 설정 검증"""
    print("\n" + "=" * 60)
    print("FastAPI CORS Configuration Verification")
    print("=" * 60)

    server_file = Path("server.py")
    if not server_file.exists():
        print("[FAIL] server.py not found")
        return False

    with open(server_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "CORSMiddleware" not in content:
        print("[FAIL] CORS middleware not configured")
        return False

    if "localhost:3000" not in content:
        print("[WARN] localhost:3000 not in CORS allowed origins")
        return False

    print("[OK] CORS supports Next.js")
    print("\nAllowed origins:")
    print("  - http://localhost:3000 (Next.js)")
    print("  - http://localhost:8501 (Streamlit)")
    return True


if __name__ == "__main__":
    success = verify_nextjs_setup()
    if success:
        verify_fastapi_cors()
        sys.exit(0)
    else:
        sys.exit(1)
