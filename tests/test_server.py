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
