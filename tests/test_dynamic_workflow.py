# @TASK P3-T4 - Dynamic Workflow Execution
# @SPEC TASKS.md#P3-T4
"""Dynamic Workflow Execution 테스트

PI가 결정한 팀 구성에 따라 동적으로 워크플로우를 생성하고 실행하는 테스트
"""
import pytest
from workflow.dynamic_graph import build_dynamic_workflow


@pytest.mark.asyncio
async def test_build_graph_with_two_specialists():
    """2명의 전문가로 그래프 구성"""
    team_profiles = [
        {
            "role": "Metabolomics Expert",
            "focus": "lipid composition analysis",
        },
        {
            "role": "Allergen Specialist",
            "focus": "protein cross-reactivity assessment",
        },
    ]

    query = "고올레산 대두의 지방산 조성 안전성 평가"

    # 그래프 동적 생성
    graph = build_dynamic_workflow(team_profiles)

    # 실행
    result = await graph.ainvoke({
        "query": query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 검증: 각 전문가의 응답이 수집되었는지
    assert len(result["specialist_responses"]) == 2
    assert any("lipid" in resp.lower() or "지방" in resp for resp in result["specialist_responses"])

    # 검증: 최종 종합 보고서가 생성되었는지
    assert result["final_synthesis"]
    assert len(result["final_synthesis"]) > 50


@pytest.mark.asyncio
async def test_build_graph_with_single_specialist():
    """1명의 전문가로 그래프 구성"""
    team_profiles = [
        {
            "role": "Toxicology Expert",
            "focus": "acute toxicity assessment",
        },
    ]

    query = "NGT 대두의 급성 독성 평가"

    graph = build_dynamic_workflow(team_profiles)

    result = await graph.ainvoke({
        "query": query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 검증: 1명의 전문가 응답
    assert len(result["specialist_responses"]) == 1
    assert result["final_synthesis"]


@pytest.mark.asyncio
async def test_build_graph_with_five_specialists():
    """5명의 전문가로 그래프 구성 (최대 제한 테스트)"""
    team_profiles = [
        {"role": "Expert A", "focus": "area A"},
        {"role": "Expert B", "focus": "area B"},
        {"role": "Expert C", "focus": "area C"},
        {"role": "Expert D", "focus": "area D"},
        {"role": "Expert E", "focus": "area E"},
    ]

    query = "복합 안전성 평가"

    graph = build_dynamic_workflow(team_profiles)

    result = await graph.ainvoke({
        "query": query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 검증: 5명의 전문가 응답
    assert len(result["specialist_responses"]) == 5
    assert result["final_synthesis"]


def test_build_graph_returns_compiled_graph():
    """그래프 반환 타입 검증"""
    team_profiles = [
        {"role": "Test Expert", "focus": "test area"},
    ]

    graph = build_dynamic_workflow(team_profiles)

    # CompiledStateGraph 인스턴스 확인
    assert hasattr(graph, "invoke")
    assert hasattr(graph, "ainvoke")


def test_build_graph_with_empty_team_raises_error():
    """빈 팀으로 그래프 생성 시 에러 발생"""
    with pytest.raises(ValueError, match="최소 1명"):
        build_dynamic_workflow([])


def test_build_graph_with_invalid_profile_raises_error():
    """잘못된 프로필 형식으로 그래프 생성 시 에러 발생"""
    invalid_profiles = [
        {"role": "Expert"},  # focus 누락
    ]

    with pytest.raises(ValueError):
        build_dynamic_workflow(invalid_profiles)
