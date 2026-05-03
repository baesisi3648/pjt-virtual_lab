#!/usr/bin/env python
# @TASK P3-T3 - PI Decision Logic 예제
# @SPEC TASKS.md#P3-T3
"""PI Decision Logic 사용 예제

PI가 사용자 쿼리를 분석하여 필요한 전문가 팀을 구성하고,
각 전문가를 팩토리로 생성하는 전체 워크플로우를 시연합니다.
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from dotenv import load_dotenv
from agents.pi import decide_team
from agents.factory import create_specialist

# 환경 변수 로드
load_dotenv()


def main():
    """PI Decision Logic 예제 실행"""
    print("=" * 80)
    print("PI Decision Logic - 전문가 팀 구성 예제")
    print("=" * 80)
    print()

    # 테스트 쿼리들
    queries = [
        "고올레산 대두의 지방산 조성 변화에 대한 안전성 평가",
        "유전자편집 대두의 알레르겐성 평가",
        "NGT 식품의 표준 안전성 평가 프레임워크 개발",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n[쿼리 {i}] {query}")
        print("-" * 80)

        try:
            # Step 1: PI가 전문가 팀 구성
            print("\n[Step 1] PI가 전문가 팀 구성 중...")
            team = decide_team(query)

            print(f"\n전문가 팀 ({len(team)}명):")
            for j, expert in enumerate(team, 1):
                print(f"  {j}. {expert['role']}")
                print(f"     전문 분야: {expert['focus']}")

            # Step 2: 각 전문가를 팩토리로 생성 (시연)
            print("\n[Step 2] 전문가 에이전트 생성 중...")
            specialists = []
            for expert in team:
                agent = create_specialist(expert)
                specialists.append(agent)
                print(f"  ✓ {expert['role']} 에이전트 생성 완료")

            # Step 3: 첫 번째 전문가에게 간단한 질문 (시연)
            if specialists:
                print("\n[Step 3] 첫 번째 전문가에게 질문 시연...")
                first_expert = team[0]
                first_agent = specialists[0]

                sample_query = f"당신의 전문 분야인 '{first_expert['focus']}'에 대해 간단히 설명해주세요."
                print(f"\n질문: {sample_query}")

                response = first_agent.invoke(sample_query)
                print(f"\n답변 ({first_expert['role']}):")
                print(f"  {response[:200]}..." if len(response) > 200 else f"  {response}")

        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
