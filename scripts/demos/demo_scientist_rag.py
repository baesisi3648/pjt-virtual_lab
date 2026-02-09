"""
Scientist + RAG 통합 검증 데모

P1-T4: Scientist 에이전트가 RAG Tool을 사용하여
규제 문서를 검색하고 citation을 포함한 답변을 생성하는지 검증합니다.

실행 방법:
    python demo_scientist_rag.py
"""
import os
import sys
import logging
from unittest.mock import patch, MagicMock

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_with_mock_rag():
    """Mock RAG로 Scientist 통합 테스트"""
    print("=" * 80)
    print("DEMO: Scientist + RAG Integration (Mock)")
    print("=" * 80)

    # Mock RAG retrieve
    mock_docs = [
        {
            'text': '알레르기 평가는 아미노산 서열 유사성 분석 및 in vitro 소화성 시험을 포함해야 한다.',
            'metadata': {'source': 'Codex Guideline CAC/GL 45-2003', 'year': 2003, 'page': 12},
            'distance': 0.05
        },
        {
            'text': 'Off-target 효과는 전장 유전체 시퀀싱(WGS)을 통해 검증되어야 한다.',
            'metadata': {'source': 'EFSA Scientific Opinion', 'year': 2023, 'page': 8},
            'distance': 0.08
        }
    ]

    with patch('rag.retriever.retrieve') as mock_retrieve:
        mock_retrieve.return_value = mock_docs

        # Scientist 실행 (직접 import to avoid circular dependency)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "scientist",
            "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-1-rag/agents/scientist.py"
        )
        scientist_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scientist_module)
        run_scientist = scientist_module.run_scientist

        state = {
            "topic": "대두 알레르기 평가",
            "constraints": "Codex 기준 준수",
            "messages": []
        }

        print("\n[INPUT STATE]")
        print(f"Topic: {state['topic']}")
        print(f"Constraints: {state['constraints']}")

        print("\n[EXECUTING SCIENTIST...]")
        result = run_scientist(state)

        print("\n[RESULT]")
        print(f"Draft length: {len(result['draft'])} characters")
        print("\n[DRAFT CONTENT]")
        print(result['draft'])

        # 검증
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)

        has_citation = "[출처:" in result['draft']
        has_codex = "Codex" in result['draft'] or "CAC/GL" in result['draft']
        has_content = len(result['draft']) > 100

        print(f"✓ Contains citation: {has_citation}")
        print(f"✓ References Codex: {has_codex}")
        print(f"✓ Sufficient content: {has_content}")

        if has_citation and has_codex and has_content:
            print("\n✅ SUCCESS: Scientist successfully uses RAG and includes citations!")
        else:
            print("\n❌ FAILED: Missing citation or reference")
            print("Note: LLM may not always use tools. Check logs for tool calls.")

        # RAG 호출 여부 확인
        if mock_retrieve.called:
            print(f"\n✓ RAG was called {mock_retrieve.call_count} times")
            for call in mock_retrieve.call_args_list:
                print(f"  - Query: {call[0][0]}")
        else:
            print("\n⚠️  RAG was NOT called (LLM chose not to use tool)")


def demo_without_rag():
    """RAG 없이 Scientist 실행 (baseline)"""
    print("\n" + "=" * 80)
    print("DEMO: Scientist without RAG (Baseline)")
    print("=" * 80)

    # Mock empty RAG
    with patch('rag.retriever.retrieve') as mock_retrieve:
        mock_retrieve.return_value = []

        from agents.scientist import run_scientist

        state = {
            "topic": "NGT 안전성 평가 일반론",
            "constraints": "",
            "messages": []
        }

        print("\n[INPUT STATE]")
        print(f"Topic: {state['topic']}")

        print("\n[EXECUTING SCIENTIST...]")
        result = run_scientist(state)

        print("\n[RESULT]")
        print(f"Draft length: {len(result['draft'])} characters")
        print(result['draft'][:500] + "...")

        print("\n✓ Scientist can work without RAG results (fallback mode)")


def main():
    """메인 실행 함수"""
    try:
        # Test 1: Mock RAG로 통합 테스트
        demo_with_mock_rag()

        # Test 2: RAG 없이 기본 동작 확인
        demo_without_rag()

        print("\n" + "=" * 80)
        print("ALL DEMOS COMPLETED")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
