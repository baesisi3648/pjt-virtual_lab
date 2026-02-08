#!/usr/bin/env python3
# @TASK P3-T4 - Dynamic Workflow Execution Example
# @SPEC TASKS.md#P3-T4
"""Dynamic Workflow Execution 사용 예시

PI가 팀을 결정하고(P3-T3), 결정된 팀으로 동적 워크플로우를 실행(P3-T4)하는 전체 플로우를 시연합니다.

## 실행 방법
```bash
cd worktree/phase-3-api-ui
python examples/dynamic_workflow_example.py
```

## 주요 기능
1. PI가 사용자 질문을 분석하여 필요한 전문가 팀 구성
2. 결정된 팀 프로필로 동적 워크플로우 생성
3. 전문가들의 병렬 분석 수행
4. PI가 전문가 의견을 종합하여 최종 보고서 생성
"""
import asyncio
import os

from agents.pi import decide_team
from workflow.dynamic_graph import build_dynamic_workflow


async def main():
    """메인 실행 함수"""

    # OpenAI API Key 확인
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return

    # 사용자 질문
    user_query = "고올레산 대두의 지방산 조성 변화가 알레르기 유발 가능성에 미치는 영향 평가"

    print("=" * 80)
    print("Dynamic Workflow Execution - 전체 플로우 시연")
    print("=" * 80)
    print()

    # Step 1: PI가 팀 구성 결정 (P3-T3)
    print("[Step 1] PI가 질문을 분석하여 전문가 팀 구성...")
    print(f"질문: {user_query}")
    print()

    team_profiles = decide_team(user_query)

    print(f"결정된 팀 ({len(team_profiles)}명):")
    for i, profile in enumerate(team_profiles, 1):
        print(f"  {i}. {profile['role']}")
        print(f"     - 집중 분야: {profile['focus']}")
    print()

    # Step 2: 동적 워크플로우 생성 (P3-T4)
    print("[Step 2] 팀 구성에 따라 동적 워크플로우 생성...")
    graph = build_dynamic_workflow(team_profiles)
    print("워크플로우 생성 완료!")
    print()

    # Step 3: 워크플로우 실행
    print("[Step 3] 전문가들의 병렬 분석 실행 중...")
    print("(각 전문가가 GPT-4o를 사용하여 분석 수행)")
    print()

    initial_state = {
        "query": user_query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    }

    result = await graph.ainvoke(initial_state)

    # Step 4: 결과 출력
    print("[Step 4] 분석 결과")
    print("=" * 80)
    print()

    for i, response in enumerate(result["specialist_responses"], 1):
        print(f"[전문가 {i}: {team_profiles[i-1]['role']}]")
        print(response[:300] + "..." if len(response) > 300 else response)
        print()
        print("-" * 80)
        print()

    print("[PI 종합 보고서]")
    print(result["final_synthesis"])
    print()
    print("=" * 80)
    print("실행 완료!")


if __name__ == "__main__":
    asyncio.run(main())
