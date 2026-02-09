#!/usr/bin/env python3
"""
@TASK P4-T2 - Timeline Setup Verification
@SPEC TASKS.md#P4-T2

Verify P4-T2 implementation setup.
"""
import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if file exists"""
    path = Path(file_path)
    if path.exists():
        print(f"[OK] {description}: {file_path}")
        return True
    else:
        print(f"[FAIL] {description} not found: {file_path}")
        return False


def check_code_contains(file_path: str, search_text: str, description: str) -> bool:
    """Check if file contains specific text"""
    path = Path(file_path)
    if not path.exists():
        print(f"[SKIP] File not found: {file_path}")
        return False

    content = path.read_text(encoding="utf-8")
    if search_text in content:
        print(f"[OK] {description}")
        return True
    else:
        print(f"[FAIL] {description} (not found: {search_text})")
        return False


def main():
    """Main verification function"""
    print("=" * 60)
    print("P4-T2: Live Process Timeline Setup Verification")
    print("=" * 60)

    base_dir = Path(__file__).parent
    frontend_dir = base_dir / "frontend"

    checks = []

    # 1. Backend files
    print("\n1. Backend Files")
    print("-" * 60)

    checks.append(
        check_file_exists(
            str(base_dir / "server.py"),
            "FastAPI server"
        )
    )

    checks.append(
        check_code_contains(
            str(base_dir / "server.py"),
            "generate_research_events",
            "SSE generator function defined"
        )
    )

    checks.append(
        check_code_contains(
            str(base_dir / "server.py"),
            "/api/research/stream",
            "SSE endpoint defined"
        )
    )

    checks.append(
        check_code_contains(
            str(base_dir / "server.py"),
            "StreamingResponse",
            "StreamingResponse used"
        )
    )

    # 2. Frontend files
    print("\n2. Frontend Files")
    print("-" * 60)

    checks.append(
        check_file_exists(
            str(frontend_dir / "src/components/ProcessTimeline.tsx"),
            "ProcessTimeline component"
        )
    )

    checks.append(
        check_code_contains(
            str(frontend_dir / "src/components/ProcessTimeline.tsx"),
            "'use client'",
            "Client Component defined"
        )
    )

    checks.append(
        check_code_contains(
            str(frontend_dir / "src/components/ProcessTimeline.tsx"),
            "AGENT_CONFIG",
            "Agent config defined"
        )
    )

    checks.append(
        check_file_exists(
            str(frontend_dir / "src/app/timeline/page.tsx"),
            "Timeline demo page"
        )
    )

    # 3. Configuration files
    print("\n3. Configuration Files")
    print("-" * 60)

    checks.append(
        check_file_exists(
            str(base_dir / ".env"),
            ".env file"
        )
    )

    checks.append(
        check_code_contains(
            str(base_dir / ".env"),
            "OPENAI_API_KEY",
            "OpenAI API Key configured"
        )
    )

    checks.append(
        check_file_exists(
            str(frontend_dir / ".env.local"),
            "Frontend .env.local file"
        )
    )

    # 4. TypeScript configuration
    print("\n4. TypeScript Configuration")
    print("-" * 60)

    checks.append(
        check_file_exists(
            str(frontend_dir / "tsconfig.json"),
            "TypeScript config"
        )
    )

    checks.append(
        check_code_contains(
            str(frontend_dir / "tsconfig.json"),
            '"@/*": ["./src/*"]',
            "Path alias configured"
        )
    )

    # 5. Dependencies
    print("\n5. Dependencies")
    print("-" * 60)

    # Check Python modules
    try:
        import fastapi
        print(f"[OK] fastapi installed (v{fastapi.__version__})")
        checks.append(True)
    except ImportError:
        print("[FAIL] fastapi not installed")
        checks.append(False)

    try:
        import httpx
        print(f"[OK] httpx installed (v{httpx.__version__})")
        checks.append(True)
    except ImportError:
        print("[FAIL] httpx not installed")
        checks.append(False)

    # Check node modules
    node_modules = frontend_dir / "node_modules"
    if node_modules.exists():
        print("[OK] Node modules installed")
        checks.append(True)
    else:
        print("[FAIL] Node modules not installed (run: npm install)")
        checks.append(False)

    # 6. Test scripts
    print("\n6. Test Scripts")
    print("-" * 60)

    checks.append(
        check_file_exists(
            str(base_dir / "test_sse_timeline.py"),
            "SSE test script"
        )
    )

    checks.append(
        check_file_exists(
            str(base_dir / "P4-T2-COMPLETION-REPORT.md"),
            "Completion report"
        )
    )

    # Results
    print("\n" + "=" * 60)
    print("Verification Results")
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"\nPassed: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print("\n[SUCCESS] All checks passed! P4-T2 setup completed.")
        print("\nNext steps:")
        print("1. Start backend: uvicorn server:app --reload")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Open browser: http://localhost:3000/timeline")
        print("4. Run SSE test: python test_sse_timeline.py")
        return True
    else:
        print(f"\n[WARNING] {total - passed} checks failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
