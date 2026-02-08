# @TASK P3-R1-T1 - FastAPI 서버 테스트
# @SPEC TASKS.md#P3-R1-T1
"""FastAPI 서버 테스트"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


@pytest.fixture
def client():
    """TestClient fixture"""
    from server import app
    return TestClient(app)


class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트"""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/health")
        assert response.json() == {"status": "ok"}


class TestResearchEndpoint:
    """연구 워크플로우 엔드포인트 테스트"""

    @patch("server.create_workflow")
    def test_research_returns_200(self, mock_workflow, client):
        # Mock workflow
        mock_wf = Mock()
        mock_wf.invoke.return_value = {
            "topic": "NGT",
            "constraints": "",
            "draft": "draft text",
            "critique": None,
            "iteration": 0,
            "final_report": "# final report",
            "messages": [{"role": "pi", "content": "done"}],
        }
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research",
            json={"topic": "NGT evaluation", "constraints": "rational regulation"}
        )
        assert response.status_code == 200

    @patch("server.create_workflow")
    def test_research_returns_report(self, mock_workflow, client):
        mock_wf = Mock()
        mock_wf.invoke.return_value = {
            "final_report": "# report",
            "messages": [],
            "iteration": 0,
        }
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research",
            json={"topic": "NGT", "constraints": ""}
        )
        data = response.json()
        assert "report" in data
        assert data["report"] == "# report"

    @patch("server.create_workflow")
    def test_research_returns_messages(self, mock_workflow, client):
        mock_wf = Mock()
        mock_wf.invoke.return_value = {
            "final_report": "# report",
            "messages": [{"role": "pi", "content": "done"}],
            "iteration": 1,
        }
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research",
            json={"topic": "NGT", "constraints": ""}
        )
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 1

    @patch("server.create_workflow")
    def test_research_returns_iterations(self, mock_workflow, client):
        mock_wf = Mock()
        mock_wf.invoke.return_value = {
            "final_report": "# report",
            "messages": [],
            "iteration": 2,
        }
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research",
            json={"topic": "NGT", "constraints": ""}
        )
        data = response.json()
        assert "iterations" in data
        assert data["iterations"] == 2

    def test_research_requires_topic(self, client):
        response = client.post("/api/research", json={})
        assert response.status_code == 422  # Validation error


class TestStreamEndpoint:
    """SSE 스트리밍 엔드포인트 테스트 (P4-T4)"""

    @patch("server.create_workflow")
    def test_stream_returns_200(self, mock_workflow, client):
        """스트림 엔드포인트가 200을 반환하는지 테스트"""
        mock_wf = Mock()
        mock_wf.stream.return_value = iter([
            {"drafting": {"draft": "test draft", "iteration": 0}},
            {"critique": {"critique": Mock(decision="approve", feedback="good"), "iteration": 0}},
            {"finalizing": {"final_report": "# Final Report", "iteration": 0}},
        ])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT evaluation", "constraints": ""}
        )
        assert response.status_code == 200

    @patch("server.create_workflow")
    def test_stream_returns_event_stream(self, mock_workflow, client):
        """스트림 엔드포인트가 text/event-stream을 반환하는지 테스트"""
        mock_wf = Mock()
        mock_wf.stream.return_value = iter([])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT", "constraints": ""}
        )
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch("server.create_workflow")
    def test_stream_sends_start_event(self, mock_workflow, client):
        """스트림이 시작 이벤트를 전송하는지 테스트"""
        mock_wf = Mock()
        mock_wf.stream.return_value = iter([])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT", "constraints": ""}
        )

        content = response.text
        assert "data: " in content
        assert '"type": "start"' in content
        assert '"topic": "NGT"' in content

    @patch("server.create_workflow")
    def test_stream_sends_complete_event(self, mock_workflow, client):
        """스트림이 완료 이벤트를 전송하는지 테스트"""
        mock_wf = Mock()
        mock_wf.stream.return_value = iter([
            {"finalizing": {
                "final_report": "# Report",
                "iteration": 0,
                "messages": []
            }}
        ])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT", "constraints": ""}
        )

        content = response.text
        assert '"type": "complete"' in content
        assert '"report": "# Report"' in content

    @patch("server.create_workflow")
    def test_stream_sends_agent_events(self, mock_workflow, client):
        """스트림이 에이전트별 이벤트를 전송하는지 테스트"""
        mock_critique = Mock()
        mock_critique.decision = "approve"
        mock_critique.feedback = "Good work"

        mock_wf = Mock()
        mock_wf.stream.return_value = iter([
            {"drafting": {"draft": "draft", "iteration": 0}},
            {"critique": {"critique": mock_critique, "iteration": 0}},
        ])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT", "constraints": ""}
        )

        content = response.text
        # Scientist 이벤트 확인
        assert '"agent": "scientist"' in content
        # Critic 이벤트 확인
        assert '"agent": "critic"' in content

    @patch("server.create_workflow")
    def test_stream_sends_progressive_chunks(self, mock_workflow, client):
        """스트림이 점진적으로 청크를 전송하는지 테스트"""
        mock_critique = Mock()
        mock_critique.decision = "revise"
        mock_critique.feedback = "Needs improvement"

        mock_wf = Mock()
        mock_wf.stream.return_value = iter([
            {"drafting": {"draft": "draft1", "iteration": 0}},
            {"critique": {"critique": mock_critique, "iteration": 0}},
            {"increment": {"iteration": 1}},
            {"drafting": {"draft": "draft2", "iteration": 1}},
        ])
        mock_workflow.return_value = mock_wf

        response = client.post(
            "/api/research/stream",
            json={"topic": "NGT", "constraints": ""}
        )

        content = response.text
        # 여러 이벤트가 전송되었는지 확인
        event_count = content.count("data: ")
        assert event_count >= 4  # start + drafting + critique + increment
