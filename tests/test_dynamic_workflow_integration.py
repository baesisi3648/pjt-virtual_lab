# @TASK P3-T4 - Dynamic Workflow Integration Test
# @SPEC TASKS.md#P3-T4
"""Dynamic Workflow 통합 테스트

P3-T3(decide_team)과 P3-T4(build_dynamic_workflow)의 통합을 검증합니다.
"""
import pytest


@pytest.mark.asyncio
async def test_full_dynamic_workflow_integration():
    """전체 플로우 통합 테스트: decide_team -> build_dynamic_workflow -> execute"""
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    # 사용자 질문
    user_query = "고올레산 대두의 지방산 조성 안전성 평가"

    # Step 1: PI가 팀 구성 결정
    team_profiles = decide_team(user_query)

    # 검증: 팀이 구성되었는지
    assert len(team_profiles) >= 1
    assert all("role" in p and "focus" in p for p in team_profiles)

    # Step 2: 동적 워크플로우 생성
    graph = build_dynamic_workflow(team_profiles)

    # 검증: 그래프가 생성되었는지
    assert graph is not None
    assert hasattr(graph, "ainvoke")

    # Step 3: 워크플로우 실행
    result = await graph.ainvoke({
        "query": user_query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 검증: 각 전문가의 응답이 수집되었는지
    assert len(result["specialist_responses"]) == len(team_profiles)
    assert all(isinstance(resp, str) and len(resp) > 0 for resp in result["specialist_responses"])

    # 검증: 최종 종합 보고서가 생성되었는지
    assert result["final_synthesis"]
    assert len(result["final_synthesis"]) > 100


@pytest.mark.asyncio
async def test_dynamic_workflow_handles_different_queries():
    """다양한 질문에 대해 동적 워크플로우가 작동하는지 확인"""
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    queries = [
        "NGT 대두의 알레르기 평가",
        "유전자편집 옥수수의 영양성분 분석",
        "CRISPR로 개발된 토마토의 독성 평가",
    ]

    for query in queries:
        # PI가 팀 구성 결정
        team = decide_team(query)
        assert len(team) >= 1

        # 워크플로우 생성 및 실행
        graph = build_dynamic_workflow(team)
        result = await graph.ainvoke({
            "query": query,
            "team_profiles": team,
            "specialist_responses": [],
            "final_synthesis": "",
        })

        # 응답 검증
        assert len(result["specialist_responses"]) == len(team)
        assert result["final_synthesis"]


@pytest.mark.asyncio
async def test_dynamic_workflow_preserves_query_context():
    """워크플로우가 질문 컨텍스트를 유지하는지 확인"""
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    query = "고올레산 대두의 P34 단백질 알레르기 유발 가능성"

    team = decide_team(query)
    graph = build_dynamic_workflow(team)

    result = await graph.ainvoke({
        "query": query,
        "team_profiles": team,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 최종 보고서에 질문의 핵심 키워드가 포함되어 있는지 확인
    synthesis_lower = result["final_synthesis"].lower()
    assert any(keyword in synthesis_lower for keyword in ["대두", "soy", "알레르기", "allerg", "단백질", "protein"])
