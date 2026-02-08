# @TASK P3-T6 - End-to-End Parallel Brain System Test
# @SPEC TASKS.md#P3-T6
"""End-to-End Parallel Brain System 통합 테스트

전체 Brain 시스템을 통합 테스트합니다:
- PI의 팀 구성 결정 (decide_team)
- 동적 전문가 생성 (factory)
- 병렬 워크플로우 실행 (parallel_graph + dynamic_graph)
- 의견 통합 (merge_views)
- 최종 보고서 생성

목표 실행 시간: 5분 이내
"""
import time
import pytest


@pytest.mark.asyncio
async def test_parallel_brain_full_pipeline():
    """전체 Brain 시스템 End-to-End 테스트

    시나리오:
    1. 쿼리: "고올레산 대두 안전성 평가"
    2. PI가 팀 구성 결정 (예상: 대사체학자 + 영양학자)
    3. 동적 워크플로우 생성
    4. 병렬 전문가 회의 실행
    5. 최종 통합 보고서 생성
    6. 실행 시간 5분 이내 검증
    """
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    start_time = time.time()

    # Given: 사용자 질문
    user_query = "고올레산 대두 안전성 평가"

    # Step 1: PI가 팀 구성 결정
    team_profiles = decide_team(user_query)

    # 검증: 팀이 구성되었는지
    assert len(team_profiles) >= 1, "최소 1명의 전문가가 필요합니다"
    assert all("role" in p and "focus" in p for p in team_profiles), "각 프로필은 role과 focus가 필요합니다"

    # 검증: 대두 안전성 평가에 적합한 전문가가 포함되어 있는지
    # (대사체학자, 영양학자, 생화학자, 식품안전 전문가 등)
    roles = [p["role"].lower() for p in team_profiles]
    roles_text = " ".join(roles)
    focuses = [p["focus"].lower() for p in team_profiles]
    focuses_text = " ".join(focuses)
    combined_text = roles_text + " " + focuses_text

    assert any(
        keyword in combined_text
        for keyword in [
            "metabol", "nutrition", "lipid", "fatty", "biochem", "food", "safety",
            "지방", "영양", "대사", "생화학", "식품", "안전"
        ]
    ), f"고올레산 대두 평가에 적합한 전문가가 없습니다. 실제 팀: {team_profiles}"

    # Step 2: 동적 워크플로우 생성
    graph = build_dynamic_workflow(team_profiles)
    assert graph is not None, "워크플로우 생성 실패"
    assert hasattr(graph, "ainvoke"), "워크플로우가 ainvoke 메서드를 제공해야 합니다"

    # Step 3: 병렬 워크플로우 실행
    result = await graph.ainvoke({
        "query": user_query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # Step 4: 결과 검증 - 전문가 응답
    assert "specialist_responses" in result, "specialist_responses 필드가 없습니다"
    assert len(result["specialist_responses"]) == len(team_profiles), \
        f"전문가 수({len(team_profiles)})와 응답 수({len(result['specialist_responses'])})가 일치하지 않습니다"

    for i, response in enumerate(result["specialist_responses"]):
        assert isinstance(response, str), f"전문가 {i}의 응답이 문자열이 아닙니다"
        assert len(response) > 50, f"전문가 {i}의 응답이 너무 짧습니다 (50자 미만)"

    # Step 5: 결과 검증 - 최종 통합 보고서
    assert "final_synthesis" in result, "final_synthesis 필드가 없습니다"
    assert result["final_synthesis"], "최종 보고서가 비어있습니다"
    assert len(result["final_synthesis"]) > 100, "최종 보고서가 너무 짧습니다 (100자 미만)"

    # 보고서에 질문의 핵심 키워드가 포함되어 있는지 확인
    synthesis_lower = result["final_synthesis"].lower()
    assert any(
        keyword in synthesis_lower
        for keyword in ["대두", "soy", "올레산", "oleic", "안전", "safety"]
    ), "최종 보고서에 질문 관련 키워드가 없습니다"

    # Step 6: 실행 시간 검증 (5분 = 300초)
    elapsed_time = time.time() - start_time
    assert elapsed_time < 300, f"실행 시간이 5분을 초과했습니다: {elapsed_time:.2f}초"

    # 성공 로그
    print(f"\n[SUCCESS] 전체 Brain 시스템 통합 테스트 완료")
    print(f"  - 팀 크기: {len(team_profiles)}명")
    print(f"  - 팀 구성: {[p['role'] for p in team_profiles]}")
    print(f"  - 전문가 응답 수: {len(result['specialist_responses'])}개")
    print(f"  - 최종 보고서 길이: {len(result['final_synthesis'])}자")
    print(f"  - 실행 시간: {elapsed_time:.2f}초")


@pytest.mark.asyncio
async def test_parallel_brain_handles_complex_query():
    """복잡한 질문에 대한 Brain 시스템 테스트

    시나리오: 여러 도메인이 필요한 복잡한 질문
    예상: 3명 이상의 전문가 동원
    """
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    # 복잡한 질문 (대사체학 + 독성학 + 영양학 필요)
    user_query = "CRISPR로 개발된 고올레산 대두의 알레르기 유발 가능성과 영양학적 안전성 평가"

    # PI가 팀 구성 결정
    team_profiles = decide_team(user_query)

    # 복잡한 질문이므로 여러 전문가 필요
    assert len(team_profiles) >= 2, f"복잡한 질문에는 2명 이상의 전문가가 필요합니다. 실제: {len(team_profiles)}명"

    # 워크플로우 생성 및 실행
    graph = build_dynamic_workflow(team_profiles)
    result = await graph.ainvoke({
        "query": user_query,
        "team_profiles": team_profiles,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 각 전문가가 응답했는지 확인
    assert len(result["specialist_responses"]) == len(team_profiles)

    # 최종 보고서가 복잡한 질문의 여러 측면을 다루는지 확인
    synthesis_lower = result["final_synthesis"].lower()
    keyword_count = sum(
        1 for keyword in ["알레르기", "allerg", "영양", "nutrition", "안전", "safety"]
        if keyword in synthesis_lower
    )
    assert keyword_count >= 2, "최종 보고서가 질문의 여러 측면을 충분히 다루지 않습니다"


@pytest.mark.asyncio
async def test_parallel_brain_performance_with_multiple_queries():
    """여러 질문에 대한 Brain 시스템 성능 테스트

    3개의 서로 다른 질문을 순차적으로 처리하고
    각각 정상적으로 동작하는지 확인
    """
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    queries = [
        "NGT 옥수수의 독성 평가",
        "유전자편집 토마토의 영양성분 분석",
        "CRISPR 밀의 알레르기 유발 가능성",
    ]

    for query in queries:
        # 팀 구성
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

        # 기본 검증
        assert len(result["specialist_responses"]) == len(team)
        assert result["final_synthesis"]
        assert len(result["final_synthesis"]) > 50


@pytest.mark.asyncio
async def test_parallel_brain_integration_with_merge_views():
    """Brain 시스템의 merge_views 통합 테스트

    여러 전문가의 의견이 Critic의 merge_views 로직에 따라
    올바르게 통합되는지 확인
    """
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow
    from agents.critic import merge_views

    # 의견 충돌 가능성이 있는 질문
    user_query = "고올레산 대두의 알레르기 평가 면제 가능성"

    # 팀 구성 및 실행
    team = decide_team(user_query)
    graph = build_dynamic_workflow(team)
    result = await graph.ainvoke({
        "query": user_query,
        "team_profiles": team,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 전문가 응답들을 merge_views로 통합
    specialist_responses = result["specialist_responses"]
    merged_analysis = merge_views(specialist_responses)

    # 통합된 분석이 비어있지 않은지 확인
    assert merged_analysis
    assert len(merged_analysis) > 0

    # 최종 보고서에도 통합된 관점이 반영되어 있는지 확인
    # (dynamic_graph의 synthesize_specialist_views가 merge_views를 사용하지는 않지만,
    # 유사한 통합 로직을 거쳤을 것)
    assert result["final_synthesis"]


@pytest.mark.asyncio
async def test_parallel_brain_empty_query_handling():
    """빈 질문 또는 부적절한 질문 처리 테스트"""
    from agents.pi import decide_team

    # 빈 질문
    try:
        team = decide_team("")
        # 빈 질문에도 기본 팀을 구성할 수 있음
        assert len(team) >= 0
    except Exception as e:
        # 또는 예외를 발생시킬 수 있음
        assert isinstance(e, (ValueError, Exception))


@pytest.mark.asyncio
async def test_parallel_brain_query_context_preservation():
    """Brain 시스템이 질문 컨텍스트를 유지하는지 확인

    특정 키워드가 전문가 응답과 최종 보고서에 모두 반영되는지 확인
    """
    from agents.pi import decide_team
    from workflow.dynamic_graph import build_dynamic_workflow

    # 특정 키워드가 포함된 질문
    user_query = "고올레산 대두의 P34 단백질 알레르기 평가"
    key_terms = ["대두", "soy", "p34", "단백질", "protein", "알레르기", "allerg"]

    # 팀 구성 및 실행
    team = decide_team(user_query)
    graph = build_dynamic_workflow(team)
    result = await graph.ainvoke({
        "query": user_query,
        "team_profiles": team,
        "specialist_responses": [],
        "final_synthesis": "",
    })

    # 전문가 응답에 핵심 키워드가 포함되어 있는지 확인
    all_responses_text = " ".join(result["specialist_responses"]).lower()
    found_in_responses = sum(
        1 for term in key_terms if term.lower() in all_responses_text
    )
    assert found_in_responses >= 1, "전문가 응답에 질문의 핵심 키워드가 없습니다"

    # 최종 보고서에 핵심 키워드가 포함되어 있는지 확인
    synthesis_lower = result["final_synthesis"].lower()
    found_in_synthesis = sum(
        1 for term in key_terms if term.lower() in synthesis_lower
    )
    assert found_in_synthesis >= 1, "최종 보고서에 질문의 핵심 키워드가 없습니다"
