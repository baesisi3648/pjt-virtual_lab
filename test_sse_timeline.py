#!/usr/bin/env python3
"""
@TASK P4-T2 - SSE Timeline 검증 스크립트
@SPEC TASKS.md#P4-T2

FastAPI SSE 엔드포인트가 올바르게 이벤트를 스트리밍하는지 검증합니다.
"""
import sys
import asyncio
import json
from typing import AsyncIterator


async def test_sse_endpoint():
    """SSE 엔드포인트 테스트"""
    try:
        import httpx
    except ImportError:
        print("❌ httpx가 설치되지 않았습니다. 설치: pip install httpx")
        return False

    print("=" * 60)
    print("P4-T2: SSE Timeline 검증")
    print("=" * 60)

    # 서버 연결 확인
    print("\n1. 서버 헬스체크...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ 서버가 실행 중입니다.")
            else:
                print(f"❌ 서버 응답 이상: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 서버에 연결할 수 없습니다: {e}")
        print("   서버를 먼저 실행하세요: uvicorn server:app --reload")
        return False

    # SSE 스트리밍 테스트
    print("\n2. SSE 스트리밍 테스트...")
    print("   주제: CRISPR-Cas9 토마토 테스트")
    print("   제약: 간단한 테스트\n")

    event_count = 0
    event_types = set()

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/research/stream",
                json={
                    "topic": "CRISPR-Cas9 토마토 테스트",
                    "constraints": "간단한 테스트",
                },
                timeout=60.0,  # 60초 타임아웃
            ) as response:
                if response.status_code != 200:
                    print(f"❌ SSE 스트리밍 시작 실패: {response.status_code}")
                    return False

                print("✅ SSE 스트리밍 시작\n")

                # 이벤트 수신
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    lines = buffer.split("\n")

                    # 마지막 불완전한 줄은 버퍼에 보관
                    buffer = lines[-1]
                    lines = lines[:-1]

                    for line in lines:
                        if line.startswith("data: "):
                            data = line[6:]  # 'data: ' 제거
                            try:
                                event = json.loads(data)
                                event_type = event.get("type", "unknown")
                                message = event.get("message", "")
                                agent = event.get("agent", "")

                                event_types.add(event_type)
                                event_count += 1

                                # 이벤트 출력
                                icon = {
                                    "start": "🚀",
                                    "phase": "📍",
                                    "agent": "🤖",
                                    "decision": "⚖️",
                                    "iteration": "🔄",
                                    "complete": "✅",
                                    "error": "❌",
                                }.get(event_type, "•")

                                agent_icon = {
                                    "scientist": "🔬",
                                    "critic": "🔍",
                                    "pi": "👔",
                                }.get(agent, "")

                                print(f"{icon} [{event_type}] {agent_icon} {message}")

                                # 완료 또는 에러 시 종료
                                if event_type in ("complete", "error"):
                                    if event_type == "complete":
                                        report_length = len(event.get("report", ""))
                                        print(f"\n📄 보고서 길이: {report_length}자")
                                    else:
                                        print(f"\n❌ 에러: {event.get('error', 'Unknown')}")
                                    break

                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON 파싱 실패: {e}")
                                continue

    except asyncio.TimeoutError:
        print("❌ 타임아웃: 60초 내에 완료되지 않았습니다.")
        return False
    except Exception as e:
        print(f"❌ 스트리밍 중 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 결과 검증
    print("\n" + "=" * 60)
    print("검증 결과")
    print("=" * 60)

    print(f"✅ 총 {event_count}개의 이벤트 수신")
    print(f"✅ 이벤트 타입: {', '.join(sorted(event_types))}")

    # 필수 이벤트 타입 확인
    required_types = {"start", "agent", "complete"}
    missing_types = required_types - event_types

    if missing_types:
        print(f"⚠️  누락된 이벤트 타입: {', '.join(missing_types)}")
        return False

    print("\n✅ 모든 검증 통과!")
    return True


async def main():
    """메인 함수"""
    success = await test_sse_endpoint()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
