#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P4-T3 검증 스크립트: Interactive Report Editor
"""

import sys
import os
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def check_file_exists(path: str, description: str) -> bool:
    """파일 존재 확인"""
    if Path(path).exists():
        print(f"[OK] {description}")
        return True
    else:
        print(f"[FAIL] {description} - 파일이 없습니다: {path}")
        return False


def check_content(path: str, keywords: list[str], description: str) -> bool:
    """파일 내용에 특정 키워드 포함 확인"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = [kw for kw in keywords if kw not in content]
        if not missing:
            print(f"[OK] {description}")
            return True
        else:
            print(f"[FAIL] {description} - 누락된 키워드: {', '.join(missing)}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} - {str(e)}")
        return False


def main():
    print("=" * 60)
    print("P4-T3 검증: Interactive Report Editor")
    print("=" * 60)

    worktree = "worktree/phase-4-nextjs"
    frontend = f"{worktree}/frontend"

    results = []

    # 1. ReportEditor 컴포넌트 존재 확인
    print("\n[1] ReportEditor 컴포넌트")
    results.append(check_file_exists(
        f"{frontend}/src/components/ReportEditor.tsx",
        "ReportEditor.tsx 파일 존재"
    ))

    # 2. ReportEditor 필수 기능 확인
    print("\n[2] ReportEditor 필수 기능")
    results.append(check_content(
        f"{frontend}/src/components/ReportEditor.tsx",
        [
            "react-markdown",
            "RegenerateRequest",
            "onRegenerate",
            "편집",
            "재검토",
            "피드백",
        ],
        "ReportEditor 필수 기능 포함"
    ))

    # 3. 테스트 파일 존재 확인
    print("\n[3] 테스트 파일")
    results.append(check_file_exists(
        f"{frontend}/src/components/__tests__/ReportEditor.test.tsx",
        "ReportEditor.test.tsx 파일 존재"
    ))

    # 4. 테스트 케이스 확인
    print("\n[4] 테스트 케이스")
    results.append(check_content(
        f"{frontend}/src/components/__tests__/ReportEditor.test.tsx",
        [
            "마크다운 보고서를 렌더링한다",
            "재검토 요청 버튼이 표시된다",
            "피드백 제출 시 onRegenerate 콜백이 호출된다",
            "편집 모드 토글이 가능하다",
        ],
        "주요 테스트 케이스 포함"
    ))

    # 5. API 클라이언트 업데이트 확인
    print("\n[5] API 클라이언트")
    results.append(check_content(
        f"{frontend}/src/lib/api.ts",
        [
            "RegenerateRequest",
            "RegenerateResponse",
            "regenerateSection",
        ],
        "API 클라이언트에 regenerateSection 추가"
    ))

    # 6. FastAPI 엔드포인트 확인
    print("\n[6] FastAPI 백엔드")
    results.append(check_content(
        f"{worktree}/server.py",
        [
            "RegenerateRequest",
            "RegenerateResponse",
            "/api/report/regenerate",
        ],
        "FastAPI에 재검토 API 엔드포인트 추가"
    ))

    # 7. 데모 페이지 확인
    print("\n[7] 데모 페이지")
    results.append(check_file_exists(
        f"{frontend}/src/app/report-demo/page.tsx",
        "report-demo 페이지 존재"
    ))

    # 8. 패키지 의존성 확인
    print("\n[8] 패키지 의존성")
    results.append(check_content(
        f"{frontend}/package.json",
        [
            "react-markdown",
            "remark-gfm",
            "vitest",
        ],
        "필수 패키지 설치됨"
    ))

    # 결과 요약
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)

    total = len(results)
    passed = sum(results)

    print(f"총 {total}개 항목 중 {passed}개 통과")

    if passed == total:
        print("\n✅ 모든 검증 통과!")
        print("\n다음 단계:")
        print("1. FastAPI 서버 시작: cd worktree/phase-4-nextjs && uvicorn server:app --reload --port 8000")
        print("2. Next.js 서버 시작: cd frontend && npm run dev")
        print("3. 브라우저에서 http://localhost:3000/report-demo 접속")
        print("4. '알레르기' 섹션 클릭 → 재검토 요청 → 피드백 입력 → 제출")
        print("5. 업데이트된 내용 확인")
        return 0
    else:
        print(f"\n❌ {total - passed}개 항목 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
